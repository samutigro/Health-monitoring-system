import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


API_KEY = os.getenv("API_KEY", "demo-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Missing or invalid API key.",
            },
        )
