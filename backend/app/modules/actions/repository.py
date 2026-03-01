"""
Persistence for ActionManifest and ActionExecution using Redis (fast reads)
and Cosmos DB Gremlin (durable storage + graph relationships).

Action manifests are vertices labelled 'Action'.
Executions are vertices labelled 'ActionExecution' with an edge to their Action.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import structlog

from app.clients.cosmos_gremlin import execute_query
from app.clients.redis_client import get_redis
from app.modules.actions.models import ActionExecution, ActionManifest

logger = structlog.get_logger()

MANIFEST_CACHE_TTL = 300   # 5 min — manifests rarely change
EXEC_CACHE_TTL = 30        # 30 s — executions change frequently


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _p(props: dict, key: str, default: Any = "") -> Any:
    val = props.get(key, [{}])
    if isinstance(val, list) and val:
        return val[0].get("value", default)
    return default


def _props_to_manifest(vertex: Any) -> ActionManifest | None:
    if not isinstance(vertex, dict):
        return None
    props = vertex.get("properties", {})

    def pj(k: str, d: Any = None) -> Any:
        raw = _p(props, k, "")
        if raw == "":
            return d
        try:
            return json.loads(raw)
        except Exception:
            return raw

    return ActionManifest(
        id=vertex.get("id", ""),
        name=_p(props, "name"),
        description=_p(props, "description"),
        category=_p(props, "category"),
        executor_type=_p(props, "executor_type", "manual"),
        executor_config=pj("executor_config", {}),
        parameters=pj("parameters", []),
        approval=pj("approval", {}),
        allowed_roles=pj("allowed_roles", []),
        target_entity_types=pj("target_entity_types", []),
        tags=pj("tags", []),
        enabled=_p(props, "enabled", "true") != "false",
        created_by=_p(props, "created_by"),
        created_at=datetime.fromisoformat(_p(props, "created_at", _utcnow())),
        updated_at=datetime.fromisoformat(_p(props, "updated_at", _utcnow())),
    )


def _props_to_execution(vertex: Any) -> ActionExecution | None:
    if not isinstance(vertex, dict):
        return None
    props = vertex.get("properties", {})

    def pj(k: str, d: Any = None) -> Any:
        raw = _p(props, k, "")
        if raw == "":
            return d
        try:
            return json.loads(raw)
        except Exception:
            return raw

    def pd(k: str) -> datetime | None:
        raw = _p(props, k, "")
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw)
        except Exception:
            return None

    return ActionExecution(
        id=vertex.get("id", ""),
        action_id=_p(props, "action_id"),
        action_name=_p(props, "action_name"),
        target_entity_id=_p(props, "target_entity_id"),
        parameters=pj("parameters", {}),
        comment=_p(props, "comment"),
        status=_p(props, "status", "pending_approval"),
        triggered_by=_p(props, "triggered_by"),
        triggered_by_name=_p(props, "triggered_by_name"),
        approved_by=_p(props, "approved_by"),
        rejected_by=_p(props, "rejected_by"),
        rejection_reason=_p(props, "rejection_reason"),
        executor_run_id=_p(props, "executor_run_id"),
        result=pj("result", {}),
        error_message=_p(props, "error_message"),
        started_at=pd("started_at"),
        completed_at=pd("completed_at"),
        expires_at=pd("expires_at"),
        created_at=datetime.fromisoformat(_p(props, "created_at", _utcnow())),
        updated_at=datetime.fromisoformat(_p(props, "updated_at", _utcnow())),
    )


class ActionRepository:
    # ── Manifests ─────────────────────────────────────────────────────────────

    async def list_manifests(self, limit: int = 50) -> list[ActionManifest]:
        cache_key = f"actions:manifests:list:{limit}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return [ActionManifest(**m) for m in json.loads(cached)]

        results = execute_query(
            "g.V().hasLabel('Action').has('enabled', 'true').limit(%(limit)s)",
            {"limit": limit},
        )
        manifests = [m for v in results if (m := _props_to_manifest(v))]
        await redis.setex(cache_key, MANIFEST_CACHE_TTL, json.dumps([m.model_dump(mode="json") for m in manifests]))
        return manifests

    async def get_manifest(self, action_id: str) -> ActionManifest | None:
        cache_key = f"actions:manifest:{action_id}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return ActionManifest(**json.loads(cached))

        results = execute_query(
            "g.V().hasLabel('Action').has('id', %(id)s)",
            {"id": action_id},
        )
        if not results:
            return None
        m = _props_to_manifest(results[0])
        if m:
            await redis.setex(cache_key, MANIFEST_CACHE_TTL, m.model_dump_json())
        return m

    async def save_manifest(self, manifest: ActionManifest) -> ActionManifest:
        """Upsert an action manifest vertex."""
        now = _utcnow()
        props = {
            "id": manifest.id,
            "name": manifest.name,
            "description": manifest.description,
            "category": manifest.category,
            "executor_type": manifest.executor_type,
            "executor_config": json.dumps(manifest.executor_config),
            "parameters": json.dumps([p.model_dump() for p in manifest.parameters]),
            "approval": json.dumps(manifest.approval.model_dump()),
            "allowed_roles": json.dumps(manifest.allowed_roles),
            "target_entity_types": json.dumps(manifest.target_entity_types),
            "tags": json.dumps(manifest.tags),
            "enabled": str(manifest.enabled).lower(),
            "created_by": manifest.created_by,
            "created_at": manifest.created_at.isoformat() if manifest.created_at else now,
            "updated_at": now,
        }
        prop_str = "".join(f".property('{k}', %({k})s)" for k in props)
        # Upsert: merge vertex (add if not exists, update if exists)
        execute_query(
            f"g.V().hasLabel('Action').has('id', %(id)s).fold()"
            f".coalesce(unfold(), addV('Action').property('id', %(id)s)){prop_str}",
            props,
        )
        redis = await get_redis()
        await redis.delete(f"actions:manifest:{manifest.id}")
        await redis.delete(f"actions:manifests:list:50")
        return manifest

    async def delete_manifest(self, action_id: str) -> bool:
        results = execute_query("g.V().hasLabel('Action').has('id', %(id)s)", {"id": action_id})
        if not results:
            return False
        execute_query("g.V().hasLabel('Action').has('id', %(id)s).drop()", {"id": action_id})
        redis = await get_redis()
        await redis.delete(f"actions:manifest:{action_id}")
        await redis.delete(f"actions:manifests:list:50")
        return True

    # ── Executions ────────────────────────────────────────────────────────────

    async def create_execution(self, execution: ActionExecution) -> ActionExecution:
        now = _utcnow()
        props = {
            "id": execution.id,
            "action_id": execution.action_id,
            "action_name": execution.action_name,
            "target_entity_id": execution.target_entity_id,
            "parameters": json.dumps(execution.parameters),
            "comment": execution.comment,
            "status": execution.status,
            "triggered_by": execution.triggered_by,
            "triggered_by_name": execution.triggered_by_name,
            "approved_by": "",
            "rejected_by": "",
            "rejection_reason": "",
            "executor_run_id": "",
            "result": "{}",
            "error_message": "",
            "started_at": "",
            "completed_at": "",
            "expires_at": execution.expires_at.isoformat() if execution.expires_at else "",
            "created_at": now,
            "updated_at": now,
        }
        prop_str = "".join(f".property('{k}', %({k})s)" for k in props)
        execute_query(f"g.addV('ActionExecution'){prop_str}", props)

        # Link execution → action
        execute_query(
            "g.V().hasLabel('ActionExecution').has('id', %(exec_id)s)"
            ".addE('execution_of')"
            ".to(g.V().hasLabel('Action').has('id', %(action_id)s))",
            {"exec_id": execution.id, "action_id": execution.action_id},
        )
        return execution

    async def get_execution(self, exec_id: str) -> ActionExecution | None:
        cache_key = f"actions:exec:{exec_id}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return ActionExecution(**json.loads(cached))

        results = execute_query(
            "g.V().hasLabel('ActionExecution').has('id', %(id)s)",
            {"id": exec_id},
        )
        if not results:
            return None
        ex = _props_to_execution(results[0])
        if ex:
            await redis.setex(cache_key, EXEC_CACHE_TTL, ex.model_dump_json())
        return ex

    async def update_execution_status(
        self,
        exec_id: str,
        status: str,
        **extra_fields: Any,
    ) -> ActionExecution | None:
        now = _utcnow()
        updates: dict[str, Any] = {"status": status, "updated_at": now}
        updates.update(extra_fields)

        prop_str = "".join(f".property('{k}', %({k})s)" for k in updates)
        params = dict(updates)
        params["id"] = exec_id

        for k, v in params.items():
            if isinstance(v, (dict, list)):
                params[k] = json.dumps(v)
            elif isinstance(v, datetime):
                params[k] = v.isoformat()
            elif v is None:
                params[k] = ""

        execute_query(
            f"g.V().hasLabel('ActionExecution').has('id', %(id)s){prop_str}",
            params,
        )
        redis = await get_redis()
        await redis.delete(f"actions:exec:{exec_id}")
        return await self.get_execution(exec_id)

    async def list_executions(
        self,
        user_oid: str | None = None,
        action_id: str | None = None,
        limit: int = 25,
    ) -> list[ActionExecution]:
        if action_id:
            results = execute_query(
                "g.V().hasLabel('Action').has('id', %(action_id)s)"
                ".in('execution_of').limit(%(limit)s)",
                {"action_id": action_id, "limit": limit},
            )
        elif user_oid:
            results = execute_query(
                "g.V().hasLabel('ActionExecution').has('triggered_by', %(oid)s)"
                ".order().by('created_at', decr).limit(%(limit)s)",
                {"oid": user_oid, "limit": limit},
            )
        else:
            results = execute_query(
                "g.V().hasLabel('ActionExecution').order().by('created_at', decr).limit(%(limit)s)",
                {"limit": limit},
            )
        return [ex for v in results if (ex := _props_to_execution(v))]
