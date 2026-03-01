import re
import uuid
import yaml
import structlog
from app.modules.catalog.models import ServiceCreate

logger = structlog.get_logger()

VALID_STATUSES = {"active", "deprecated", "experimental"}
VALID_LIFECYCLES = {"production", "staging", "development", "end-of-life"}


def parse_catalog_info(content: str, repo_url: str = "") -> ServiceCreate | None:
    """Parse catalog-info.yaml content into a ServiceCreate model."""
    try:
        doc = yaml.safe_load(content)
        if not isinstance(doc, dict):
            logger.warning("catalog_parser.invalid_yaml")
            return None

        metadata = doc.get("metadata", {})
        spec = doc.get("spec", {})

        name = metadata.get("name", "")
        if not name:
            logger.warning("catalog_parser.missing_name")
            return None

        status = spec.get("status", "active")
        if status not in VALID_STATUSES:
            status = "active"

        lifecycle = spec.get("lifecycle", "development")
        if lifecycle not in VALID_LIFECYCLES:
            lifecycle = "development"

        return ServiceCreate(
            name=name,
            description=metadata.get("description", ""),
            team=spec.get("owner", ""),
            status=status,
            lifecycle=lifecycle,
            repository_url=repo_url,
            runbook_url=spec.get("runbookUrl", ""),
            tags=metadata.get("tags", []),
        )
    except yaml.YAMLError as e:
        logger.warning("catalog_parser.yaml_error", error=str(e))
        return None


def make_deterministic_id(repo_url: str) -> str:
    """UUID v5 deterministic ID based on repo URL."""
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # URL namespace
    return str(uuid.uuid5(namespace, repo_url))
