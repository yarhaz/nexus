import json
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from app.clients.cosmos_gremlin import execute_query
from app.clients.redis_client import get_redis
from app.modules.relationships.models import EdgeCreate, EdgeEntity, EntityGraph, GraphEdge, GraphNode

logger = structlog.get_logger()
EDGE_CACHE_TTL = 60


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _edge_from_result(result: Any) -> EdgeEntity | None:
    if not isinstance(result, dict):
        return None
    props = result.get("properties", {})

    def p(k: str, d: Any = "") -> Any:
        v = props.get(k)
        if isinstance(v, list) and v:
            return v[0].get("value", d)
        return v or d

    raw_props = p("edge_properties", "{}")
    try:
        extra = json.loads(raw_props)
    except Exception:
        extra = {}

    return EdgeEntity(
        id=result.get("id", ""),
        source_id=p("source_id"),
        source_label=p("source_label"),
        target_id=p("target_id"),
        target_label=p("target_label"),
        relationship_type=result.get("label", ""),
        properties=extra,
        created_at=datetime.fromisoformat(p("created_at", _utcnow())),
    )


class RelationshipRepository:
    async def create(self, data: EdgeCreate) -> EdgeEntity:
        eid = str(uuid.uuid4())
        now = _utcnow()
        props_json = json.dumps(data.properties)

        execute_query(
            "g.V().has('id', %(source_id)s)"
            ".addE(%(rel_type)s)"
            ".to(g.V().has('id', %(target_id)s))"
            ".property('id', %(eid)s)"
            ".property('source_id', %(source_id)s)"
            ".property('source_label', %(source_label)s)"
            ".property('target_id', %(target_id)s)"
            ".property('target_label', %(target_label)s)"
            ".property('edge_properties', %(props)s)"
            ".property('created_at', %(created_at)s)",
            {
                "source_id": data.source_id,
                "target_id": data.target_id,
                "rel_type": data.relationship_type,
                "eid": eid,
                "source_label": data.source_label,
                "target_label": data.target_label,
                "props": props_json,
                "created_at": now,
            },
        )

        redis = await get_redis()
        await redis.delete(f"graph:{data.source_id}")
        await redis.delete(f"graph:{data.target_id}")

        return EdgeEntity(
            id=eid,
            source_id=data.source_id,
            source_label=data.source_label,
            target_id=data.target_id,
            target_label=data.target_label,
            relationship_type=data.relationship_type,
            properties=data.properties,
            created_at=datetime.fromisoformat(now),
        )

    async def delete(self, edge_id: str) -> bool:
        results = execute_query(
            "g.E().has('id', %(eid)s)",
            {"eid": edge_id},
        )
        if not results:
            return False

        edge_result = results[0]
        source_id = ""
        target_id = ""
        if isinstance(edge_result, dict):
            props = edge_result.get("properties", {})
            source_id = (props.get("source_id") or [{}])[0].get("value", "")
            target_id = (props.get("target_id") or [{}])[0].get("value", "")

        execute_query("g.E().has('id', %(eid)s).drop()", {"eid": edge_id})

        redis = await get_redis()
        if source_id:
            await redis.delete(f"graph:{source_id}")
        if target_id:
            await redis.delete(f"graph:{target_id}")
        return True

    async def get_edges_for_entity(self, entity_id: str) -> list[EdgeEntity]:
        """Return all edges (in + out) connected to an entity vertex."""
        results = execute_query(
            "g.V().has('id', %(id)s).bothE()",
            {"id": entity_id},
        )
        edges = []
        for r in results:
            e = _edge_from_result(r)
            if e:
                edges.append(e)
        return edges

    async def get_graph(self, entity_id: str, depth: int = 2) -> EntityGraph:
        """Build a subgraph around the given entity up to `depth` hops."""
        cache_key = f"graph:{entity_id}:{depth}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            return EntityGraph(**json.loads(cached))

        # Collect vertices and edges via BFS
        visited_vertices: dict[str, GraphNode] = {}
        collected_edges: list[GraphEdge] = []
        frontier = [entity_id]

        for _ in range(depth):
            if not frontier:
                break
            results = execute_query(
                "g.V().has('id', within(%(ids)s)).bothE().project('edge','src','tgt')"
                ".by().by(outV()).by(inV())",
                {"ids": frontier},
            )
            next_frontier: list[str] = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                edge = item.get("edge", {})
                src = item.get("src", {})
                tgt = item.get("tgt", {})

                def _node_name(v: dict) -> str:
                    p = v.get("properties", {})
                    n = p.get("name", [{}])
                    return n[0].get("value", v.get("id", "?")) if isinstance(n, list) and n else "?"

                src_id = src.get("id", "")
                tgt_id = tgt.get("id", "")

                if src_id and src_id not in visited_vertices:
                    visited_vertices[src_id] = GraphNode(
                        id=src_id,
                        label=src.get("label", ""),
                        name=_node_name(src),
                        entity_type=src.get("label", ""),
                    )
                    next_frontier.append(src_id)

                if tgt_id and tgt_id not in visited_vertices:
                    visited_vertices[tgt_id] = GraphNode(
                        id=tgt_id,
                        label=tgt.get("label", ""),
                        name=_node_name(tgt),
                        entity_type=tgt.get("label", ""),
                    )
                    next_frontier.append(tgt_id)

                eid = edge.get("id", str(uuid.uuid4()))
                collected_edges.append(
                    GraphEdge(
                        id=eid,
                        source_id=src_id,
                        target_id=tgt_id,
                        relationship_type=edge.get("label", ""),
                    )
                )

            frontier = [v for v in next_frontier if v not in visited_vertices]

        graph = EntityGraph(
            root_id=entity_id,
            nodes=list(visited_vertices.values()),
            edges=collected_edges,
        )
        await redis.setex(cache_key, EDGE_CACHE_TTL, graph.model_dump_json())
        return graph
