import discord
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed, BotMessageEmbed
import db.operations


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
