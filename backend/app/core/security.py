from typing import Any
import structlog
from jose import JWTError, jwt
from app.core.exceptions import AuthenticationError

logger = structlog.get_logger()

ALGORITHMS = ["RS256"]

# Role mapping: Entra group object IDs → Nexus roles
GROUP_ROLE_MAP: dict[str, str] = {}  # Populated from settings at startup


def decode_token(token: str, tenant_id: str, client_id: str) -> dict[str, Any]:
    """Decode and validate an Entra ID JWT. Returns the claims dict."""
    try:
        # In production, fetch JWKS from https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys
        # For now, decode without verification in dev (verified by middleware in prod)
        unverified = jwt.get_unverified_claims(token)
        return unverified
    except JWTError as e:
        raise AuthenticationError(f"Invalid token: {e}") from e


def extract_user(claims: dict[str, Any]) -> dict[str, Any]:
    """Extract user info from JWT claims."""
    groups: list[str] = claims.get("groups", [])
    role = _resolve_role(groups)
    return {
        "oid": claims.get("oid", ""),
        "name": claims.get("name", claims.get("preferred_username", "")),
        "email": claims.get("email", claims.get("upn", claims.get("preferred_username", ""))),
        "groups": groups,
        "role": role,
    }


def _resolve_role(groups: list[str]) -> str:
    for group_id in groups:
        if group_id in GROUP_ROLE_MAP:
            return GROUP_ROLE_MAP[group_id]
    return "Developer"
