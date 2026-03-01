from pydantic import BaseModel
from typing import Any


class GitHubWebhookPayload(BaseModel):
    action: str = ""
    ref: str = ""
    repository: dict[str, Any] = {}
    pusher: dict[str, Any] = {}
    commits: list[dict[str, Any]] = []


class ADOWebhookPayload(BaseModel):
    eventType: str = ""
    resource: dict[str, Any] = {}
    resourceContainers: dict[str, Any] = {}


# ─── PagerDuty ────────────────────────────────────────────────────────────────

class PagerDutyWebhookPayload(BaseModel):
    """PagerDuty v3 webhook envelope."""
    event: dict[str, Any] = {}

    @property
    def event_type(self) -> str:
        return self.event.get("event_type", "")

    @property
    def incident_data(self) -> dict[str, Any]:
        return self.event.get("data", {})


# ─── OpsGenie ─────────────────────────────────────────────────────────────────

class OpsGenieWebhookPayload(BaseModel):
    action: str = ""
    alert: dict[str, Any] = {}
    source: dict[str, Any] = {}


# ─── ADO Work Item ────────────────────────────────────────────────────────────

class ADOWorkItemWebhookPayload(BaseModel):
    """Azure DevOps work item created/updated webhook."""
    eventType: str = ""       # workitem.created | workitem.updated
    resource: dict[str, Any] = {}
    resourceContainers: dict[str, Any] = {}


# ─── GitHub dependency graph manifest ────────────────────────────────────────

class GitHubDependencyManifest(BaseModel):
    """GitHub dependency submission API manifest entry."""
    name: str = ""
    file: dict[str, Any] = {}
    resolved: dict[str, Any] = {}   # package name → {package_url, relationship, scope}
