import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed
from utils.loggingsetup import getlog


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='Online', description='Create a embed with your own fields')
    async def createPost(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=BotConfirmationEmbed(description='Online'),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
