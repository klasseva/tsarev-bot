from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import has_admin_role
from utils.embeds import base_embed, success, error
from utils.helpers import hex_to_color
from views.roles import RolePanelView


class RolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="roles", description="Роли по кнопке")

    @group.command(name="create", description="Создать панель ролей")
    @has_admin_role()
    async def create(self, inter: discord.Interaction,
                     title: str, color: str = "#5865F2",
                     description: str | None = None,
                     multi: bool = True,
                     channel: discord.TextChannel | None = None):
        cur = await self.bot.db.execute(
            """INSERT INTO role_panels(guild_id, channel_id, title, description, color, multi)
               VALUES (?,?,?,?,?,?)""",
            (inter.guild_id, (channel or inter.channel).id, title, description, color, int(multi)),
        )
        await inter.response.send_message(embed=success(f"Панель создана (ID `{cur.lastrowid}`).\nДобавьте роли командой `/roles add`."),
                                          ephemeral=True)

    @group.command(name="add", description="Добавить роль в панель")
    @has_admin_role()
    async def add(self, inter: discord.Interaction, panel_id: int, role: discord.Role,
                  label: str | None = None, emoji: str | None = None,
                  style: str = "secondary"):
        await self.bot.db.execute(
            """INSERT OR REPLACE INTO role_panel_roles(panel_id, role_id, label, emoji, style)
               VALUES (?,?,?,?,?)""",
            (panel_id, role.id, label or role.name, emoji, style),
        )
        await inter.response.send_message(embed=success(f"Добавлено: {role.mention}"), ephemeral=True)

    @group.command(name="publish", description="Опубликовать панель")
    @has_admin_role()
    async def publish(self, inter: discord.Interaction, panel_id: int):
        p = await self.bot.db.fetchone("SELECT * FROM role_panels WHERE id=?", (panel_id,))
        if not p:
            return await inter.response.send_message(embed=error("Панель не найдена."), ephemeral=True)
        items = [dict(r) for r in await self.bot.db.fetchall(
            "SELECT role_id, label, emoji, style FROM role_panel_roles WHERE panel_id=? ORDER BY position",
            (panel_id,),
        )]
        if not items:
            return await inter.response.send_message(embed=error("В панели нет ролей."), ephemeral=True)
        emb = base_embed(p["title"], p["description"], hex_to_color(p["color"]))
        ch = inter.guild.get_channel(p["channel_id"]) or inter.channel
        msg = await ch.send(embed=emb, view=RolePanelView(items))
        await self.bot.db.execute("UPDATE role_panels SET message_id=? WHERE id=?", (msg.id, panel_id))
        await inter.response.send_message(embed=success("Опубликовано."), ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        panels = await self.bot.db.fetchall("SELECT id FROM role_panels")
        for p in panels:
            items = [dict(r) for r in await self.bot.db.fetchall(
                "SELECT role_id, label, emoji, style FROM role_panel_roles WHERE panel_id=?",
                (p["id"],),
            )]
            if items:
                self.bot.add_view(RolePanelView(items))


async def setup(bot):
    await bot.add_cog(RolesCog(bot))
