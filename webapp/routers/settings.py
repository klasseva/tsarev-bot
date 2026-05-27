from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.db import db
from webapp.security import require_admin, require_login

router = APIRouter()


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request):
    guilds = await db.fetchall("SELECT * FROM guild_settings")
    logs = await db.fetchall("SELECT * FROM log_channels")
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"guilds": guilds, "logs": logs, "user": request.session["user"]},
    )


@router.post("/guild")
@require_admin
async def upsert_guild(
    request: Request,
    guild_id: int = Form(...),
    admin_role: int | None = Form(None),
    mod_role: int | None = Form(None),
    log_channel: int | None = Form(None),
    welcome_channel: int | None = Form(None),
):
    await db.execute(
        """INSERT INTO guild_settings(guild_id, admin_role, mod_role, log_channel, welcome_channel)
           VALUES (?,?,?,?,?)
           ON CONFLICT(guild_id) DO UPDATE SET
             admin_role=excluded.admin_role,
             mod_role=excluded.mod_role,
             log_channel=excluded.log_channel,
             welcome_channel=excluded.welcome_channel""",
        (guild_id, admin_role, mod_role, log_channel, welcome_channel),
    )
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/log")
@require_admin
async def upsert_log(
    request: Request,
    guild_id: int = Form(...),
    category: str = Form(...),
    channel_id: int = Form(...),
):
    await db.execute(
        """INSERT INTO log_channels(guild_id, category, channel_id) VALUES (?,?,?)
           ON CONFLICT(guild_id, category) DO UPDATE SET channel_id=excluded.channel_id""",
        (guild_id, category, channel_id),
    )
    return RedirectResponse(url="/settings", status_code=303)
