from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, Field
import uuid


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Action manifest (stored in catalog) ─────────────────────────────────────

class ActionParameter(BaseModel):
    name: str
    label: str
    type: Literal["string", "integer", "boolean", "select"] = "string"
    required: bool = True
    default: Any = None
    options: list[str] = []          # For select type
    description: str = ""
    secret: bool = False             # Mask value in logs/UI


class ApprovalConfig(BaseModel):
    required: bool = False
    approvers: list[str] = []        # email / Entra OIDs
    timeout_minutes: int = 60        # auto-expire pending approval
    auto_approve_roles: list[str] = []  # e.g. ["Admin"] skip approval


class ActionManifest(BaseModel):
    """
    Describes a self-service action available in the portal.
    Stored in the catalog action registry.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=128)
    description: str = ""
    category: str = ""               # e.g. "AKS", "Secrets", "Pipelines"
    executor_type: Literal[
        "ado_pipeline",
        "github_actions",
        "http_webhook",
        "azure_function",
        "manual",
    ] = "manual"
    executor_config: dict[str, Any] = {}   # type-specific config (org, project, pipeline_id, …)
    parameters: list[ActionParameter] = []
    approval: ApprovalConfig = Field(default_factory=ApprovalConfig)
    allowed_roles: list[str] = []    # empty = any role; ["Admin"] = Admin only
    target_entity_types: list[str] = []  # which entity types this action applies to
    rollback_action_id: str = ""     # optional reverse action
    tags: list[str] = []
    enabled: bool = True
    created_by: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


# ─── Execution ────────────────────────────────────────────────────────────────

class ExecutionStatus(str):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ActionExecutionRequest(BaseModel):
    action_id: str
    target_entity_id: str = ""
    parameters: dict[str, Any] = {}
    comment: str = ""


class ActionExecution(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_id: str
    action_name: str
    target_entity_id: str = ""
    parameters: dict[str, Any] = {}
    comment: str = ""
    status: str = "pending_approval"
    triggered_by: str = ""            # user OID
    triggered_by_name: str = ""
    approved_by: str = ""
    rejected_by: str = ""
    rejection_reason: str = ""
    executor_run_id: str = ""         # external run ID (ADO run, GH run, etc.)
    result: dict[str, Any] = {}
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    expires_at: datetime | None = None   # approval expiry
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    model_config = {"from_attributes": True}


# ─── Approval ─────────────────────────────────────────────────────────────────

class ApprovalDecision(BaseModel):
    approved: bool
    reason: str = ""
