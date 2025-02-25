
# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import random
from dotenv import load_dotenv
import os
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

description = '8s Private Battle Bot'

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='^', description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.tree.sync()
    print('------')

@bot.tree.command(name='setup')
async def setup_channels(interaction: discord.Interaction):
    set_category = await interaction.guild.create_category(name='8s')
    await set_category.create_text_channel(name='8s-chat')
    await set_category.create_voice_channel(name='Alpha')
    await set_category.create_voice_channel(name='Bravo')
    await interaction.response.send_message('Setup!')


bot.run(DISCORD_BOT_TOKEN)
