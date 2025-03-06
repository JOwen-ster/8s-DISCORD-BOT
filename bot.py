import discord
from discord.ui import Select, View
from discord.ext import commands
import random
from collections import defaultdict
from dotenv import load_dotenv
import os
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

description = '8s Private Battle Bot'

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='^', description=description, intents=intents)

class GameState:
    def __init__(self, creator_id):
        self.creator_id: int = creator_id
        self.players: list[discord.Member] = []
        self.backlines: list[discord.Member] = []
        self.supports: list[discord.Member] = []
        self.slayers: list[discord.Member] = []
        self.lobby_category: discord.CategoryChannel = None
        self.rules_channel: discord.TextChannel = None
        self.alpha_channel: discord.VoiceChannel = None
        self.bravo_channel: discord.VoiceChannel = None
        self.lobby_channel: discord.VoiceChannel = None
# Each guild has its own unique id which is associated with a list of players, each guild has 1 unique game at a time
# "data" "base"
# instead each creators id's value being a dict, it should be an object
stored_games: dict[int, dict[int, list[discord.Member]]] = defaultdict(
    lambda: defaultdict(
        lambda: {'players': [], 'split-roles': []}
        )
    )
game_states = defaultdict(lambda: defaultdict(GameState))

# MIGRATE TO THIS
# games_states = {
#     12345: {67890: object},
#     ...
# }

