import discord


class RoleSelectView(discord.ui.View):
    def __init__(self, guild_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id # guild id since each guild can only have 1 persistent view.
        self.ROLE_MAP = {
            "Backline": "8s-backline",
            "Support": "8s-support",
            "Slayer": "8s-slayer",
        }

        # Dynamically add buttons
        for key, role_name in self.ROLE_MAP.items():
            button = discord.ui.Button(
                label=key,
                style=discord.ButtonStyle.primary,
                custom_id=f"persistent_view:{key}:{guild_id}"
            )
            button.callback = self.make_callback(role_name)
            self.add_item(button)

    def make_callback(self, role_name: str):
        async def callback(interaction: discord.Interaction):
            if role_name in [role.name for role in interaction.user.roles]:
                return await interaction.response.send_message(
                    f"You already have that role!", ephemeral=True
                )
            guild = interaction.guild
            member = interaction.user

            # Find target role
            role = discord.utils.get(guild.roles, name=role_name)
            if role is None:
                return await interaction.response.send_message(
                    f"❌ Role `{role_name}` not found.", ephemeral=True
                )

            # Remove any of the other roles in ROLE_MAP
            removed_roles = []
            for r in self.ROLE_MAP.values():
                rr = discord.utils.get(guild.roles, name=r)
                if rr in member.roles:
                    await member.remove_roles(rr)
                    removed_roles.append(rr.name)

            # Add the selected role
            await member.add_roles(role)

            msg = f"✅ You now have **{role.name}**."
            if removed_roles:
                msg += f" Removed {', '.join(removed_roles)}."
            await interaction.response.send_message(msg, ephemeral=True)

        return callback
