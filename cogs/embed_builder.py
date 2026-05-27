from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.checks import has_mod_role
from views.embed_builder import EmbedBuilderModal


class EmbedBuilderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="embed", description="Конструктор embed-сообщений")
    @has_mod_role()
    async def embed_cmd(self, inter: discord.Interaction, channel: discord.TextChannel | None = None):
        await inter.response.send_modal(EmbedBuilderModal(channel))


async def setup(bot):
    await bot.add_cog(EmbedBuilderCog(bot))
