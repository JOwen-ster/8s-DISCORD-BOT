import discord
from discord import app_commands
from discord.ext import commands
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed
from utils.loggingsetup import getlog

class CreatorSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-setup', description='Add 8s Lobby Creator Category')
    async def setup_eights_creator(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=BotConfirmationEmbed(description='Thinking...'),
            ephemeral=True
        )
        category = discord.utils.get(interaction.guild.categories, name='8s_Bot')
        if category:
            await interaction.followup.send(
                embed=BotErrorEmbed(description='Bot Setup Catgeory Already Found. No New Setup was created.'),
                ephemeral=True
            )
            return

        bot_member = interaction.guild.me
        everyone_role = interaction.guild.default_role
        default_perms = discord.PermissionOverwrite(send_messages=False, view_channel=True)
        bot_perms = discord.PermissionOverwrite()
        for permission in dict(discord.Permissions().all()):
            setattr(bot_perms, permission, True)

        # Create category
        bot_category = await interaction.guild.create_category(
            name='8s_Bot',
            overwrites={
                everyone_role: default_perms, # No one can send messages
                bot_member: bot_perms # Bot has all perms
            }
        )

        # Create rules text channel with same overwrites as category
        rules_channel = await bot_category.create_text_channel(name='8s-rules')
        await rules_channel.edit(sync_permissions=True)

        # Create and send an embed with rules
        rules_embed = discord.Embed(
            title='Rules',
            # make all long text in pother files and import the vars
            description='2 Teams of 4 players are created. There are 2 backlines, 2 supports, and 4 slayers. Each team will have 1 backline, 1 support, and 2 slayers. Once teams are randomly created, play a best of 3 or 5 with those teams. Once the set is over, the supports will be swapped and the slayers for each team will randomly be re-assigned. Backlines are always on opposite teams.',
            color=discord.Color.red()
        )
        await rules_channel.send(embed=rules_embed)

        # Create 4 voice channels with 1-person limit
        for i in range(1, 5):
            await bot_category.create_voice_channel(
                name=f'8s-Lobby-Create-{i}',
                user_limit=1,
                overwrites={}
            )

        await interaction.followup.send(
            embed=BotConfirmationEmbed(description='Create 8s Lobby Generators!'),
            ephemeral=True
        )

    @app_commands.command(name='8s-deactivate', description='Remove 8s Lobby Creator Category')
    async def delete_eights_setup(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=BotConfirmationEmbed(description='Deactivating 8s'), ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name='8s_Bot')
        if not category:
            await interaction.followup.send("No '8s_Bot' category found.", ephemeral=True)
            return

        for channel in category.channels:
            await channel.delete()
        await category.delete()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # --- JOIN / MOVE INTO GENERATOR CHANNEL ---
        if after.channel:
            if '8s-Lobby-Create-' in after.channel.name and after.channel.category and after.channel.category.name == '8s_Bot':
                current_guild = after.channel.guild

                # Create a new category for this game
                created_category = await current_guild.create_category(name=f'8s_Game_{member.display_name}')

                # Create voice channels
                lobby = await created_category.create_voice_channel(name='8s-Lobby', user_limit=8)
                alpha = await created_category.create_voice_channel(name='8s-Alpha', user_limit=4)
                bravo = await created_category.create_voice_channel(name='8s-Bravo', user_limit=4)

                # Create a text channel
                await created_category.create_text_channel(name=f'Chat-8s')

                # Move the member to the lobby
                if lobby:
                    await member.move_to(lobby)

        # --- LEAVE / MOVE OUT OF GAME CHANNEL ---
        if before.channel and before.channel.category and before.channel.category.name.startswith('8s_Game_'):
            category = before.channel.category
            voice_channels = category.voice_channels

            # Check if all voice channels in the category are empty
            if all(len(vc.members) == 0 for vc in voice_channels):
                for channel in category.channels:
                    await channel.delete()
                await category.delete()

async def setup(bot):
    await bot.add_cog(CreatorSetup(bot))
