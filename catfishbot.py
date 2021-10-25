import asyncio
import os
from catfish_discord.bot import discord_bot
from tortoise import Tortoise


async def database_init():
    # Here we connect to a SQLite DB file.
    # also specify the app name of "models"
    # which contain models from "app.models"
    await Tortoise.init(
        db_url='sqlite://db.sqlite3',
        modules={'models': ['models.race']}
    )
    # Generate the schema
    await Tortoise.generate_schemas()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(database_init(),)
    loop.create_task(discord_bot.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
