from __future__ import annotations

import json

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from database.db import db
from webapp.security import require_admin, require_login

router = APIRouter()


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request):
    types = await db.fetchall("SELECT * FROM application_types ORDER BY id DESC")
    apps = await db.fetchall(
        """SELECT a.*, t.title AS type_title FROM applications a
           LEFT JOIN application_types t ON t.id = a.type_id
           ORDER BY a.id DESC LIMIT 50"""
    )
    return request.app.state.templates.TemplateResponse(
        request,
        "applications.html",
        {"types": types, "apps": apps, "user": request.session["user"]},
    )


@router.post("/types/create")
@require_admin
async def create_type(
    request: Request,
    guild_id: int = Form(...),
    name: str = Form(...),
    title: str = Form(...),
    channel_id: int = Form(...),
    questions: str = Form(...),    # 'Имя|Возраст|Опыт'
    accept_role: int | None = Form(None),
    review_hours: int = Form(24),
    color: str = Form("#8B0000"),
    image_url: str | None = Form(None),
    description: str | None = Form(None),
):
    qs = [{"label": q.strip(), "long": True, "required": True}
          for q in questions.split("|") if q.strip()][:5]
    if not qs:
        raise HTTPException(400, "Нужен хотя бы один вопрос")
    await db.execute(
        """INSERT INTO application_types(guild_id, name, title, description, channel_id,
                                         review_hours, questions_json, accept_role, image_url, color)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (guild_id, name, title, description, channel_id, review_hours,
         json.dumps(qs, ensure_ascii=False), accept_role, image_url, color),
    )
    return RedirectResponse(url="/applications", status_code=303)


@router.post("/types/{type_id}/delete")
@require_admin
async def delete_type(request: Request, type_id: int):
    await db.execute("DELETE FROM application_types WHERE id=?", (type_id,))
    return RedirectResponse(url="/applications", status_code=303)


@router.get("/{app_id}", response_class=HTMLResponse)
@require_login
async def view_app(request: Request, app_id: int):
    app = await db.fetchone(
        """SELECT a.*, t.title AS type_title FROM applications a
           LEFT JOIN application_types t ON t.id = a.type_id WHERE a.id=?""",
        (app_id,),
    )
    if not app:
        raise HTTPException(404, "Заявка не найдена")
    answers = json.loads(app["answers_json"])
    return request.app.state.templates.TemplateResponse(
        request,
        "application_detail.html",
        {"app": app, "answers": answers},
    )


@router.post("/{app_id}/status")
@require_admin
async def update_status(request: Request, app_id: int, status: str = Form(...), comment: str = Form("")):
    if status not in ("pending", "review", "call", "accepted", "declined"):
        raise HTTPException(400, "Bad status")
    user = request.session["user"]
    await db.execute(
        """UPDATE applications SET status=?, moderator_id=?, comment=?,
                                   updated_at=datetime('now') WHERE id=?""",
        (status, int(user["id"]), comment or None, app_id),
    )
    return RedirectResponse(url="/applications", status_code=303)
