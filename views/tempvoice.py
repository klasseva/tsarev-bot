from __future__ import annotations

import discord

from config.constants import Colors
from utils.embeds import base_embed, success, error


class RenameModal(discord.ui.Modal, title="Переименовать канал"):
    name = discord.ui.TextInput(label="Новое имя", max_length=90)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch:
            return await interaction.response.send_message(embed=error("Вы не в голосовом канале."), ephemeral=True)
        await ch.edit(name=str(self.name))
        await interaction.response.send_message(embed=success(f"Новое имя: **{self.name}**"), ephemeral=True)


class LimitModal(discord.ui.Modal, title="Лимит участников"):
    limit = discord.ui.TextInput(label="Число (0 = без лимита)", max_length=2)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            n = max(0, min(99, int(str(self.limit))))
        except ValueError:
            return await interaction.response.send_message(embed=error("Введите число."), ephemeral=True)
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch:
            return await interaction.response.send_message(embed=error("Вы не в голосовом канале."), ephemeral=True)
        await ch.edit(user_limit=n)
        await interaction.response.send_message(embed=success(f"Лимит: **{n or '∞'}**"), ephemeral=True)


class KickSelect(discord.ui.UserSelect):
    def __init__(self):
        super().__init__(placeholder="Кого выгнать из канала?", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        user = self.values[0]
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch or user not in ch.members:
            return await interaction.response.send_message(embed=error("Участник не в вашем канале."), ephemeral=True)
        try:
            await user.move_to(None)
        except discord.Forbidden:
            return await interaction.response.send_message(embed=error("Нет прав."), ephemeral=True)
        await interaction.response.send_message(embed=success(f"Выгнан: {user.mention}"), ephemeral=True)


class TempVoicePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Название", emoji="✏️", style=discord.ButtonStyle.primary, custom_id="tv:rename")
    async def rename(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(RenameModal())

    @discord.ui.button(label="Лимит", emoji="👥", style=discord.ButtonStyle.primary, custom_id="tv:limit")
    async def limit(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.send_modal(LimitModal())

    @discord.ui.button(label="Закрыть", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="tv:lock")
    async def lock(self, interaction: discord.Interaction, _: discord.ui.Button):
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch: return await interaction.response.send_message(embed=error("Вы не в войсе."), ephemeral=True)
        await ch.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message(embed=success("Канал закрыт."), ephemeral=True)

    @discord.ui.button(label="Открыть", emoji="🔓", style=discord.ButtonStyle.secondary, custom_id="tv:unlock")
    async def unlock(self, interaction: discord.Interaction, _: discord.ui.Button):
        ch = interaction.user.voice.channel if interaction.user.voice else None
        if not ch: return await interaction.response.send_message(embed=error("Вы не в войсе."), ephemeral=True)
        await ch.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message(embed=success("Канал открыт."), ephemeral=True)

    @discord.ui.button(label="Выгнать", emoji="👢", style=discord.ButtonStyle.danger, custom_id="tv:kick")
    async def kick(self, interaction: discord.Interaction, _: discord.ui.Button):
        v = discord.ui.View(timeout=60)
        v.add_item(KickSelect())
        await interaction.response.send_message("Выберите участника:", view=v, ephemeral=True)


def panel_embed() -> discord.Embed:
    return base_embed(
        title="🎛️ Управление вашим каналом",
        description=(
            "Используйте кнопки ниже, чтобы управлять **временным голосовым каналом**.\n"
            "Только владелец канала может менять параметры."
        ),
        color=Colors.PRIMARY,
    )
