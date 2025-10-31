import logging
import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import ssl
import aiohttp

from bot.core.logging import setup_logging
from bot.core.loader import load_feature_extensions


def create_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)
    return bot


def main() -> None:
    load_dotenv()
    
    setup_logging()
    logger = logging.getLogger("utilitybot")

    bot = create_bot()

    @bot.event
    async def on_ready():
        logger.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
        # Load all feature module extensions
        await load_feature_extensions(bot)

    # Import settings after loading .env
    from bot.config import settings
    token = settings.token


    if not token:
        logger.error("DISCORD_TOKEN is not set. Please configure it in .env.")
        return

    bot.run(token)


if __name__ == "__main__":
    main()