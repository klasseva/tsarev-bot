from functools import wraps

from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException

from config.settings import settings


def get_session_user(request: Request) -> dict | None:
    return request.session.get("user")


def _is_admin(bot, user_id: int) -> tuple[bool, str]:
    """Returns (is_admin, reason_if_not)."""
    if not settings.MAIN_GUILD_ID:
        return False, "MAIN_GUILD_ID not configured"

    guild = bot.get_guild(settings.MAIN_GUILD_ID)
    if guild is None:
        return False, "Bot is not in the main guild yet"

    member = guild.get_member(user_id)
    if member is None:
        return False, "You are not a member of the main guild"

    if settings.OWNER_ID and user_id == settings.OWNER_ID:
        return True, ""

    if member.guild_permissions.administrator:
        return True, ""

    admin_roles = set(settings.ADMIN_ROLE_IDS)
    if admin_roles and any(r.id in admin_roles for r in member.roles):
        return True, ""

    return False, "You do not have admin role on this server"


def require_login(func):
    """Decorator: redirect to /login if user is not authenticated."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return RedirectResponse("/login", status_code=302)
        return await func(request, *args, **kwargs)
    return wrapper


def require_admin(func):
    """Decorator: require login + admin permissions on the main guild."""
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return RedirectResponse("/login", status_code=302)
        bot = request.app.state.bot
        ok, reason = _is_admin(bot, int(user["id"]))
        if not ok:
            raise HTTPException(status_code=403, detail=reason)
        return await func(request, *args, **kwargs)
    return wrapper
