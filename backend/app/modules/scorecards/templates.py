"""
Built-in scorecard templates.
Seeded on startup; stored in Redis (no Gremlin needed — they're config, not data).
"""
import hashlib
from app.modules.scorecards.models import ScorecardTemplate, ScorecardRule


def _tid(slug: str) -> str:
    return hashlib.sha256(f"seed:scorecard:{slug}".encode()).hexdigest()[:32]


def _rid(slug: str) -> str:
    return hashlib.sha256(f"seed:rule:{slug}".encode()).hexdigest()[:16]


PRODUCTION_READINESS = ScorecardTemplate(
    id=_tid("production-readiness"),
    name="Production Readiness",
    description="Ensures a service meets baseline production standards before go-live.",
    applies_to=["Service"],
    rules=[
        ScorecardRule(
            id=_rid("pr-has-runbook"),
            name="Runbook URL set",
            description="Service must have a runbook URL for incident response.",
            weight=3,
            check_type="has_runbook",
            remedy_url="https://wiki.example.com/runbooks",
        ),
        ScorecardRule(
            id=_rid("pr-has-repo"),
            name="Repository URL set",
            description="Service must link to its source repository.",
            weight=2,
            check_type="has_repo",
        ),
        ScorecardRule(
            id=_rid("pr-lifecycle-prod"),
            name="Lifecycle is production",
            description="Service lifecycle should be 'production' before go-live.",
            weight=2,
            check_type="lifecycle_equals",
            check_config={"value": "production"},
        ),
        ScorecardRule(
            id=_rid("pr-has-team"),
            name="Team set",
            description="Service must be assigned to a team.",
            weight=2,
            check_type="field_present",
            check_config={"field": "team"},
        ),
        ScorecardRule(
            id=_rid("pr-no-critical-inc"),
            name="No critical open incidents",
            description="Service must not have any open critical incidents.",
            weight=4,
            check_type="no_critical_incidents",
        ),
        ScorecardRule(
            id=_rid("pr-no-open-bugs"),
            name="No open bugs",
            description="Service must not have open Bug work items.",
            weight=2,
            check_type="no_open_bugs",
        ),
        ScorecardRule(
            id=_rid("pr-no-vuln-pkg"),
            name="No vulnerable packages",
            description="All consumed packages must have zero known CVEs.",
            weight=3,
            check_type="no_vulnerable_packages",
        ),
    ],
)

SECURITY_POSTURE = ScorecardTemplate(
    id=_tid("security-posture"),
    name="Security Posture",
    description="Checks security hygiene: CVEs, incident history, and secret hygiene indicators.",
    applies_to=["Service"],
    rules=[
        ScorecardRule(
            id=_rid("sec-no-vuln-pkg"),
            name="No vulnerable packages",
            description="Zero consumed packages with known CVEs.",
            weight=5,
            check_type="no_vulnerable_packages",
        ),
        ScorecardRule(
            id=_rid("sec-no-critical-inc"),
            name="No open critical security incidents",
            description="No active critical incidents.",
            weight=4,
            check_type="no_critical_incidents",
        ),
        ScorecardRule(
            id=_rid("sec-has-runbook"),
            name="Security runbook exists",
            description="Service has a runbook URL (implies incident response documentation).",
            weight=2,
            check_type="has_runbook",
            remedy_url="https://wiki.example.com/security-runbooks",
        ),
        ScorecardRule(
            id=_rid("sec-status-active"),
            name="Service status is active",
            description="Deprecated services should not be in production.",
            weight=1,
            check_type="field_equals",
            check_config={"field": "status", "value": "active"},
        ),
    ],
)

BUILT_IN_TEMPLATES: list[ScorecardTemplate] = [
    PRODUCTION_READINESS,
    SECURITY_POSTURE,
]
