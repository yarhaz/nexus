"""
Rule evaluator — checks a single ScorecardRule against a ServiceEntity
and contextual entity data (incidents, work items, packages).
"""
from app.modules.scorecards.models import ScorecardRule, RuleResult
from app.modules.catalog.models import ServiceEntity
from app.modules.entities.models import IncidentEntity, ADOWorkItemEntity, PackageEntity


def evaluate_rule(
    rule: ScorecardRule,
    service: ServiceEntity,
    incidents: list[IncidentEntity],
    work_items: list[ADOWorkItemEntity],
    packages: list[PackageEntity],
) -> RuleResult:
    passed = False
    reason = ""

    match rule.check_type:

        case "field_present":
            field = rule.check_config.get("field", "")
            value = getattr(service, field, None)
            passed = bool(value)
            reason = f"Field '{field}' is {'set' if passed else 'empty'}"

        case "field_equals":
            field = rule.check_config.get("field", "")
            expected = rule.check_config.get("value", "")
            actual = getattr(service, field, None)
            passed = str(actual) == str(expected)
            reason = f"Field '{field}' is '{actual}' (expected '{expected}')"

        case "field_not_equals":
            field = rule.check_config.get("field", "")
            expected = rule.check_config.get("value", "")
            actual = getattr(service, field, None)
            passed = str(actual) != str(expected)
            reason = f"Field '{field}' is '{actual}'"

        case "tag_present":
            tag = rule.check_config.get("tag", "")
            passed = tag in service.tags
            reason = f"Tag '{tag}' {'found' if passed else 'not found'}"

        case "has_runbook":
            passed = bool(service.runbook_url)
            reason = "runbook_url is set" if passed else "runbook_url is empty"

        case "has_repo":
            passed = bool(service.repository_url)
            reason = "repository_url is set" if passed else "repository_url is empty"

        case "lifecycle_equals":
            expected = rule.check_config.get("value", "production")
            passed = service.lifecycle == expected
            reason = f"lifecycle is '{service.lifecycle}' (expected '{expected}')"

        case "no_critical_incidents":
            svc_incidents = [
                i for i in incidents
                if (i.affected_service_id == service.id or service.name in i.tags)
                and i.status != "resolved"
                and i.severity == "critical"
            ]
            passed = len(svc_incidents) == 0
            reason = f"{len(svc_incidents)} open critical incident(s)" if not passed else "No open critical incidents"

        case "no_open_bugs":
            svc_bugs = [
                w for w in work_items
                if w.linked_service_id == service.id
                and w.work_item_type == "Bug"
                and w.status not in ("Closed", "Resolved", "Done")
            ]
            passed = len(svc_bugs) == 0
            reason = f"{len(svc_bugs)} open bug(s)" if not passed else "No open bugs"

        case "no_vulnerable_packages":
            vuln = [p for p in packages if service.id in p.consumers and p.cve_count > 0]
            passed = len(vuln) == 0
            reason = f"{len(vuln)} vulnerable package(s)" if not passed else "No vulnerable packages"

        case _:
            passed = False
            reason = f"Unknown check type: {rule.check_type}"

    return RuleResult(
        rule_id=rule.id,
        rule_name=rule.name,
        passed=passed,
        weight=rule.weight,
        remedy_url=rule.remedy_url,
        reason=reason,
    )
