from __future__ import annotations

from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.constants import Colors
from utils.embeds import base_embed, success


class AfkCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="afk", description="Установить AFK статус")
    async def afk(self, inter: discord.Interaction, reason: str = "AFK"):
        await self.bot.db.execute(
            "INSERT OR REPLACE INTO afk_users(guild_id, user_id, reason, since) VALUES (?,?,?, datetime('now'))",
            (inter.guild_id, inter.user.id, reason),
        )
        try:
            if isinstance(inter.user, discord.Member):
                old = inter.user.display_name
                if not old.startswith("[AFK]"):
                    await inter.user.edit(nick=f"[AFK] {old}"[:32])
        except discord.Forbidden:
            pass
        await inter.response.send_message(
            embed=success(f"Вы ушли в AFK: _{reason}_"), ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # авто-снятие AFK для автора
        row = await self.bot.db.fetchone(
            "SELECT since FROM afk_users WHERE guild_id=? AND user_id=?",
            (message.guild.id, message.author.id),
        )
        if row:
            await self.bot.db.execute(
                "DELETE FROM afk_users WHERE guild_id=? AND user_id=?",
                (message.guild.id, message.author.id),
            )
            try:
                if isinstance(message.author, discord.Member) and message.author.display_name.startswith("[AFK]"):
                    await message.author.edit(nick=message.author.display_name.replace("[AFK] ", "", 1))
            except discord.Forbidden:
                pass
            since = datetime.fromisoformat(row["since"])
            delta = datetime.utcnow() - since
            await message.channel.send(
                embed=base_embed(
                    "👋 С возвращением!",
                    f"{message.author.mention}, вы были AFK **{_humanize(delta.total_seconds())}**.",
                    Colors.SUCCESS,
                ),
                delete_after=10,
            )

        # уведомление об упомянутых AFK
        for u in message.mentions:
            r = await self.bot.db.fetchone(
                "SELECT reason, since FROM afk_users WHERE guild_id=? AND user_id=?",
                (message.guild.id, u.id),
            )
            if r:
                since = datetime.fromisoformat(r["since"])
                delta = datetime.utcnow() - since
                await message.reply(
                    embed=base_embed(
                        f"💤 {u.display_name} в AFK",
                        f"**Причина:** {r['reason']}\n**Отсутствует:** {_humanize(delta.total_seconds())}",
                        Colors.WARNING,
                    ),
                    mention_author=False,
                )
                break


def _humanize(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    parts = []
    if h: parts.append(f"{h}ч")
    if m: parts.append(f"{m}м")
    if sec or not parts: parts.append(f"{sec}с")
    return " ".join(parts)


async def setup(bot):
    await bot.add_cog(AfkCog(bot))
