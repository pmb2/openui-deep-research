import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # API Settings
    PORT: int = Field(default=8000, env="PORT")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Groq API settings
    GROQ_API_KEY: str = Field(default="", env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="deepseek-r1-distill-llama-70b", env="GROQ_MODEL")

    # Ollama settings
    OLLAMA_HOST: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    OLLAMA_MODEL: str = Field(default="deepseek-r1-distill-llama-70b", env="OLLAMA_MODEL")
    USE_OLLAMA_FALLBACK: bool = Field(default=True, env="USE_OLLAMA_FALLBACK")

    # Perplexica settings
    PERPLEXICA_URL: str = Field(default="http://localhost:3000", env="PERPLEXICA_URL")

    # Application settings
    DATA_DIR: str = Field(default="/app/data", env="DATA_DIR")
    SESSION_TIMEOUT_MINUTES: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")

    # Security settings
    SECRET_KEY: str = Field(default_factory=lambda: os.urandom(24).hex())

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
