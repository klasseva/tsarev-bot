from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config.settings import MAIN_GUILD_ID
from database.db import db
from webapp.security import require_admin, require_login

router = APIRouter()


@router.get("", response_class=HTMLResponse)
@require_login
async def index(request: Request, status: str | None = None):
    sql = "SELECT * FROM contracts"
    params: list = []
    if status:
        sql += " WHERE status=?"
        params.append(status)
    sql += " ORDER BY id DESC LIMIT 100"
    rows = await db.fetchall(sql, params)

    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "contracts.html",
        {"rows": rows, "current_status": status, "user": request.session["user"]},
    )


def _opt_int(value: str | None) -> int | None:
    if value is None or value == "" or value == "null":
        return None
    try:
        return int(value)
    except ValueError:
        return None


@router.post("/create")
@require_admin
async def create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    reward: str = Form(""),
    deadline: str | None = Form(None),
    executor_id: str | None = Form(None),
    reward_role: str | None = Form(None),
    channel_id: str | None = Form(None),
):
    user = request.session["user"]
    await db.execute(
        """INSERT INTO contracts(guild_id, title, description, reward, deadline,
                                  executor_id, creator_id, reward_role, channel_id, status)
           VALUES (?,?,?,?,?,?,?,?,?, 'active')""",
        (MAIN_GUILD_ID, title, description, reward, deadline,
         _opt_int(executor_id), int(user["id"]),
         _opt_int(reward_role), _opt_int(channel_id)),
    )
    return RedirectResponse(url="/contracts", status_code=303)


@router.post("/{cid}/status")
@require_admin
async def set_status(request: Request, cid: int, status: str = Form(...)):
    completed = "datetime('now')" if status in ("done", "cancelled") else "NULL"
    await db.execute(
        f"UPDATE contracts SET status=?, completed_at={completed} WHERE id=?",
        (status, cid),
    )
    return RedirectResponse(url="/contracts", status_code=303)


@router.post("/{cid}/delete")
@require_admin
async def delete(request: Request, cid: int):
    await db.execute("DELETE FROM contracts WHERE id=?", (cid,))
    return RedirectResponse(url="/contracts", status_code=303)
