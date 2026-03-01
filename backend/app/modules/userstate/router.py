from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.modules.userstate.service import UserStateService

router = APIRouter(prefix="/api/v1/userstate", tags=["userstate"])
_svc = UserStateService()


@router.get("/me")
async def get_my_state(user: dict = Depends(get_current_user)):
    """Return pre-computed user state: owned services, team, incidents, work items."""
    state = await _svc.get_for_user(user)
    return {"data": state.model_dump(), "meta": {}, "error": None}


@router.post("/me/invalidate", status_code=204)
async def invalidate_my_state(user: dict = Depends(get_current_user)):
    """Force-invalidate the cached user state (triggers recompute on next GET)."""
    await _svc.invalidate(user.get("oid", ""))
