import discord
from discord import app_commands
from discord.ext import commands
import db.operations
import db.checks
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed,FullTeamsEmbed
from utils.loggingsetup import getlog


class EightsGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-start')
    async def start_users_eights_game(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotConfirmationEmbed(description='Starting...'), ephemeral=True)
        await interaction.channel.send(embed=FullTeamsEmbed())
        await interaction.followup.send(embed=BotConfirmationEmbed(description='✅Started!'), ephemeral=True)
        # check db to see if user already in a started game
        # only hosts should be able top start
        # check if user id in players (account for categoeies being named the same name
        # like I make a lobby then have a friend join and I leave to use the generator again
        # but the first one to start will be added to players)
        if '8s-chat' != interaction.channel.name:
            return await interaction.followup.send(embed=BotErrorEmbed(
                description='Please run this command in a `8s-chat` text channel'),
                ephemeral=True
            )

        user_id = interaction.user.id
        response = db.checks.is_playing(self.bot.db_pool, user_id)
        if response:
            return await interaction.followup.send(embed=BotErrorEmbed(
                description='You must not be in a started game, please leave or end it.'),
                ephemeral=True
            )

        # check name of category and use the user id in that for the host
        guild = interaction.guild
        matched_category_name = f"8s_Game_{user_id}"
        category = discord.utils.get(guild.categories, name=matched_category_name)
        if not category:
            return await interaction.followup.send(embed=BotErrorEmbed(
                description='No 8s category with your user id found in this guild.'),
                ephemeral=True
            )

        chat_channel= discord.utils.get(category.text_channels, name="8s-chat")
        lobby_channel = discord.utils.get(category.voice_channels, name="8s-Lobby")
        alpha_channel = discord.utils.get(category.voice_channels, name="8s-Alpha")
        bravo_channel = discord.utils.get(category.voice_channels, name="8s-Bravo")
        chat_channel= discord.utils.get(category.text_channels, name="8s-chat")

        if not chat_channel:
            return await interaction.followup.send(
                embed=BotErrorEmbed(description="Your 8s-chat was not found."),
                ephemeral=True
            )

        if not lobby_channel:
            return await interaction.followup.send(
                embed=BotErrorEmbed(description="Your 8s-Lobby call was not found."),
                ephemeral=True
            )

        if interaction.user not in lobby_channel.members:
            return await interaction.followup.send(
                embed=BotErrorEmbed(
                    description="You must be inside your own 8s-Lobby voice channel to start the game."),
                ephemeral=True
            )

        if not alpha_channel:
            return await interaction.followup.send(
                embed=BotErrorEmbed(description="Your 8s-Alpha call was not found."),
                ephemeral=True
            )

        if not bravo_channel:
            return await interaction.followup.send(
                embed=BotErrorEmbed(description="Your 8s-Bravo call was not found."),
                ephemeral=True
            )

        if len(lobby_channel.members) != 8:
            return await interaction.followup.send(
                embed=BotErrorEmbed(description="The lobby must have exactly 8 players."),
                ephemeral=True
            )

        required_roles = {
            "8s-backline": 2,
            "8s-support": 2,
            "8s-slayer": 4,
        }

        role_count = {
            "8s-backline": 0,
            "8s-support": 0,
            "8s-slayer": 0,
        }
        current_lobby = []
        lobby_host = None

        for member in lobby_channel.members:
            for role in member.roles:
                if role.name in role_count:
                    role_count[role.name] += 1

                    if role_count[role.name] > required_roles[role.name]:
                        return await interaction.followup.send(
                            embed=BotErrorEmbed(
                                description=f"Too many members with {role.name} role in the lobby."),
                            ephemeral=True
                        )

            if member.id == user_id:
                lobby_host = member
            current_lobby.append(member)

        if required_roles == role_count:
            print("Lobby is valid")
            await db.operations.insert_full_game_session(
                self.bot.db_pool,
                game_id=lobby_host.id, # might use auto incrememnt since this column is duplicated... change forgein key for players as well
                guild_id=guild.id,
                category_id=category.id,
                chat_id=chat_channel.id,
                lobby_id=lobby_channel.id,
                alpha_id=alpha_channel.id,
                bravo_id=bravo_channel.id,
                host_id=lobby_host.id,
                lobby_members=current_lobby,
                isStarted=True
            )
            await db.operations.print_tables(self.bot.db_pool)
        else:
            print("Lobby is not valid")
            print("Current counts:", role_count)
            return await interaction.followup.send(
                embed=BotErrorEmbed(
                    description='The lobby does not have the correct amount of roles.'),
                ephemeral=True
            )

        await interaction.channel.send(embed=BotConfirmationEmbed(description=f'{[member.name for member in current_lobby]}'))
        
        # use interaction.guild.id, if a user runs the start command in a different server
        #that isnt where you are grouping in, tell them to use it in the correct corresponding server
        # Check if the lobby vc is full (8 players)
        # Send blank embed (will be edited) to chat
        # Add details to db for both games and players tables
        # Set voice calls limited to 10 6 and 6 for specs
        # Create teams from lobby vc (people can leave vc after since info on who is playing is now stored)
        # Edit embed with teams
        # Attach shuffle button view with end game button
async def setup(bot):
    await bot.add_cog(EightsGame(bot))
