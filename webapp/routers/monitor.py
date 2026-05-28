from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.db import db
from webapp.security import require_admin, require_login

router = APIRouter()


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request):
    panels = await db.fetchall("SELECT * FROM monitor_panels ORDER BY id DESC")
    return request.app.state.templates.TemplateResponse(
        "monitor.html",
        {"request": request, "panels": panels, "user": request.session["user"]},
    )


@router.post("/create")
@require_admin
async def create(
    request: Request,
    guild_id: int = Form(...),
    channel_id: int = Form(...),
    server_ids: str = Form(...),
):
    await db.execute(
        """INSERT INTO monitor_panels(guild_id, channel_id, message_id, server_ids)
           VALUES (?,?, 0, ?)""",
        (guild_id, channel_id, server_ids),
    )
    return RedirectResponse(url="/monitor", status_code=303)


@router.post("/{panel_id}/delete")
@require_admin
async def delete(request: Request, panel_id: int):
    await db.execute("DELETE FROM monitor_panels WHERE id=?", (panel_id,))
    return RedirectResponse(url="/monitor", status_code=303)
