from __future__ import annotations

import json

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
    templates_list = await db.fetchall(
        "SELECT * FROM embed_templates ORDER BY id DESC LIMIT 50"
    )
    return templates.TemplateResponse(
        "embed_builder.html",
        {"request": request, "templates_list": templates_list, "user": request.session["user"]},
    )


@router.post("/preview", response_class=HTMLResponse)
@require_login
async def preview(
    request: Request,
    title: str = Form(""),
    description: str = Form(""),
    color: str = Form("#5865F2"),
    image: str = Form(""),
    thumbnail: str = Form(""),
    footer: str = Form(""),
):
    # рендерим только embed-карточку для HTMX swap
    return templates.TemplateResponse(
        "_embed_preview.html",
        {
            "request": request,
            "title": title, "description": description, "color": color,
            "image": image, "thumbnail": thumbnail, "footer": footer,
        },
    )


@router.post("/save")
@require_admin
async def save(
    request: Request,
    guild_id: int = Form(...),
    name: str = Form(...),
    title: str = Form(""),
    description: str = Form(""),
    color: str = Form("#5865F2"),
    image: str = Form(""),
    thumbnail: str = Form(""),
    footer: str = Form(""),
):
    payload = json.dumps({
        "title": title, "description": description, "color": color,
        "image": image, "thumbnail": thumbnail, "footer": footer,
    }, ensure_ascii=False)
    user = request.session["user"]
    await db.execute(
        """INSERT OR REPLACE INTO embed_templates(guild_id, name, payload, author_id)
           VALUES (?,?,?,?)""",
        (guild_id, name, payload, int(user["id"])),
    )
    return RedirectResponse(url="/embed", status_code=303)
