from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.modules.entities import models
from app.modules.entities.repository import EntityRepository
from app.modules.entities.service import EntityService

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])

# ─── Service instances ────────────────────────────────────────────────────────

_azure_resource_svc = EntityService(EntityRepository("AzureResource", models.AzureResourceEntity))
_environment_svc = EntityService(EntityRepository("Environment", models.EnvironmentEntity))
_team_svc = EntityService(EntityRepository("Team", models.TeamEntity))
_api_endpoint_svc = EntityService(EntityRepository("ApiEndpoint", models.ApiEndpointEntity))
_package_svc = EntityService(EntityRepository("Package", models.PackageEntity))
_incident_svc = EntityService(EntityRepository("Incident", models.IncidentEntity))
_ado_svc = EntityService(EntityRepository("ADOWorkItem", models.ADOWorkItemEntity))


def _ok(data: object, meta: dict | None = None) -> dict:
    return {"data": data, "meta": meta or {}, "error": None}


def _page(entities: list, next_cursor: str | None) -> dict:
    return _ok([e.model_dump() for e in entities], {"next_cursor": next_cursor})


# ─── AzureResource ────────────────────────────────────────────────────────────

@router.get("/azure-resources")
async def list_azure_resources(
    cursor: str | None = None,
    limit: int = 25,
    _=Depends(get_current_user),
):
    entities, next_cursor = await _azure_resource_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/azure-resources/{entity_id}")
async def get_azure_resource(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _azure_resource_svc.get(entity_id)).model_dump())


@router.post("/azure-resources", status_code=201)
async def create_azure_resource(body: models.AzureResourceCreate, _=Depends(get_current_user)):
    return _ok((await _azure_resource_svc.create(body)).model_dump())


@router.put("/azure-resources/{entity_id}")
async def update_azure_resource(entity_id: str, body: models.AzureResourceUpdate, _=Depends(get_current_user)):
    return _ok((await _azure_resource_svc.update(entity_id, body)).model_dump())


@router.delete("/azure-resources/{entity_id}", status_code=204)
async def delete_azure_resource(entity_id: str, _=Depends(get_current_user)):
    await _azure_resource_svc.delete(entity_id)


# ─── Environment ──────────────────────────────────────────────────────────────

@router.get("/environments")
async def list_environments(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _environment_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/environments/{entity_id}")
async def get_environment(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _environment_svc.get(entity_id)).model_dump())


@router.post("/environments", status_code=201)
async def create_environment(body: models.EnvironmentCreate, _=Depends(get_current_user)):
    return _ok((await _environment_svc.create(body)).model_dump())


@router.put("/environments/{entity_id}")
async def update_environment(entity_id: str, body: models.EnvironmentUpdate, _=Depends(get_current_user)):
    return _ok((await _environment_svc.update(entity_id, body)).model_dump())


@router.delete("/environments/{entity_id}", status_code=204)
async def delete_environment(entity_id: str, _=Depends(get_current_user)):
    await _environment_svc.delete(entity_id)


# ─── Team ─────────────────────────────────────────────────────────────────────

@router.get("/teams")
async def list_teams(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _team_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/teams/{entity_id}")
async def get_team(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _team_svc.get(entity_id)).model_dump())


@router.post("/teams", status_code=201)
async def create_team(body: models.TeamCreate, _=Depends(get_current_user)):
    return _ok((await _team_svc.create(body)).model_dump())


@router.put("/teams/{entity_id}")
async def update_team(entity_id: str, body: models.TeamUpdate, _=Depends(get_current_user)):
    return _ok((await _team_svc.update(entity_id, body)).model_dump())


@router.delete("/teams/{entity_id}", status_code=204)
async def delete_team(entity_id: str, _=Depends(get_current_user)):
    await _team_svc.delete(entity_id)


# ─── ApiEndpoint ──────────────────────────────────────────────────────────────

@router.get("/api-endpoints")
async def list_api_endpoints(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _api_endpoint_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/api-endpoints/{entity_id}")
async def get_api_endpoint(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _api_endpoint_svc.get(entity_id)).model_dump())


@router.post("/api-endpoints", status_code=201)
async def create_api_endpoint(body: models.ApiEndpointCreate, _=Depends(get_current_user)):
    return _ok((await _api_endpoint_svc.create(body)).model_dump())


@router.put("/api-endpoints/{entity_id}")
async def update_api_endpoint(entity_id: str, body: models.ApiEndpointUpdate, _=Depends(get_current_user)):
    return _ok((await _api_endpoint_svc.update(entity_id, body)).model_dump())


@router.delete("/api-endpoints/{entity_id}", status_code=204)
async def delete_api_endpoint(entity_id: str, _=Depends(get_current_user)):
    await _api_endpoint_svc.delete(entity_id)


# ─── Package ──────────────────────────────────────────────────────────────────

@router.get("/packages")
async def list_packages(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _package_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/packages/{entity_id}")
async def get_package(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _package_svc.get(entity_id)).model_dump())


@router.post("/packages", status_code=201)
async def create_package(body: models.PackageCreate, _=Depends(get_current_user)):
    return _ok((await _package_svc.create(body)).model_dump())


@router.put("/packages/{entity_id}")
async def update_package(entity_id: str, body: models.PackageUpdate, _=Depends(get_current_user)):
    return _ok((await _package_svc.update(entity_id, body)).model_dump())


@router.delete("/packages/{entity_id}", status_code=204)
async def delete_package(entity_id: str, _=Depends(get_current_user)):
    await _package_svc.delete(entity_id)


# ─── Incident ─────────────────────────────────────────────────────────────────

@router.get("/incidents")
async def list_incidents(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _incident_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/incidents/{entity_id}")
async def get_incident(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _incident_svc.get(entity_id)).model_dump())


@router.post("/incidents", status_code=201)
async def create_incident(body: models.IncidentCreate, _=Depends(get_current_user)):
    return _ok((await _incident_svc.create(body)).model_dump())


@router.put("/incidents/{entity_id}")
async def update_incident(entity_id: str, body: models.IncidentUpdate, _=Depends(get_current_user)):
    return _ok((await _incident_svc.update(entity_id, body)).model_dump())


@router.delete("/incidents/{entity_id}", status_code=204)
async def delete_incident(entity_id: str, _=Depends(get_current_user)):
    await _incident_svc.delete(entity_id)


# ─── ADOWorkItem ──────────────────────────────────────────────────────────────

@router.get("/ado-work-items")
async def list_ado_work_items(cursor: str | None = None, limit: int = 25, _=Depends(get_current_user)):
    entities, next_cursor = await _ado_svc.list(cursor, limit)
    return _page(entities, next_cursor)


@router.get("/ado-work-items/{entity_id}")
async def get_ado_work_item(entity_id: str, _=Depends(get_current_user)):
    return _ok((await _ado_svc.get(entity_id)).model_dump())


@router.post("/ado-work-items", status_code=201)
async def create_ado_work_item(body: models.ADOWorkItemCreate, _=Depends(get_current_user)):
    return _ok((await _ado_svc.create(body)).model_dump())


@router.put("/ado-work-items/{entity_id}")
async def update_ado_work_item(entity_id: str, body: models.ADOWorkItemUpdate, _=Depends(get_current_user)):
    return _ok((await _ado_svc.update(entity_id, body)).model_dump())


@router.delete("/ado-work-items/{entity_id}", status_code=204)
async def delete_ado_work_item(entity_id: str, _=Depends(get_current_user)):
    await _ado_svc.delete(entity_id)
