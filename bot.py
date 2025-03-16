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
        if not self.isStarted:
            await interaction.response.send_message("The game cant not be continued, most likely not enough players", ephemeral=True)
            return
        # TODO CHECK IF THEIR ARE STILL 8 PLAYERS IN .players when shuffling, if not or their are not 8 players in the channels, do not shuffle
        self.shuffle_button = button
    
        # Reference the current game state
        game_state = game_states[interaction.guild.id][interaction.user.id]
    
        # Swap support players
        game_state.alpha_team['support_a'], game_state.bravo_team['support_b'] = (
            game_state.bravo_team['support_b'], 
            game_state.alpha_team['support_a']
        )
    
        # Shuffle slayers
        random.shuffle(game_state.slayers)
    
        # Reassign slayers to teams
        game_state.alpha_team['slayers_a'] = game_state.slayers[0]
        game_state.alpha_team['slayers_a2'] = game_state.slayers[1]
        game_state.bravo_team['slayers_b'] = game_state.slayers[2]
        game_state.bravo_team['slayers_b2'] = game_state.slayers[3]
    
        # Update the embed with new team information
        new_embed = discord.Embed(title='Teams', color=discord.Color.blurple())
        new_embed.add_field(name='Alpha Backline', value=game_state.alpha_team['backline_a'].nick, inline=True)
        new_embed.add_field(name='Alpha Support', value=game_state.alpha_team['support_a'].nick, inline=True)
        new_embed.add_field(name='Alpha Slayers', value=game_state.alpha_team['slayers_a'].nick + ' and ' + game_state.alpha_team['slayers_a2'].nick, inline=True)
        new_embed.add_field(name='Bravo Backline', value=game_state.bravo_team['backline_b'].nick, inline=True)
        new_embed.add_field(name='Bravo Support', value=game_state.bravo_team['support_b'].nick, inline=True)
        new_embed.add_field(name='Bravo Slayers', value=game_state.bravo_team['slayers_b'].nick + ' and ' + game_state.bravo_team['slayers_b2'].nick, inline=True)
    
        # Save updated embed in game state
        game_state.game_embed = new_embed

        for player in game_state.alpha_team.values():
            await player.move_to(game_state.alpha_channel)
        for player in game_state.bravo_team.values():
            await player.move_to(game_state.bravo_channel)
    
        # Edit the original message instead of sending a new one
        await interaction.response.edit_message(embed=game_state.game_embed)
    
        await interaction.followup.send("Shuffling complete!", ephemeral=True)

    @discord.ui.button(label="End Game", style=discord.ButtonStyle.danger)
    async def end_game(self, interaction: discord.Interaction, button: Button):
        self.end_button = button
        for child in self.children:
            child.disabled = True  # Disable buttons after ending the game
        game_states[interaction.guild.id][interaction.user.id].isStarted = False
        await end_8s_game(guild_obj=interaction.guild, u_id=interaction.user.id)
        await interaction.response.edit_message(embed=discord.Embed(title="Game has ended", color=discord.Color.red()), view=self)

class GameState:
    def __init__(self, creator_id: int=None):
        self.creator_id: int = creator_id
        self.players: list[discord.Member] = []
        self.backlines: list[discord.Member] = []
        self.supports: list[discord.Member] = []
        self.slayers: list[discord.Member] = []
        self.alpha_team: dict[str:discord.Member] = {}
        self.bravo_team: dict[str:discord.Member] = {}
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
    role_names = ('8s', 'backline', 'support', 'slayer')
    guild_roles = [role.name for role in interaction.guild.roles]

    for role_name in role_names - guild_roles:  # Only create missing roles
        await interaction.guild.create_role(name=role_name)
        await interaction.send(f"Role '{role_name}' has been created.")

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
        guild = interaction.guild
        user = interaction.user
        target_roles = ("backline", "support", "slayer")
        user_roles = [role for role in interaction.user.roles if role.name in target_roles]

        if user_roles:
            await user.remove_roles(*user_roles)

        new_role = discord.utils.get(guild.roles, name=self.values[0])
        if new_role:
            try:
                await user.add_roles(new_role)
                await interaction.response.send_message(f"Your role has been updated to: {self.values[0]}", ephemeral=True)
            except discord.errors.Forbidden:
                await interaction.response.send_message(f"I do not have permission to assign the role {self.values[0]}", ephemeral=True)
        else:
            await interaction.response.send_message("The selected role does not exist.", ephemeral=True)


