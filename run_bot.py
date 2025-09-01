import asyncio
import botclient
import discord
import asyncpg
from utils.logging_setup import getlog
from dotenv import load_dotenv
from os import getenv


# The docker compose discord_bot service loads 1 environment variable when started
# If you are not using docker to run this application, that env var will never be loaded
# This is how we switch from locally running to runing in a containerized environment
is_containerized = getenv("IS_DOCKER_CONTAINER") # True or None

async def main() -> None:
    load_dotenv()
    TOKEN = getenv("DISCORD_BOT_TOKEN")
    env_msg = None
    if is_containerized == 'True':
        # Postgre Server Created By Postgre Docker Image
        env_msg = 'Docker Environment Variable Set - Using Container Env Vars.'
        getlog().info(env_msg)
        print(env_msg)
        DB_USER = getenv('POSTGRES_USER')
        DB_PASS = getenv('POSTGRES_PASSWORD')
        DB_NAME = getenv('POSTGRES_DB')
        DB_HOST = getenv('POSTGRES_HOST')
        DB_PORT = getenv('POSTGRES_PORT')
        loaded_env_msg = 'Loaded Container Environment Variables.'
        getlog().info(loaded_env_msg)
        print(loaded_env_msg)
    else:
        # Locally Hosted Postre Server, NOT Created By Postgre Docker Image
        env_msg = 'Docker Environment Variable Not Found - Using Local Env Vars.'
        getlog().info(env_msg)
        print(env_msg)
        DB_USER = getenv('LOCAL_POSTGRES_USER')     # development environment variable
        DB_PASS = getenv('LOCAL_POSTGRES_PASSWORD') # development environment variable
        DB_NAME = getenv('LOCAL_POSTGRES_DB')       # development environment variable
        DB_HOST = getenv('LOCAL_POSTGRES_HOST')     # development environment variable
        DB_PORT = getenv('LOCAL_POSTGRES_PORT')     # development environment variable
        loaded_env_msg = 'Loaded Local Environment Variables.'
        getlog().info(loaded_env_msg)
        print(loaded_env_msg)

    assert TOKEN is not None, 'Missing Discord Bot Token'
    assert all([DB_USER, DB_PASS, DB_NAME, DB_HOST, DB_PORT]), 'Missing Database Environment Variables'

    getlog().info('Running...')

    # Data Source Name
    POSTGRE_DSN = f'postgres://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Establish Database Pool Connection
    try: 
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
            except Exception as bot_error:
                print(bot_error)
                getlog().error(bot_error)
    except Exception as conn_error:
        getlog().info(conn_error)
        print(conn_error)

asyncio.run(main())
