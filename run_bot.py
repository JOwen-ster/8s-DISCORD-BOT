import asyncio
import botclient
import discord
import asyncpg
from utils.loggingsetup import getlog
from dotenv import load_dotenv
from os import getenv


load_dotenv()
TOKEN   = getenv("DISCORD_BOT_TOKEN")
DB_USER = getenv('POSTGRE_USER')
DB_PASS = getenv('POSTGRE_PASSWORD')
DB_HOST = getenv('POSTGRE_HOSTNAME')
DB_PORT = getenv('POSTGRE_PORT')
DB_NAME = getenv('POSTGRE_DATABASE_NAME')

assert TOKEN is not None, 'Missing Discord Bot Token'

assert all([DB_NAME, DB_HOST, DB_PASS, DB_PORT, DB_USER]), 'Missing Database Environment Variables'

async def confirmation():
    getlog().info('Running main bot instance...')

async def main() -> None:
    # Run other async tasks
    await confirmation()

    # Data Source Name
    POSTGRE_DSN = f'postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Establish Database Pool Connection
    async with asyncpg.create_pool(dsn=POSTGRE_DSN) as pool:
        # Setup Discord Bot Client
        intents: discord.Intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True

        discord_bot: botclient.Bot = botclient.Bot(
            command_prefix='}',
            help_command=None,
            intents=intents,
            db_pool=pool
        )
        # Start Discord Bot
        try:
            async with discord_bot:
                await discord_bot.start(TOKEN)
        except Exception as error:
            print(error)
            getlog().error(error)

asyncio.run(main())

# Examples
# https://github.com/Rapptz/discord.py/tree/master/docs
# https://github.com/Rapptz/discord.py/tree/master/examples

# COG EXAMPLE
# https://github.com/Rapptz/discord.py/blob/master/docs/ext/commands/cogs.rst