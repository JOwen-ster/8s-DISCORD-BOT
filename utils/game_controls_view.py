import discord
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed, BotMessageEmbed, FullTeamsEmbed
import db.operations
import db.checks
from utils import role_checks
import utils.shuffle
import db.team_change


class PersistentView(discord.ui.View):
    def __init__(self, bot, guild_id, channel_id, post_id: int):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.bot = bot
        self.post_id = post_id

        # Shuffle button
        self.shuffle_button = discord.ui.Button(
            label="Shuffle Teams",
            emoji="🔀",
            style=discord.ButtonStyle.green,
            custom_id=f"shuffle-btn-{guild_id}-{channel_id}-{post_id}"
        )
        self.shuffle_button.callback = self.shuffle_callback
        self.add_item(self.shuffle_button)

        # End Game button
        self.end_button = discord.ui.Button(
            label="End Game",
            style=discord.ButtonStyle.red,
            custom_id=f"end-btn-{guild_id}-{channel_id}-{post_id}"
        )
        self.end_button.callback = self.end_callback
        self.add_item(self.end_button)

    async def shuffle_callback(self, interaction: discord.Interaction):
        self.shuffle_button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send("Shuffling...", ephemeral=True)
        is_host, game_session = await db.checks.is_host(self.bot.db_pool, interaction.user.id)

        if is_host and game_session['chat_id'] == interaction.channel_id: # ensure you are using your own 8s-chat
            current_alpha_ids, current_bravo_ids = await db.operations.get_current_teams(self.bot.db_pool, interaction.user.id)
            are_roles_valid, current_role_count, current_member_list, current_role_map = await role_checks.check_role_structure(
                self.bot,
                interaction.guild_id,
                current_alpha_ids+current_bravo_ids
            )

            if are_roles_valid:
                current_alpha, current_bravo = await utils.shuffle.split_into_teams(current_role_map)
                new_alpha, new_bravo = await utils.shuffle.shuffle_teams(current_role_map, current_alpha, current_bravo)
                new_alpha_ids = [pid for sublist in new_alpha.values() for pid in sublist]
                new_bravo_ids = [pid for sublist in new_bravo.values() for pid in sublist]
                await db.team_change.update_teams(self.bot.db_pool, game_session['game_id'], new_alpha_ids, new_bravo_ids)

                updated_team_embed = FullTeamsEmbed(new_alpha, new_bravo)
                channel = await self.bot.fetch_channel(game_session['chat_id'])
                message = await channel.fetch_message(game_session['team_message_id'])
                await message.edit(embed=updated_team_embed)
                self.shuffle_button.disabled = True
                await interaction.response.edit_message(view=self)

                await utils.shuffle.drag_teams(
                    current_member_list,
                    new_alpha, new_bravo,
                    self.bot,
                    game_session['alpha_id'],
                    game_session['bravo_id']
                )
                await interaction.followup.send("Shuffled!", ephemeral=True)
            else:
                await interaction.followup.send(f'CURRENT ROLES ARE INVALID - {current_role_count}', ephemeral=True)
        await interaction.followup.send("You can only shuffle the 8s session YOU are hosting, not someone else's.", ephemeral=True)

    async def end_callback(self, interaction: discord.Interaction):
        self.end_button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=BotMessageEmbed(description="Ending Game..."))
        isEnded, _ = await db.operations.delete_game_if_host(self.bot.db_pool, interaction.user.id)
        if isEnded:
            return await interaction.followup.send(embed=BotConfirmationEmbed(description="Game Ended"))

        await interaction.followup.send(embed=BotErrorEmbed(description="You are not the host, game was not ended."))
        self.end_button.disabled = False
        return await interaction.response.edit_message(view=self)
