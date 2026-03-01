from fastapi import APIRouter
from app.core.deps import CurrentUser

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me")
async def get_me(current_user: CurrentUser) -> dict:
    return {"data": current_user, "meta": {}, "error": None}
