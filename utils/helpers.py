from __future__ import annotations

import re
from datetime import datetime, timedelta

import discord

_DURATION_RE = re.compile(r"(?P<n>\d+)(?P<u>[smhdw])")
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_duration(text: str) -> timedelta | None:
    """'1d2h30m' -> timedelta."""
    total = 0
    matched = False
    for m in _DURATION_RE.finditer(text.lower()):
        matched = True
        total += int(m["n"]) * _UNITS[m["u"]]
    return timedelta(seconds=total) if matched else None


def fmt_user(u: discord.abc.User | discord.Member | None) -> str:
    return f"{u.mention} (`{u.id}`)" if u else "—"


def chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def hex_to_color(value: str | None, default: int = 0x5865F2) -> discord.Color:
    if not value:
        return discord.Color(default)
    try:
        return discord.Color.from_str(value if value.startswith("#") else f"#{value}")
    except ValueError:
        return discord.Color(default)
