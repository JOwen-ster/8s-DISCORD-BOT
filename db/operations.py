from asyncpg import Pool
from discord import Member
from tabulate import tabulate


async def insert_full_game_session(
    connection_pool: Pool,
    guild_id: int,
    category_id: int,
    chat_id: int,
    lobby_id: int,
    alpha_id: int,
    bravo_id: int,
    host_id: int,
    lobby_members: list[Member],   # all players (including host)
    isAlpha: bool,
    isStarted: bool = False,
    team_message_id: int | None = None,
):
    async with connection_pool.acquire() as conn:
        async with conn.transaction():
            # Insert game session and get the generated game_id
            game_id = await conn.fetchval(
                """
                INSERT INTO game_sessions (
                    guild_id,
                    category_id,
                    chat_id,
                    lobby_id,
                    alpha_id,
                    bravo_id,
                    host_id,
                    isStarted,
                    team_message_id
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                RETURNING game_id
                """,
                guild_id,
                category_id,
                chat_id,
                lobby_id,
                alpha_id,
                bravo_id,
                host_id,
                isStarted,
                team_message_id,
            )

            # Insert all lobby members into players
            for member in lobby_members:
                await conn.execute(
                    """
                    INSERT INTO players (game_ref, user_id, isHost, isAlpha)
                    VALUES ($1, $2, $3, $4)
                    """,
                    game_id,
                    member.id,
                    member.id == host_id,  # True if host
                    isAlpha
                )
    print(game_id)
    return game_id  # return the new session id so you can use it later

async def select_players(connection_pool: Pool, *player_ids: int):
    if not player_ids:
        return []

    async with connection_pool.acquire() as conn:
        query = "SELECT * FROM players WHERE user_id = ANY($1::BIGINT[])"
        return await conn.fetch(query, list(player_ids))

async def print_tables(connection_pool: Pool):
    async with connection_pool.acquire() as conn:
        # game_sessions
        print("\n=== game_sessions ===")
        rows = await conn.fetch("SELECT * FROM game_sessions;")
        if rows:
            headers = rows[0].keys()
            data = [tuple(r.values()) for r in rows]
            print(tabulate(data, headers=headers, tablefmt="psql"))
        else:
            print("No rows found.")

        # players
        print("\n=== players ===")
        rows = await conn.fetch("SELECT * FROM players;")
        if rows:
            headers = rows[0].keys()
            data = [tuple(r.values()) for r in rows]
            print(tabulate(data, headers=headers, tablefmt="psql"))
        else:
            print("No rows found.")
