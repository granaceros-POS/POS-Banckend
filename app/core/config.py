from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SYSTEMDIR: str = "textos" 
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # 1 día

    # ¡Lee la URL de la base de datos!
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()
os.environ["SYSTEMDIR"] = settings.SYSTEMDIR