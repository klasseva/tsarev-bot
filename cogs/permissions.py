from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import success


class PermissionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="settings", description="Настройки сервера")

    @group.command(name="roles", description="Установить admin/mod роли")
    @app_commands.default_permissions(administrator=True)
    async def roles(self, inter: discord.Interaction,
                    admin_role: discord.Role | None = None,
                    mod_role: discord.Role | None = None):
        await self.bot.db.execute(
            """INSERT INTO guild_settings(guild_id, admin_role, mod_role) VALUES (?,?,?)
               ON CONFLICT(guild_id) DO UPDATE SET
                 admin_role=COALESCE(excluded.admin_role, guild_settings.admin_role),
                 mod_role  =COALESCE(excluded.mod_role,   guild_settings.mod_role)""",
            (inter.guild_id, admin_role.id if admin_role else None, mod_role.id if mod_role else None),
        )
        await inter.response.send_message(
            embed=success(f"Admin: {admin_role.mention if admin_role else '—'}\nMod: {mod_role.mention if mod_role else '—'}"),
            ephemeral=True,
        )

    @group.command(name="log", description="Установить лог-канал для категории")
    @app_commands.choices(category=[
        app_commands.Choice(name="Сообщения", value="messages"),
        app_commands.Choice(name="Голос", value="voice"),
        app_commands.Choice(name="Модерация", value="moderation"),
        app_commands.Choice(name="Участники", value="members"),
        app_commands.Choice(name="Роли", value="roles"),
        app_commands.Choice(name="Каналы", value="channels"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def log(self, inter: discord.Interaction,
                  category: app_commands.Choice[str],
                  channel: discord.TextChannel):
        await self.bot.db.execute(
            """INSERT INTO log_channels(guild_id, category, channel_id) VALUES (?,?,?)
               ON CONFLICT(guild_id, category) DO UPDATE SET channel_id=excluded.channel_id""",
            (inter.guild_id, category.value, channel.id),
        )
        await inter.response.send_message(
            embed=success(f"Логи **{category.name}** → {channel.mention}"), ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(PermissionsCog(bot))
