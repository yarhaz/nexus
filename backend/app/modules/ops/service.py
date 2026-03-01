"""
Ops Hub service — health summaries, change log, and impact analysis.
All data is derived from existing entity repositories; no new storage needed.
"""
from datetime import datetime, timezone

import structlog

from app.clients.redis_client import get_redis
from app.modules.catalog.repository import ServiceRepository
from app.modules.entities.models import (
    IncidentEntity,
    ADOWorkItemEntity,
    PackageEntity,
    AzureResourceEntity,
)
from app.modules.entities.repository import EntityRepository
from app.modules.relationships.repository import RelationshipRepository
from app.modules.ops.models import (
    ServiceHealthSummary,
    OpsHealthResponse,
    ChangeEvent,
    ChangeLogResponse,
    ImpactNode,
    ImpactAnalysisResponse,
)

logger = structlog.get_logger()
HEALTH_CACHE_TTL = 30   # seconds


class OpsService:

    # ── Health Summary ─────────────────────────────────────────────────────────

    async def get_health_summary(self) -> OpsHealthResponse:
        redis = await get_redis()
        cache_key = "ops:health:summary"
        cached = await redis.get(cache_key)
        if cached:
            return OpsHealthResponse.model_validate_json(cached)

        svc_repo = ServiceRepository()
        inc_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        wi_repo: EntityRepository[ADOWorkItemEntity] = EntityRepository("ADOWorkItem", ADOWorkItemEntity)
        pkg_repo: EntityRepository[PackageEntity] = EntityRepository("Package", PackageEntity)

        services, _ = await svc_repo.list(cursor=None, limit=200)
        incidents, _ = await inc_repo.list(cursor=None, limit=500)
        work_items, _ = await wi_repo.list(cursor=None, limit=500)
        packages, _ = await pkg_repo.list(cursor=None, limit=1000)

        open_incidents = [i for i in incidents if i.status != "resolved"]
        critical_incidents = [i for i in open_incidents if i.severity == "critical"]
        open_bugs = [w for w in work_items if w.work_item_type == "Bug" and w.status not in ("Closed", "Resolved", "Done")]
        vulnerable_pkgs = {p.id for p in packages if p.cve_count > 0}

        summaries: list[ServiceHealthSummary] = []
        for svc in services:
            svc_incidents = [i for i in open_incidents if i.affected_service_id == svc.id or svc.name in i.tags]
            svc_bugs = [w for w in open_bugs if w.linked_service_id == svc.id]
            svc_vulns = sum(1 for p in packages if svc.id in p.consumers and p.cve_count > 0)

            health = "Healthy"
            if any(i.severity == "critical" for i in svc_incidents):
                health = "Unavailable"
            elif svc_incidents:
                health = "Degraded"

            summaries.append(ServiceHealthSummary(
                service_id=svc.id,
                service_name=svc.name,
                health_status=health,
                open_incidents=len(svc_incidents),
                critical_incidents=sum(1 for i in svc_incidents if i.severity == "critical"),
                open_bugs=len(svc_bugs),
                open_work_items=len([w for w in work_items if w.linked_service_id == svc.id and w.status not in ("Closed", "Resolved", "Done")]),
                vulnerable_packages=svc_vulns,
                computed_at=datetime.now(timezone.utc),
            ))

        response = OpsHealthResponse(
            services=summaries,
            total_open_incidents=len(open_incidents),
            total_critical_incidents=len(critical_incidents),
        )
        await redis.setex(cache_key, HEALTH_CACHE_TTL, response.model_dump_json())
        return response

    # ── Change Log ─────────────────────────────────────────────────────────────

    async def get_change_log(self, limit: int = 50, entity_id: str = "") -> ChangeLogResponse:
        """
        Synthesise a change log from recently updated entities.
        Events are derived from entity updated_at timestamps; for a real production
        system this would be an append-only event store, but this provides a functional
        approximation without additional storage.
        """
        inc_repo: EntityRepository[IncidentEntity] = EntityRepository("Incident", IncidentEntity)
        wi_repo: EntityRepository[ADOWorkItemEntity] = EntityRepository("ADOWorkItem", ADOWorkItemEntity)
        svc_repo = ServiceRepository()

        events: list[ChangeEvent] = []

        # Incidents → change events
        incidents, _ = await inc_repo.list(cursor=None, limit=200)
        for inc in incidents:
            if entity_id and inc.id != entity_id and inc.affected_service_id != entity_id:
                continue
            events.append(ChangeEvent(
                id=f"inc:{inc.id}",
                event_type="incident.updated" if inc.status != "open" else "incident.opened",
                entity_id=inc.id,
                entity_name=inc.title,
                entity_kind="Incident",
                summary=f"[{inc.severity.upper()}] {inc.title} — {inc.status}",
                occurred_at=inc.updated_at,
                metadata={"severity": inc.severity, "status": inc.status, "source": inc.source},
            ))

        # Work items → change events
        work_items, _ = await wi_repo.list(cursor=None, limit=200)
        for wi in work_items:
            if entity_id and wi.id != entity_id and wi.linked_service_id != entity_id:
                continue
            events.append(ChangeEvent(
                id=f"wi:{wi.id}",
                event_type="workitem.updated",
                entity_id=wi.id,
                entity_name=wi.title,
                entity_kind="ADOWorkItem",
                summary=f"[{wi.work_item_type}] {wi.title} — {wi.status}",
                actor=wi.assignee,
                occurred_at=wi.updated_at,
                metadata={"type": wi.work_item_type, "status": wi.status, "sprint": wi.sprint},
            ))

        # Services → change events
        services, _ = await svc_repo.list(cursor=None, limit=100)
        for svc in services:
            if entity_id and svc.id != entity_id:
                continue
            events.append(ChangeEvent(
                id=f"svc:{svc.id}",
                event_type="catalog.updated",
                entity_id=svc.id,
                entity_name=svc.name,
                entity_kind="Service",
                summary=f"Service {svc.name} catalog updated",
                occurred_at=svc.updated_at,
                metadata={"tier": svc.tier, "lifecycle": svc.lifecycle},
            ))

        events.sort(key=lambda e: e.occurred_at, reverse=True)
        sliced = events[:limit]
        return ChangeLogResponse(events=sliced, total=len(events))

    # ── Impact Analysis ────────────────────────────────────────────────────────

    async def get_impact_analysis(self, entity_id: str, depth: int = 3) -> ImpactAnalysisResponse:
        """
        Walk the relationship graph starting from entity_id and identify
        what could be impacted if this entity has an incident.
        """
        rel_repo = RelationshipRepository()
        graph = await rel_repo.get_graph(entity_id, depth=depth)

        # Determine root entity name
        root_name = entity_id
        for node in graph.nodes:
            if node.id == entity_id:
                root_name = node.name
                break

        # Build impact nodes — everything except the root
        impact_map: dict[str, ImpactNode] = {}
        for edge in graph.edges:
            # direct consumers of the root entity
            if edge.from_id == entity_id:
                target = next((n for n in graph.nodes if n.id == edge.to_id), None)
                if target and target.id not in impact_map:
                    impact_map[target.id] = ImpactNode(
                        entity_id=target.id,
                        entity_name=target.name,
                        entity_kind=target.label,
                        impact_level="direct",
                        relationship=edge.label,
                    )
            elif edge.to_id == entity_id:
                source = next((n for n in graph.nodes if n.id == edge.from_id), None)
                if source and source.id not in impact_map:
                    impact_map[source.id] = ImpactNode(
                        entity_id=source.id,
                        entity_name=source.name,
                        entity_kind=source.label,
                        impact_level="direct",
                        relationship=edge.label,
                    )

        # Everything else in the graph is transitive
        for node in graph.nodes:
            if node.id != entity_id and node.id not in impact_map:
                impact_map[node.id] = ImpactNode(
                    entity_id=node.id,
                    entity_name=node.name,
                    entity_kind=node.label,
                    impact_level="transitive",
                    relationship="",
                )

        affected = list(impact_map.values())
        return ImpactAnalysisResponse(
            root_entity_id=entity_id,
            root_entity_name=root_name,
            affected=affected,
            total_affected=len(affected),
        )
