import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed
from utils.loggingsetup import getlog


class EightsGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
async def setup(bot):
    await bot.add_cog(EightsGame(bot))
