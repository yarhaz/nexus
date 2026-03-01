from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Rule definition ──────────────────────────────────────────────────────────

class ScorecardRule(BaseModel):
    """
    A single check within a scorecard template.
    The evaluator interprets `check_type` + `check_config` at runtime.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    weight: int = 1                          # relative weight for score calculation
    check_type: Literal[
        "field_present",          # entity has a non-empty field
        "field_equals",           # entity field equals a specific value
        "field_not_equals",       # entity field does not equal a value
        "tag_present",            # entity has a specific tag
        "no_critical_incidents",  # no open critical incidents linked to this service
        "no_open_bugs",           # no open Bug work items linked to service
        "no_vulnerable_packages", # zero packages with cve_count > 0 consumed by service
        "has_runbook",            # runbook_url is set
        "has_repo",               # repository_url is set
        "lifecycle_equals",       # lifecycle field equals value
    ] = "field_present"
    check_config: dict[str, Any] = {}        # e.g. {"field": "runbook_url"}
    remedy_url: str = ""                     # link to docs on how to fix


# ─── Scorecard template ───────────────────────────────────────────────────────

class ScorecardTemplate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    applies_to: list[str] = ["Service"]      # entity kinds this template targets
    rules: list[ScorecardRule] = []
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    model_config = {"from_attributes": True}


# ─── Scored result ────────────────────────────────────────────────────────────

class RuleResult(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    weight: int
    remedy_url: str = ""
    reason: str = ""                         # human-readable explanation


class ScorecardResult(BaseModel):
    """Evaluation result for one entity against one template."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_id: str
    template_name: str
    entity_id: str
    entity_name: str
    entity_kind: str
    score: int = 0                           # 0-100
    max_score: int = 0
    percentage: float = 0.0
    level: Literal["bronze", "silver", "gold", "platinum", "failing"] = "failing"
    rules: list[RuleResult] = []
    evaluated_at: datetime = Field(default_factory=utcnow)
