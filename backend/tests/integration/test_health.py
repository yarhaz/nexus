import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from app.main import app


@pytest.mark.asyncio
async def test_liveness():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health/live")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_degraded():
    with patch("app.modules.health.router.ping_redis", new_callable=AsyncMock, return_value=False):
        with patch("app.modules.health.router.ping_gremlin", new_callable=AsyncMock, return_value=False):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/health/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"


@pytest.mark.asyncio
async def test_readiness_ok():
    with patch("app.modules.health.router.ping_redis", new_callable=AsyncMock, return_value=True):
        with patch("app.modules.health.router.ping_gremlin", new_callable=AsyncMock, return_value=True):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/health/ready")
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_unknown_route_returns_json_404():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "correlation_id" in body["error"]
