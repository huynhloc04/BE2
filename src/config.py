from pydantic_settings import BaseSettings
from pydantic import PostgresDsn
from typing import Any
from constants import Environment


class Config(BaseSettings):
    database_url: str = 'postgresql+asyncpg://postgres:041101@localhost:5432/sharecv'
    echo_sql: bool = True
    test: bool = False
    project_name: str = "My FastAPI project"
    oauth_token_secret: str = "my_dev_secret"
    
    ENVIRONMENT: Environment = Environment.PRODUCTION
    APP_VERSION: str = "1"



settings = Config()

app_configs: dict[str, Any] = {"title": "App API"}
if settings.ENVIRONMENT.is_deployed:
    app_configs["root_path"] = f"/v{settings.APP_VERSION}"

if not settings.ENVIRONMENT.is_debug:
    app_configs["openapi_url"] = None  # hide docs