from fastapi import HTTPException, Header, status
from typing import Annotated


async def verify_api_key(api_key: Annotated[str, Header(alias="X-API-Key")]) -> str:
    """
    Dependency to verify API key from request headers.
    
    Args:
        api_key: The API key from the X-API-Key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Please provide your API key in the X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Basic validation - ensure it's not empty and has minimum length
    if len(api_key.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key.strip()
