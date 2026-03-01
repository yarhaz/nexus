from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.modules.relationships.models import EdgeCreate
from app.modules.relationships.repository import RelationshipRepository

router = APIRouter(prefix="/api/v1/relationships", tags=["relationships"])
_repo = RelationshipRepository()


def _ok(data: object, meta: dict | None = None) -> dict:
    return {"data": data, "meta": meta or {}, "error": None}


@router.post("/", status_code=201)
async def create_relationship(body: EdgeCreate, _=Depends(get_current_user)):
    edge = await _repo.create(body)
    return _ok(edge.model_dump())


@router.delete("/{edge_id}", status_code=204)
async def delete_relationship(edge_id: str, _=Depends(get_current_user)):
    deleted = await _repo.delete(edge_id)
    if not deleted:
        raise NotFoundError(f"Edge '{edge_id}' not found.")


@router.get("/entity/{entity_id}")
async def get_entity_relationships(entity_id: str, _=Depends(get_current_user)):
    edges = await _repo.get_edges_for_entity(entity_id)
    return _ok([e.model_dump() for e in edges])


@router.get("/graph/{entity_id}")
async def get_entity_graph(
    entity_id: str,
    depth: int = 2,
    _=Depends(get_current_user),
):
    graph = await _repo.get_graph(entity_id, depth=min(depth, 3))
    return _ok(graph.model_dump())
