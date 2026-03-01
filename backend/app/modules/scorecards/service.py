"""
Scorecard service — evaluates templates against services and caches results.
"""
import json
from datetime import datetime, timezone

import structlog

from app.clients.redis_client import get_redis
from app.modules.catalog.models import ServiceEntity
from app.modules.catalog.repository import ServiceRepository
from app.modules.entities.models import IncidentEntity, ADOWorkItemEntity, PackageEntity
from app.modules.entities.repository import EntityRepository
from app.modules.scorecards.evaluator import evaluate_rule
from app.modules.scorecards.models import ScorecardResult, ScorecardTemplate
from app.modules.scorecards.templates import BUILT_IN_TEMPLATES

logger = structlog.get_logger()
SCORE_CACHE_TTL = 120   # 2 minutes

# Level thresholds (percentage)
_LEVELS = [
    (90, "platinum"),
    (75, "gold"),
    (60, "silver"),
    (40, "bronze"),
    (0,  "failing"),
]


def _pct_to_level(pct: float) -> str:
    for threshold, level in _LEVELS:
        if pct >= threshold:
            return level
    return "failing"


class ScorecardService:

    def _all_templates(self) -> list[ScorecardTemplate]:
        return BUILT_IN_TEMPLATES

    async def _load_context(self) -> tuple[
        list[IncidentEntity],
        list[ADOWorkItemEntity],
        list[PackageEntity],
    ]:
        inc_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        wi_repo: EntityRepository[ADOWorkItemEntity] = EntityRepository("ADOWorkItem", ADOWorkItemEntity)
        pkg_repo: EntityRepository[PackageEntity] = EntityRepository("Package", PackageEntity)
        incidents, _ = await inc_repo.list(cursor=None, limit=500)
        work_items, _ = await wi_repo.list(cursor=None, limit=500)
        packages, _ = await pkg_repo.list(cursor=None, limit=1000)
        return incidents, work_items, packages

    async def evaluate(
        self,
        service: ServiceEntity,
        template: ScorecardTemplate,
        incidents: list[IncidentEntity],
        work_items: list[ADOWorkItemEntity],
        packages: list[PackageEntity],
    ) -> ScorecardResult:
        rule_results = [
            evaluate_rule(rule, service, incidents, work_items, packages)
            for rule in template.rules
        ]

        max_score = sum(r.weight for r in template.rules)
        score = sum(r.weight for r in rule_results if r.passed)
        pct = (score / max_score * 100) if max_score else 0.0

        return ScorecardResult(
            template_id=template.id,
            template_name=template.name,
            entity_id=service.id,
            entity_name=service.name,
            entity_kind="Service",
            score=score,
            max_score=max_score,
            percentage=round(pct, 1),
            level=_pct_to_level(pct),
            rules=rule_results,
            evaluated_at=datetime.now(timezone.utc),
        )

    async def score_service(self, service_id: str) -> list[ScorecardResult]:
        """Evaluate all templates for a single service."""
        cache_key = f"scorecards:service:{service_id}"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return [ScorecardResult(**r) for r in json.loads(cached)]

        svc_repo = ServiceRepository()
        service = await svc_repo.get(service_id)
        if not service:
            return []

        incidents, work_items, packages = await self._load_context()
        results = [
            await self.evaluate(service, tpl, incidents, work_items, packages)
            for tpl in self._all_templates()
            if "Service" in tpl.applies_to
        ]

        await redis.setex(
            cache_key,
            SCORE_CACHE_TTL,
            json.dumps([r.model_dump(mode="json") for r in results]),
        )
        logger.info("scorecards.evaluated", service_id=service_id, templates=len(results))
        return results

    async def score_all_services(self) -> list[ScorecardResult]:
        """Evaluate all templates for every service (batch)."""
        cache_key = "scorecards:all"
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return [ScorecardResult(**r) for r in json.loads(cached)]

        svc_repo = ServiceRepository()
        services, _ = await svc_repo.list(cursor=None, limit=500)
        incidents, work_items, packages = await self._load_context()

        all_results: list[ScorecardResult] = []
        for service in services:
            for tpl in self._all_templates():
                if "Service" in tpl.applies_to:
                    result = await self.evaluate(service, tpl, incidents, work_items, packages)
                    all_results.append(result)

        await redis.setex(
            cache_key,
            SCORE_CACHE_TTL,
            json.dumps([r.model_dump(mode="json") for r in all_results]),
        )
        return all_results

    def list_templates(self) -> list[ScorecardTemplate]:
        return self._all_templates()

    def get_template(self, template_id: str) -> ScorecardTemplate | None:
        return next((t for t in self._all_templates() if t.id == template_id), None)
