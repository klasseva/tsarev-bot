import asyncio
import logging
import os

import discord
import uvicorn
from discord.ext import commands

from config.settings import settings
from database.db import init_db
from utils.logger import setup_logger
from webapp.app import create_app

logger = logging.getLogger("bot")


class TsarevBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        intents.presences = True
        super().__init__(command_prefix="!", intents=intents, help_command=None)

    async def setup_hook(self):
        await init_db()
        cogs = [
            "cogs.applications",
            "cogs.contracts",
            "cogs.inventory",
            "cogs.plus",
            "cogs.tempvoice",
            "cogs.logs",
            "cogs.roles",
            "cogs.embed_builder",
            "cogs.monitor",
            "cogs.afk",
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as exc:
                logger.exception(f"Failed to load cog {cog}: {exc}")

        if settings.MAIN_GUILD_ID:
            guild = discord.Object(id=settings.MAIN_GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} commands to guild {settings.MAIN_GUILD_ID}")
        else:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} global commands")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (id={self.user.id})")
        await self.change_presence(
            activity=discord.Game(name="Majestic RP | /help"),
            status=discord.Status.online,
        )


async def main():
    setup_logger()

    if not settings.DISCORD_TOKEN:
        logger.critical("DISCORD_TOKEN is not set in environment")
        return

    bot = TsarevBot()
    app = create_app(bot)

    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=False,
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    logger.info(f"Starting web admin panel on {host}:{port}")

    try:
        await asyncio.gather(
            bot.start(settings.DISCORD_TOKEN),
            server.serve(),
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    finally:
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
