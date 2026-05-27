from __future__ import annotations

import discord

from config.constants import Colors
from utils.embeds import base_embed


class PlusView(discord.ui.View):
    def __init__(self, bot, event_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.event_id = event_id
        self.add_item(JoinButton(event_id))
        self.add_item(LeaveButton(event_id))
        self.add_item(CloseButton(event_id))


class JoinButton(discord.ui.Button):
    def __init__(self, event_id: int):
        super().__init__(style=discord.ButtonStyle.success, label="➕ Присоединиться",
                         custom_id=f"plus:join:{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        ev = await bot.db.fetchone("SELECT * FROM plus_events WHERE id=?", (self.event_id,))
        if not ev or ev["status"] != "open":
            return await interaction.response.send_message("Сбор закрыт.", ephemeral=True)

        already = await bot.db.fetchone(
            "SELECT 1 FROM plus_participants WHERE event_id=? AND user_id=?",
            (self.event_id, interaction.user.id),
        )
        if already:
            return await interaction.response.send_message("Вы уже в списке.", ephemeral=True)

        # СТРОГО ПОРЯДОК ОЧЕРЕДИ — следующий номер
        last = await bot.db.fetchone(
            "SELECT COALESCE(MAX(queue), 0) AS m FROM plus_participants WHERE event_id=?",
            (self.event_id,),
        )
        next_q = int(last["m"]) + 1

        slots = int(ev["slots"] or 0)
        is_extra = 1 if (slots and next_q > slots) else 0

        await bot.db.execute(
            "INSERT INTO plus_participants(event_id, user_id, queue, is_extra) VALUES (?,?,?,?)",
            (self.event_id, interaction.user.id, next_q, is_extra),
        )
        await refresh_plus_message(bot, interaction.guild, self.event_id)
        tag = "запасной" if is_extra else f"место №{next_q}"
        await interaction.response.send_message(f"✅ Вы в сборе — **{tag}**.", ephemeral=True)


class LeaveButton(discord.ui.Button):
    def __init__(self, event_id: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="➖ Выйти",
                         custom_id=f"plus:leave:{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        await bot.db.execute(
            "DELETE FROM plus_participants WHERE event_id=? AND user_id=?",
            (self.event_id, interaction.user.id),
        )
        # ПЕРЕНУМЕРАЦИЯ ОЧЕРЕДИ (сохраняем порядок входа)
        rows = await bot.db.fetchall(
            "SELECT user_id FROM plus_participants WHERE event_id=? ORDER BY queue ASC",
            (self.event_id,),
        )
        ev = await bot.db.fetchone("SELECT slots FROM plus_events WHERE id=?", (self.event_id,))
        slots = int(ev["slots"] or 0) if ev else 0
        for i, r in enumerate(rows, start=1):
            is_extra = 1 if (slots and i > slots) else 0
            await bot.db.execute(
                "UPDATE plus_participants SET queue=?, is_extra=? WHERE event_id=? AND user_id=?",
                (i, is_extra, self.event_id, r["user_id"]),
            )
        await refresh_plus_message(bot, interaction.guild, self.event_id)
        await interaction.response.send_message("Вы вышли из сбора.", ephemeral=True)


class CloseButton(discord.ui.Button):
    def __init__(self, event_id: int):
        super().__init__(style=discord.ButtonStyle.danger, label="🔒 Закрыть",
                         custom_id=f"plus:close:{event_id}")
        self.event_id = event_id

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        ev = await bot.db.fetchone("SELECT creator_id FROM plus_events WHERE id=?", (self.event_id,))
        if not ev:
            return await interaction.response.send_message("Сбор не найден.", ephemeral=True)
        if interaction.user.id != ev["creator_id"] and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("⛔ Закрыть может только создатель/админ.", ephemeral=True)
        await bot.db.execute("UPDATE plus_events SET status='closed' WHERE id=?", (self.event_id,))
        await refresh_plus_message(bot, interaction.guild, self.event_id)
        await interaction.response.send_message("Сбор закрыт.", ephemeral=True)


async def refresh_plus_message(bot, guild: discord.Guild, event_id: int) -> None:
    ev = await bot.db.fetchone("SELECT * FROM plus_events WHERE id=?", (event_id,))
    if not ev:
        return
    parts = await bot.db.fetchall(
        "SELECT user_id, queue, is_extra FROM plus_participants WHERE event_id=? ORDER BY queue ASC",
        (event_id,),
    )
    color = Colors.SUCCESS if ev["status"] == "open" else Colors.DARK
    emb = base_embed(
        title=f"🔥 {ev['title']}",
        description=(
            f"**Дата:** {ev['event_date'] or '—'}\n"
            f"**Слоты:** {ev['slots'] or '∞'}"
            + (f"\n**Роль:** <@&{ev['role_id']}>" if ev['role_id'] else "")
            + (f"\n**Ветка:** {ev['branch']}" if ev['branch'] else "")
            + (f"\n**Комментарий:** {ev['comment']}" if ev['comment'] else "")
        ),
        color=color,
        image=ev["image_url"],
        footer=f"ID сбора: {event_id} • {'ОТКРЫТ' if ev['status']=='open' else 'ЗАКРЫТ'}",
    )
    main = [p for p in parts if not p["is_extra"]]
    extra = [p for p in parts if p["is_extra"]]
    if main:
        emb.add_field(
            name=f"✅ Основной состав ({len(main)})",
            value="\n".join(f"`{p['queue']:>2}.` <@{p['user_id']}>" for p in main)[:1024],
            inline=False,
        )
    else:
        emb.add_field(name="✅ Основной состав", value="_никого_", inline=False)
    if extra:
        emb.add_field(
            name=f"⏳ Запас ({len(extra)})",
            value="\n".join(f"`{p['queue']:>2}.` <@{p['user_id']}>" for p in extra)[:1024],
            inline=False,
        )

    channel = guild.get_channel(ev["channel_id"])
    if not channel:
        return
    try:
        msg = await channel.fetch_message(ev["message_id"])
        view = PlusView(bot, event_id) if ev["status"] == "open" else None
        await msg.edit(embed=emb, view=view)
    except discord.NotFound:
        pass
