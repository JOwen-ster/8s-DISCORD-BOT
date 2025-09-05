from discord import Member

ROLE_NAMES = {"8s-backline", "8s-support", "8s-slayer"}

REQUIRED_ROLES = {
    "8s-backline": 2,
    "8s-support": 2,
    "8s-slayer": 4,
}

async def has_required_role(member) -> tuple[bool, str | None]:
    for role in member.roles:
        if role.name in ROLE_NAMES:
            return True, role.name
    return False, None

async def check_role_structure(bot, guild_id, user_ids) -> tuple[bool, dict[str, int], list[Member], dict[int, str]]:
    guild = bot.get_guild(guild_id) or await bot.fetch_guild(guild_id)

    role_count = {role: 0 for role in REQUIRED_ROLES}
    members = []
    member_role_map = {}

    for user_id in user_ids:
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)

        if member:
            has_role, role_name = has_required_role(member)
            if has_role and role_name:
                role_count[role_name] += 1

                if role_count[role_name] > REQUIRED_ROLES[role_name]:
                    return False, role_count, members, member_role_map

                member_role_map[member.id] = role_name
                members.append(member)

    return True, role_count, members, member_role_map
# FETCH ALL USER IDS FROM THAT GAME THEN PASS IT IN WHEN SHUFFLING TO CHECK ROLE ORDER