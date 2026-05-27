from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import has_admin_role
from utils.embeds import success, error
from views.tempvoice import TempVoicePanel, panel_embed


class TempVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    group = app_commands.Group(name="tempvoice", description="Временные голосовые каналы")

    @group.command(name="setup", description="Настроить канал-создатель и категорию")
    @has_admin_role()
    async def setup_tv(
        self, inter: discord.Interaction,
        creator: discord.VoiceChannel,
        category: discord.CategoryChannel,
        default_limit: int = 0,
        panel_channel: discord.TextChannel | None = None,
    ):
        await self.bot.db.execute(
            """INSERT INTO tempvoice_settings(guild_id, creator_id, category_id, default_limit, panel_channel)
               VALUES (?,?,?,?,?)
               ON CONFLICT(guild_id) DO UPDATE SET
                 creator_id=excluded.creator_id, category_id=excluded.category_id,
                 default_limit=excluded.default_limit, panel_channel=excluded.panel_channel""",
            (inter.guild_id, creator.id, category.id, default_limit, panel_channel.id if panel_channel else None),
        )
        if panel_channel:
            await panel_channel.send(embed=panel_embed(), view=TempVoicePanel())
        await inter.response.send_message(embed=success("Настройки TempVoice сохранены."), ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TempVoicePanel())

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member,
        before: discord.VoiceState, after: discord.VoiceState,
    ):
        bot = self.bot
        cfg = await bot.db.fetchone("SELECT * FROM tempvoice_settings WHERE guild_id=?", (member.guild.id,))
        if not cfg:
            return

        # вход в канал-создатель -> создаём личный канал
        if after.channel and after.channel.id == cfg["creator_id"]:
            cat = member.guild.get_channel(cfg["category_id"])
            ch = await member.guild.create_voice_channel(
                name=f"🔊 {member.display_name}",
                category=cat,
                user_limit=cfg["default_limit"] or 0,
                overwrites={
                    member: discord.PermissionOverwrite(manage_channels=True, move_members=True, mute_members=True),
                },
                reason="TempVoice create",
            )
            await bot.db.execute(
                "INSERT OR REPLACE INTO tempvoice_channels(channel_id, guild_id, owner_id) VALUES (?,?,?)",
                (ch.id, member.guild.id, member.id),
            )
            try:
                await member.move_to(ch)
            except discord.HTTPException:
                pass

        # выход из временного канала -> если пуст, удалить
        if before.channel and before.channel != after.channel:
            owned = await bot.db.fetchone("SELECT 1 FROM tempvoice_channels WHERE channel_id=?", (before.channel.id,))
            if owned and len(before.channel.members) == 0:
                try:
                    await before.channel.delete(reason="TempVoice empty")
                except discord.HTTPException:
                    pass
                await bot.db.execute("DELETE FROM tempvoice_channels WHERE channel_id=?", (before.channel.id,))


async def setup(bot):
    await bot.add_cog(TempVoiceCog(bot))
