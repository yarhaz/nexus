from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.search.service import SearchService

router = APIRouter(prefix="/api/v1/search", tags=["search"])
_svc = SearchService()


@router.get("")
async def search_catalog(
    q: str = Query(..., min_length=1, max_length=256, description="Search query"),
    types: list[str] | None = Query(default=None, description="Filter by entity types"),
    limit: int = Query(default=20, ge=1, le=100),
    _=Depends(get_current_user),
):
    """
    Full-text search across all catalog entity types.
    Returns ranked hits with entity_type, name, description, and tags.
    """
    result = await _svc.search(query=q, types=types, limit=limit)
    return {"data": result.model_dump(), "meta": {}, "error": None}
