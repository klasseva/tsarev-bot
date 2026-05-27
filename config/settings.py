# webapp
DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
DISCORD_REDIRECT_URI: str = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
ADMIN_ROLE_IDS: list[int] = field(
    default_factory=lambda: [
        int(x) for x in os.getenv("ADMIN_ROLE_IDS", "").split(",") if x.strip().isdigit()
    ]
)
