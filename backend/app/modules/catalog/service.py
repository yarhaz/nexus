from app.core.exceptions import NotFoundError, ConflictError
from app.core.pagination import CursorPage
from app.modules.catalog.models import ServiceCreate, ServiceEntity, ServiceUpdate
from app.modules.catalog.repository import ServiceRepository


class CatalogService:
    def __init__(self) -> None:
        self.repo = ServiceRepository()

    async def list_services(self, cursor: str | None, limit: int) -> CursorPage[ServiceEntity]:
        entities, next_cursor = await self.repo.list(cursor, limit)
        return CursorPage(
            data=entities,
            next_cursor=next_cursor,
            has_more=next_cursor is not None,
        )

    async def get_service(self, service_id: str) -> ServiceEntity:
        entity = await self.repo.get(service_id)
        if not entity:
            raise NotFoundError(f"Service '{service_id}' was not found.")
        return entity

    async def create_service(self, data: ServiceCreate) -> ServiceEntity:
        return await self.repo.create(data)

    async def update_service(self, service_id: str, data: ServiceUpdate) -> ServiceEntity:
        entity = await self.repo.update(service_id, data)
        if not entity:
            raise NotFoundError(f"Service '{service_id}' was not found.")
        return entity

    async def delete_service(self, service_id: str) -> None:
        deleted = await self.repo.delete(service_id)
        if not deleted:
            raise NotFoundError(f"Service '{service_id}' was not found.")
