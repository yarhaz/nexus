from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.modules.catalog.models import ServiceEntity
from app.modules.entities.models import TeamEntity, IncidentEntity, ADOWorkItemEntity


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PRStub(BaseModel):
    """Placeholder for GitHub PR data (Phase 1 stub — real data in Phase 2)."""
    id: str
    title: str
    repo: str
    url: str
    created_at: str


class DeploymentStub(BaseModel):
    """Placeholder for deployment data (Phase 1 stub — real data in Phase 2)."""
    id: str
    service_name: str
    environment: str
    status: str
    deployed_at: str


class UserState(BaseModel):
    user_id: str
    name: str
    email: str
    role: str

    # Owned / associated services
    my_services: list[ServiceEntity] = []

    # Team the user belongs to
    my_team: TeamEntity | None = None

    # Active incidents on the user's services
    active_incidents: list[IncidentEntity] = []

    # Open work items assigned to this user
    my_work_items: list[ADOWorkItemEntity] = []

    # Stubs — populated in later phases via external API calls
    my_prs: list[PRStub] = []
    my_deployments: list[DeploymentStub] = []

    computed_at: datetime = Field(default_factory=utcnow)
