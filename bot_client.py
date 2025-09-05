from cogs import extensions
import asyncpg
from discord.ext import commands
from utils.logging_setup import getlog
import db.setup_db
from utils.role_select_view import RoleSelectView


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

        getlog().info('Verifying database connection...')
        await db.setup_db.verify_database_connection(
            connection_pool=self.db_pool
        )

        getlog().info('Executing schema files...')
        await db.setup_db.execute_schema_files(
            connection_pool=self.db_pool,
            schemas_path='./db/schemas'
        )

        getlog().info('Adding persistent views...')
        for guild in self.guilds:
            self.add_view(RoleSelectView(guild.id))

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
