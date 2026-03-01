import hashlib
import json
import asyncio
from typing import Any

import httpx
import structlog

from app.workers.celery_app import celery_app
from app.clients.redis_client import get_redis
from app.modules.ingestion.catalog_parser import parse_catalog_info, make_deterministic_id
from app.modules.catalog.repository import ServiceRepository
from app.modules.catalog.models import ServiceCreate, ServiceUpdate
from app.modules.entities.models import (
    PackageCreate,
    IncidentCreate,
    ADOWorkItemCreate,
)
from app.modules.entities.repository import EntityRepository
from app.modules.entities.models import PackageEntity, IncidentEntity, ADOWorkItemEntity

logger = structlog.get_logger()

DELTA_TTL = 86_400  # 24 h — how long to remember a content hash


# ─── Delta tracking ───────────────────────────────────────────────────────────

async def _has_changed(key: str, content: str) -> bool:
    """Return True if content is new or changed since last ingestion."""
    redis = await get_redis()
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    stored = await redis.get(f"delta:{key}")
    if stored and stored.decode() == content_hash:
        return False
    await redis.setex(f"delta:{key}", DELTA_TTL, content_hash)
    return True


# ─── Catalog-info.yaml ingestion ─────────────────────────────────────────────

@celery_app.task(name="ingestion.ingest_github_repo", bind=True, max_retries=3)
def ingest_github_repo(self, repo_url: str) -> None:
    """Fetch catalog-info.yaml from a GitHub repo and upsert the service."""
    async def _run() -> None:
        raw_url = _to_raw_url(repo_url)
        logger.info("ingestion.task.start", repo=repo_url)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(raw_url)
                if resp.status_code == 404:
                    logger.warning("ingestion.catalog_info.missing", repo=repo_url)
                    return
                resp.raise_for_status()
                content = resp.text
        except httpx.HTTPError as e:
            logger.error("ingestion.fetch_failed", repo=repo_url, error=str(e))
            raise self.retry(exc=e, countdown=30)

        if not await _has_changed(f"catalog:{repo_url}", content):
            logger.debug("ingestion.no_change", repo=repo_url)
            return

        service_data = parse_catalog_info(content, repo_url)
        if not service_data:
            logger.warning("ingestion.parse_failed", repo=repo_url)
            return

        entity_id = make_deterministic_id(repo_url)
        repo = ServiceRepository()
        existing = await repo.get(entity_id)

        if existing:
            await repo.update(entity_id, ServiceUpdate(**service_data.model_dump()))
            logger.info("ingestion.service.updated", id=entity_id)
        else:
            await repo.create(ServiceCreate(**service_data.model_dump()))
            logger.info("ingestion.service.created", id=entity_id)

    asyncio.run(_run())


# ─── GitHub dependency graph → Package entities ───────────────────────────────

@celery_app.task(name="ingestion.ingest_github_dependencies", bind=True, max_retries=3)
def ingest_github_dependencies(self, repo_url: str, owner: str, repo_name: str, token: str = "") -> None:
    """
    Fetch the GitHub dependency graph for a repo and upsert Package entities.
    Uses the GitHub Dependency Graph REST API (requires dependency-graph read permission).
    """
    async def _run() -> None:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        url = f"https://api.github.com/repos/{owner}/{repo_name}/dependency-graph/sbom"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 404:
                    logger.warning("ingestion.deps.no_sbom", repo=repo_url)
                    return
                resp.raise_for_status()
                sbom = resp.json()
        except httpx.HTTPError as e:
            logger.error("ingestion.deps.fetch_failed", repo=repo_url, error=str(e))
            raise self.retry(exc=e, countdown=60)

        content_str = json.dumps(sbom)
        if not await _has_changed(f"deps:{repo_url}", content_str):
            logger.debug("ingestion.deps.no_change", repo=repo_url)
            return

        pkg_repo: EntityRepository[PackageEntity] = EntityRepository("Package", PackageEntity)
        packages = sbom.get("sbom", {}).get("packages", [])

        for pkg in packages:
            name = pkg.get("name", "")
            version = pkg.get("versionInfo", "")
            license_str = " AND ".join(pkg.get("licenseConcluded", "").split()) or pkg.get("licenseDeclared", "")
            spdx_id = pkg.get("SPDXID", "")

            if not name or name == "":
                continue

            # Deterministic ID from package name + version
            pkg_id = hashlib.sha256(f"package:{name}:{version}".encode()).hexdigest()[:32]
            existing = await pkg_repo.get(pkg_id)

            service_id = make_deterministic_id(repo_url)
            consumers = [service_id] if service_id else []

            if existing:
                updated_consumers = list(set(existing.consumers) | set(consumers))
                await pkg_repo.update(
                    pkg_id,
                    PackageCreate(
                        name=name,
                        version=version,
                        license=license_str,
                        consumers=updated_consumers,
                    ),
                )
            else:
                create = PackageCreate(
                    name=name,
                    version=version,
                    license=license_str,
                    consumers=consumers,
                )
                await pkg_repo.create(create)

            logger.debug("ingestion.package.upserted", name=name, version=version)

        logger.info("ingestion.deps.done", repo=repo_url, packages=len(packages))

    asyncio.run(_run())


# ─── PagerDuty webhook → Incident entity ─────────────────────────────────────

