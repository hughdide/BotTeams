from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración global cargada desde variables de entorno o .env."""

    api_key: str = "changeme"
    postgres_host: str = "postgres"
    postgres_db: str = "botformacion"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "empresa_docs"
    anthropic_api_key: str = ""
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    llm_model: str = "claude-haiku-4-5-20251001"
    documents_path: str = "/app/storage/documents"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
