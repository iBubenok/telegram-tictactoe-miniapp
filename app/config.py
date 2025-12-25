from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    telegram_bot_username: str = Field(..., alias="TELEGRAM_BOT_USERNAME")
    web_app_url: HttpUrl = Field(..., alias="WEB_APP_URL")
    app_domain: str = Field(..., alias="APP_DOMAIN")
    app_port: int = Field(8000, alias="APP_PORT")
    init_data_ttl_seconds: int = Field(86400, alias="INIT_DATA_TTL_SECONDS")
    request_timeout: float = Field(10.0, alias="REQUEST_TIMEOUT")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def bot_api_base(self) -> str:
        return f"https://api.telegram.org/bot{self.telegram_bot_token}"
