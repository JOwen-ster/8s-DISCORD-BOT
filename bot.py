import discord
from discord.ui import Select, View, Button
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
# Users are able to generate a lobby using a generator voice channel
# Other users can fil up the lobby 
# when the lobby has 8 people, it can then be started using /start-8s
# If the game is started, the game can be ended using /end-8s or the button on the view
# If a game is started, do not allow users in that started game to generate or join a new lobby/team channel
# Add a /leave game command, this will drag everyone back to the lobby
#set the state to not started, reset the lists, removes game roles from leaver
#if the creator leaves, delete the game state and category
# LOCK ALPHA AND BRAVO CHANNELS SO USERS CAN ONLY JOIN BY BEING MOVED BY THE BOT
ENV_DEBUG = True


class GameView(View):
    def __init__(self):
        super().__init__()
        self.shuffle_button = None
        self.end_button = None

    @discord.ui.button(label="Shuffle", style=discord.ButtonStyle.blurple)
    async def shuffle(self, interaction: discord.Interaction, button: Button):
        self.shuffle_button = button
        await interaction.response.send_message("Shuffling the game!", ephemeral=True)
        # call shuffle method

    @discord.ui.button(label="End Game", style=discord.ButtonStyle.danger)
    async def end_game(self, interaction: discord.Interaction, button: Button):
        self.end_button = button
        for child in self.children:
            child.disabled = True  # Disable buttons after ending the game
        await interaction.response.edit_message(content="Game Over!", view=self)

class GameState:
    def __init__(self, creator_id: int=None):
        self.creator_id: int = creator_id
        self.players: list[discord.Member] = []
        self.backlines: list[discord.Member] = []
        self.supports: list[discord.Member] = []
        self.slayers: list[discord.Member] = []
        self.alpha_team: list[discord.Member] = []
        self.bravo_team: list[discord.Member] = []
        self.lobby_category: discord.CategoryChannel = None
        self.rules_channel: discord.TextChannel = None
        self.alpha_channel: discord.VoiceChannel = None
        self.bravo_channel: discord.VoiceChannel = None
        self.lobby_channel: discord.VoiceChannel = None
        self.isStarted: bool = False
        self.game_embed: discord.Embed = None
        self.controls: discord.ui.View = None
# Each guild has its own unique id which is associated with a list of players, each guild has 1 unique game at a time
# "data" "base"
# instead each creators id's value being a dict, it should be an object

game_states = defaultdict(lambda: defaultdict(GameState))

# MIGRATE TO THIS
# games_states = {
#     12345: {67890: object},
#     ...
# }

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    # Check if the user joined 'Lobby-Create'
    # if user has a category and lobby channel, drag them to their lobby
    # if user starts a game, do not allow them to join another game
    current_guild = member.guild
    if after.channel and after.channel.name == 'Lobby-Create':
        # TODO
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
        # /start will only work in this channel
        await created_category.create_text_channel(name='Chat-8s')
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
            if any(member.id in game_states[guild_id] for guild_id in game_states):
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
    await interaction.response.defer()
    target_roles = set("backline", "support", "slayer")
    user_roles = [role for role in interaction.user.roles if role.name in target_roles]

    if not user_roles:
        await interaction.response.send_message("You do not have any roles to remove", ephemeral=True)
        return

    removed_roles = []
    for role in user_roles:
        try:
            await interaction.user.remove_roles(role)
            removed_roles.append(role.name)
        except discord.Forbidden:
            await interaction.followup.send(
                f"I do not have permission to remove {role.name}, skipping...",
                ephemeral=True
            )

    await interaction.response.send_message(
        f"I removed the following roles: {', '.join(removed_roles)}", ephemeral=True
    )


@bot.tree.command(name='leave-8s')
async def leave_8s(interaction: discord.Interaction):
    if interaction.user in game_states[interaction.guild.id][interaction.user.id].players:
        game_states[interaction.guild.id][interaction.user.id].players.remove(interaction.user)
        await interaction.response.send_message(embed=discord.Embed(title='You left the game', color=discord.Color.green()), ephemeral=False)
    else:
        await interaction.response.send_message(embed=discord.Embed(title='You are not in a started game', color=discord.Color.red()), ephemeral=False)


