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
    events = await db.fetchall("SELECT * FROM plus_events ORDER BY id DESC LIMIT 50")
    # подсчёт участников
    counts = {}
    for e in events:
        row = await db.fetchone(
            "SELECT COUNT(*) AS c FROM plus_participants WHERE event_id=?",
            (e["id"],),
        )
        counts[e["id"]] = row["c"] if row else 0
    return templates.TemplateResponse(
        "plus.html",
        {"request": request, "events": events, "counts": counts, "user": request.session["user"]},
    )


@router.get("/{event_id}", response_class=HTMLResponse)
@require_login
async def detail(request: Request, event_id: int):
    event = await db.fetchone("SELECT * FROM plus_events WHERE id=?", (event_id,))
    if not event:
        return RedirectResponse(url="/plus")
    parts = await db.fetchall(
        "SELECT * FROM plus_participants WHERE event_id=? ORDER BY queue ASC",
        (event_id,),
    )
    return templates.TemplateResponse(
        "_plus_detail.html",
        {"request": request, "event": event, "parts": parts},
    )


@router.post("/create")
@require_admin
async def create(
    request: Request,
    guild_id: int = Form(...),
    channel_id: int = Form(...),
    title: str = Form(...),
    slots: int = Form(0),
    event_date: str | None = Form(None),
    role_id: int | None = Form(None),
    branch: str | None = Form(None),
    comment: str | None = Form(None),
    image_url: str | None = Form(None),
):
    user = request.session["user"]
    await db.execute(
        """INSERT INTO plus_events(guild_id, channel_id, title, event_date, slots,
                                   role_id, branch, comment, image_url, creator_id, status)
           VALUES (?,?,?,?,?,?,?,?,?,?, 'open')""",
        (guild_id, channel_id, title, event_date, slots,
         role_id, branch, comment, image_url, int(user["id"])),
    )
    return RedirectResponse(url="/plus", status_code=303)


@router.post("/{event_id}/close")
@require_admin
async def close(request: Request, event_id: int):
    await db.execute("UPDATE plus_events SET status='closed' WHERE id=?", (event_id,))
    return RedirectResponse(url="/plus", status_code=303)


@router.post("/{event_id}/participants/{user_id}/remove")
@require_admin
async def remove_participant(request: Request, event_id: int, user_id: int):
    await db.execute(
        "DELETE FROM plus_participants WHERE event_id=? AND user_id=?",
        (event_id, user_id),
    )
    # перенумеровать очередь
    rows = await db.fetchall(
        "SELECT user_id FROM plus_participants WHERE event_id=? ORDER BY queue ASC",
        (event_id,),
    )
    ev = await db.fetchone("SELECT slots FROM plus_events WHERE id=?", (event_id,))
    slots = int(ev["slots"] or 0) if ev else 0
    for i, r in enumerate(rows, start=1):
        is_extra = 1 if (slots and i > slots) else 0
        await db.execute(
            "UPDATE plus_participants SET queue=?, is_extra=? WHERE event_id=? AND user_id=?",
            (i, is_extra, event_id, r["user_id"]),
        )
    return RedirectResponse(url=f"/plus/{event_id}", status_code=303)
