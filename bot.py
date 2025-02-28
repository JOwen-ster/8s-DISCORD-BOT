import discord
from discord.ui import Select, View
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

description = '8s Private Battle Bot'

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='^', description=description, intents=intents)

# Each guild has its own unique id which is associated with a list of players, each guild has 1 unique game at a time
stored_games: dict[int, dict[str, list[str]]] = {}

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

def get_category(interaction: discord.Interaction):
    return discord.utils.get(interaction.guild.categories, name='Bot-8s')

@bot.tree.command(name='setup')
async def setup_channels(interaction: discord.Interaction):
    global bot
    if get_category(interaction):
        await interaction.response.send_message(embed=discord.Embed(title='Setup category "Bot-8s" already exists', color=discord.Color.red()), ephemeral=True)
        return
    set_category = await interaction.guild.create_category(name='Bot-8s')
    rules_channel = await set_category.create_text_channel(name='rules-8s')
    rules_embed = discord.Embed(
            title='Rules',
            description='2 Teams of 4 players are created. There are 2 backlines, 2 supports, and 4 slayers. Each team will have 1 backline, 1 support, and 2 slayers. Once teams are randomly created, play a best of 3 or 5 with those teams. Once the set is over, the supports will be swapped and the slayers for each team will randomly be re-assigned.',
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
    )
    rules_embed.set_author(name=bot.user.name)
    rules_embed.set_footer(text='end of rules')
    await rules_channel.send(embed=rules_embed)
    overwrite = discord.PermissionOverwrite(send_messages=False)
    await rules_channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)

    await set_category.create_text_channel(name='chat-8s')
    await set_category.create_voice_channel(name='Lobby-8s', user_limit=8)
    await set_category.create_voice_channel(name='Alpha-8s', user_limit=4)
    await set_category.create_voice_channel(name='Bravo-8s', user_limit=4)
    await interaction.response.send_message(embed=discord.Embed(title='Setup complete', color=discord.Color.green()), ephemeral=False)

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
        stored_games[interaction.guild.id] = [
            member.id for member in
            discord.utils.get(find_category.voice_channels, name='Lobby-8s').members
        ]
        print(stored_games)
        await interaction.followup.send(embed=discord.Embed(title=f'8s started in {find_category.name}', color=discord.Color.green()), ephemeral=False)
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


@bot.tree.command(name='export-members')
async def dm_typos(interaction: discord.Interaction):
    await interaction.response.defer()
    for member in interaction.guild.members:
        await interaction.user.send(f'{member.name}, {member.id}')

    await interaction.followup.send(embed=discord.Embed(title='Exported members', color=discord.Color.green()), ephemeral=False)


# Maybe have it so only the people the in vc are randomly selected
bot.run(DISCORD_BOT_TOKEN)
