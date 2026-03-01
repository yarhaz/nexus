from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.modules.scorecards.service import ScorecardService

router = APIRouter(prefix="/api/v1/scorecards", tags=["scorecards"])
_svc = ScorecardService()


def _ok(data: object) -> dict:
    return {"data": data, "meta": {}, "error": None}


@router.get("/templates", response_model=None)
async def list_templates(_: dict = Depends(get_current_user)) -> dict:
    """List all available scorecard templates."""
    templates = _svc.list_templates()
    return _ok([t.model_dump(mode="json") for t in templates])


@router.get("/templates/{template_id}", response_model=None)
async def get_template(template_id: str, _: dict = Depends(get_current_user)) -> dict:
    """Get a specific scorecard template by ID."""
    tpl = _svc.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return _ok(tpl.model_dump(mode="json"))


@router.get("/services/{service_id}", response_model=None)
async def score_service(service_id: str, _: dict = Depends(get_current_user)) -> dict:
    """Evaluate all scorecard templates for a specific service."""
    results = await _svc.score_service(service_id)
    return _ok([r.model_dump(mode="json") for r in results])


@router.get("/services", response_model=None)
async def score_all_services(_: dict = Depends(get_current_user)) -> dict:
    """Evaluate all templates across all services (dashboard view)."""
    results = await _svc.score_all_services()
    return _ok([r.model_dump(mode="json") for r in results])
