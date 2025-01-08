from pydantic_settings import BaseSettings, SettingsConfigDict

URSA_PERMISSIONS = 36768768

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="URSA_", env_file='.env')

    APPID: int
    TOKEN: str

settings = Settings()

INVITE_LINK = f'https://discord.com/oauth2/authorize?client_id={settings.APPID}&permissions={URSA_PERMISSIONS}&scope=bot'
