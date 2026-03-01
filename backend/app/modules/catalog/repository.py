import json
from typing import Any
import structlog
from app.clients.cosmos_gremlin import execute_query
from app.clients.redis_client import get_redis
from app.modules.catalog.models import ServiceCreate, ServiceEntity, ServiceUpdate
import uuid
from datetime import datetime, timezone

logger = structlog.get_logger()
CACHE_TTL = 30


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _gremlin_to_entity(vertex: Any) -> ServiceEntity:
    """Convert Gremlin vertex result to ServiceEntity."""
    if isinstance(vertex, dict):
        props = vertex.get("properties", {})
        def p(key: str, default: Any = "") -> Any:
            val = props.get(key, [{}])
            if isinstance(val, list) and val:
                return val[0].get("value", default)
            return default

        tags_raw = p("tags", "[]")
        try:
            tags = json.loads(tags_raw)
        except Exception:
            tags = []

        return ServiceEntity(
            id=vertex.get("id", ""),
            name=p("name"),
            description=p("description"),
            team=p("team"),
            status=p("status", "active"),
            lifecycle=p("lifecycle", "development"),
            repository_url=p("repository_url"),
            runbook_url=p("runbook_url"),
            tags=tags,
            created_at=datetime.fromisoformat(p("created_at", _utcnow())),
            updated_at=datetime.fromisoformat(p("updated_at", _utcnow())),
        )
    return ServiceEntity(id="unknown", name="unknown")


class ServiceRepository:
    async def list(self, cursor: str | None, limit: int) -> tuple[list[ServiceEntity], str | None]:
        cache_key = f"catalog:services:list:{cursor or 'start'}:{limit}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            logger.debug("cache.hit", key=cache_key)
            data = json.loads(cached)
            return [ServiceEntity(**e) for e in data["entities"]], data["next_cursor"]

        logger.debug("cache.miss", key=cache_key)
        # Cursor-based: use the cursor as offset vertex id
        query = "g.V().hasLabel('Service').order().by('created_at').limit(%(limit)s)"
        results = execute_query(
            "g.V().hasLabel('Service').order().by('created_at', incr).range(%(start)s, %(end)s)",
            {"start": 0, "end": limit + 1},
        )

        entities = [_gremlin_to_entity(v) for v in results[: limit]]
        next_cursor = results[limit].get("id") if len(results) > limit else None

        payload = {"entities": [e.model_dump(mode="json") for e in entities], "next_cursor": next_cursor}
        await redis.setex(cache_key, CACHE_TTL, json.dumps(payload))
        return entities, next_cursor

    async def get(self, service_id: str) -> ServiceEntity | None:
        cache_key = f"catalog:service:{service_id}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            logger.debug("cache.hit", key=cache_key)
            return ServiceEntity(**json.loads(cached))

        logger.debug("cache.miss", key=cache_key)
        results = execute_query(
            "g.V().hasLabel('Service').has('id', %(id)s)",
            {"id": service_id},
        )
        if not results:
            return None

        entity = _gremlin_to_entity(results[0])
        await redis.setex(cache_key, CACHE_TTL, entity.model_dump_json())
        return entity

    async def create(self, data: ServiceCreate) -> ServiceEntity:
        entity = ServiceEntity(**data.model_dump())
        now = _utcnow()
        tags_json = json.dumps(entity.tags)

        execute_query(
            "g.addV('Service')"
            ".property('id', %(id)s)"
            ".property('name', %(name)s)"
            ".property('description', %(description)s)"
            ".property('team', %(team)s)"
            ".property('status', %(status)s)"
            ".property('lifecycle', %(lifecycle)s)"
            ".property('repository_url', %(repository_url)s)"
            ".property('runbook_url', %(runbook_url)s)"
            ".property('tags', %(tags)s)"
            ".property('created_at', %(created_at)s)"
            ".property('updated_at', %(updated_at)s)",
            {
                "id": entity.id,
                "name": entity.name,
                "description": entity.description,
                "team": entity.team,
                "status": entity.status,
                "lifecycle": entity.lifecycle,
                "repository_url": entity.repository_url,
                "runbook_url": entity.runbook_url,
                "tags": tags_json,
                "created_at": now,
                "updated_at": now,
            },
        )
        return entity

    async def update(self, service_id: str, data: ServiceUpdate) -> ServiceEntity | None:
        existing = await self.get(service_id)
        if not existing:
            return None

        now = _utcnow()
        tags_json = json.dumps(data.tags)
        execute_query(
            "g.V().hasLabel('Service').has('id', %(id)s)"
            ".property('name', %(name)s)"
            ".property('description', %(description)s)"
            ".property('team', %(team)s)"
            ".property('status', %(status)s)"
            ".property('lifecycle', %(lifecycle)s)"
            ".property('repository_url', %(repository_url)s)"
            ".property('runbook_url', %(runbook_url)s)"
            ".property('tags', %(tags)s)"
            ".property('updated_at', %(updated_at)s)",
            {
                "id": service_id,
                "name": data.name,
                "description": data.description,
                "team": data.team,
                "status": data.status,
                "lifecycle": data.lifecycle,
                "repository_url": data.repository_url,
                "runbook_url": data.runbook_url,
                "tags": tags_json,
                "updated_at": now,
            },
        )
        redis = await get_redis()
        await redis.delete(f"catalog:service:{service_id}")
        return ServiceEntity(**{**existing.model_dump(), **data.model_dump(), "updated_at": datetime.fromisoformat(now)})

    async def delete(self, service_id: str) -> bool:
        existing = await self.get(service_id)
        if not existing:
            return False
        execute_query(
            "g.V().hasLabel('Service').has('id', %(id)s).drop()",
            {"id": service_id},
        )
        redis = await get_redis()
        await redis.delete(f"catalog:service:{service_id}")
        return True
