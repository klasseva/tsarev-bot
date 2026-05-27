from __future__ import annotations

from datetime import datetime

import discord

from config.constants import Colors


def base_embed(
    title: str | None = None,
    description: str | None = None,
    color: discord.Color | int = Colors.PRIMARY,
    *,
    image: str | None = None,
    thumbnail: str | None = None,
    footer: str | None = None,
    timestamp: bool = True,
) -> discord.Embed:
    emb = discord.Embed(title=title, description=description, color=color)
    if image:
        emb.set_image(url=image)
    if thumbnail:
        emb.set_thumbnail(url=thumbnail)
    if footer:
        emb.set_footer(text=footer)
    if timestamp:
        emb.timestamp = datetime.utcnow()
    return emb


def success(text: str, title: str = "Готово") -> discord.Embed:
    return base_embed(f"✅ {title}", text, Colors.SUCCESS)


def error(text: str, title: str = "Ошибка") -> discord.Embed:
    return base_embed(f"⛔ {title}", text, Colors.DANGER)


def info(text: str, title: str = "Информация") -> discord.Embed:
    return base_embed(f"ℹ️ {title}", text, Colors.INFO)


def warning(text: str, title: str = "Внимание") -> discord.Embed:
    return base_embed(f"⚠️ {title}", text, Colors.WARNING)