# stored_games = {
#     guild_id: {
#         'game_id': object
#         ...
#     },
#     ...
# }

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Check if the user joined 'Lobby-Create'
    current_guild = member.guild
    if after.channel and after.channel.name == 'Lobby-Create':
        
        if any(member.id in game_states[guild_id] for guild_id in game_states):
            await member.send(embed=discord.Embed(title='You currently have a lobby created, please empty it.', color=discord.Color.red()))
            await member.move_to(None)
            return
        
        # Create the new category and channels
        created_category = await current_guild.create_category(name=f'8s-{member.id}')
        rules_channel = await created_category.create_text_channel(name='rules-8s')

        # Set permissions for the rules channel
        overwrite = discord.PermissionOverwrite(send_messages=False)
        await rules_channel.set_permissions(current_guild.default_role, overwrite=overwrite)

        # Create and send an embed with rules
        rules_embed = discord.Embed(
            title='Rules',
            description='2 Teams of 4 players are created. There are 2 backlines, 2 supports, and 4 slayers. Each team will have 1 backline, 1 support, and 2 slayers. Once teams are randomly created, play a best of 3 or 5 with those teams. Once the set is over, the supports will be swapped and the slayers for each team will randomly be re-assigned.',
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        await rules_channel.send(embed=rules_embed)

        # Create voice channels
        await created_category.create_voice_channel(name='Lobby-8s', user_limit=8)
        await created_category.create_voice_channel(name='Alpha-8s', user_limit=4)
        await created_category.create_voice_channel(name='Bravo-8s', user_limit=4)

        # Move the member to the newly created 'Lobby-8s' voice channel
        lobby_channel = discord.utils.get(created_category.voice_channels, name='Lobby-8s')
        if lobby_channel:
            await member.move_to(lobby_channel)

    # Check if the user left a category starting with '8s-' and delete it if empty
    if before.channel and before.channel.category and before.channel.category.name.startswith('8s-'):
        category = before.channel.category
        voice_channels = category.voice_channels

        # Check if all voice channels in the category are empty
        if all(len(vc.members) == 0 for vc in voice_channels):
            for channel in category.channels:
                await channel.delete()
            await category.delete()
            del game_states[category.guild.id][member.id]


def get_category(interaction: discord.Interaction):
    return discord.utils.get(interaction.guild.categories, name=f'8s-{interaction.user.id}')


# TODO
# Create a category that has a 1 voice channel called Lobby-Create
# joining this voice channel will create a category called 8s-{creator-id}
# this category will have 3 voice channels called Alpha-8s, Bravo-8s, and Lobby-8s
# create a text channel called rules-8s
# create a text channel called chat-8s
@bot.tree.command(name='setup')
async def setup_channels(interaction: discord.Interaction):
    bot_category = await interaction.guild.create_category(name='Bot-8s')
    await bot_category.create_voice_channel(name='Lobby-Create', user_limit=1)


class Dropdown(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Backline player", description="", value="backline"),
            discord.SelectOption(label="Support player", description="", value="support"),
            discord.SelectOption(label="Slayer player", description="", value="slayer"),
        ]
        super().__init__(placeholder="Choose one option...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.user.add_roles(discord.utils.get(interaction.guild.roles, name=self.values[0]))
        except discord.errors.Forbidden:
            await interaction.response.send_message(f"I do not have permission to give {interaction.user.mention} the role {self.values[0]}", ephemeral=True)
        await interaction.response.send_message(f"You selected: {self.values[0]}", ephemeral=True)


class DropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())


@bot.tree.command(name='set-role')
async def set_role(interaction: discord.Interaction):
    await interaction.response.send_message("Select an option:", view=DropdownView(), ephemeral=True)


@bot.tree.command(name='remove-role')
async def remove_role(interaction: discord.Interaction):
    removed_roles = []
    for role in interaction.user.roles:
        try:
            if role.name in ['backline', 'support', 'slayer']:
                await interaction.user.remove_roles(role)
                removed_roles.append(role.name)
        except discord.errors.Forbidden:
            await interaction.response.send_message(f"I do not have permission to remove {role.name}, skipping...", ephemeral=True)
            pass

    await interaction.response.send_message(f"I removed the following roles: {', '.join(removed_roles)}", ephemeral=True) if removed_roles else await interaction.response.send_message("You do not have any roles to remove", ephemeral=True)


# TODO
# Posssibly have it so when starting a game, 8 dropdowns (linked to the 8 people currently in the lobby channel) appear that will each ask for a members player role
# Also lock the lobby channel so only the players can join
# Create a way to leave a game and have the roles removed from the user
# Create a way to end a game, remove the roles from the users, and remove the creator's user id from the stored_games
# Delete that ended games category

# could make a generator channel
# creates a category with 3 voice channels and 1 text channel
# auto delete the 8s-user.id categrory along with its children channels
#after no memebers are in any of the voice channels
@bot.tree.command(name='start-8s')
async def start_8s(interaction: discord.Interaction):
    await interaction.response.defer()
    find_category = get_category(interaction)
    if find_category:
        lobby_count = len(discord.utils.get(find_category.voice_channels, name='Lobby-8s').members)
        print(lobby_count)
        # if lobby_count < 8:
        #     await interaction.followup.send_message(embed=discord.Embed(title='Not enough players', color=discord.Color.red()), ephemeral=False)
        # else:
        for guild in bot.guilds:
            if discord.utils.get(guild.categories, name=f'8s-{interaction.user.id}'):
                await interaction.followup.send_message(embed=discord.Embed(title='You are already in a game', color=discord.Color.red()), ephemeral=False)
                return

        game_states[interaction.guild.id][interaction.user.id] = GameState(interaction.user.id)
        lobby = discord.utils.get(find_category.voice_channels, name='Lobby-8s').members
        game_states[interaction.guild.id][interaction.user.id].players = lobby
        game_states[interaction.guild.id][interaction.user.id].category = find_category
        game_states[interaction.guild.id][interaction.user.id].rules_channel = discord.utils.get(find_category.text_channels, name='rules-8s')
        game_states[interaction.guild.id][interaction.user.id].alpha_channel = discord.utils.get(find_category.voice_channels, name='Alpha-8s')
        game_states[interaction.guild.id][interaction.user.id].bravo_channel = discord.utils.get(find_category.voice_channels, name='Bravo-8s')
        game_states[interaction.guild.id][interaction.user.id].lobby_channel = discord.utils.get(find_category.voice_channels, name='Lobby-8s')
        current_state = game_states[interaction.guild.id][interaction.user.id]
        role_mapping = {
            "backline": [],
            "support": [],
            "slayer": []
        }       
        for member in lobby:
            for role_name in role_mapping:
                if any(role.name == role_name for role in member.roles):
                    role_mapping[role_name].append(member)

        # Separate members by roles
        current_state.backlines = role_mapping["backline"]
        current_state.supports = role_mapping['support']
        current_state.slayers = role_mapping["slayer"]

        # Ensure correct role distribution
        if len(current_state.backlines) != 2 or len(current_state.supports) != 2 or len(current_state.slayers) != 4:
            await interaction.response.send_message("Invalid role distribution. Make sure there are exactly 2 backlines, 2 supports, and 4 slayers.")
            return

        # Shuffle and assign teams
        random.shuffle(current_state.slayers)  # Randomize slayers

        team_alpha = [current_state.backlines.pop(), current_state.supports.pop(), current_state.slayers.pop(), current_state.slayers.pop()]
        team_bravo = [current_state.backlines.pop(), current_state.supports.pop(), current_state.slayers.pop(), current_state.slayers.pop()]

        # Move players to their respective teams
        for member in team_alpha:
            await member.move_to(current_state.alpha_channel)
        for member in team_bravo:
            await member.move_to(current_state.bravo_channel)

        print(stored_games)
        teamsEmbed = discord.Embed(title='Teams', color=discord.Color.black())
        teamsEmbed.add_field(name='Alpha Backline', value=team_alpha[0].name, inline=True)
        teamsEmbed.add_field(name='Alpha Support', value=team_alpha[1].name, inline=True)
        teamsEmbed.add_field(name='Alpha Slayers', value=team_alpha[2].name + ' and ' + team_alpha[3].name, inline=True)
        teamsEmbed.add_field(name='Bravo Backline', value=team_bravo[0].name, inline=True)
        teamsEmbed.add_field(name='Bravo Support', value=team_bravo[1].name, inline=True)
        teamsEmbed.add_field(name='Bravo Slayers', value=team_bravo[2].name + ' and ' + team_bravo[3].name, inline=True)
        await interaction.followup.send(embed=teamsEmbed)
    else:
        await interaction.followup.send(embed=discord.Embed(title='Setup category "Bot-8s" not found', color=discord.Color.red()), ephemeral=True)


# optimize to only drag players who are in a team channel, if there are no players in a alpha or bravo channel, then skip that channel
@bot.tree.command(name='drag-players')
async def drag_players(interaction: discord.Interaction):
    await interaction.response.defer()
    category = get_category(interaction)
    if category:
        for member in discord.utils.get(category.voice_channels, name='Alpha-8s').members:
            await member.move_to(discord.utils.get(category.voice_channels, name='Lobby-8s'))
        for member in discord.utils.get(category.voice_channels, name='Bravo-8s').members:
            await member.move_to(discord.utils.get(category.voice_channels, name='Lobby-8s'))
        await interaction.followup.send(embed=discord.Embed(title='Players dragged', color=discord.Color.green()), ephemeral=False)
    else:
        await interaction.followup.send(embed=discord.Embed(title='Setup category "Bot-8s" not found or there are no players for a team', color=discord.Color.red()), ephemeral=True)


@bot.tree.command(name='delete-setup')
async def delete_setup(interaction: discord.Interaction):
    found_setup_category = get_category(interaction)
    if found_setup_category:
        for channel in found_setup_category.channels:
            try:
                await channel.delete()
            except discord.errors.Forbidden:
                await interaction.response.send_message(f'I do not have permission to delete {channel.name}, skipping...', ephemeral=True)
                pass
        try:
            await found_setup_category.delete()
        except discord.errors.Forbidden: 
            await interaction.response.send_message(f'I do not have permission to delete {found_setup_category.name}', ephemeral=True)
        await interaction.response.send_message(embed=discord.Embed(title='Setup deleted', color=discord.Color.green()), ephemeral=False)
    else:
        await interaction.response.send_message(embed=discord.Embed(title='Setup category "Bot-8s" not found', color=discord.Color.red()), ephemeral=True)


@bot.tree.command(name='shuffle')
async def shuffle(interaction: discord.Interaction):
    await interaction.response.defer()
    await drag_players(interaction)
    await interaction.followup.send(embed=discord.Embed(title='Shuffle complete', color=discord.Color.green()), ephemeral=False)


@bot.tree.command(name='export-members')
async def dm_typos(interaction: discord.Interaction):
    await interaction.response.defer()
    for member in interaction.guild.members:
        await interaction.user.send(f'{member.name}, {member.id}')
    await interaction.followup.send(embed=discord.Embed(title='Exported members', color=discord.Color.green()), ephemeral=False)


# Maybe have it so only the people the in vc are randomly selected
bot.run(DISCORD_BOT_TOKEN)
