from typing import Annotated
from fastapi import APIRouter, Query, status
from app.core.deps import CurrentUser
from app.modules.catalog.models import ServiceCreate, ServiceEntity, ServiceUpdate
from app.modules.catalog.service import CatalogService
from app.core.pagination import CursorPage

router = APIRouter(prefix="/api/v1/catalog", tags=["catalog"])
_svc = CatalogService()


@router.get("/services", response_model=dict)
async def list_services(
    current_user: CurrentUser,
    cursor: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
) -> dict:
    page = await _svc.list_services(cursor, limit)
    return {"data": page.model_dump(), "meta": {}, "error": None}


@router.get("/services/{service_id}", response_model=dict)
async def get_service(service_id: str, current_user: CurrentUser) -> dict:
    entity = await _svc.get_service(service_id)
    return {"data": entity.model_dump(), "meta": {}, "error": None}


@router.post("/services", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_service(body: ServiceCreate, current_user: CurrentUser) -> dict:
    entity = await _svc.create_service(body)
    return {"data": entity.model_dump(), "meta": {}, "error": None}


@router.put("/services/{service_id}", response_model=dict)
async def update_service(service_id: str, body: ServiceUpdate, current_user: CurrentUser) -> dict:
    entity = await _svc.update_service(service_id, body)
    return {"data": entity.model_dump(), "meta": {}, "error": None}


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(service_id: str, current_user: CurrentUser) -> None:
    await _svc.delete_service(service_id)
