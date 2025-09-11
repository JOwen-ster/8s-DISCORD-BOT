async def is_playing(connection_pool, user_id: int) -> bool:
    """
    Check if a user is registered as a current player.

    Returns True if they are in the players table.
    """
    async with connection_pool.acquire() as conn:
        query = 'SELECT 1 FROM players WHERE user_id = $1 LIMIT 1;'
        result = await conn.fetchval(query, user_id)  # returns 1 or None
    return result == 1

async def is_host(connection_pool, user_id: int) -> tuple[bool, dict | None]:
    """
    Check if a user is a host.

    Returns (True, game_session) if the user is a host, otherwise (False, None).
    """
    async with connection_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT *
            FROM game_sessions
            WHERE host_id = $1
            LIMIT 1
            """,
            user_id
        )

    return (True, row) if row else (False, None)
