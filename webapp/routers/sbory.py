from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/sbory", tags=["sbory"])
templates = Jinja2Templates(directory="webapp/templates")


# ---------- Pydantic-модели настроек ----------
class ChannelOption(BaseModel):
    id: str
    name: str
    category: Optional[str] = None
    emoji: Optional[str] = None


class RoleOption(BaseModel):
    id: str
    name: str


class SboryConfig(BaseModel):
    enabled: bool = True
    log_channel_id: Optional[str] = None
    creator_role_ids: List[str] = []

    hierarchy_enabled: bool = False
    hierarchy_role_ids: List[str] = []
    reserve_enabled: bool = False
    sort_enabled: bool = False

    # Основные функции
    auto_ready: bool = True
    moderation: bool = False
    edits: bool = False
    respawn: bool = False

    # Голосовой канал
    voice_create: bool = False
    voice_pick: bool = True

    # Напоминания
    remind_dm: bool = True
    remind_channel: bool = False

    # Дополнительно
    mvp: bool = False
    giveaway: bool = False


# ---------- Заглушки данных (замените на чтение из БД/Discord) ----------
def get_config(guild_id: str) -> SboryConfig:
    # TODO: загрузка из БД
    return SboryConfig()


def save_config(guild_id: str, cfg: SboryConfig) -> None:
    # TODO: сохранение в БД
    pass


def get_channels(guild_id: str) -> List[ChannelOption]:
    # TODO: получить из Discord API
    return [
        ChannelOption(id="1", name="majestic-news", category=None, emoji="🔔"),
        ChannelOption(id="2", name="правила", category="Информация", emoji="🟥"),
        ChannelOption(id="3", name="новости", category="Информация", emoji="🔔"),
        ChannelOption(id="4", name="staff-list", category="Информация", emoji="🔴"),
        ChannelOption(id="5", name="сборы", category="Информация", emoji="🔴"),
        ChannelOption(id="6", name="plus", category="Информация", emoji="🟩"),
    ]


def get_roles(guild_id: str) -> List[RoleOption]:
    # TODO: получить из Discord API
    return [
        RoleOption(id="r1", name="8 | Leader"),
        RoleOption(id="r2", name="7 | Deputy"),
        RoleOption(id="r3", name="admin (ಠ‿ಠ)"),
        RoleOption(id="r4", name="DS mod"),
        RoleOption(id="r5", name="Koller"),
        RoleOption(id="r6", name="6 | Legend"),
    ]


# ---------- Маршруты ----------
@router.get("", response_class=HTMLResponse)
async def sbory_page(request: Request, guild_id: str = "default"):
    return templates.TemplateResponse(
        "sbory.html",
        {
            "request": request,
            "cfg": get_config(guild_id),
            "channels": get_channels(guild_id),
            "roles": get_roles(guild_id),
            "guild_id": guild_id,
        },
    )


@router.post("/save")
async def sbory_save(cfg: SboryConfig, guild_id: str = "default"):
    save_config(guild_id, cfg)
    return {"ok": True}
