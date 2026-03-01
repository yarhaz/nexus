from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.actions.models import (
    ActionExecutionRequest,
    ActionManifest,
    ApprovalDecision,
)
from app.modules.actions.parser import parse_manifest
from app.modules.actions.service import ActionService

router = APIRouter(prefix="/api/v1/actions", tags=["actions"])
_svc = ActionService()


def _ok(data: object, meta: dict | None = None) -> dict:
    return {"data": data, "meta": meta or {}, "error": None}


# ─── Action registry ──────────────────────────────────────────────────────────

@router.get("")
async def list_actions(limit: int = Query(default=50, le=200), _=Depends(get_current_user)):
    """List all registered self-service actions."""
    actions = await _svc.list_actions(limit)
    return _ok([a.model_dump() for a in actions])


@router.get("/{action_id}")
async def get_action(action_id: str, _=Depends(get_current_user)):
    action = await _svc.get_action(action_id)
    return _ok(action.model_dump())


@router.post("", status_code=201)
async def register_action(
    body: ActionManifest,
    user: dict = Depends(get_current_user),
):
    """Register a new action manifest (Admin / PlatformEngineer only)."""
    action = await _svc.register_action(body, user)
    return _ok(action.model_dump())


@router.post("/parse", status_code=200)
async def parse_action_yaml(
    raw_yaml: str,
    _=Depends(get_current_user),
):
    """Validate and parse a YAML action manifest. Returns the parsed ActionManifest or validation errors."""
    manifest = parse_manifest(raw_yaml)
    return _ok(manifest.model_dump())


@router.put("/{action_id}")
async def update_action(
    action_id: str,
    body: ActionManifest,
    user: dict = Depends(get_current_user),
):
    action = await _svc.update_action(action_id, body, user)
    return _ok(action.model_dump())


@router.delete("/{action_id}", status_code=204)
async def delete_action(action_id: str, _=Depends(get_current_user)):
    await _svc.delete_action(action_id)


# ─── Executions ───────────────────────────────────────────────────────────────

@router.post("/{action_id}/execute", status_code=201)
async def execute_action(
    action_id: str,
    body: ActionExecutionRequest,
    user: dict = Depends(get_current_user),
):
    """Trigger an action execution. If approval is required the execution starts in pending_approval state."""
    body.action_id = action_id
    execution = await _svc.trigger(body, user)
    return _ok(execution.model_dump())


@router.get("/executions/me")
async def list_my_executions(
    limit: int = Query(default=25, le=100),
    user: dict = Depends(get_current_user),
):
    """List the current user's action executions."""
    executions = await _svc.list_executions(user_oid=user.get("oid"), limit=limit)
    return _ok([e.model_dump() for e in executions])


@router.get("/executions/all")
async def list_all_executions(
    action_id: str | None = None,
    limit: int = Query(default=25, le=100),
    _=Depends(get_current_user),
):
    """List all executions (optionally filtered by action)."""
    executions = await _svc.list_executions(action_id=action_id, limit=limit)
    return _ok([e.model_dump() for e in executions])


@router.get("/executions/{exec_id}")
async def get_execution(exec_id: str, _=Depends(get_current_user)):
    execution = await _svc.get_execution(exec_id)
    return _ok(execution.model_dump())


@router.post("/executions/{exec_id}/approve")
async def approve_execution(
    exec_id: str,
    body: ApprovalDecision,
    user: dict = Depends(get_current_user),
):
    """Approve or reject a pending execution."""
    execution = await _svc.decide_approval(exec_id, body, user)
    return _ok(execution.model_dump())


@router.post("/executions/{exec_id}/cancel", status_code=200)
async def cancel_execution(
    exec_id: str,
    user: dict = Depends(get_current_user),
):
    execution = await _svc.cancel_execution(exec_id, user)
    return _ok(execution.model_dump())
