from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── AzureResource ────────────────────────────────────────────────────────────

class AzureResourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    resource_type: str = ""   # e.g. "Microsoft.Compute/virtualMachines"
    sku: str = ""
    region: str = ""
    subscription_id: str = ""
    resource_group: str = ""
    azure_resource_id: str = ""
    health_status: Literal["Healthy", "Degraded", "Unavailable", "Unknown"] = "Unknown"
    cost_stub: float = 0.0
    tags: list[str] = []


class AzureResourceCreate(AzureResourceBase):
    pass


class AzureResourceUpdate(AzureResourceBase):
    pass


class AzureResourceEntity(AzureResourceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["AzureResource"] = "AzureResource"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── Environment ──────────────────────────────────────────────────────────────

class EnvironmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    stage: Literal["dev", "staging", "prod", "dr"] = "dev"
    region: str = ""
    subscription_id: str = ""
    linked_services: list[str] = []
    tags: list[str] = []


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(EnvironmentBase):
    pass


class EnvironmentEntity(EnvironmentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["Environment"] = "Environment"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── Team ─────────────────────────────────────────────────────────────────────

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    entra_group_id: str = ""
    members: list[str] = []
    owned_services: list[str] = []
    on_call_schedule: str = ""
    tags: list[str] = []


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    pass


class TeamEntity(TeamBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["Team"] = "Team"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── ApiEndpoint ──────────────────────────────────────────────────────────────

class ApiEndpointBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    version: str = "1.0.0"
    base_url: str = ""
    spec_url: str = ""
    auth_scheme: Literal["none", "api-key", "oauth2", "jwt"] = "none"
    sla: str = ""
    consumers: list[str] = []
    owner_service_id: str = ""
    tags: list[str] = []


class ApiEndpointCreate(ApiEndpointBase):
    pass


class ApiEndpointUpdate(ApiEndpointBase):
    pass


class ApiEndpointEntity(ApiEndpointBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["ApiEndpoint"] = "ApiEndpoint"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── Package ──────────────────────────────────────────────────────────────────

class PackageBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: str = ""
    version: str = ""
    license: str = ""
    registry_url: str = ""
    consumers: list[str] = []
    cve_count: int = 0
    cve_ids: list[str] = []
    tags: list[str] = []


class PackageCreate(PackageBase):
    pass


class PackageUpdate(PackageBase):
    pass


class PackageEntity(PackageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["Package"] = "Package"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── Incident ─────────────────────────────────────────────────────────────────

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: str = ""
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    status: Literal["open", "investigating", "resolved"] = "open"
    affected_service_id: str = ""
    started_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None
    mttr_minutes: int | None = None
    source: str = ""
    source_id: str = ""
    tags: list[str] = []


class IncidentCreate(IncidentBase):
    pass


class IncidentUpdate(IncidentBase):
    pass


class IncidentEntity(IncidentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["Incident"] = "Incident"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── ADOWorkItem ──────────────────────────────────────────────────────────────

class ADOWorkItemBase(BaseModel):
    ado_id: int = 0
    work_item_type: Literal["Bug", "UserStory", "Task", "Feature", "Epic"] = "Task"
    title: str = Field(..., min_length=1, max_length=256)
    description: str = ""
    status: str = "New"
    sprint: str = ""
    assignee: str = ""
    linked_service_id: str = ""
    iteration_path: str = ""
    area_path: str = ""
    tags: list[str] = []


class ADOWorkItemCreate(ADOWorkItemBase):
    pass


class ADOWorkItemUpdate(ADOWorkItemBase):
    pass


class ADOWorkItemEntity(ADOWorkItemBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["ADOWorkItem"] = "ADOWorkItem"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}
