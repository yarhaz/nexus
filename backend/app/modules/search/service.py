import json
from typing import Any

import structlog

from app.clients.cosmos_gremlin import execute_query
from app.clients.redis_client import get_redis
from app.modules.search.models import SEARCHABLE_LABELS, NAME_PROPERTY, SearchHit, SearchResponse

logger = structlog.get_logger()
SEARCH_CACHE_TTL = 10  # seconds — short TTL so catalog changes are visible quickly


def _extract_prop(props: dict, key: str) -> str:
    val = props.get(key, [{}])
    if isinstance(val, list) and val:
        return str(val[0].get("value", ""))
    return ""


def _vertex_to_hit(vertex: Any, entity_type: str, query_lower: str) -> SearchHit | None:
    if not isinstance(vertex, dict):
        return None
    props = vertex.get("properties", {})
    name_key = NAME_PROPERTY.get(entity_type, "name")
    name = _extract_prop(props, name_key)
    description = _extract_prop(props, "description")

    tags_raw = _extract_prop(props, "tags")
    try:
        tags = json.loads(tags_raw) if tags_raw else []
    except Exception:
        tags = []

    # Relevance scoring: name match = 1.0, description match = 0.5
    name_lower = name.lower()
    desc_lower = description.lower()
    if query_lower in name_lower:
        score = 1.0
    elif query_lower in desc_lower:
        score = 0.5
    else:
        return None  # No match — shouldn't happen with hasTextContains but be safe

    return SearchHit(
        id=vertex.get("id", ""),
        entity_type=entity_type,
        name=name,
        description=description,
        score=score,
        tags=tags,
    )


class SearchService:
    async def search(
        self,
        query: str,
        types: list[str] | None = None,
        limit: int = 20,
    ) -> SearchResponse:
        q = query.strip()
        if not q:
            return SearchResponse(query=q, total=0, hits=[])

        labels = [t for t in (types or SEARCHABLE_LABELS) if t in SEARCHABLE_LABELS]
        cache_key = f"search:{q.lower()}:{'|'.join(sorted(labels))}:{limit}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            return SearchResponse(**json.loads(cached))

        q_lower = q.lower()
        hits: list[SearchHit] = []

        for label in labels:
            name_key = NAME_PROPERTY.get(label, "name")
            # Gremlin: match vertices whose name/title contains the query string (case-insensitive)
            # Cosmos DB Gremlin supports TextP.containing for full-text, but we use has() with
            # within() for exact; for contains we filter post-fetch on small sets.
            # In production upgrade to Azure AI Search for proper full-text.
            try:
                results = execute_query(
                    f"g.V().hasLabel('{label}').has('{name_key}').limit(200)",
                    {},
                )
                for v in results:
                    hit = _vertex_to_hit(v, label, q_lower)
                    if hit:
                        hits.append(hit)
            except Exception as exc:
                logger.warning("search.label.error", label=label, error=str(exc))

        # Sort by score desc, then name asc
        hits.sort(key=lambda h: (-h.score, h.name.lower()))
        hits = hits[:limit]

        response = SearchResponse(query=q, total=len(hits), hits=hits)
        await redis.setex(cache_key, SEARCH_CACHE_TTL, response.model_dump_json())
        return response
