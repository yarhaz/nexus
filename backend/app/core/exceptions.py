from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class NexusError(Exception):
    """Base exception for all Nexus errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.correlation_id = correlation_id
        self.timestamp = datetime.now(timezone.utc).isoformat()


class NotFoundError(NexusError):
    status_code = 404
    error_code = "ENTITY_NOT_FOUND"


class AuthenticationError(NexusError):
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(NexusError):
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"


class ValidationError(NexusError):
    status_code = 422
    error_code = "VALIDATION_ERROR"


class ConflictError(NexusError):
    status_code = 409
    error_code = "CONFLICT_ERROR"


class ExternalServiceError(NexusError):
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
