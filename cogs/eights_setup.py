import discord
from discord import app_commands
from discord.ext import commands
from utils.role_select_view import RoleSelectView
from utils.embeds import BotConfirmationEmbed, BotErrorEmbed
from utils.logging_setup import getlog


class CreatorSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='8s-setup', description='Add 8s Lobby Creator Category')
    async def setup_eights_creator(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=BotConfirmationEmbed(description='Setting up...'),
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
        for name in ['backline', 'support', 'slayer']:
            await interaction.guild.create_role(name=f'8s-{name}')
        roles_channel = await bot_category.create_text_channel(name='8s-roles')

        # Create and send an embed with rules
        rules_embed = discord.Embed(
            title='Rules',
            # make all long text in pother files and import the vars
            description='2 Teams of 4 players are created. There are 2 backlines, 2 supports, and 4 slayers. Each team will have 1 backline, 1 support, and 2 slayers. Once teams are randomly created, play a best of 3 or 5 with those teams. Once the set is over, the supports will be swapped and the slayers for each team will randomly be re-assigned. Backlines are always on opposite teams.',
            color=discord.Color.red()
        )
        await rules_channel.send(embed=rules_embed)

        roles_embed = BotConfirmationEmbed(description='Select the role you will use for eights today!')
        roles_view = RoleSelectView(interaction.guild.id)
        await roles_channel.send(embed=roles_embed, view=roles_view)
        self.bot.add_view(roles_view)

        # Create 4 voice channels with 1-person limit
        for i in range(1, 5):
            await bot_category.create_voice_channel(
                name=f'8s-Lobby-Create-{i}',
                user_limit=1,
                overwrites={}
            )

        await interaction.followup.send(
            embed=BotConfirmationEmbed(description='✅Created 8s Lobby Generators! Setup Complete!'),
            ephemeral=True
        )

    @app_commands.command(name='8s-deactivate', description='Remove 8s Lobby Creator Category')
    async def delete_eights_setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You must be an **Administrator** to use this command.", 
                ephemeral=True
            )
            return

        await interaction.response.send_message(embed=BotConfirmationEmbed(description='Deactivating 8s.. Finished once the 8s_Bot Category is deleted.'), ephemeral=True)
        category = discord.utils.get(interaction.guild.categories, name='8s_Bot')
        if not category:
            await interaction.followup.send("No '8s_Bot' category found.", ephemeral=True)
            return

        for role in interaction.guild.roles:
            if role.name in {"8s-backline", "8s-support", "8s-slayer"}:
                await role.delete()

        for channel in category.channels:
            await channel.delete()
        await category.delete()

    @commands.Cog.listener(name='on_voice_state_update')
    async def creator_manager(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # --- JOIN / MOVE INTO GENERATOR CHANNEL ---
        if after.channel and '8s-Lobby-Create-' in after.channel.name:
            guild = after.channel.guild

            # Double-check member is in channel
            if not member.voice or member.voice.channel != after.channel:
                return  

            # Validate category
            if not after.channel.category or after.channel.category.name != '8s_Bot':
                return

            # Create game category + channels
            bot_perms = discord.PermissionOverwrite()
            for perm in dict(discord.Permissions().all()):
                setattr(bot_perms, perm, True)

            created_category = await guild.create_category(
                name=f'8s_Game_{member.id}',
                overwrites={guild.me: bot_perms}
            )

            await created_category.create_text_channel(name='8s-chat')
            lobby = await created_category.create_voice_channel(name='8s-Lobby', user_limit=10)
            await created_category.create_voice_channel(name='8s-Alpha', user_limit=6)
            await created_category.create_voice_channel(name='8s-Bravo', user_limit=6)

            if not member.voice or member.voice.channel != after.channel:
                for ch in created_category.channels:
                    await ch.delete()
                await created_category.delete()
                return

            try:
                if member.voice and member.voice.channel == after.channel:
                    await member.move_to(lobby)
            except Exception as e:
                getlog().info(e)
                for ch in created_category.channels:
                    await ch.delete()
                await created_category.delete()
                return

        # --- LEAVE / MOVE OUT OF GAME CHANNEL ---
        # CHECK IF GAME WAS IN DATABASE IF NOT DELETE IT FROM GAME SESSIONS THEN DELETE IN DISCORD
        if before.channel and before.channel.category and before.channel.category.name.startswith('8s_Game_'):
            category = before.channel.category
            if all(len(vc.members) == 0 for vc in category.voice_channels):
                for ch in category.channels:
                    await ch.delete()
                await category.delete()

async def setup(bot):
    await bot.add_cog(CreatorSetup(bot))
