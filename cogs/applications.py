from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands

from config.constants import Colors
from utils.checks import has_admin_role
from utils.embeds import base_embed, success, error
from utils.helpers import hex_to_color
from views.applications import ApplicationPanelView, ApplicationDecisionView, build_application_embed


class ApplicationsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="apply", description="Заявки")

    @group.command(name="create-type", description="Создать тип заявки")
    @has_admin_role()
    async def create_type(
        self, inter: discord.Interaction,
        name: str,
        title: str,
        channel: discord.TextChannel,
        questions: str,                       # 'Имя|Возраст|Опыт'  -> до 5 вопросов через |
        accept_role: discord.Role | None = None,
        review_hours: int = 24,
        color: str = "#8B0000",
        image_url: str | None = None,
        description: str | None = None,
    ):
        qs = [{"label": q.strip(), "long": True, "required": True} for q in questions.split("|") if q.strip()][:5]
        if not qs:
            return await inter.response.send_message(embed=error("Не задано ни одного вопроса."), ephemeral=True)
        cur = await self.bot.db.execute(
            """INSERT INTO application_types(guild_id, name, title, description, channel_id,
               review_hours, questions_json, accept_role, image_url, color)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (inter.guild_id, name, title, description, channel.id, review_hours,
             json.dumps(qs, ensure_ascii=False),
             accept_role.id if accept_role else None, image_url, color),
        )
        await inter.response.send_message(
            embed=success(f"Тип создан: **{title}** (ID `{cur.lastrowid}`). Используйте `/apply panel`."),
            ephemeral=True,
        )

    @group.command(name="panel", description="Отправить публичную панель заявок")
    @has_admin_role()
    async def panel(self, inter: discord.Interaction, type_id: int, channel: discord.TextChannel | None = None):
        row = await self.bot.db.fetchone("SELECT * FROM application_types WHERE id=?", (type_id,))
        if not row:
            return await inter.response.send_message(embed=error("Тип заявки не найден."), ephemeral=True)
        emb = base_embed(
            title=f"Приветствую! Оставляй свою заявку — **{row['title']}**",
            description=(row["description"] or "")
                + f"\n\n_Заявка рассматривается в течение **{row['review_hours']}** часов._",
            color=hex_to_color(row["color"]),
            image=row["image_url"],
        )
        view = ApplicationPanelView(self.bot, type_id)
        target = channel or inter.channel
        await target.send(embed=emb, view=view)
        await inter.response.send_message(embed=success("Панель опубликована."), ephemeral=True)

    @group.command(name="history", description="История заявок пользователя")
    async def history(self, inter: discord.Interaction, user: discord.User | None = None):
        u = user or inter.user
        rows = await self.bot.db.fetchall(
            """SELECT a.id, a.status, a.created_at, t.title FROM applications a
               JOIN application_types t ON t.id = a.type_id
               WHERE a.guild_id=? AND a.user_id=? ORDER BY a.id DESC LIMIT 25""",
            (inter.guild_id, u.id),
        )
        if not rows:
            return await inter.response.send_message(embed=base_embed("История заявок", "_пусто_", Colors.DARK), ephemeral=True)
        text = "\n".join(f"`#{r['id']:>4}` • {r['title']} — **{r['status']}** • {r['created_at']}" for r in rows)
        await inter.response.send_message(
            embed=base_embed(f"История заявок {u}", text, Colors.INFO), ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_ready(self):
        # ре-регистрируем persistent views
        rows = await self.bot.db.fetchall("SELECT id FROM application_types")
        for r in rows:
            self.bot.add_view(ApplicationPanelView(self.bot, r["id"]))
        opens = await self.bot.db.fetchall("SELECT id FROM applications WHERE status IN ('pending','review','call')")
        for r in opens:
            self.bot.add_view(ApplicationDecisionView(self.bot, r["id"]))


async def setup(bot):
    await bot.add_cog(ApplicationsCog(bot))
