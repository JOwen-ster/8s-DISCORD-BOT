from asyncpg.pool import Pool

async def update_teams(pool: Pool, game_id: int, alpha_users: list[int], bravo_users: list[int]) -> None:
    """
    Update the players table to set isAlpha based on the provided alpha/bravo user IDs.
    
    :param pool: asyncpg Pool
    :param game_id: The game session ID (game_ref)
    :param alpha_users: List of user IDs in the alpha team
    :param bravo_users: List of user IDs in the bravo team
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Update alpha team
            if alpha_users:
                await conn.executemany(
                    """
                    UPDATE players
                    SET isAlpha = TRUE
                    WHERE game_ref = $1 AND user_id = $2
                    """,
                    [(game_id, uid) for uid in alpha_users]
                )

            # Update bravo team
            if bravo_users:
                await conn.executemany(
                    """
                    UPDATE players
                    SET isAlpha = FALSE
                    WHERE game_ref = $1 AND user_id = $2
                    """,
                    [(game_id, uid) for uid in bravo_users]
                )
