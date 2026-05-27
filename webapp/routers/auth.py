from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from webapp.discord_oauth import authorize_url, exchange_code, fetch_me, new_state
from webapp.security import _is_admin

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    state = new_state()
    request.session["oauth_state"] = state
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "oauth_url": authorize_url(state)},
    )


@router.get("/auth/callback")
async def auth_callback(request: Request, code: str | None = None, state: str | None = None):
    saved_state = request.session.pop("oauth_state", None)
    if not code or not state or state != saved_state:
        return RedirectResponse("/login?error=state", status_code=302)

    try:
        token_data = await exchange_code(code)
        user = await fetch_me(token_data["access_token"])
    except Exception:
        return RedirectResponse("/login?error=oauth", status_code=302)

    bot = request.app.state.bot
    ok, reason = _is_admin(bot, int(user["id"]))
    if not ok:
        templates = request.app.state.templates
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "oauth_url": authorize_url(new_state()),
                "error": f"Доступ запрещён: {reason}",
            },
            status_code=403,
        )

    request.session["user"] = {
        "id": user["id"],
        "username": user.get("global_name") or user["username"],
        "avatar": user.get("avatar"),
    }
    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


@router.get("/")
async def root(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)
