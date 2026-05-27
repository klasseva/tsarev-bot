from __future__ import annotations

from typing import Callable

import discord
from discord import app_commands
from discord.ext import commands


class MissingPermission(app_commands.CheckFailure):
    def __init__(self, msg: str = "У вас нет прав для этой команды.") -> None:
        super().__init__(msg)
        self.msg = msg


def _has_role_or_admin(member: discord.Member, role_ids: set[int]) -> bool:
    if member.guild_permissions.administrator:
        return True
    return any(r.id in role_ids for r in member.roles)


def has_mod_role() -> Callable:
    async def predicate(inter: discord.Interaction) -> bool:
        bot = inter.client
        db = getattr(bot, "db", None)
        if db is None:
            raise MissingPermission("База данных ещё не готова, попробуйте позже.")

        row = await db.fetchone(
            "SELECT mod_role, admin_role FROM guild_settings WHERE guild_id=?",
            (inter.guild_id,),
        )
        allowed = {row["mod_role"], row["admin_role"]} if row else set()
        allowed.discard(None)
        member = inter.user
        if isinstance(member, discord.Member) and _has_role_or_admin(member, allowed):
            return True
        raise MissingPermission("Нужна модераторская роль.")
    return app_commands.check(predicate)


def has_admin_role() -> Callable:
    async def predicate(inter: discord.Interaction) -> bool:
        bot = inter.client
        db = getattr(bot, "db", None)
        if db is None:
            raise MissingPermission("База данных ещё не готова, попробуйте позже.")

        row = await db.fetchone(
            "SELECT admin_role FROM guild_settings WHERE guild_id=?",
            (inter.guild_id,),
        )
        allowed = {row["admin_role"]} if row else set()
        allowed.discard(None)
        member = inter.user
        if isinstance(member, discord.Member) and _has_role_or_admin(member, allowed):
            return True
        raise MissingPermission("Нужна административная роль.")
    return app_commands.check(predicate)


def is_owner() -> Callable:
    async def predicate(inter: discord.Interaction) -> bool:
        bot = inter.client
        owner_id = getattr(getattr(bot, "settings", None), "owner_id", None)
        if owner_id is not None and inter.user.id == owner_id:
            return True
        raise MissingPermission("Только владелец бота.")
    return app_commands.check(predicate)
