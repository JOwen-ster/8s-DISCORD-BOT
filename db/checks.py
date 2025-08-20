async def is_playing(connection_pool, user_id) -> bool:
    """
    Check if a user is registered as a current player.

    Returns True if they are in the players table.
    """
    async with connection_pool.acquire() as conn:
        query = 'SELECT 1 FROM players WHERE user_id = $1 LIMIT 1;'
        result = await conn.fetchval(query, user_id)  # returns 1 or None
    return result is not None
# also check if game id which is a user id is in sessions