from fastapi import Header, HTTPException
from app.core.config import settings


def verify_api_key(x_api_key: str = Header(...)) -> None:
    """Valida el header X-Api-Key en cada petición."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="API Key inválida")
