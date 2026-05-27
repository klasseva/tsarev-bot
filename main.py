"""
Tsarev Bot — точка входа.
Запуск: python main.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config.settings import Settings
from database.db import Database
from utils.logger import setup_logger

load_dotenv()
log = setup_logger("bot")


class TsarevBot(commands.Bot):
    """Главный класс бота."""

    def __init__(self) -> None:
        intents = discord.Intents.all()  # включите только нужные в проде
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None,
            case_insensitive=True,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
        )
        self.settings = Settings.load()
        self.db: Database = Database(self.settings.db_path)
        self.start_time: float | None = None

    async def setup_hook(self) -> None:
        """Вызывается один раз при старте."""
        # инициализация БД
        await self.db.connect()
        await self.db.init_schema()
        log.info("Database initialized at %s", self.settings.db_path)

        # загрузка cogs
        cogs_dir = Path(__file__).parent / "cogs"
        for file in sorted(cogs_dir.glob("*.py")):
            if file.stem.startswith("_"):
                continue
            ext = f"cogs.{file.stem}"
            try:
                await self.load_extension(ext)
                log.info("Loaded cog: %s", ext)
            except Exception as e:
                log.exception("Failed to load %s: %s", ext, e)

        # синхронизация slash-команд
        if self.settings.main_guild_id:
            guild = discord.Object(id=self.settings.main_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to guild %d", len(synced), self.settings.main_guild_id)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (id=%s)", self.user, self.user.id if self.user else "?")
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="TSAREV FAMILY 👑"),
        )

    async def close(self) -> None:
        log.info("Shutting down...")
        await self.db.close()
        await super().close()


async def _main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        log.critical("DISCORD_TOKEN is not set in .env")
        sys.exit(1)

    bot = TsarevBot()
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass
