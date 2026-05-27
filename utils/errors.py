from __future__ import annotations

import traceback

import discord
from discord import app_commands

from utils.embeds import error as err_embed
from utils.logger import setup_logger
from utils.checks import MissingPermission

log = setup_logger("errors")


async def handle_app_error(inter: discord.Interaction, error: app_commands.AppCommandError) -> None:
    if isinstance(error, MissingPermission):
        await _send(inter, err_embed(error.msg))
        return
    if isinstance(error, app_commands.CommandOnCooldown):
        await _send(inter, err_embed(f"Подождите ещё `{error.retry_after:.1f}` сек."))
        return
    if isinstance(error, app_commands.MissingPermissions):
        await _send(inter, err_embed("У вас нет прав Discord для этой команды."))
        return
    if isinstance(error, app_commands.BotMissingPermissions):
        await _send(inter, err_embed("У бота недостаточно прав."))
        return

    log.error("Unhandled app error: %s", "".join(traceback.format_exception(error)))
    await _send(inter, err_embed("Произошла внутренняя ошибка. Логи отправлены администраторам."))


async def _send(inter: discord.Interaction, embed: discord.Embed) -> None:
    try:
        if inter.response.is_done():
            await inter.followup.send(embed=embed, ephemeral=True)
        else:
            await inter.response.send_message(embed=embed, ephemeral=True)
    except discord.HTTPException:
        pass
