"""
Built-in action manifest seeds.
Called once at startup to ensure the 6 standard platform actions exist.
Each manifest is upserted by deterministic ID so re-runs are idempotent.
"""
import hashlib
import structlog

from app.modules.actions.models import ActionManifest, ActionParameter, ApprovalConfig
from app.modules.actions.repository import ActionRepository

logger = structlog.get_logger()

# Deterministic IDs so re-seeding is always idempotent
def _seed_id(slug: str) -> str:
    return hashlib.sha256(f"seed:action:{slug}".encode()).hexdigest()[:32]


BUILT_IN_MANIFESTS: list[ActionManifest] = [

    # 1. Restart AKS Deployment
    ActionManifest(
        id=_seed_id("aks-restart-deployment"),
        name="Restart AKS Deployment",
        description="Perform a rolling restart of a Kubernetes deployment in AKS.",
        category="AKS",
        executor_type="ado_pipeline",
        executor_config={
            "organization": "",          # set via env override
            "project": "Platform",
            "pipeline_id": 101,
        },
        parameters=[
            ActionParameter(name="namespace", label="Namespace", type="string", required=True, description="Kubernetes namespace"),
            ActionParameter(name="deployment", label="Deployment name", type="string", required=True),
            ActionParameter(
                name="environment",
                label="Environment",
                type="select",
                required=True,
                options=["dev", "staging", "prod"],
            ),
        ],
        approval=ApprovalConfig(required=True, timeout_minutes=30, auto_approve_roles=["Admin"]),
        target_entity_types=["Service", "AzureResource"],
        tags=["aks", "kubernetes", "restart"],
    ),

    # 2. Scale AKS Deployment
    ActionManifest(
        id=_seed_id("aks-scale-deployment"),
        name="Scale AKS Deployment",
        description="Change the replica count for a deployment.",
        category="AKS",
        executor_type="ado_pipeline",
        executor_config={
            "organization": "",
            "project": "Platform",
            "pipeline_id": 102,
        },
        parameters=[
            ActionParameter(name="namespace", label="Namespace", type="string", required=True),
            ActionParameter(name="deployment", label="Deployment name", type="string", required=True),
            ActionParameter(name="replicas", label="Replica count", type="integer", required=True, default=2),
            ActionParameter(
                name="environment",
                label="Environment",
                type="select",
                required=True,
                options=["dev", "staging", "prod"],
            ),
        ],
        approval=ApprovalConfig(required=True, timeout_minutes=30, auto_approve_roles=["Admin"]),
        target_entity_types=["Service"],
        tags=["aks", "kubernetes", "scale"],
    ),

    # 3. Rotate Key Vault Secret
    ActionManifest(
        id=_seed_id("keyvault-rotate-secret"),
        name="Rotate Key Vault Secret",
        description="Generate a new version of a secret in Azure Key Vault and update the referencing service.",
        category="Secrets",
        executor_type="azure_function",
        executor_config={
            "function_url": "",          # set via env override
            "function_key": "",
        },
        parameters=[
            ActionParameter(name="vault_name", label="Key Vault name", type="string", required=True),
            ActionParameter(name="secret_name", label="Secret name", type="string", required=True),
            ActionParameter(name="notify_email", label="Notify email", type="string", required=False, default=""),
        ],
        approval=ApprovalConfig(required=True, approvers=[], timeout_minutes=60, auto_approve_roles=["Admin"]),
        target_entity_types=["Service", "AzureResource"],
        tags=["keyvault", "secrets", "security"],
    ),

    # 4. Trigger CI/CD Pipeline
    ActionManifest(
        id=_seed_id("ado-trigger-pipeline"),
        name="Trigger CI/CD Pipeline",
        description="Manually kick off an Azure DevOps pipeline for a service.",
        category="Pipelines",
        executor_type="ado_pipeline",
        executor_config={
            "organization": "",
            "project": "",
            "pipeline_id": 0,           # overridden per-execution via parameters
        },
        parameters=[
            ActionParameter(name="pipeline_id", label="Pipeline ID", type="integer", required=True),
            ActionParameter(
                name="branch",
                label="Branch",
                type="string",
                required=False,
                default="main",
                description="Source branch to build from",
            ),
            ActionParameter(
                name="environment",
                label="Target environment",
                type="select",
                required=True,
                options=["dev", "staging", "prod"],
            ),
        ],
        approval=ApprovalConfig(required=False, auto_approve_roles=["Admin", "Engineer"]),
        target_entity_types=["Service"],
        tags=["ado", "pipeline", "deploy"],
    ),

    # 5. Enable / Disable Feature Flag
    ActionManifest(
        id=_seed_id("feature-flag-toggle"),
        name="Toggle Feature Flag",
        description="Enable or disable an Azure App Configuration feature flag.",
        category="Feature Flags",
        executor_type="http_webhook",
        executor_config={
            "url": "",                   # Azure App Config REST endpoint
            "method": "PATCH",
            "headers": {"Content-Type": "application/json"},
        },
        parameters=[
            ActionParameter(name="flag_key", label="Flag key", type="string", required=True),
            ActionParameter(name="enabled", label="Enable flag", type="boolean", required=True, default=True),
            ActionParameter(name="label", label="Label (env)", type="string", required=False, default=""),
        ],
        approval=ApprovalConfig(required=False, auto_approve_roles=["Admin", "Engineer"]),
        target_entity_types=["Service"],
        tags=["feature-flag", "app-config"],
    ),

    # 6. Create Incident
    ActionManifest(
        id=_seed_id("create-incident"),
        name="Create Incident",
        description="Manually open an incident record for a service and page the on-call team.",
        category="Incidents",
        executor_type="http_webhook",
        executor_config={
            "url": "",                   # PagerDuty or OpsGenie events API
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
        },
        parameters=[
            ActionParameter(name="title", label="Incident title", type="string", required=True),
            ActionParameter(
                name="severity",
                label="Severity",
                type="select",
                required=True,
                options=["critical", "high", "medium", "low"],
            ),
            ActionParameter(name="service_id", label="Affected service ID", type="string", required=False, default=""),
            ActionParameter(name="description", label="Description", type="string", required=False, default=""),
        ],
        approval=ApprovalConfig(required=False),
        target_entity_types=["Service", "Incident"],
        tags=["incident", "oncall", "pagerduty"],
    ),
]


async def seed_built_in_actions() -> None:
    """Upsert all built-in action manifests. Safe to call on every startup."""
    repo = ActionRepository()
    for manifest in BUILT_IN_MANIFESTS:
        try:
            existing = await repo.get_manifest(manifest.id)
            if not existing:
                await repo.save_manifest(manifest)
                logger.info("actions.seed.created", action_id=manifest.id, name=manifest.name)
            else:
                logger.debug("actions.seed.exists", action_id=manifest.id, name=manifest.name)
        except Exception as exc:
            logger.warning("actions.seed.failed", action_id=manifest.id, error=str(exc))
