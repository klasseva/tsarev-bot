from __future__ import annotations

import io
import json

import discord
from discord import app_commands
from discord.ext import commands

from config.constants import Colors
from utils.checks import has_mod_role
from utils.embeds import base_embed, success, error


class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="inv", description="Учёт имущества")

    @group.command(name="add", description="Добавить запись")
    @has_mod_role()
    async def add(self, inter: discord.Interaction, name: str,
                  category: str | None = None,
                  owner: discord.Member | None = None,
                  description: str | None = None):
        cat_id = None
        if category:
            cur = await self.bot.db.execute(
                "INSERT OR IGNORE INTO inventory_categories(guild_id, name) VALUES (?,?)",
                (inter.guild_id, category),
            )
            row = await self.bot.db.fetchone(
                "SELECT id FROM inventory_categories WHERE guild_id=? AND name=?",
                (inter.guild_id, category),
            )
            cat_id = row["id"]
        cur = await self.bot.db.execute(
            """INSERT INTO inventory_items(guild_id, category_id, name, owner_id, description)
               VALUES (?,?,?,?,?)""",
            (inter.guild_id, cat_id, name, owner.id if owner else None, description),
        )
        await self.bot.db.execute(
            "INSERT INTO inventory_log(item_id, actor_id, action) VALUES (?,?, 'create')",
            (cur.lastrowid, inter.user.id),
        )
        await inter.response.send_message(embed=success(f"Добавлено `#{cur.lastrowid}`."), ephemeral=True)

    @group.command(name="remove", description="Удалить запись")
    @has_mod_role()
    async def remove(self, inter: discord.Interaction, item_id: int):
        await self.bot.db.execute(
            "INSERT INTO inventory_log(item_id, actor_id, action) VALUES (?,?, 'delete')",
            (item_id, inter.user.id),
        )
        await self.bot.db.execute("DELETE FROM inventory_items WHERE id=? AND guild_id=?",
                                  (item_id, inter.guild_id))
        await inter.response.send_message(embed=success("Удалено."), ephemeral=True)

    @group.command(name="search", description="Поиск")
    async def search(self, inter: discord.Interaction, query: str):
        rows = await self.bot.db.fetchall(
            """SELECT i.id, i.name, i.owner_id, c.name AS cat
               FROM inventory_items i LEFT JOIN inventory_categories c ON c.id = i.category_id
               WHERE i.guild_id=? AND (i.name LIKE ? OR i.description LIKE ?)
               ORDER BY i.id DESC LIMIT 25""",
            (inter.guild_id, f"%{query}%", f"%{query}%"),
        )
        if not rows:
            return await inter.response.send_message(embed=error("Ничего не найдено."), ephemeral=True)
        text = "\n".join(
            f"`#{r['id']:>3}` • **{r['name']}** • {r['cat'] or '—'}"
            + (f" • <@{r['owner_id']}>" if r['owner_id'] else "")
            for r in rows
        )
        await inter.response.send_message(
            embed=base_embed(f"🔍 Результаты по `{query}`", text, Colors.INFO), ephemeral=True,
        )

    @group.command(name="export", description="Экспорт всех записей в JSON")
    @has_mod_role()
    async def export(self, inter: discord.Interaction):
        rows = await self.bot.db.fetchall(
            "SELECT * FROM inventory_items WHERE guild_id=?", (inter.guild_id,),
        )
        data = [dict(r) for r in rows]
        buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
        await inter.response.send_message(
            file=discord.File(buf, filename=f"inventory_{inter.guild_id}.json"), ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(InventoryCog(bot))
