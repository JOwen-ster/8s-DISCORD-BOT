import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed
from utils.embeds import createEmbedFields
from utils.logging_setup import getlog


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='post', description='Create a embed with your own fields')
    @app_commands.describe(title='Title',
        date='Insert a date as MM/DD/YY',
        time='Insert a time as XX:XXam/pm using a 12-hour clock',
        details='Insert a description',
        location='Location of reminder (optional)'
    )
    async def createPost(self, interaction: discord.Interaction,
                        title: str, 
                        date: str, 
                        time: str,
                        details: str,
                        location: str = "N/A"
    ):
        if interaction.user.id != interaction.guild.owner_id:
            return
        embed = createEmbedFields(embed_title=title,
                            date=date,
                            time=time,
                            details=details,
                            location=location
        )
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(
            embed=BotConfirmationEmbed(description='Sent'),
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Test(bot))
