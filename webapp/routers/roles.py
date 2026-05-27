from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from core.database import db
from core.security import require_admin, require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request):
    panels = await db.fetchall("SELECT * FROM role_panels ORDER BY id DESC")
    return templates.TemplateResponse(
        "roles.html",
        {"request": request, "panels": panels, "user": request.session["user"]},
    )


@router.get("/{panel_id}", response_class=HTMLResponse)
@require_login
async def detail(request: Request, panel_id: int):
    panel = await db.fetchone("SELECT * FROM role_panels WHERE id=?", (panel_id,))
    if not panel:
        return RedirectResponse(url="/roles")
    items = await db.fetchall(
        "SELECT * FROM role_panel_roles WHERE panel_id=? ORDER BY position",
        (panel_id,),
    )
    return templates.TemplateResponse(
        "_role_panel_detail.html",
        {"request": request, "panel": panel, "items": items},
    )


@router.post("/create")
@require_admin
async def create(
    request: Request,
    guild_id: int = Form(...),
    channel_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    color: str = Form("#5865F2"),
    multi: bool = Form(True),
):
    await db.execute(
        """INSERT INTO role_panels(guild_id, channel_id, title, description, color, multi)
           VALUES (?,?,?,?,?,?)""",
        (guild_id, channel_id, title, description, color, int(multi)),
    )
    return RedirectResponse(url="/roles", status_code=303)


@router.post("/{panel_id}/add")
@require_admin
async def add_role(
    request: Request, panel_id: int,
    role_id: int = Form(...),
    label: str = Form(...),
    emoji: str = Form(""),
    style: str = Form("secondary"),
):
    await db.execute(
        """INSERT OR REPLACE INTO role_panel_roles(panel_id, role_id, label, emoji, style)
           VALUES (?,?,?,?,?)""",
        (panel_id, role_id, label, emoji or None, style),
    )
    return RedirectResponse(url=f"/roles/{panel_id}", status_code=303)


@router.post("/{panel_id}/roles/{role_id}/delete")
@require_admin
async def delete_role(request: Request, panel_id: int, role_id: int):
    await db.execute(
        "DELETE FROM role_panel_roles WHERE panel_id=? AND role_id=?",
        (panel_id, role_id),
    )
    return RedirectResponse(url=f"/roles/{panel_id}", status_code=303)
