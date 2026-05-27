from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import has_mod_role
from utils.embeds import success, error
from views.contracts import contract_embed, ContractActionsView


class ContractsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="contract", description="RP-контракты")

    @group.command(name="create", description="Создать новый контракт")
    @has_mod_role()
    async def create(
        self, inter: discord.Interaction,
        title: str,
        description: str,
        reward: str,
        deadline: str | None = None,
        executor: discord.Member | None = None,
        reward_role: discord.Role | None = None,
        channel: discord.TextChannel | None = None,
    ):
        ch = channel or inter.channel
        cur = await self.bot.db.execute(
            """INSERT INTO contracts(guild_id, title, description, reward, deadline,
                                     executor_id, creator_id, reward_role, channel_id, status)
               VALUES (?,?,?,?,?,?,?,?,?, 'active')""",
            (inter.guild_id, title, description, reward, deadline,
             executor.id if executor else None, inter.user.id,
             reward_role.id if reward_role else None, ch.id),
        )
        cid = cur.lastrowid
        row = await self.bot.db.fetchone("SELECT * FROM contracts WHERE id=?", (cid,))
        msg = await ch.send(embed=contract_embed(row), view=ContractActionsView(cid))
        await self.bot.db.execute("UPDATE contracts SET message_id=? WHERE id=?", (msg.id, cid))
        await inter.response.send_message(embed=success(f"Контракт `#{cid}` создан."), ephemeral=True)

    @group.command(name="list", description="Журнал контрактов")
    async def list_(self, inter: discord.Interaction, status: str | None = None):
        sql = "SELECT id, title, status, executor_id FROM contracts WHERE guild_id=?"
        params: list = [inter.guild_id]
        if status:
            sql += " AND status=?"
            params.append(status)
        sql += " ORDER BY id DESC LIMIT 25"
        rows = await self.bot.db.fetchall(sql, params)
        if not rows:
            return await inter.response.send_message(embed=error("Контрактов нет."), ephemeral=True)
        text = "\n".join(
            f"`#{r['id']:>3}` • **{r['title']}** • {r['status']}"
            + (f" • <@{r['executor_id']}>" if r['executor_id'] else "")
            for r in rows
        )
        await inter.response.send_message(content=text, ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        rows = await self.bot.db.fetchall("SELECT id FROM contracts WHERE status='active'")
        for r in rows:
            self.bot.add_view(ContractActionsView(r["id"]))


async def setup(bot):
    await bot.add_cog(ContractsCog(bot))
