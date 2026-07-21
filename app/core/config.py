from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings,SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env" 


class Settings(BaseSettings):
    secret_key: str = ""  
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    root_password: str = "hello" 
    root_code: str = "admin"

    server_debug: str = "true"
    db_url: str = ""

    telegram_bot_client_id: str = ""
        
    model_config = SettingsConfigDict(env_file=ENV_PATH,env_file_encoding="utf-8")
   
    @computed_field
    @property
    def debug(self) -> bool:
        return self.server_debug.lower() == "true"


settings = Settings()



