import json
import uuid
import typing
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, Type

import structlog
from pydantic import BaseModel

from app.clients.cosmos_gremlin import execute_query
from app.clients.redis_client import get_redis

logger = structlog.get_logger()
CACHE_TTL = 30

T = TypeVar("T", bound=BaseModel)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _serialize_prop(v: Any) -> Any:
    """Serialize a Python value to a Gremlin-compatible primitive."""
    if isinstance(v, (list, dict)):
        return json.dumps(v)
    if isinstance(v, datetime):
        return v.isoformat()
    if v is None:
        return ""
    return v


def _gremlin_prop(props: dict, key: str, default: Any = "") -> Any:
    val = props.get(key, [{}])
    if isinstance(val, list) and val:
        return val[0].get("value", default)
    return default


def _is_list_annotation(annotation: Any) -> bool:
    origin = typing.get_origin(annotation)
    if origin is list:
        return True
    if origin is typing.Union:
        return any(typing.get_origin(a) is list for a in typing.get_args(annotation))
    return False


def _is_datetime_annotation(annotation: Any) -> bool:
    if annotation is datetime:
        return True
    if typing.get_origin(annotation) is typing.Union:
        return datetime in typing.get_args(annotation)
    return False


class EntityRepository(Generic[T]):
    def __init__(self, label: str, entity_class: Type[T]) -> None:
        self.label = label
        self.entity_class = entity_class

    def _vertex_to_entity(self, vertex: Any) -> T:
        if not isinstance(vertex, dict):
            raise ValueError(f"Expected dict vertex, got {type(vertex)}")
        props = vertex.get("properties", {})
        fields: dict[str, Any] = {"id": vertex.get("id", "")}

        for field_name, field_info in self.entity_class.model_fields.items():
            if field_name == "id":
                continue
            raw = _gremlin_prop(props, field_name)
            ann = field_info.annotation

            if _is_list_annotation(ann):
                try:
                    fields[field_name] = json.loads(raw) if isinstance(raw, str) and raw else []
                except Exception:
                    fields[field_name] = []
            elif _is_datetime_annotation(ann):
                if raw and raw != "":
                    try:
                        fields[field_name] = datetime.fromisoformat(str(raw))
                    except Exception:
                        fields[field_name] = None
                else:
                    fields[field_name] = None
            else:
                default = field_info.default
                fields[field_name] = raw if raw != "" else (default if default is not None else "")

        return self.entity_class(**fields)

    async def list(self, cursor: str | None, limit: int) -> tuple[list[T], str | None]:
        cache_key = f"catalog:{self.label}:list:{cursor or 'start'}:{limit}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            return [self.entity_class(**e) for e in data["entities"]], data["next_cursor"]

        results = execute_query(
            f"g.V().hasLabel('{self.label}').order().by('created_at', incr).range(%(start)s, %(end)s)",
            {"start": 0, "end": limit + 1},
        )
        entities = [self._vertex_to_entity(v) for v in results[:limit]]
        next_cursor = results[limit].get("id") if len(results) > limit else None

        payload = {"entities": [e.model_dump(mode="json") for e in entities], "next_cursor": next_cursor}
        await redis.setex(cache_key, CACHE_TTL, json.dumps(payload))
        return entities, next_cursor

    async def get(self, entity_id: str) -> T | None:
        cache_key = f"catalog:{self.label}:{entity_id}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            return self.entity_class(**json.loads(cached))

        results = execute_query(
            f"g.V().hasLabel('{self.label}').has('id', %(id)s)",
            {"id": entity_id},
        )
        if not results:
            return None

        entity = self._vertex_to_entity(results[0])
        await redis.setex(cache_key, CACHE_TTL, entity.model_dump_json())
        return entity

    async def create(self, data: BaseModel) -> T:
        eid = str(uuid.uuid4())
        now = _utcnow()
        props = data.model_dump()
        props["id"] = eid
        props["created_at"] = now
        props["updated_at"] = now

        prop_str = "".join(f".property('{k}', %({k})s)" for k in props)
        params = {k: _serialize_prop(v) for k, v in props.items()}

        execute_query(f"g.addV('{self.label}'){prop_str}", params)

        entity_data = data.model_dump()
        entity_data["id"] = eid
        entity_data["created_at"] = now
        entity_data["updated_at"] = now
        return self.entity_class(**entity_data)

    async def update(self, entity_id: str, data: BaseModel) -> T | None:
        existing = await self.get(entity_id)
        if not existing:
            return None

        now = _utcnow()
        props = data.model_dump()
        props["updated_at"] = now

        prop_str = "".join(f".property('{k}', %({k})s)" for k in props)
        params = {k: _serialize_prop(v) for k, v in props.items()}
        params["id"] = entity_id

        execute_query(
            f"g.V().hasLabel('{self.label}').has('id', %(id)s){prop_str}",
            params,
        )
        redis = await get_redis()
        await redis.delete(f"catalog:{self.label}:{entity_id}")

        updated = existing.model_dump()
        updated.update(data.model_dump())
        updated["updated_at"] = now
        return self.entity_class(**updated)

    async def delete(self, entity_id: str) -> bool:
        existing = await self.get(entity_id)
        if not existing:
            return False
        execute_query(
            f"g.V().hasLabel('{self.label}').has('id', %(id)s).drop()",
            {"id": entity_id},
        )
        redis = await get_redis()
        await redis.delete(f"catalog:{self.label}:{entity_id}")
        return True

    async def find_by_field(self, field: str, value: str, limit: int = 25) -> list[T]:
        """Find entities where a specific property matches a value."""
        results = execute_query(
            f"g.V().hasLabel('{self.label}').has(%(field)s, %(value)s).limit(%(limit)s)",
            {"field": field, "value": value, "limit": limit},
        )
        return [self._vertex_to_entity(v) for v in results]
