from fastapi import APIRouter
from app.clients.redis_client import ping_redis
from app.clients.cosmos_gremlin import ping_gremlin

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def liveness() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness() -> dict:
    redis_ok = await ping_redis()
    gremlin_ok = await ping_gremlin()
    status = "ok" if redis_ok and gremlin_ok else "degraded"
    return {
        "status": status,
        "dependencies": {
            "redis": "ok" if redis_ok else "unavailable",
            "gremlin": "ok" if gremlin_ok else "unavailable",
        },
    }
