from fastapi import APIRouter, Depends, Query
from app.core.security import get_current_user
from app.modules.ops.service import OpsService
from app.modules.ops.models import OpsHealthResponse, ChangeLogResponse, ImpactAnalysisResponse

router = APIRouter(prefix="/api/v1/ops", tags=["ops"])
_svc = OpsService()


def _ok(data: object) -> dict:
    return {"data": data, "meta": {}, "error": None}


@router.get("/health", response_model=None)
async def get_health_summary(
    _: dict = Depends(get_current_user),
) -> dict:
    """Overall health dashboard: per-service summary + aggregate incident counts."""
    result = await _svc.get_health_summary()
    return _ok(result.model_dump(mode="json"))


@router.get("/changelog", response_model=None)
async def get_change_log(
    limit: int = Query(50, ge=1, le=200),
    entity_id: str = Query(""),
    _: dict = Depends(get_current_user),
) -> dict:
    """Recent change events across services, incidents, and work items."""
    result = await _svc.get_change_log(limit=limit, entity_id=entity_id)
    return _ok(result.model_dump(mode="json"))


@router.get("/impact/{entity_id}", response_model=None)
async def get_impact_analysis(
    entity_id: str,
    depth: int = Query(3, ge=1, le=5),
    _: dict = Depends(get_current_user),
) -> dict:
    """Blast-radius analysis: which entities are affected if this entity has an incident."""
    result = await _svc.get_impact_analysis(entity_id=entity_id, depth=depth)
    return _ok(result.model_dump(mode="json"))
