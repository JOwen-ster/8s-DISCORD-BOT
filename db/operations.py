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
    lobby_members: list[Member],
    is_started: bool = True,
    team_message_id: int | None = None,
):
    async with connection_pool.acquire() as conn:
        async with conn.transaction():
            # Insert the game session
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
                is_started,
                team_message_id,
            )

            player_values = [
                (game_id, member.id, member.id == host_id, None)
                for member in lobby_members
            ]

            # Bulk insert all players at once
            await conn.executemany(
                """
                INSERT INTO players (game_ref, user_id, isHost, isAlpha)
                VALUES ($1, $2, $3, $4)
                """,
                player_values,
            )

    print(f"Inserted game session {game_id}")
    return game_id

async def get_current_teams(connection: Pool, host_id: int) -> tuple[list[int], list[int]]:
    query = """
        SELECT p.user_id, p.isAlpha
        FROM players p
        JOIN game_sessions gs ON p.game_ref = gs.game_id
        WHERE gs.host_id = $1
    """

    # Execute the query
    rows = await connection.fetch(query, host_id)

    # Separate users into alpha and bravo teams
    alpha_team = []
    bravo_team = []

    for row in rows:
        user_id = row['user_id']
        is_alpha = row['isalpha']  # asyncpg returns column names in lowercase

        if is_alpha:
            alpha_team.append(user_id)
        else:
            bravo_team.append(user_id)
    
    return alpha_team, bravo_team

async def get_team_message_id(pool, user_id: int) -> int | None:
    query = """
        SELECT gs.team_message_id
        FROM game_sessions gs
        JOIN players p ON gs.game_id = p.game_ref
        WHERE p.user_id = $1
    """
    async with pool.acquire() as conn:
        return await conn.fetchval(query, user_id)

async def delete_game_if_host(pool: Pool, user_id: int) -> tuple[bool, int | None]:
    """
    Deletes a game session if the given user is the host.
    Returns (True, team_message_id) if a game was deleted,
    (False, None) otherwise.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            game = await conn.fetchrow(
                """
                SELECT game_id, team_message_id
                FROM game_sessions
                WHERE host_id = $1
                """,
                user_id
            )

            if not game:
                return False, None

            # Delete the game session
            await conn.execute(
                """
                DELETE FROM game_sessions
                WHERE game_id = $1
                """,
                game["game_id"]
            )

            return True, game["team_message_id"]

async def delete_game_by_category(pool: Pool, category_id: int) -> int | None:
    """
    Deletes a game session (and its players via ON DELETE CASCADE)
    given the category_id.

    Returns the game_id if a game was deleted, None otherwise.
    """
    async with pool.acquire() as conn:
        async with conn.transaction():
            game_id = await conn.fetchval(
                """
                SELECT game_id
                FROM game_sessions
                WHERE category_id = $1
                """,
                category_id
            )

            if not game_id:
                return None  # no game in this category

            await conn.execute(
                """
                DELETE FROM game_sessions
                WHERE game_id = $1
                """,
                game_id
            )

            return game_id

async def game_session_exists_by_category(pool: Pool, category_id: int) -> int | None:
    """
    Checks if a game session exists for the given category_id.
    
    Returns the game_id if it exists, None otherwise.
    """
    async with pool.acquire() as conn:
        game_id = await conn.fetchval(
            """
            SELECT game_id
            FROM game_sessions
            WHERE category_id = $1
            """,
            category_id
        )
        return game_id

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
