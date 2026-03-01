from typing import Any
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import get_settings

logger = structlog.get_logger()

try:
    from gremlin_python.driver import client as gremlin_client
    from gremlin_python.driver import serializer
    GREMLIN_AVAILABLE = True
except ImportError:
    GREMLIN_AVAILABLE = False
    logger.warning("gremlin_python not available — using mock")

_gremlin_client: Any = None


def get_gremlin_client() -> Any:
    global _gremlin_client
    if _gremlin_client is None:
        settings = get_settings()
        if GREMLIN_AVAILABLE:
            _gremlin_client = gremlin_client.Client(
                settings.cosmos_endpoint,
                "g",
                username=f"/dbs/{settings.cosmos_database}/colls/{settings.cosmos_container}",
                password=settings.cosmos_key,
                message_serializer=serializer.GraphSONSerializersV2d0(),
            )
        else:
            _gremlin_client = None
    return _gremlin_client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def execute_query(query: str, bindings: dict[str, Any] | None = None) -> list[Any]:
    client = get_gremlin_client()
    if client is None:
        logger.warning("gremlin.mock", query=query)
        return []
    callback = client.submitAsync(query, bindings or {})
    return callback.result().all().result()


async def ping_gremlin() -> bool:
    try:
        execute_query("g.V().limit(1).count()")
        return True
    except Exception as e:
        logger.warning("gremlin.ping_failed", error=str(e))
        return False
