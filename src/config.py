from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM API Keys
    GEMINI_API_KEY: str | None = Field(default=None)
    GROQ_API_KEY: str | None = Field(default=None)
    DEEPSEEK_API_KEY: str | None = Field(default=None)
    
    # GitHub Token
    GITHUB_TOKEN: str | None = Field(default=None)
    
    # Database URL
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./data/intelligence_graph.db")
    
    # Crawler Settings
    LOG_LEVEL: str = Field(default="INFO")
    MAX_CONCURRENT_REQUESTS: int = Field(default=25)
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30)
    RATE_LIMIT_RETRIES: int = Field(default=5)
    ENABLE_STEALTH_MODE: bool = Field(default=True)
    TARGET_SCRAPE_COUNT: int = Field(default=1000)
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    OUTPUT_DIR: Path = DATA_DIR / "output"
    SEED_DIR: Path = DATA_DIR / "seed"

settings = Settings()
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
settings.SEED_DIR.mkdir(parents=True, exist_ok=True)
