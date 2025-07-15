from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    TOKEN: SecretStr
    # Данные для подключения к Google Sheets
    SHEET_ID: SecretStr
    SERVICE_ACCOUNT_FILE: SecretStr

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')


config = Settings()
TRACKED_CHAT = 0
