from typing import Generic, TypeVar
from pydantic import BaseModel

from app.core.exceptions import NotFoundError
from app.modules.entities.repository import EntityRepository

T = TypeVar("T", bound=BaseModel)


class EntityService(Generic[T]):
    def __init__(self, repo: EntityRepository[T]) -> None:
        self.repo = repo

    async def list(self, cursor: str | None, limit: int) -> tuple[list[T], str | None]:
        return await self.repo.list(cursor, limit)

    async def get(self, entity_id: str) -> T:
        entity = await self.repo.get(entity_id)
        if entity is None:
            raise NotFoundError(f"{self.repo.label} '{entity_id}' not found.")
        return entity

    async def create(self, data: BaseModel) -> T:
        return await self.repo.create(data)

    async def update(self, entity_id: str, data: BaseModel) -> T:
        entity = await self.repo.update(entity_id, data)
        if entity is None:
            raise NotFoundError(f"{self.repo.label} '{entity_id}' not found.")
        return entity

    async def delete(self, entity_id: str) -> None:
        deleted = await self.repo.delete(entity_id)
        if not deleted:
            raise NotFoundError(f"{self.repo.label} '{entity_id}' not found.")
