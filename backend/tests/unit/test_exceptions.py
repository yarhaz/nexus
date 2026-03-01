import pytest
from app.core.exceptions import (
    NexusError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ConflictError,
    ExternalServiceError,
)


def test_not_found_has_correct_status():
    err = NotFoundError("Service not found")
    assert err.status_code == 404
    assert err.error_code == "ENTITY_NOT_FOUND"
    assert err.message == "Service not found"


def test_auth_error():
    err = AuthenticationError("Invalid token")
    assert err.status_code == 401
    assert err.error_code == "AUTHENTICATION_ERROR"


def test_authorization_error():
    err = AuthorizationError("Insufficient permissions")
    assert err.status_code == 403


def test_conflict_error():
    err = ConflictError("Entity already exists")
    assert err.status_code == 409


def test_external_service_error():
    err = ExternalServiceError("Cosmos DB unavailable")
    assert err.status_code == 502


def test_error_with_details():
    err = NotFoundError("Not found", details={"id": "123"}, correlation_id="abc")
    assert err.details == {"id": "123"}
    assert err.correlation_id == "abc"
    assert err.timestamp
