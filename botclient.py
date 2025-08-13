from cogs import extensions
import asyncpg
from discord.ext import commands
from utils.loggingsetup import getlog


class Bot(commands.Bot):
    def __init__(self, *args, db_pool: asyncpg.Pool, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db_pool: asyncpg.Pool = db_pool
        self.cog_counter = 0

    async def setup_hook(self) -> None:
        getlog().info('Running bot setup_hook...')
        for i, cog in enumerate(extensions, 1):
            try:
                await self.load_extension(f'cogs.{cog}')
                getlog().info(f'{cog} cog loaded ({i}/{len(extensions)})')
            except Exception as e:
                getlog().error(f'Could not load {cog} cog ({i}/{len(extensions)}): {e}')

        async with self.db_pool.acquire() as conn:
            version = await conn.fetchval('SELECT version();')
            version_msg = f'Connected to database on PostgreSQL Version: {version}'
            getlog().info(version_msg)
            print(version_msg)

        getlog().info('Ran bot setup_hook!')

    async def on_ready(self) -> None:
        tree = await self.tree.sync()
        ready_msg_tree = f'Synced {len(tree)} tree commands.'
        ready_msg_cogs = f"Loaded {len(extensions)} {'cogs' if len(extensions) > 1 else 'cog'}"
        bot_ready_msg = 'Bot ready'

        getlog().info(ready_msg_cogs)
        getlog().info(ready_msg_tree)
        getlog().info(bot_ready_msg)
        print(ready_msg_cogs)
        print(ready_msg_tree)
        print(bot_ready_msg)

    async def query(self, sql_query: str, *args, mode: str = "fetch"):
        """
        Run a database query.
        
        :param sql_query: SQL query string (can use $1, $2 placeholders for parameters)
        :param args: Parameters for the query
        :param mode: "fetch" (many rows), "fetchval" (single value), or "execute" (no return rows)
        :return: Query result or None
        """
        if not self.db_pool:
            raise RuntimeError("Database pool is not initialized.")

        async with self.db_pool.acquire() as conn:
            if mode == "fetch":
                result = await conn.fetch(sql_query, *args)
            elif mode == "fetchval":
                result = await conn.fetchval(sql_query, *args)
            elif mode == "execute":
                result = await conn.execute(sql_query, *args)
            else:
                raise ValueError("Invalid mode. Use 'fetch', 'fetchval', or 'execute'.")

            getlog().info(f"SENT_QUERY [{mode.upper()}]:\n{sql_query} | args={args}")
            return result
