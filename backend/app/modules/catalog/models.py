from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
import uuid

# Align with Phase 1 entity_type convention


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    team: str = ""
    status: Literal["active", "deprecated", "experimental"] = "active"
    lifecycle: Literal["production", "staging", "development", "end-of-life"] = "development"
    repository_url: str = ""
    runbook_url: str = ""
    tags: list[str] = []


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(ServiceBase):
    pass


class ServiceEntity(ServiceBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: Literal["Service"] = "Service"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}
