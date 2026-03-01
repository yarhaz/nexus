import hashlib
import hmac
import structlog
from fastapi import APIRouter, Header, HTTPException, Request, status
from app.config import get_settings
from app.modules.ingestion.models import (
    GitHubWebhookPayload,
    ADOWebhookPayload,
    PagerDutyWebhookPayload,
    OpsGenieWebhookPayload,
    ADOWorkItemWebhookPayload,
)
from app.modules.ingestion import tasks

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/ingestion", tags=["ingestion"])


def _verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/webhooks/github", status_code=status.HTTP_202_ACCEPTED)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(...),
    x_github_event: str = Header("push"),
) -> dict:
    settings = get_settings()
    body = await request.body()

    if not _verify_github_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    if x_github_event == "push":
        payload = GitHubWebhookPayload.model_validate_json(body)
        repo_url = payload.repository.get("html_url", "")
        owner = payload.repository.get("owner", {}).get("login", "")
        repo_name = payload.repository.get("name", "")
        default_branch = payload.repository.get("default_branch", "main")
        ref_branch = payload.ref.replace("refs/heads/", "")

        if ref_branch == default_branch and repo_url:
            tasks.ingest_github_repo.delay(repo_url)
            if owner and repo_name:
                tasks.ingest_github_dependencies.delay(
                    repo_url, owner, repo_name, settings.github_token
                )
            logger.info("ingestion.github.queued", repo=repo_url)

    return {"data": {"accepted": True}, "meta": {}, "error": None}


@router.post("/webhooks/ado", status_code=status.HTTP_202_ACCEPTED)
async def ado_webhook(
    request: Request,
    payload: ADOWebhookPayload,
) -> dict:
    settings = get_settings()
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.ado_webhook_secret}"
    if not hmac.compare_digest(auth, expected):
        raise HTTPException(status_code=401, detail="Invalid secret")

    if payload.eventType == "git.push":
        repo_url = payload.resource.get("repository", {}).get("remoteUrl", "")
        if repo_url:
            tasks.ingest_github_repo.delay(repo_url)

    return {"data": {"accepted": True}, "meta": {}, "error": None}


@router.post("/webhooks/pagerduty", status_code=status.HTTP_202_ACCEPTED)
async def pagerduty_webhook(
    request: Request,
    payload: PagerDutyWebhookPayload,
) -> dict:
    """PagerDuty v3 webhook — create/update Incident entities."""
    event_type = payload.event_type
    incident_data = payload.incident_data
    if event_type and incident_data.get("id"):
        tasks.ingest_pagerduty_incident.delay(event_type, incident_data)
        logger.info("ingestion.pagerduty.queued", event_type=event_type)
    return {"data": {"accepted": True}, "meta": {}, "error": None}


@router.post("/webhooks/opsgenie", status_code=status.HTTP_202_ACCEPTED)
async def opsgenie_webhook(
    request: Request,
    payload: OpsGenieWebhookPayload,
) -> dict:
    """OpsGenie webhook — create/update Incident entities."""
    if payload.alert.get("alertId"):
        tasks.ingest_opsgenie_alert.delay(payload.action, payload.alert)
        logger.info("ingestion.opsgenie.queued", action=payload.action)
    return {"data": {"accepted": True}, "meta": {}, "error": None}


@router.post("/webhooks/ado/workitems", status_code=status.HTTP_202_ACCEPTED)
async def ado_workitem_webhook(
    request: Request,
    payload: ADOWorkItemWebhookPayload,
) -> dict:
    """ADO work item created/updated webhook — upsert ADOWorkItem entities."""
    settings = get_settings()
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.ado_webhook_secret}"
    if not hmac.compare_digest(auth, expected):
        raise HTTPException(status_code=401, detail="Invalid secret")

    if payload.eventType in ("workitem.created", "workitem.updated") and payload.resource.get("id"):
        tasks.ingest_ado_work_item.delay(payload.eventType, payload.resource)
        logger.info("ingestion.ado_workitem.queued", event_type=payload.eventType)

    return {"data": {"accepted": True}, "meta": {}, "error": None}
