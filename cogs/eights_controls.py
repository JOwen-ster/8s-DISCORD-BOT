import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed, BotMessageEmbed, BotErrorEmbed
import db.operations
from utils.logging_setup import getlog


class Controls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-teams', description='Link to the current teams')
    async def jump_to_teams(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotMessageEmbed(description='Finding your 8s session...'))
        teams_message_id = await db.operations.get_team_message_id(self.bot.db_pool, interaction.user.id)
        if teams_message_id:
            message = await self.bot.user.fetch_message(teams_message_id)
            return await interaction.followup.send(BotConfirmationEmbed(
                title='Current teams',
                description=f'https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}')
            )
        return await interaction.followup.send(embed=BotErrorEmbed(descrption='Could not find your 8s session...'))

    @app_commands.command(name='8s-end', description='End your current 8s session.')
    async def end_session(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotMessageEmbed(description='Ending your session...'))
        isDeleted, teams_message_id = await db.operations.delete_game_if_host(self.bot.db_pool, interaction.user.id)
        if isDeleted:
            message = await self.bot.user.fetch_message(teams_message_id)
            await message.delete()
            return await interaction.response.send_message(embed=BotConfirmationEmbed(description='Session Ended.'))
        return await interaction.response.send_message(embed=BotErrorEmbed(description='You must be the host to end a session.'))

async def setup(bot):
    await bot.add_cog(Controls(bot))