@celery_app.task(name="ingestion.ingest_pagerduty_incident", bind=True, max_retries=2)
def ingest_pagerduty_incident(self, event_type: str, incident_data: dict[str, Any]) -> None:
    """Create or update an Incident entity from a PagerDuty webhook event."""
    async def _run() -> None:
        pd_id = incident_data.get("id", "")
        if not pd_id:
            return

        title = incident_data.get("title", "Untitled Incident")
        urgency = incident_data.get("urgency", "low")
        pd_status = incident_data.get("status", "triggered")
        service_name = incident_data.get("service", {}).get("summary", "")

        severity_map = {"high": "critical", "low": "low"}
        severity = severity_map.get(urgency, "medium")

        status_map = {"triggered": "open", "acknowledged": "investigating", "resolved": "resolved"}
        status = status_map.get(pd_status, "open")

        incident_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        entity_id = hashlib.sha256(f"incident:pagerduty:{pd_id}".encode()).hexdigest()[:32]

        existing = await incident_repo.get(entity_id)
        create_data = IncidentCreate(
            title=title,
            description=incident_data.get("summary", ""),
            severity=severity,
            status=status,
            source="pagerduty",
            source_id=pd_id,
            tags=[service_name] if service_name else [],
        )

        if existing:
            await incident_repo.update(entity_id, create_data)
            logger.info("ingestion.incident.updated", pd_id=pd_id, status=status)
        else:
            await incident_repo.create(create_data)
            logger.info("ingestion.incident.created", pd_id=pd_id, title=title)

    asyncio.run(_run())


# ─── OpsGenie webhook → Incident entity ──────────────────────────────────────

@celery_app.task(name="ingestion.ingest_opsgenie_alert", bind=True, max_retries=2)
def ingest_opsgenie_alert(self, action: str, alert_data: dict[str, Any]) -> None:
    """Create or update an Incident entity from an OpsGenie webhook alert."""
    async def _run() -> None:
        alert_id = alert_data.get("alertId", "")
        if not alert_id:
            return

        title = alert_data.get("message", "OpsGenie Alert")
        priority = alert_data.get("priority", "P3")
        og_status = alert_data.get("status", "open")

        priority_map = {"P1": "critical", "P2": "high", "P3": "medium", "P4": "low", "P5": "low"}
        severity = priority_map.get(priority, "medium")
        status = "resolved" if og_status == "closed" else "open"

        incident_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        entity_id = hashlib.sha256(f"incident:opsgenie:{alert_id}".encode()).hexdigest()[:32]

        existing = await incident_repo.get(entity_id)
        create_data = IncidentCreate(
            title=title,
            description=alert_data.get("description", ""),
            severity=severity,
            status=status,
            source="opsgenie",
            source_id=alert_id,
            tags=alert_data.get("tags", []),
        )

        if existing:
            await incident_repo.update(entity_id, create_data)
        else:
            await incident_repo.create(create_data)

        logger.info("ingestion.opsgenie.done", alert_id=alert_id, status=status)

    asyncio.run(_run())


# ─── ADO Work Item webhook → ADOWorkItem entity ───────────────────────────────

@celery_app.task(name="ingestion.ingest_ado_work_item", bind=True, max_retries=2)
def ingest_ado_work_item(self, event_type: str, resource: dict[str, Any]) -> None:
    """Upsert an ADOWorkItem entity from a work item created/updated event."""
    async def _run() -> None:
        ado_id = resource.get("id", 0)
        fields = resource.get("fields", {})

        if not ado_id:
            return

        title = fields.get("System.Title", "")
        wi_type = fields.get("System.WorkItemType", "Task")
        status = fields.get("System.State", "New")
        assignee_raw = fields.get("System.AssignedTo", {})
        assignee = assignee_raw.get("uniqueName", "") if isinstance(assignee_raw, dict) else str(assignee_raw)
        sprint = fields.get("System.IterationPath", "")
        area = fields.get("System.AreaPath", "")
        description = fields.get("System.Description", "")

        # Normalise work item type to our enum
        type_map = {
            "Bug": "Bug", "User Story": "UserStory", "Task": "Task",
            "Feature": "Feature", "Epic": "Epic",
        }
        normalised_type = type_map.get(wi_type, "Task")

        wi_repo: EntityRepository[ADOWorkItemEntity] = EntityRepository("ADOWorkItem", ADOWorkItemEntity)
        entity_id = hashlib.sha256(f"workitem:ado:{ado_id}".encode()).hexdigest()[:32]

        existing = await wi_repo.get(entity_id)
        create_data = ADOWorkItemCreate(
            ado_id=ado_id,
            work_item_type=normalised_type,
            title=title,
            description=description,
            status=status,
            sprint=sprint,
            assignee=assignee,
            area_path=area,
        )

        if existing:
            await wi_repo.update(entity_id, create_data)
            logger.info("ingestion.workitem.updated", ado_id=ado_id)
        else:
            await wi_repo.create(create_data)
            logger.info("ingestion.workitem.created", ado_id=ado_id, title=title)

    asyncio.run(_run())


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _to_raw_url(repo_url: str) -> str:
    url = repo_url.rstrip("/")
    if "github.com" in url:
        url = url.replace("https://github.com", "https://raw.githubusercontent.com")
        return f"{url}/HEAD/catalog-info.yaml"
    return f"{url}/catalog-info.yaml"