class DropdownView(View):
    def __init__(self):
        super().__init__()
        self.add_item(Dropdown())


@bot.tree.command(name='set-role')
async def set_role(interaction: discord.Interaction):
    await interaction.response.send_message("Select an option:", view=DropdownView(), ephemeral=True)

@bot.tree.command(name='leave-8s')
async def leave_8s(interaction: discord.Interaction):
    if interaction.user in game_states[interaction.guild.id][interaction.user.id].players:
        game_states[interaction.guild.id][interaction.user.id].players.remove(interaction.user)
        game_states[interaction.guild.id][interaction.user.id].isStarted = False # no longer 8 players
        await interaction.response.send_message(embed=discord.Embed(title='You left the game', color=discord.Color.green()), ephemeral=False)
    else:
        await interaction.response.send_message(embed=discord.Embed(title='You are not in a started game', color=discord.Color.red()), ephemeral=False)


async def end_8s_game(guild_obj: discord.Guild, u_id: int):
    for member in game_states[guild_obj.id][u_id].players:
        await member.move_to(None)
# TODO
# Posssibly have it so when starting a game, 8 dropdowns (linked to the 8 people currently in the lobby channel) appear that will each ask for a members player role
# Lock lobby, alpha, and bravo channels so only the players can join
# Create a way to leave a game and have the roles removed from the user
# Create a way to end a game, remove the roles from all the users, and remove the creator's user id from the game_states
# If a member is in a lobby, then that lobby gets started, do not allow them to join another lobby or create one until they leave that game
@bot.tree.command(name='start-8s')
async def start_8s(interaction: discord.Interaction):
    await interaction.response.defer()
    if game_states[interaction.guild.id][interaction.user.id].isStarted:
        await interaction.followup.send(embed=discord.Embed(title='Game is already started', color=discord.Color.red()), ephemeral=False)
        return

    find_category = get_category(interaction)
    if find_category:
        current_lobby_obj = discord.utils.get(find_category.voice_channels, name='Lobby-8s')
        current_lobby_count = 0
        if current_lobby_obj and len(current_lobby_obj.members) != 8:
            await interaction.followup.send_message(embed=discord.Embed(title='Not enough players', color=discord.Color.red()), ephemeral=False)
            return
        if not ENV_DEBUG:
            if current_lobby_count < 8:
                await interaction.followup.send_message(embed=discord.Embed(title='Not enough players', color=discord.Color.red()), ephemeral=False)
                return
            elif interaction.user not in current_lobby_obj.members:
                await interaction.followup.send_message(embed=discord.Embed(title=f'The creator {interaction.user.mention} is not in the lobby', color=discord.Color.red()), ephemeral=False)
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
        lobby = discord.utils.get(find_category.voice_channels, name='Lobby-8s').members
        game_states[interaction.guild.id][interaction.user.id].players = lobby
        game_states[interaction.guild.id][interaction.user.id].category = find_category
        game_states[interaction.guild.id][interaction.user.id].rules_channel = discord.utils.get(find_category.text_channels, name='rules-8s')
        game_states[interaction.guild.id][interaction.user.id].alpha_channel = discord.utils.get(find_category.voice_channels, name='Alpha-8s')
        game_states[interaction.guild.id][interaction.user.id].bravo_channel = discord.utils.get(find_category.voice_channels, name='Bravo-8s')
        game_states[interaction.guild.id][interaction.user.id].lobby_channel = discord.utils.get(find_category.voice_channels, name='Lobby-8s')
        game_states[interaction.guild.id][interaction.user.id].controls = GameView()

        role_mapping = {
            "backline": [],
            "support": [],
            "slayer": [],
        }
        for member in lobby:
            for role_name in role_mapping:
                if any(role.name == role_name for role in member.roles):
                    role_mapping[role_name].append(member)

        # Separate members by roles
        game_states[interaction.guild.id][interaction.user.id].backlines = role_mapping["backline"]
        game_states[interaction.guild.id][interaction.user.id].supports = role_mapping['support']
        game_states[interaction.guild.id][interaction.user.id].slayers = role_mapping["slayer"]
        print(game_states[interaction.guild.id][interaction.user.id].slayers)
        print(game_states[interaction.guild.id][interaction.user.id].backlines)
        print(game_states[interaction.guild.id][interaction.user.id].supports)
        current_state = game_states[interaction.guild.id][interaction.user.id]
        # Ensure correct role distribution
        if len(current_state.backlines) != 2 or len(current_state.supports) != 2 or len(current_state.slayers) != 4:
            await interaction.followup.send("Invalid role distribution. Make sure there are exactly 2 backlines, 2 supports, and 4 slayers.")
            return

        # Shuffle and assign teams
        random.shuffle(game_states[interaction.guild.id][interaction.user.id].slayers)  # Randomize slayers
        current_state = game_states[interaction.guild.id][interaction.user.id]
        team_alpha = {
            'backline_a': current_state.backlines.pop().nick,
            'support_a': current_state.supports.pop().nick,
            'slayer_a': current_state.slayers.pop().nick,
            'slayer_a2': current_state.slayers.pop().nick
        }
        team_bravo = {
            'backline_b': current_state.backlines.pop().nick,
            'support_b': current_state.supports.pop().nick,
            'slayer_b': current_state.slayers.pop().nick,
            'slayer_b2': current_state.slayers.pop().nick
        }
        game_states[interaction.guild.id][interaction.user.id].alpha_team = team_alpha
        game_states[interaction.guild.id][interaction.user.id].bravo_team = team_bravo

        # Move players to their respective teams
        for member in team_alpha:
            await member.move_to(current_state.alpha_channel)
        for member in team_bravo:
            await member.move_to(current_state.bravo_channel)

        teamsEmbed = discord.Embed(title='Teams', color=discord.Color.blurple())
        teamsEmbed.add_field(name='Alpha Backline', value=team_alpha[0].nick, inline=True)
        teamsEmbed.add_field(name='Alpha Support', value=team_alpha[1].nick, inline=True)
        teamsEmbed.add_field(name='Alpha Slayers', value=team_alpha[2].nick + ' and ' + team_alpha[3].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Backline', value=team_bravo[0].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Support', value=team_bravo[1].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Slayers', value=team_bravo[2].nick + ' and ' + team_bravo[3].nick, inline=True)

        teamsEmbed = discord.Embed(title='Teams', color=discord.Color.blurple())
        teamsEmbed.add_field(name='Alpha Backline', value=team_alpha['backline_a'].nick, inline=True)
        teamsEmbed.add_field(name='Alpha Support', value=team_alpha['support_a'].nick, inline=True)
        teamsEmbed.add_field(name='Alpha Slayers', value=team_alpha['slayer_a'].nick + ' and ' + team_alpha['slayer_a2'].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Backline', value=team_bravo['backline_b'].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Support', value=team_bravo['support_b'].nick, inline=True)
        teamsEmbed.add_field(name='Bravo Slayers', value=team_bravo['slayer_b'].nick + ' and ' + team_bravo['slayer_b2'].nick, inline=True)

        game_states[interaction.guild.id][interaction.user.id].game_embed = teamsEmbed
        game_states[interaction.guild.id][interaction.user.id].isStarted = True
        await interaction.followup.send(embed=game_states[interaction.guild.id][interaction.user.id].game_embed, view=game_states[interaction.guild.id][interaction.user.id].controls, ephemeral=False)
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
    for member in game_states[interaction.guild.id][interaction.user.id].players:
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


@bot.tree.command(name='export-members')
async def dm_typos(interaction: discord.Interaction):
    await interaction.response.defer()
    for member in interaction.guild.members:
        await interaction.user.send(f'{member.name}, {member.id}')
    await interaction.followup.send(embed=discord.Embed(title='Exported members', color=discord.Color.green()), ephemeral=False)


# Maybe have it so only the people the in vc are randomly selected
bot.run(DISCORD_BOT_TOKEN)