# TODO
# Posssibly have it so when starting a game, 8 dropdowns (linked to the 8 people currently in the lobby channel) appear that will each ask for a members player role
# Lock lobby, alpha, and bravo channels so only the players can join
# Create a way to leave a game and have the roles removed from the user
# Create a way to end a game, remove the roles from all the users, and remove the creator's user id from the game_states
# If a member is in a lobby, then that lobby gets started, do not allow them to join another lobby or create one until they leave that game
@bot.tree.command(name='start-8s')
async def start_8s(interaction: discord.Interaction):
    await interaction.response.defer()
    find_category = get_category(interaction)
    if find_category:
        current_lobby_obj = discord.utils.get(find_category.voice_channels, name='Lobby-8s')
        if current_lobby_obj and current_lobby_obj.members:
            current_lobby_count = len(current_lobby_obj.members)
        else:
            await interaction.followup.send_message(embed=discord.Embed(title='Not enough players', color=discord.Color.red()), ephemeral=False)
            return
        if not ENV_DEBUG:
            if current_lobby_count < 8:
                await interaction.followup.send_message(embed=discord.Embed(title='Not enough players', color=discord.Color.red()), ephemeral=False)
                return
            elif interaction.user not in current_lobby_obj.members:
                await interaction.followup.send_message(embed=discord.Embed(title=f'{interaction.user.mention} is in the lobby', color=discord.Color.red()), ephemeral=False)
                return
            if any(discord.utils.get(guild.categories, name=f'8s-{interaction.user.id}') for guild in bot.guilds):
                await interaction.followup.send_message(
                    embed=discord.Embed(
                        title='You currently have an outstanding game category created, please end it or have everyone leave',
                        color=discord.Color.red()
                    ),
                    ephemeral=False
                )
                return

        game_states[interaction.guild.id][interaction.user.id] = GameState(interaction.user.id)
        current_state = game_states[interaction.guild.id][interaction.user.id]
        lobby = discord.utils.get(find_category.voice_channels, name='Lobby-8s').members
        current_state.players = lobby
        current_state.category = find_category
        current_state.rules_channel = discord.utils.get(find_category.text_channels, name='rules-8s')
        current_state.alpha_channel = discord.utils.get(find_category.voice_channels, name='Alpha-8s')
        current_state.bravo_channel = discord.utils.get(find_category.voice_channels, name='Bravo-8s')
        current_state.lobby_channel = discord.utils.get(find_category.voice_channels, name='Lobby-8s')
        current_state.controls = GameView()
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
        current_state.controls.alpha_team = team_alpha
        current_state.controls.bravo_team = team_bravo
        # Move players to their respective teams
        for member in team_alpha:
            await member.move_to(current_state.alpha_channel)
        for member in team_bravo:
            await member.move_to(current_state.bravo_channel)

        teamsEmbed = discord.Embed(title='Teams', color=discord.Color.black())
        teamsEmbed.add_field(name='Alpha Backline', value=team_alpha[0].name, inline=True)
        teamsEmbed.add_field(name='Alpha Support', value=team_alpha[1].name, inline=True)
        teamsEmbed.add_field(name='Alpha Slayers', value=team_alpha[2].name + ' and ' + team_alpha[3].name, inline=True)
        teamsEmbed.add_field(name='Bravo Backline', value=team_bravo[0].name, inline=True)
        teamsEmbed.add_field(name='Bravo Support', value=team_bravo[1].name, inline=True)
        teamsEmbed.add_field(name='Bravo Slayers', value=team_bravo[2].name + ' and ' + team_bravo[3].name, inline=True)
        current_state.game_emebed = teamsEmbed
        await interaction.followup.send(embed=current_state.game_emebed, view=current_state.controls, ephemeral=False)
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


@bot.tree.command(name='end-8s')
async def end_8s(interaction: discord.Interaction):
    await interaction.response.defer()
    creator = interaction.user
    await drag_players(interaction)
    creator_lobby = game_states[interaction.guild.id][creator.id].lobby_channel
    for member in creator_lobby.members:
        await member.move_to(None)
    await interaction.followup.send(embed=discord.Embed(title='8s game ended', color=discord.Color.green()), ephemeral=False)

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

# take in user and then lookup the game state and shuffle the players
async def shuffle(interaction: discord.Interaction):
    await interaction.response.defer()
    creator_state = game_states[interaction.guild.id][interaction.user.id]
    await interaction.followup.send(embed=discord.Embed(title='Shuffle complete', color=discord.Color.green()), ephemeral=False)


@bot.tree.command(name='export-members')
async def dm_typos(interaction: discord.Interaction):
    await interaction.response.defer()
    for member in interaction.guild.members:
        await interaction.user.send(f'{member.name}, {member.id}')
    await interaction.followup.send(embed=discord.Embed(title='Exported members', color=discord.Color.green()), ephemeral=False)


# Maybe have it so only the people the in vc are randomly selected
bot.run(DISCORD_BOT_TOKEN)
