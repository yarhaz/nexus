import structlog
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import NexusError
from app.middleware.correlation_id import CorrelationIdMiddleware, get_correlation_id
from app.middleware.logging import RequestLoggingMiddleware
from app.modules.health.router import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.ingestion.router import router as ingestion_router
from app.modules.entities.router import router as entities_router
from app.modules.relationships.router import router as relationships_router
from app.modules.userstate.router import router as userstate_router
from app.modules.search.router import router as search_router
from app.modules.actions.router import router as actions_router
from app.modules.ops.router import router as ops_router
from app.modules.scorecards.router import router as scorecards_router
from app.modules.actions.seeds import seed_built_in_actions
from app.clients.redis_client import close_redis


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer() if get_settings().debug else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG if get_settings().debug else logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    structlog.get_logger().info("nexus.startup", environment=get_settings().environment)
    await seed_built_in_actions()
    yield
    await close_redis()
    structlog.get_logger().info("nexus.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Nexus IDP API",
        version="0.1.0",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # Middleware (order matters: first added = outermost)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Correlation-ID"],
    )

    # Exception handlers
    @app.exception_handler(NexusError)
    async def nexus_error_handler(request: Request, exc: NexusError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "data": None,
                "meta": {},
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "correlation_id": get_correlation_id(request),
                    "timestamp": exc.timestamp,
                },
            },
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Any) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "data": None,
                "meta": {},
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Route {request.url.path} not found.",
                    "details": {},
                    "correlation_id": get_correlation_id(request),
                    "timestamp": "",
                },
            },
        )

    # Routers
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(ingestion_router)
    app.include_router(entities_router)
    app.include_router(relationships_router)
    app.include_router(userstate_router)
    app.include_router(search_router)
    app.include_router(actions_router)
    app.include_router(ops_router)
    app.include_router(scorecards_router)

    return app


app = create_app()
