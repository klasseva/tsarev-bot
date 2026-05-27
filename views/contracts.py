# views/contracts.py
from __future__ import annotations
import discord
from config.constants import Colors
from utils.embeds import base_embed


def contract_embed(row) -> discord.Embed:
    color = {
        "active": Colors.INFO,
        "done": Colors.SUCCESS,
        "cancelled": Colors.DANGER,
    }.get(row["status"], Colors.PRIMARY)
    emb = base_embed(
        title=f"📜 Контракт №{row['id']}: {row['title']}",
        description=row["description"] or "_без описания_",
        color=color,
    )
    emb.add_field(name="💰 Награда", value=row["reward"] or "—", inline=True)
    emb.add_field(name="⏰ Дедлайн", value=row["deadline"] or "—", inline=True)
    emb.add_field(name="👤 Исполнитель", value=f"<@{row['executor_id']}>" if row['executor_id'] else "—", inline=True)
    emb.add_field(name="📌 Статус", value=row["status"].upper(), inline=True)
    emb.add_field(name="🧾 Создатель", value=f"<@{row['creator_id']}>", inline=True)
    return emb


class ContractActionsView(discord.ui.View):
    def __init__(self, contract_id: int):
        super().__init__(timeout=None)
        self.contract_id = contract_id

    @discord.ui.button(label="Выполнен", style=discord.ButtonStyle.success, emoji="✅", custom_id="ctr:done")
    async def done(self, interaction: discord.Interaction, _):
        await _update_status(interaction, self.contract_id, "done")

    @discord.ui.button(label="Отменить", style=discord.ButtonStyle.danger, emoji="🚫", custom_id="ctr:cancel")
    async def cancel(self, interaction: discord.Interaction, _):
        await _update_status(interaction, self.contract_id, "cancelled")


async def _update_status(interaction: discord.Interaction, contract_id: int, status: str) -> None:
    bot = interaction.client
    row = await bot.db.fetchone("SELECT * FROM contracts WHERE id=?", (contract_id,))
    if not row:
        return await interaction.response.send_message("Контракт не найден.", ephemeral=True)
    if not interaction.user.guild_permissions.manage_guild and interaction.user.id != row["creator_id"]:
        return await interaction.response.send_message("⛔ Нет прав.", ephemeral=True)
    await bot.db.execute(
        "UPDATE contracts SET status=?, completed_at=datetime('now') WHERE id=?", (status, contract_id),
    )
    if status == "done" and row["reward_role"] and row["executor_id"]:
        member = interaction.guild.get_member(row["executor_id"])
        role = interaction.guild.get_role(row["reward_role"])
        if member and role:
            try:
                await member.add_roles(role, reason=f"Контракт {contract_id} выполнен")
            except discord.Forbidden:
                pass
    new_row = await bot.db.fetchone("SELECT * FROM contracts WHERE id=?", (contract_id,))
    await interaction.message.edit(embed=contract_embed(new_row), view=None)
    await interaction.response.send_message(f"Статус обновлён: **{status}**", ephemeral=True)
