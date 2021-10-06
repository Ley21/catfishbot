import asyncio
import os
from catfish_discord.bot import discord_bot

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(discord_bot.start(os.environ.get("DISCORD_TOKEN")))
    loop.run_forever()
