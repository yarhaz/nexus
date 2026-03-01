"""
YAML action manifest parser and validator.

Action manifests are YAML files stored in repos (e.g. .nexus/actions/*.yaml).
They declare self-service actions engineers can trigger from the portal.

Example manifest:
-----------------
name: Scale AKS Deployment
description: Scale replicas for an AKS deployment
category: AKS
executor_type: ado_pipeline
executor_config:
  organization: my-org
  project: platform
  pipeline_id: 42
parameters:
  - name: replicas
    label: Replica count
    type: integer
    required: true
    default: 2
    description: Target replica count (1-20)
  - name: deployment_name
    label: Deployment name
    type: string
    required: true
approval:
  required: true
  approvers:
    - platform-team@company.com
  timeout_minutes: 30
allowed_roles:
  - Developer
  - PlatformEngineer
target_entity_types:
  - Service
"""

from typing import Any

import yaml

from app.core.exceptions import ValidationError
from app.modules.actions.models import ActionManifest, ActionParameter, ApprovalConfig

VALID_EXECUTOR_TYPES = {"ado_pipeline", "github_actions", "http_webhook", "azure_function", "manual"}
VALID_PARAM_TYPES = {"string", "integer", "boolean", "select"}
VALID_ROLES = {"Developer", "PlatformEngineer", "TeamLead", "Admin"}


def parse_manifest(raw_yaml: str) -> ActionManifest:
    """Parse and validate a YAML action manifest. Returns an ActionManifest or raises ValidationError."""
    try:
        data: dict[str, Any] = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML: {e}") from e

    if not isinstance(data, dict):
        raise ValidationError("Manifest must be a YAML mapping.")

    _require(data, "name", str)
    _require(data, "executor_type", str)

    executor_type = data["executor_type"]
    if executor_type not in VALID_EXECUTOR_TYPES:
        raise ValidationError(f"executor_type must be one of {VALID_EXECUTOR_TYPES}, got '{executor_type}'")

    parameters: list[ActionParameter] = []
    for i, raw_param in enumerate(data.get("parameters", [])):
        if not isinstance(raw_param, dict):
            raise ValidationError(f"parameters[{i}] must be a mapping")
        _require(raw_param, "name", str, context=f"parameters[{i}]")
        _require(raw_param, "label", str, context=f"parameters[{i}]")
        ptype = raw_param.get("type", "string")
        if ptype not in VALID_PARAM_TYPES:
            raise ValidationError(f"parameters[{i}].type must be one of {VALID_PARAM_TYPES}")
        if ptype == "select" and not raw_param.get("options"):
            raise ValidationError(f"parameters[{i}].options required when type=select")
        parameters.append(ActionParameter(**{k: v for k, v in raw_param.items() if k in ActionParameter.model_fields}))

    raw_approval = data.get("approval", {})
    approval = ApprovalConfig(**(raw_approval if isinstance(raw_approval, dict) else {}))

    allowed_roles = data.get("allowed_roles", [])
    unknown_roles = set(allowed_roles) - VALID_ROLES
    if unknown_roles:
        raise ValidationError(f"Unknown roles in allowed_roles: {unknown_roles}")

    return ActionManifest(
        name=data["name"],
        description=data.get("description", ""),
        category=data.get("category", ""),
        executor_type=executor_type,
        executor_config=data.get("executor_config", {}),
        parameters=parameters,
        approval=approval,
        allowed_roles=allowed_roles,
        target_entity_types=data.get("target_entity_types", []),
        tags=data.get("tags", []),
        enabled=data.get("enabled", True),
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _require(data: dict, key: str, expected_type: type, context: str = "") -> None:
    prefix = f"{context}." if context else ""
    if key not in data:
        raise ValidationError(f"'{prefix}{key}' is required")
    if not isinstance(data[key], expected_type):
        raise ValidationError(f"'{prefix}{key}' must be {expected_type.__name__}")
