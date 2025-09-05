import discord
from discord import app_commands
from discord.ext import commands
import db.operations
import db.checks
import utils.role_checks
from utils.shuffle import split_into_teams, drag_teams
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed, FullTeamsEmbed, send_error
from utils.game_controls_view import PersistentView
from utils.logging_setup import getlog


class EightsGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-start')
    async def start_users_eights_game(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotConfirmationEmbed(description='Starting...'), ephemeral=True)
        # check db to see if user already in a started game
        # only hosts should be able to start
        # check if user id in players (account for categoeies being named the same name
        # EX. I make a lobby then have a friend join. I leave and use the generator again.
        # The first chat I use /8s-start in will be the one registered since both have my category name
        # channel restriction
        if interaction.channel.name != '8s-chat':
            return await send_error(interaction, "Please run this command in a `8s-chat` text channel")

        user_id = interaction.user.id
        if db.checks.is_playing(self.bot.db_pool, user_id):
            return await send_error(interaction, "You must not be in a started game, please leave or end it.")

        # category and required channels
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=f"8s_Game_{user_id}")
        if not category:
            return await send_error(interaction, "No 8s category with your user id found in this guild.")

        required_channels = {
            "chat_channel": ("8s-chat", category.text_channels, "Your `8s-chat` was not found."),
            "lobby_channel": ("8s-Lobby", category.voice_channels, "Your `8s-Lobby` was not found."),
            "alpha_channel": ("8s-Alpha", category.voice_channels, "Your `8s-Alpha` call was not found."),
            "bravo_channel": ("8s-Bravo", category.voice_channels, "Your `8s-Bravo` call was not found."),
        }

        channels = {}
        for identifier, (name, group, error_msg) in required_channels.items():
            channel = discord.utils.get(group, name=name)
            if not channel:
                return await send_error(interaction, error_msg)
            channels[identifier] = channel
        chat_channel = channels['chat_channel']
        lobby_channel = channels['lobby_channel']
        alpha_channel = channels['alpha_channel']
        bravo_channel = channels['bravo_channel']

        # host and player count checks
        if interaction.user not in lobby_channel.members:
            return await send_error(
                interaction, 'You must `be inside your own 8s-Lobby` voice channel to start the game.'
            )

        if len(lobby_channel.members) != 8:
            return await send_error(
                interaction, 'The lobby must have `exactly 8` players. **SPECTATORS MUST LEAVE AND JOIN AFTER START**'
            )

        lobby_member_ids = (member.id for member in lobby_channel.members)

        is_valid_role_structure, role_count, current_lobby, role_map = await utils.role_checks.check_role_structure(
            self.bot,
            guild.id,
            lobby_member_ids
        )
        # when calling shuffle the last 2 current teams will be passed in
        # they will be created via fetching user ids and isAlpha for that session via host_id then finding roles in Discord
        init_alpha_team, init_bravo_team = await split_into_teams(role_map)

        if is_valid_role_structure and len(current_lobby) == 8:
            getlog().info(f'VALID TEAM SETUP FOR {user_id} - INSERTING INTO DATABASE')
            teams_message_embed_message = await interaction.channel.send(
                embed=FullTeamsEmbed(init_alpha_team, init_bravo_team)
            )
            
            # TODO: CHANGE METHOD TO SET TEAMS AT START DONT MAKE NONE THIS CAUSES ISSUES WITH SHUFFLE
            # Pass in init teams
            #when insert into players check if backline or support and make it first
            #occurance alpha then the second occurance bravo
            # For slayers first 2 occurances are alpha 3rd and 4th are bravo
            game_id = await db.operations.insert_full_game_session(
                self.bot.db_pool,
                guild_id=guild.id,
                category_id=category.id,
                chat_id=chat_channel.id,
                lobby_id=lobby_channel.id,
                alpha_id=alpha_channel.id,
                bravo_id=bravo_channel.id,
                host_id=user_id,
                lobby_members=current_lobby,
                init_alpha_team=init_alpha_team,
                init_bravo_team=init_bravo_team,
                is_started=True,
                team_message_id=teams_message_embed_message.id
            )

            await teams_message_embed_message.edit(view=PersistentView(self.bot, guild.id, chat_channel.id, teams_message_embed_message.id))

            await db.operations.print_tables(self.bot.db_pool)
            getlog().info(f'CREATED GAME FOR {user_id} - SESSION_ID: {game_id}')
        else:
            getlog().info(f'IN-VALID TEAM SETUP FOR {user_id} - Current roles: {role_count}')
            return await interaction.followup.send(
                embed=BotErrorEmbed(
                    description='Invalid role structure, you must have 2 backlines, 2 supports, and 4 slayers.'),
                ephemeral=True
            )
        await drag_teams(current_lobby, init_alpha_team, init_bravo_team, self.bot, alpha_channel.id, bravo_channel.id)

        await interaction.channel.send(embed=BotConfirmationEmbed(
                description='Players successfuly stored! You may now choose to stay in team voice calls or leave.')
            )

        await interaction.channel.send(embed=BotConfirmationEmbed(
            title='✅Game Started',
            description=f'Your game_session_id is {game_id} Good luck everyone!')
        )

        # TODO: DELETE THE SENT EMBED USING IDS THEN RESEND AND UPDATE DB MESSAGE ID
        # channel = bot.get_channel(channel_id)  # gets the channel object from cache
        # if channel is None:
        #     channel = await bot.fetch_channel(channel_id)  # fetch from API if not cached
        # message = await channel.fetch_message(message_id)
        # await message.delete()

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
