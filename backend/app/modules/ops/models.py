from datetime import datetime
from typing import Any
from pydantic import BaseModel


# ─── Health Summary ────────────────────────────────────────────────────────────

class ServiceHealthSummary(BaseModel):
    service_id: str
    service_name: str
    health_status: str = "Unknown"          # Healthy / Degraded / Unavailable / Unknown
    open_incidents: int = 0
    critical_incidents: int = 0
    open_bugs: int = 0
    open_work_items: int = 0
    vulnerable_packages: int = 0            # packages with cve_count > 0
    computed_at: datetime


class OpsHealthResponse(BaseModel):
    services: list[ServiceHealthSummary]
    total_open_incidents: int
    total_critical_incidents: int


# ─── Change Log ───────────────────────────────────────────────────────────────

class ChangeEvent(BaseModel):
    id: str
    event_type: str                          # push / workitem.updated / incident.opened / …
    entity_id: str
    entity_name: str
    entity_kind: str                         # Service / Incident / ADOWorkItem / …
    summary: str
    actor: str = ""
    occurred_at: datetime
    metadata: dict[str, Any] = {}


class ChangeLogResponse(BaseModel):
    events: list[ChangeEvent]
    total: int


# ─── Impact Analysis ──────────────────────────────────────────────────────────

class ImpactNode(BaseModel):
    entity_id: str
    entity_name: str
    entity_kind: str
    impact_level: str                        # direct / transitive
    relationship: str                        # e.g. "depends_on", "consumes"


class ImpactAnalysisResponse(BaseModel):
    root_entity_id: str
    root_entity_name: str
    affected: list[ImpactNode]
    total_affected: int
