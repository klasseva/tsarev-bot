from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from utils.errors import handle_app_error


class ErrorsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.tree.on_error = self.on_app_error

    async def on_app_error(self, inter: discord.Interaction, error: app_commands.AppCommandError):
        await handle_app_error(inter, error)


async def setup(bot):
    await bot.add_cog(ErrorsCog(bot))
