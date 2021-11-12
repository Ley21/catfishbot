import asyncio
import os

import tortoise

from catfish_discord.bot import discord_bot
from tortoise import Tortoise
from models.models import GuildSettings


async def database_init():
    # Here we connect to a SQLite DB file.
    # also specify the app name of "models"
    # which contain models from "app.models"
    await Tortoise.init(
        db_url=f"sqlite://{os.environ.get('DATABASE_PATH','database/db.sqlite3')}",
        modules={'models': ['models.models']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_init())
    loop.create_task(discord_bot.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
    tortoise.Tortoise.close_connections()
