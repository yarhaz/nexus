import json
import structlog

from app.clients.redis_client import get_redis
from app.modules.catalog.repository import ServiceRepository
from app.modules.entities.repository import EntityRepository
from app.modules.entities.models import TeamEntity, IncidentEntity, ADOWorkItemEntity
from app.modules.userstate.models import UserState

logger = structlog.get_logger()
USER_STATE_TTL = 60  # seconds


class UserStateService:
    def __init__(self) -> None:
        self._service_repo = ServiceRepository()
        self._team_repo: EntityRepository[TeamEntity] = EntityRepository("Team", TeamEntity)
        self._incident_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        self._ado_repo: EntityRepository[ADOWorkItemEntity] = EntityRepository("ADOWorkItem", ADOWorkItemEntity)

    async def get_for_user(self, user: dict) -> UserState:
        oid: str = user.get("oid", "")
        name: str = user.get("name", "")
        email: str = user.get("email", "")
        role: str = user.get("role", "Developer")

        cache_key = f"userstate:{oid}"
        redis = await get_redis()

        cached = await redis.get(cache_key)
        if cached:
            logger.debug("userstate.cache.hit", oid=oid)
            return UserState(**json.loads(cached))

        logger.debug("userstate.cache.miss", oid=oid)

        # 1. Services owned by the user's team
        my_services = []
        if email:
            team_hint = email.split("@")[0] if "@" in email else name
            all_services, _ = await self._service_repo.list(None, 100)
            my_services = [s for s in all_services if s.team and team_hint.lower() in s.team.lower()]

        # 2. Find user's team entity
        my_team: TeamEntity | None = None
        teams, _ = await self._team_repo.list(None, 50)
        for team in teams:
            if email in team.members or oid in team.members:
                my_team = team
                break

        # 3. Active incidents on user's services
        service_ids = {s.id for s in my_services}
        active_incidents: list[IncidentEntity] = []
        if service_ids:
            all_incidents, _ = await self._incident_repo.list(None, 100)
            active_incidents = [
                i for i in all_incidents
                if i.affected_service_id in service_ids and i.status != "resolved"
            ]

        # 4. Work items assigned to this user
        my_work_items: list[ADOWorkItemEntity] = []
        all_items, _ = await self._ado_repo.list(None, 100)
        my_work_items = [
            item for item in all_items
            if item.assignee and (
                item.assignee.lower() == email.lower()
                or item.assignee.lower() == name.lower()
            )
        ]

        state = UserState(
            user_id=oid,
            name=name,
            email=email,
            role=role,
            my_services=my_services,
            my_team=my_team,
            active_incidents=active_incidents,
            my_work_items=my_work_items,
        )

        await redis.setex(cache_key, USER_STATE_TTL, state.model_dump_json())
        return state

    async def invalidate(self, user_oid: str) -> None:
        redis = await get_redis()
        await redis.delete(f"userstate:{user_oid}")
