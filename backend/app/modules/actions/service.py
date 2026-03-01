"""
Actions engine service layer.

Handles:
- Action manifest CRUD (registry)
- Execution lifecycle: trigger → [approval] → run → complete/fail
- Approval workflow (approve/reject by authorised users)
- Audit log (every state transition logged via structlog → Application Insights)
"""

from datetime import datetime, timezone, timedelta

import structlog

from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.modules.actions.models import (
    ActionExecution,
    ActionExecutionRequest,
    ActionManifest,
    ApprovalDecision,
)
from app.modules.actions.repository import ActionRepository

logger = structlog.get_logger()


class ActionService:
    def __init__(self) -> None:
        self._repo = ActionRepository()

    # ── Registry ─────────────────────────────────────────────────────────────

    async def list_actions(self, limit: int = 50) -> list[ActionManifest]:
        return await self._repo.list_manifests(limit)

    async def get_action(self, action_id: str) -> ActionManifest:
        manifest = await self._repo.get_manifest(action_id)
        if not manifest:
            raise NotFoundError(f"Action '{action_id}' not found.")
        return manifest

    async def register_action(self, manifest: ActionManifest, user: dict) -> ActionManifest:
        manifest.created_by = user.get("oid", "")
        return await self._repo.save_manifest(manifest)

    async def update_action(self, action_id: str, manifest: ActionManifest, user: dict) -> ActionManifest:
        existing = await self.get_action(action_id)
        manifest.id = existing.id
        manifest.created_by = existing.created_by
        manifest.created_at = existing.created_at
        return await self._repo.save_manifest(manifest)

    async def delete_action(self, action_id: str) -> None:
        deleted = await self._repo.delete_manifest(action_id)
        if not deleted:
            raise NotFoundError(f"Action '{action_id}' not found.")

    # ── Execution ─────────────────────────────────────────────────────────────

    async def trigger(self, req: ActionExecutionRequest, user: dict) -> ActionExecution:
        """Trigger an action. If approval required, creates a pending execution."""
        manifest = await self.get_action(req.action_id)

        if not manifest.enabled:
            raise ValidationError(f"Action '{manifest.name}' is disabled.")

        # Role check
        user_role = user.get("role", "Developer")
        if manifest.allowed_roles and user_role not in manifest.allowed_roles:
            raise AuthorizationError(
                f"Role '{user_role}' is not permitted to execute '{manifest.name}'."
            )

        # Validate required parameters
        for param in manifest.parameters:
            if param.required and param.name not in req.parameters:
                raise ValidationError(f"Required parameter '{param.name}' is missing.")

        # Determine initial status
        needs_approval = manifest.approval.required and user_role not in manifest.approval.auto_approve_roles
        initial_status = "pending_approval" if needs_approval else "approved"

        expires_at = None
        if needs_approval:
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=manifest.approval.timeout_minutes)

        execution = ActionExecution(
            action_id=manifest.id,
            action_name=manifest.name,
            target_entity_id=req.target_entity_id,
            parameters=req.parameters,
            comment=req.comment,
            status=initial_status,
            triggered_by=user.get("oid", ""),
            triggered_by_name=user.get("name", ""),
            expires_at=expires_at,
        )

        saved = await self._repo.create_execution(execution)

        logger.info(
            "action.triggered",
            action_id=manifest.id,
            action_name=manifest.name,
            execution_id=saved.id,
            status=initial_status,
            triggered_by=user.get("oid"),
        )

        # If no approval needed, kick off execution immediately
        if initial_status == "approved":
            saved = await self._run_execution(saved, manifest)

        return saved

    async def decide_approval(
        self,
        exec_id: str,
        decision: ApprovalDecision,
        user: dict,
    ) -> ActionExecution:
        """Approve or reject a pending execution."""
        execution = await self._repo.get_execution(exec_id)
        if not execution:
            raise NotFoundError(f"Execution '{exec_id}' not found.")

        if execution.status != "pending_approval":
            raise ValidationError(f"Execution is not pending approval (status: {execution.status}).")

        # Check expiry
        if execution.expires_at and datetime.now(timezone.utc) > execution.expires_at:
            await self._repo.update_execution_status(exec_id, "expired")
            raise ValidationError("Approval window has expired.")

        # Check approver is authorised
        manifest = await self.get_action(execution.action_id)
        user_email = user.get("email", "")
        user_oid = user.get("oid", "")
        if manifest.approval.approvers and (
            user_email not in manifest.approval.approvers
            and user_oid not in manifest.approval.approvers
        ):
            raise AuthorizationError("You are not authorised to approve this action.")

        if decision.approved:
            updated = await self._repo.update_execution_status(
                exec_id,
                "approved",
                approved_by=user_oid,
            )
            logger.info("action.approved", execution_id=exec_id, approver=user_oid)
            if updated:
                updated = await self._run_execution(updated, manifest)
        else:
            updated = await self._repo.update_execution_status(
                exec_id,
                "rejected",
                rejected_by=user_oid,
                rejection_reason=decision.reason,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.info("action.rejected", execution_id=exec_id, approver=user_oid, reason=decision.reason)

        return updated  # type: ignore[return-value]

    async def cancel_execution(self, exec_id: str, user: dict) -> ActionExecution:
        execution = await self._repo.get_execution(exec_id)
        if not execution:
            raise NotFoundError(f"Execution '{exec_id}' not found.")

        if execution.status not in ("pending_approval", "running"):
            raise ValidationError(f"Cannot cancel execution in status '{execution.status}'.")

        # Only the triggerer or an Admin can cancel
        if execution.triggered_by != user.get("oid") and user.get("role") != "Admin":
            raise AuthorizationError("You are not authorised to cancel this execution.")

        updated = await self._repo.update_execution_status(
            exec_id,
            "cancelled",
            completed_at=datetime.now(timezone.utc).isoformat(),
        )
        logger.info("action.cancelled", execution_id=exec_id, cancelled_by=user.get("oid"))
        return updated  # type: ignore[return-value]

    async def get_execution(self, exec_id: str) -> ActionExecution:
        ex = await self._repo.get_execution(exec_id)
        if not ex:
            raise NotFoundError(f"Execution '{exec_id}' not found.")
        return ex

    async def list_executions(
        self,
        user_oid: str | None = None,
        action_id: str | None = None,
        limit: int = 25,
    ) -> list[ActionExecution]:
        return await self._repo.list_executions(user_oid=user_oid, action_id=action_id, limit=limit)

    # ── Internal execution router ─────────────────────────────────────────────

    async def _run_execution(self, execution: ActionExecution, manifest: ActionManifest) -> ActionExecution:
        """Route the execution to the appropriate executor backend."""
        now = datetime.now(timezone.utc)

        updated = await self._repo.update_execution_status(
            execution.id,
            "running",
            started_at=now.isoformat(),
        )

        try:
            run_id = await self._dispatch(manifest, execution)
            updated = await self._repo.update_execution_status(
                execution.id,
                "succeeded",
                executor_run_id=run_id,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.info("action.succeeded", execution_id=execution.id, run_id=run_id)
        except Exception as exc:
            updated = await self._repo.update_execution_status(
                execution.id,
                "failed",
                error_message=str(exc),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
            logger.error("action.failed", execution_id=execution.id, error=str(exc))

        return updated  # type: ignore[return-value]

    async def _dispatch(self, manifest: ActionManifest, execution: ActionExecution) -> str:
        """
        Dispatch execution to the executor backend.
        Returns the external run ID for tracking.

        Phase 2 note: each executor type is a stub — real implementations call
        ADO Pipelines API / GitHub Actions API / Azure Functions / HTTP in Phase 2.
        """
        executor = manifest.executor_type
        config = manifest.executor_config
        params = execution.parameters

        if executor == "ado_pipeline":
            return await _dispatch_ado_pipeline(config, params)
        if executor == "github_actions":
            return await _dispatch_github_actions(config, params)
        if executor == "http_webhook":
            return await _dispatch_http_webhook(config, params, execution)
        if executor == "azure_function":
            return await _dispatch_azure_function(config, params, execution)
        if executor == "manual":
            # Manual actions are just logged — no automatic dispatch
            return "manual"

        raise ValueError(f"Unknown executor type: {executor}")


# ─── Executor stubs (implemented in Phase 2 with real API clients) ───────────

async def _dispatch_ado_pipeline(config: dict, params: dict) -> str:
    """Trigger an Azure DevOps pipeline run."""
    import httpx
    org = config.get("organization", "")
    project = config.get("project", "")
    pipeline_id = config.get("pipeline_id", "")
    pat = config.get("pat", "")  # In prod: fetched from Key Vault

    if not all([org, project, pipeline_id]):
        raise ValueError("ADO pipeline executor requires organization, project, and pipeline_id")

    url = f"https://dev.azure.com/{org}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1"
    body = {"templateParameters": params}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json=body,
            headers={"Authorization": f"Basic {pat}", "Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("id", ""))


async def _dispatch_github_actions(config: dict, params: dict) -> str:
    """Trigger a GitHub Actions workflow_dispatch."""
    import httpx
    owner = config.get("owner", "")
    repo = config.get("repo", "")
    workflow_id = config.get("workflow_id", "")
    ref = config.get("ref", "main")
    token = config.get("token", "")  # In prod: fetched from Key Vault

    if not all([owner, repo, workflow_id]):
        raise ValueError("GitHub Actions executor requires owner, repo, and workflow_id")

    url = f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
    body = {"ref": ref, "inputs": params}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            json=body,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        resp.raise_for_status()
        return f"gh-{owner}/{repo}/{workflow_id}"


async def _dispatch_http_webhook(config: dict, params: dict, execution: ActionExecution) -> str:
    """POST to an arbitrary HTTP webhook."""
    import httpx
    url = config.get("url", "")
    if not url:
        raise ValueError("HTTP webhook executor requires url")

    headers = config.get("headers", {})
    payload = {
        "execution_id": execution.id,
        "action_id": execution.action_id,
        "triggered_by": execution.triggered_by,
        "parameters": params,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return execution.id


async def _dispatch_azure_function(config: dict, params: dict, execution: ActionExecution) -> str:
    """Invoke an Azure Function via HTTP trigger."""
    return await _dispatch_http_webhook(
        {"url": config.get("function_url", ""), "headers": config.get("headers", {})},
        params,
        execution,
    )
