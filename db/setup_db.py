import aiofiles
from asyncpg import Pool
from pathlib import Path
from utils.loggingsetup import getlog


async def verify_database_connection(connection_pool: Pool):
    async with connection_pool.acquire() as conn:
        version = await conn.fetchval('SELECT version();')
        name = await conn.fetchval('SELECT current_database();')
        db_msg = f'Connected to {name} database on {version}'
        getlog().info(db_msg)
        print(db_msg)

async def execute_schema_files(connection_pool: Pool, schemas_path: str):
    '''
    Find and execute all .sql files with 'schema' in their name from the given directory.

    :param connection_pool: Database Connection Pool
    :param schemas_path: Directory where all database schemas are located
    '''
    # Use pathlib to find all .sql files containing 'schema' in their name
    all_sql_files = Path(schemas_path).rglob('*schema*.sql')

    async with connection_pool.acquire() as conn:
        for sql_file in all_sql_files:
            try:
                # Read the contents of the SQL file
                async with aiofiles.open(sql_file, 'r') as current_file:
                    sql_queries = await current_file.read()

                # Execute SQL queries in file
                await conn.execute(sql_queries)
                executed_msg = f'{sql_file} executed successfully.'
                getlog().info(executed_msg)
                print(executed_msg)

            except Exception as e:
                error_msg = f'An error occurred while executing {sql_file}: {e}'
                getlog().info(error_msg)
                print(error_msg)
