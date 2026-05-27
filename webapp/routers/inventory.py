from __future__ import annotations

import io
import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from database.db import db
from webapp.security import require_admin, require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request, q: str = ""):
    if q:
        rows = await db.fetchall(
            """SELECT i.*, c.name AS cat_name FROM inventory_items i
               LEFT JOIN inventory_categories c ON c.id = i.category_id
               WHERE i.name LIKE ? OR i.description LIKE ?
               ORDER BY i.id DESC LIMIT 200""",
            (f"%{q}%", f"%{q}%"),
        )
    else:
        rows = await db.fetchall(
            """SELECT i.*, c.name AS cat_name FROM inventory_items i
               LEFT JOIN inventory_categories c ON c.id = i.category_id
               ORDER BY i.id DESC LIMIT 200"""
        )
    cats = await db.fetchall("SELECT * FROM inventory_categories ORDER BY name")
    return templates.TemplateResponse(
        "inventory.html",
        {"request": request, "rows": rows, "cats": cats, "q": q, "user": request.session["user"]},
    )


@router.post("/create")
@require_admin
async def create(
    request: Request,
    guild_id: int = Form(...),
    name: str = Form(...),
    category_id: int | None = Form(None),
    owner_id: int | None = Form(None),
    description: str = Form(""),
):
    user = request.session["user"]
    cur = await db.execute(
        """INSERT INTO inventory_items(guild_id, category_id, name, owner_id, description)
           VALUES (?,?,?,?,?)""",
        (guild_id, category_id, name, owner_id, description),
    )
    await db.execute(
        "INSERT INTO inventory_log(item_id, actor_id, action) VALUES (?,?, 'create')",
        (cur.lastrowid, int(user["id"])),
    )
    return RedirectResponse(url="/inventory", status_code=303)


@router.post("/categories/create")
@require_admin
async def create_category(request: Request, guild_id: int = Form(...), name: str = Form(...)):
    await db.execute(
        "INSERT OR IGNORE INTO inventory_categories(guild_id, name) VALUES (?,?)",
        (guild_id, name),
    )
    return RedirectResponse(url="/inventory", status_code=303)


@router.post("/{item_id}/delete")
@require_admin
async def delete(request: Request, item_id: int):
    user = request.session["user"]
    await db.execute(
        "INSERT INTO inventory_log(item_id, actor_id, action) VALUES (?,?, 'delete')",
        (item_id, int(user["id"])),
    )
    await db.execute("DELETE FROM inventory_items WHERE id=?", (item_id,))
    return RedirectResponse(url="/inventory", status_code=303)


@router.get("/export")
@require_login
async def export(request: Request):
    rows = await db.fetchall("SELECT * FROM inventory_items")
    data = [dict(r) for r in rows]
    buf = io.BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=inventory.json"},
    )
