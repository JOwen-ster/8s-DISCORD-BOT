import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed, FullTeamsEmbed
from utils.loggingsetup import getlog


class EightsGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-start')
    async def start_users_eights_game(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotConfirmationEmbed(description='Starting...'), ephemeral=True)
        await interaction.channel.send(embed=FullTeamsEmbed())
        await interaction.followup.send(embed=BotConfirmationEmbed(description='✅Started!'), ephemeral=True)
        # check db to see if user has a category (already in a started game)
        # use interaction.guild.id, if a user runs the start command in a different server
        #that isnt where you are grouping in, tell them to use it in the correct corresponding server
        # Check if the lobby vc is full (8 players)
        # Send blank embed (will be edited) to chat
        # Add details to db for both games and players tables
        # Set voice calls limited to 10 6 and 6 for specs
        # Create teams from lobby vc (people can leave vc after since info on who is playing is now stored)
        # Edit embed with teams
        # Attach shuffle button view with end game button
        pass
async def setup(bot):
    await bot.add_cog(EightsGame(bot))
