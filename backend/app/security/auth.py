from typing import Optional
from fastapi import Header, HTTPException, status
from app.config import settings

async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """
    Validates optional X-API-Key header if API key protection is enabled in settings.
    """
    api_key_required = getattr(settings, "API_KEY_REQUIRED", False)
    expected_api_key = getattr(settings, "API_KEY", None)

    if api_key_required and expected_api_key:
        if not x_api_key or x_api_key != expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-API-Key authentication header."
            )
    return x_api_key
