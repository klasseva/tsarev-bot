from __future__ import annotations

import json
from typing import Any

import discord

from config.constants import Colors
from utils.embeds import base_embed


class ApplicationModal(discord.ui.Modal):
    """Динамическая модалка по списку вопросов (до 5 полей)."""

    def __init__(self, bot, type_id: int, questions: list[dict[str, Any]]):
        super().__init__(title="Подача заявки", timeout=600)
        self.bot = bot
        self.type_id = type_id
        self.questions = questions[:5]
        self.inputs: list[discord.ui.TextInput] = []
        for q in self.questions:
            ti = discord.ui.TextInput(
                label=q["label"][:45],
                style=discord.TextStyle.paragraph if q.get("long") else discord.TextStyle.short,
                required=q.get("required", True),
                max_length=q.get("max_length", 400),
                placeholder=q.get("placeholder", ""),
            )
            self.inputs.append(ti)
            self.add_item(ti)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        bot = self.bot
        answers = [
            {"q": q["label"], "a": ti.value} for q, ti in zip(self.questions, self.inputs)
        ]
        type_row = await bot.db.fetchone("SELECT * FROM application_types WHERE id=?", (self.type_id,))
        if not type_row:
            return await interaction.response.send_message("Тип заявки не найден.", ephemeral=True)

        cur = await bot.db.execute(
            """INSERT INTO applications(type_id, guild_id, user_id, answers_json, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (self.type_id, interaction.guild_id, interaction.user.id, json.dumps(answers, ensure_ascii=False)),
        )
        app_id = cur.lastrowid

        channel = interaction.guild.get_channel(type_row["channel_id"])
        if channel is None:
            return await interaction.response.send_message("Канал заявок не настроен.", ephemeral=True)

        emb = build_application_embed(interaction.user, type_row, answers, app_id, status="pending")
        view = ApplicationDecisionView(bot, app_id)
        msg = await channel.send(embed=emb, view=view)
        await bot.db.execute("UPDATE applications SET message_id=? WHERE id=?", (msg.id, app_id))

        await interaction.response.send_message(
            embed=base_embed("📨 Заявка отправлена", "Ожидайте решения модерации.", Colors.SUCCESS),
            ephemeral=True,
        )


def build_application_embed(user, type_row, answers, app_id: int, status: str) -> discord.Embed:
    color = {
        "pending": Colors.WARNING,
        "review": Colors.INFO,
        "call": Colors.GOLD,
        "accepted": Colors.SUCCESS,
        "declined": Colors.DANGER,
    }.get(status, Colors.PRIMARY)

    emb = base_embed(
        title=f"Заявление №{app_id}",
        description=f"**Тип:** {type_row['title']}\n**Пользователь:** {user.mention} (`{user.id}`)",
        color=color,
    )
    for a in answers:
        emb.add_field(name=a["q"][:256], value=(a["a"] or "—")[:1024], inline=False)
    emb.add_field(name="Статус", value=_status_label(status), inline=False)
    if type_row["image_url"]:
        emb.set_thumbnail(url=type_row["image_url"])
    return emb


def _status_label(s: str) -> str:
    return {
        "pending": "🕒 Ожидает",
        "review": "📋 На рассмотрении",
        "call": "📞 Вызван на обзвон",
        "accepted": "✅ Принят",
        "declined": "❌ Отклонён",
    }.get(s, s)


class ApplicationPanelView(discord.ui.View):
    """Публичная панель: кнопка ‘Подать заявку’."""

    def __init__(self, bot, type_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.type_id = type_id
        self.add_item(ApplyButton(type_id))


class ApplyButton(discord.ui.Button):
    def __init__(self, type_id: int):
        super().__init__(
            style=discord.ButtonStyle.primary,
            emoji="📨",
            label="Подать заявку",
            custom_id=f"apply:open:{type_id}",
        )
        self.type_id = type_id

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        row = await bot.db.fetchone("SELECT * FROM application_types WHERE id=?", (self.type_id,))
        if not row:
            return await interaction.response.send_message("Тип заявки удалён.", ephemeral=True)
        questions = json.loads(row["questions_json"])
        await interaction.response.send_modal(ApplicationModal(bot, self.type_id, questions))


class ApplicationDecisionView(discord.ui.View):
    """Кнопки модерации под заявкой."""

    def __init__(self, bot, app_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.app_id = app_id
        self.add_item(DecisionButton(app_id, "accept", discord.ButtonStyle.success, "Принять", "✅"))
        self.add_item(DecisionButton(app_id, "review", discord.ButtonStyle.primary, "Взять на рассмотрение", "📋"))
        self.add_item(DecisionButton(app_id, "call", discord.ButtonStyle.secondary, "Вызвать на обзвон", "📞"))
        self.add_item(DecisionButton(app_id, "decline", discord.ButtonStyle.danger, "Отклонить", "❌"))


class DeclineReasonModal(discord.ui.Modal, title="Причина отклонения"):
    reason = discord.ui.TextInput(label="Причина", style=discord.TextStyle.paragraph, required=True, max_length=500)

    def __init__(self, app_id: int):
        super().__init__()
        self.app_id = app_id

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await _finalize(interaction, self.app_id, "declined", str(self.reason))


class DecisionButton(discord.ui.Button):
    def __init__(self, app_id: int, action: str, style, label: str, emoji: str):
        super().__init__(style=style, label=label, emoji=emoji, custom_id=f"apply:{action}:{app_id}")
        self.app_id = app_id
        self.action = action

    async def callback(self, interaction: discord.Interaction) -> None:
        bot = interaction.client
        # проверка прав
        row = await bot.db.fetchone("SELECT mod_role, admin_role FROM guild_settings WHERE guild_id=?", (interaction.guild_id,))
        if not interaction.user.guild_permissions.administrator:
            allowed = {(row["mod_role"] if row else None), (row["admin_role"] if row else None)}
            if not any(r.id in allowed for r in interaction.user.roles):
                return await interaction.response.send_message("⛔ Нет прав.", ephemeral=True)

        if self.action == "decline":
            return await interaction.response.send_modal(DeclineReasonModal(self.app_id))

        status = {"accept": "accepted", "review": "review", "call": "call"}[self.action]
        await _finalize(interaction, self.app_id, status)


async def _finalize(interaction: discord.Interaction, app_id: int, status: str, comment: str | None = None) -> None:
    bot = interaction.client
    app = await bot.db.fetchone("SELECT * FROM applications WHERE id=?", (app_id,))
    if not app:
        return await interaction.response.send_message("Заявка не найдена.", ephemeral=True)
    type_row = await bot.db.fetchone("SELECT * FROM application_types WHERE id=?", (app["type_id"],))
    answers = json.loads(app["answers_json"])
    user = interaction.guild.get_member(app["user_id"]) or await interaction.client.fetch_user(app["user_id"])

    await bot.db.execute(
        "UPDATE applications SET status=?, moderator_id=?, comment=?, updated_at=datetime('now') WHERE id=?",
        (status, interaction.user.id, comment, app_id),
    )

    # обновление сообщения
    emb = build_application_embed(user, type_row, answers, app_id, status)
    emb.add_field(name="Модератор", value=interaction.user.mention, inline=True)
    if comment:
        emb.add_field(name="Комментарий", value=comment[:1024], inline=False)

    view: discord.ui.View | None = ApplicationDecisionView(bot, app_id) if status in ("review", "call") else None
    try:
        await interaction.message.edit(embed=emb, view=view)
    except discord.HTTPException:
        pass

    # выдача роли при accept
    if status == "accepted" and isinstance(user, discord.Member) and type_row["accept_role"]:
        role = interaction.guild.get_role(type_row["accept_role"])
        if role:
            try:
                await user.add_roles(role, reason=f"Заявка #{app_id} принята")
            except discord.Forbidden:
                pass

    # уведомление пользователю
    try:
        await user.send(
            embed=base_embed(
                title=f"Ваша заявка №{app_id}",
                description=f"Статус: **{_status_label(status)}**" + (f"\nКомментарий: {comment}" if comment else ""),
                color=Colors.PRIMARY,
            )
        )
    except (discord.Forbidden, AttributeError):
        pass

    await interaction.response.send_message(f"Готово: {_status_label(status)}", ephemeral=True)
