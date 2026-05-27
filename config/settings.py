from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    token: str = ""
    main_guild_id: int = 0
    owner_id: int = 0
    log_level: str = "INFO"
    db_path: str = "database/bot.db"
    majestic_server_ids: list[int] = field(default_factory=list)

    @classmethod
    def load(cls) -> "Settings":
        ids = os.getenv("MAJESTIC_SERVER_IDS", "").strip()
        return cls(
            token=os.getenv("DISCORD_TOKEN", ""),
            main_guild_id=int(os.getenv("MAIN_GUILD_ID", "0") or 0),
            owner_id=int(os.getenv("OWNER_ID", "0") or 0),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            db_path=os.getenv("DB_PATH", "database/bot.db"),
            majestic_server_ids=[int(x) for x in ids.split(",") if x.strip().isdigit()],
        )
