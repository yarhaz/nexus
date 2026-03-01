from typing import Annotated
from fastapi import Depends, Header, Request
from app.core.exceptions import AuthenticationError
from app.core.security import decode_token, extract_user
from app.config import Settings, get_settings


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    claims = decode_token(token, settings.azure_tenant_id, settings.azure_client_id)
    return extract_user(claims)


async def get_optional_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    if not authorization:
        return None
    try:
        return await get_current_user(request, settings, authorization)
    except AuthenticationError:
        return None


CurrentUser = Annotated[dict, Depends(get_current_user)]
OptionalUser = Annotated[dict | None, Depends(get_optional_user)]
AppSettings = Annotated[Settings, Depends(get_settings)]
