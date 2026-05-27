from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from database.db import db
from webapp.security import require_login

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", response_class=HTMLResponse)
@require_login
async def dashboard(request: Request):
    # сводная статистика
    stats = {}
    queries = {
        "apps_total": "SELECT COUNT(*) AS c FROM applications",
        "apps_pending": "SELECT COUNT(*) AS c FROM applications WHERE status='pending'",
        "contracts_active": "SELECT COUNT(*) AS c FROM contracts WHERE status='active'",
        "contracts_done": "SELECT COUNT(*) AS c FROM contracts WHERE status='done'",
        "inventory_items": "SELECT COUNT(*) AS c FROM inventory_items",
        "plus_open": "SELECT COUNT(*) AS c FROM plus_events WHERE status='open'",
        "role_panels": "SELECT COUNT(*) AS c FROM role_panels",
        "afk_users": "SELECT COUNT(*) AS c FROM afk_users",
    }
    for key, sql in queries.items():
        try:
            row = await db.fetchone(sql)
            stats[key] = row["c"] if row else 0
        except Exception:
            stats[key] = 0

    # последние 5 заявок
    try:
        recent_apps = await db.fetchall(
            """SELECT a.id, a.status, a.created_at, t.title
               FROM applications a LEFT JOIN application_types t ON t.id = a.type_id
               ORDER BY a.id DESC LIMIT 5"""
        )
    except Exception:
        recent_apps = []

    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "stats": stats, "recent_apps": recent_apps, "user": request.session["user"]},
    )
