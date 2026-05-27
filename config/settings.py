import os
from dataclasses import dataclass, field


MAIN_GUILD_ID = int(os.getenv("MAIN_GUILD_ID", "0"))

@dataclass
class Settings:
    # === Discord Bot ===
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    MAIN_GUILD_ID: int = int(os.getenv("MAIN_GUILD_ID", "0") or "0")
    OWNER_ID: int = int(os.getenv("OWNER_ID", "0") or "0")

    # === Web Admin Panel ===
    DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI: str = os.getenv(
        "DISCORD_REDIRECT_URI",
        "http://localhost:8000/auth/callback",
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    ADMIN_ROLE_IDS: list[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_ROLE_IDS", "").split(",") if x.strip().isdigit()
        ]
    )

    # === Misc ===
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH: str = os.getenv("DB_PATH", "database/bot.db")
    MAJESTIC_SERVER_IDS: list[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("MAJESTIC_SERVER_IDS", "").split(",") if x.strip().isdigit()
        ]
    )


settings = Settings()
