from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "UKI Spend & Investment Trends"
    database_url: str = "postgresql://lead_engine:lead_engine@localhost:5432/lead_engine"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
