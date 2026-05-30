from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Product Manager"
    debug: bool = False

    database_url: str = "sqlite+aiosqlite:///./ai_pm.db"

    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"


settings = Settings()
