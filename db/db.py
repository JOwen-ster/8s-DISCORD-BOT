from tortoise import Tortoise
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="../.env")

async def init_db():
    await Tortoise.init(
        db_url=os.getenv("DATABASE_URL"),
        modules={"models": ["models"]}
    )
