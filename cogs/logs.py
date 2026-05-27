from __future__ import annotations

import discord
from discord.ext import commands

from config.constants import Colors
from utils.embeds import base_embed


class LogsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _send(self, guild: discord.Guild, category: str, emb: discord.Embed) -> None:
        row = await self.bot.db.fetchone(
            "SELECT channel_id FROM log_channels WHERE guild_id=? AND category=?",
            (guild.id, category),
        )
        if not row:
            return
        ch = guild.get_channel(row["channel_id"])
        if ch:
            try:
                await ch.send(embed=emb)
            except discord.HTTPException:
                pass

    # ===== messages =====
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        emb = base_embed("🗑️ Сообщение удалено",
                         f"**Автор:** {message.author.mention}\n**Канал:** {message.channel.mention}\n\n{message.content[:1900]}",
                         Colors.DANGER)
        await self._send(message.guild, "messages", emb)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot or before.content == after.content:
            return
        emb = base_embed("✏️ Сообщение изменено",
                         f"**Автор:** {before.author.mention}\n**Канал:** {before.channel.mention}",
                         Colors.WARNING)
        emb.add_field(name="До", value=before.content[:1024] or "_пусто_", inline=False)
        emb.add_field(name="После", value=after.content[:1024] or "_пусто_", inline=False)
        await self._send(before.guild, "messages", emb)

    # ===== members =====
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._send(member.guild, "members",
                         base_embed("➡️ Вход", member.mention, Colors.SUCCESS))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._send(member.guild, "members",
                         base_embed("⬅️ Выход", f"{member} ({member.id})", Colors.DANGER))

    # ===== voice =====
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel == after.channel:
            return
        if before.channel is None:
            text = f"🔊 {member.mention} зашёл в {after.channel.mention}"
        elif after.channel is None:
            text = f"🔇 {member.mention} вышел из {before.channel.mention}"
        else:
            text = f"↔️ {member.mention}: {before.channel.mention} → {after.channel.mention}"
        await self._send(member.guild, "voice", base_embed("Voice", text, Colors.INFO))

    # ===== bans =====
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self._send(guild, "moderation",
                         base_embed("🔨 Бан", f"{user} (`{user.id}`)", Colors.DANGER))

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await self._send(guild, "moderation",
                         base_embed("♻️ Разбан", f"{user} (`{user.id}`)", Colors.SUCCESS))

    # ===== roles =====
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        if not added and not removed:
            return
        emb = base_embed("🎚️ Изменение ролей", after.mention, Colors.INFO)
        if added:
            emb.add_field(name="Добавлено", value=", ".join(r.mention for r in added), inline=False)
        if removed:
            emb.add_field(name="Снято", value=", ".join(r.mention for r in removed), inline=False)
        await self._send(after.guild, "roles", emb)

    # ===== channels =====
    @commands.Cog.listener()
    async def on_guild_channel_create(self, ch):
        await self._send(ch.guild, "channels",
                         base_embed("➕ Канал создан", f"{ch.mention} (`{ch.id}`)", Colors.SUCCESS))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, ch):
        await self._send(ch.guild, "channels",
                         base_embed("➖ Канал удалён", f"`{ch.name}` (`{ch.id}`)", Colors.DANGER))


async def setup(bot):
    await bot.add_cog(LogsCog(bot))
