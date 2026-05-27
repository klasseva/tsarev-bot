from __future__ import annotations

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks

from config.constants import Colors
from utils.checks import has_admin_role
from utils.embeds import base_embed, success, error

MAJESTIC_API = "https://api.majestic-files.com/monitoring"  # пример, проверьте актуальный


class MonitorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None
        self.tick.start()

    async def cog_load(self):
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        self.tick.cancel()
        if self.session:
            await self.session.close()

    @app_commands.command(name="monitor", description="Создать панель мониторинга Majestic RP")
    @has_admin_role()
    async def monitor(self, inter: discord.Interaction,
                      server_ids: str,
                      channel: discord.TextChannel | None = None):
        ch = channel or inter.channel
        msg = await ch.send(embed=base_embed("📡 Загрузка мониторинга...", color=Colors.DARK))
        await self.bot.db.execute(
            """INSERT INTO monitor_panels(guild_id, channel_id, message_id, server_ids)
               VALUES (?,?,?,?)""",
            (inter.guild_id, ch.id, msg.id, server_ids),
        )
        await inter.response.send_message(embed=success("Панель создана. Обновляется каждые 60 сек."), ephemeral=True)

    @tasks.loop(seconds=60)
    async def tick(self):
        if not self.session:
            return
        try:
            async with self.session.get(MAJESTIC_API, timeout=10) as r:
                data = await r.json(content_type=None)
        except Exception:
            data = None

        panels = await self.bot.db.fetchall("SELECT * FROM monitor_panels")
        for p in panels:
            ids = [int(x) for x in (p["server_ids"] or "").split(",") if x.strip().isdigit()]
            emb = base_embed("📡 Majestic RP — Мониторинг", color=Colors.PRIMARY,
                             footer="Обновление каждую минуту")
            if not data:
                emb.description = "⚠️ Не удалось получить данные API."
            else:
                for sid in ids:
                    srv = _find_server(data, sid)
                    if not srv:
                        emb.add_field(name=f"Сервер #{sid}", value="`нет данных`", inline=False)
                        continue
                    status = "🟢 Онлайн" if srv.get("online") else "🔴 Оффлайн"
                    emb.add_field(
                        name=f"{srv.get('name', f'Server #{sid}')}",
                        value=f"{status} • Игроков: **{srv.get('players', 0)}/{srv.get('max', 0)}**",
                        inline=False,
                    )
            guild = self.bot.get_guild(p["guild_id"])
            if not guild:
                continue
            ch = guild.get_channel(p["channel_id"])
            if not ch:
                continue
            try:
                msg = await ch.fetch_message(p["message_id"])
                await msg.edit(embed=emb)
            except discord.NotFound:
                pass

    @tick.before_loop
    async def _before(self):
        await self.bot.wait_until_ready()


def _find_server(data, sid: int):
    if isinstance(data, list):
        return next((s for s in data if int(s.get("id", 0)) == sid), None)
    if isinstance(data, dict):
        return data.get(str(sid)) or data.get(sid)
    return None


async def setup(bot):
    await bot.add_cog(MonitorCog(bot))
