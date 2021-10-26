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


async def init_dev_guild():
    dev_guild = await GuildSettings.filter(guild=859817345743978497).first()
    if not dev_guild:
        dev_guild = GuildSettings(
            guild=859817345743978497,
            race_registration_channel_id=902486000570339378,
            race_chat_channel_id=902486023282503682,
            race_channel_id=902486067540811797,
            race_result_channel_id=902486108833738802,
            race_active_role=902486581515014165,
            race_finish_role=902486629560774767
        )
    await dev_guild.save()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_init())
    loop.run_until_complete(init_dev_guild())
    loop.create_task(discord_bot.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
    tortoise.Tortoise.close_connections()
