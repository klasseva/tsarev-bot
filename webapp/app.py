from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config.settings import settings
from webapp.routers import (
    applications,
    auth,
    contracts,
    dashboard,
    embed_builder,
    inventory,
    monitor,
    plus,
    roles,
    sbory,
)
from webapp.routers import settings as settings_router

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app(bot):
    app = FastAPI(title="Tsarev Bot Admin", docs_url=None, redoc_url=None)
    app.state.bot = bot
    app.state.templates = templates

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        session_cookie="tsarev_session",
        max_age=60 * 60 * 24 * 7,
        same_site="lax",
        https_only=False,
    )

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    app.include_router(sbory.router)
    app.include_router(auth.router)
    app.include_router(dashboard.router)
    app.include_router(applications.router, prefix="/applications", tags=["applications"])
    app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
    app.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
    app.include_router(plus.router, prefix="/plus", tags=["plus"])
    app.include_router(roles.router, prefix="/roles", tags=["roles"])
    app.include_router(embed_builder.router, prefix="/embed", tags=["embed"])
    app.include_router(monitor.router, prefix="/monitor", tags=["monitor"])
    app.include_router(settings_router.router, prefix="/settings", tags=["settings"])

    return app
