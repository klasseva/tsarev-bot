# views/roles.py
from __future__ import annotations
import discord

STYLE_MAP = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
}

class RoleToggleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str | None, style: str):
        super().__init__(
            style=STYLE_MAP.get(style, discord.ButtonStyle.secondary),
            label=label[:80], emoji=emoji or None,
            custom_id=f"rolepanel:{role_id}",
        )
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction) -> None:
        role = interaction.guild.get_role(self.role_id)
        if not role:
            return await interaction.response.send_message("Роль удалена.", ephemeral=True)
        member = interaction.user
        try:
            if role in member.roles:
                await member.remove_roles(role, reason="role panel")
                await interaction.response.send_message(f"➖ Снята роль {role.mention}", ephemeral=True)
            else:
                await member.add_roles(role, reason="role panel")
                await interaction.response.send_message(f"➕ Выдана роль {role.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("⛔ У бота нет прав на эту роль.", ephemeral=True)


class RolePanelView(discord.ui.View):
    def __init__(self, items: list[dict]):
        super().__init__(timeout=None)
        for it in items[:25]:
            self.add_item(RoleToggleButton(it["role_id"], it["label"], it.get("emoji"), it.get("style", "secondary")))
