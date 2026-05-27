from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import has_mod_role
from utils.embeds import success, error
from views.plus import PlusView, refresh_plus_message

EVENT_TYPES = [
    app_commands.Choice(name="MCL", value="MCL"),
    app_commands.Choice(name="ВЗМ", value="VZM"),
    app_commands.Choice(name="Контракт", value="contract"),
    app_commands.Choice(name="Кастом", value="custom"),
]


class PlusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="plus", description="Сборы «Плюсы»")

    @group.command(name="create", description="Создать сбор")
    @app_commands.choices(event=EVENT_TYPES)
    @has_mod_role()
    async def create(
        self, inter: discord.Interaction,
        title: str,
        event: app_commands.Choice[str],
        slots: int = 0,
        date: str | None = None,
        role: discord.Role | None = None,
        branch: str | None = None,
        comment: str | None = None,
        image_url: str | None = None,
        channel: discord.TextChannel | None = None,
    ):
        ch = channel or inter.channel
        cur = await self.bot.db.execute(
            """INSERT INTO plus_events(guild_id, channel_id, title, event_date, slots,
                                       role_id, branch, comment, image_url, creator_id, status)
               VALUES (?,?,?,?,?,?,?,?,?,?, 'open')""",
            (inter.guild_id, ch.id, f"{event.value} • {title}", date, slots,
             role.id if role else None, branch, comment, image_url, inter.user.id),
        )
        event_id = cur.lastrowid
        msg = await ch.send(embed=discord.Embed(description="Загрузка..."), view=PlusView(self.bot, event_id))
        await self.bot.db.execute("UPDATE plus_events SET message_id=? WHERE id=?", (msg.id, event_id))
        if role:
            try:
                await ch.send(f"{role.mention}", delete_after=10)
            except discord.HTTPException:
                pass
        await refresh_plus_message(self.bot, inter.guild, event_id)
        await inter.response.send_message(embed=success(f"Сбор `#{event_id}` создан."), ephemeral=True)

    @group.command(name="close", description="Закрыть сбор")
    @has_mod_role()
    async def close(self, inter: discord.Interaction, event_id: int):
        ev = await self.bot.db.fetchone("SELECT * FROM plus_events WHERE id=? AND guild_id=?", (event_id, inter.guild_id))
        if not ev:
            return await inter.response.send_message(embed=error("Сбор не найден."), ephemeral=True)
        await self.bot.db.execute("UPDATE plus_events SET status='closed' WHERE id=?", (event_id,))
        await refresh_plus_message(self.bot, inter.guild, event_id)
        await inter.response.send_message(embed=success("Сбор закрыт."), ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        rows = await self.bot.db.fetchall("SELECT id FROM plus_events WHERE status='open'")
        for r in rows:
            self.bot.add_view(PlusView(self.bot, r["id"]))


async def setup(bot):
    await bot.add_cog(PlusCog(bot))
