from __future__ import annotations

from typing import Any

import discord
from fastapi import APIRouter, HTTPException, Request

from config.settings import MAIN_GUILD_ID
from webapp.security import require_login

router = APIRouter(prefix="/api")

_CHANNEL_TYPE_NAMES = {
    discord.ChannelType.text: "text",
    discord.ChannelType.voice: "voice",
    discord.ChannelType.category: "category",
    discord.ChannelType.news: "news",
    discord.ChannelType.stage_voice: "stage",
    discord.ChannelType.forum: "forum",
    discord.ChannelType.public_thread: "thread",
    discord.ChannelType.private_thread: "thread",
}


def _get_guild(request: Request) -> discord.Guild:
    bot: discord.Client | None = getattr(request.app.state, "bot", None)
    if bot is None:
        raise HTTPException(503, "Bot is not attached to app.state.bot")
    guild = bot.get_guild(MAIN_GUILD_ID)
    if guild is None:
        raise HTTPException(503, f"Bot is not in guild {MAIN_GUILD_ID}")
    return guild


@router.get("/channels")
@require_login
async def list_channels(request: Request) -> dict[str, Any]:
    """All channels of MAIN_GUILD grouped by category.

    Response: { items: [{id, name, type, category_id, category_name}] }
    """
    guild = _get_guild(request)
    items: list[dict[str, Any]] = []
    for ch in guild.channels:
        category = getattr(ch, "category", None)
        items.append({
            "id": str(ch.id),
            "name": ch.name,
            "type": _CHANNEL_TYPE_NAMES.get(ch.type, str(ch.type)),
            "position": getattr(ch, "position", 0),
            "category_id": str(category.id) if category else None,
            "category_name": category.name if category else None,
        })
    # Категории → свои каналы по position
    items.sort(key=lambda x: (
        x["category_name"] is None,
        x["category_name"] or "",
        x["position"],
    ))
    return {"items": items}


@router.get("/roles")
@require_login
async def list_roles(request: Request) -> dict[str, Any]:
    guild = _get_guild(request)
    items = [
        {
            "id": str(r.id),
            "name": r.name,
            "color": f"#{r.color.value:06x}" if r.color.value else None,
            "mentionable": r.mentionable,
            "position": r.position,
        }
        for r in guild.roles
        if not r.is_default()  # скрываем @everyone
    ]
    items.sort(key=lambda x: -x["position"])  # сверху высокие роли
    return {"items": items}


@router.get("/members")
@require_login
async def search_members(request: Request, q: str = "", limit: int = 25) -> dict[str, Any]:
    """Search members by username/display name. Empty q returns the first `limit` members."""
    guild = _get_guild(request)
    q_lower = q.strip().lower()
    results: list[dict[str, Any]] = []
    for m in guild.members:
        name = m.name.lower()
        display = (m.display_name or "").lower()
        if not q_lower or q_lower in name or q_lower in display:
            results.append({
                "id": str(m.id),
                "name": m.name,
                "display_name": m.display_name,
                "avatar": str(m.display_avatar.url) if m.display_avatar else None,
            })
            if len(results) >= limit:
                break
    return {"items": results}
