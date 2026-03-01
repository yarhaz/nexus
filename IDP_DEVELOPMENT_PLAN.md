# Azure Nexus — Internal Developer Platform
## Development Plan
**Target:** Internal org use | 1,000+ users | Azure + GitHub + Azure DevOps

---

## Guiding Principles

- **Catalog-first:** Everything is built on top of the catalog. No feature ships without catalog backing.
- **Azure-native:** Use managed Azure services — no self-managed infra where avoidable.
- **Progressive delivery:** Each phase delivers standalone value. Don't wait for everything before shipping.
- **Dogfood early:** Use the platform to build itself from Phase 1 onward.
- **No gold-plating:** Internal tool — ship working software, not perfect software.

---

## Technical Stack (Fixed Decisions)

| Layer | Technology |
|---|---|
| Frontend | React SPA on Azure Static Web Apps |
| API Gateway | Azure API Management |
| Backend | Azure Container Apps (microservices) |
| Graph DB | Azure Cosmos DB (Gremlin API) |
| Search | Azure AI Search |
| Event Bus | Azure Service Bus + Azure Event Grid |
| State/Cache | Cosmos DB (NoSQL) + Azure Cache for Redis |
| Secrets | Azure Key Vault |
| Monitoring | Azure Monitor + Application Insights |
| Identity | Azure Entra ID (SSO, RBAC, Managed Identity) |
| AI | Azure OpenAI (GPT-4o) — Phase 4 only |
| Storage | Azure Blob Storage |
| CDN/WAF | Azure Front Door |
| IaC | Azure Bicep (all infra) |
| CI/CD | Azure DevOps Pipelines |

---

## Team Structure Recommendation

- **2 backend engineers** — Catalog, Actions, Sync services
- **1 frontend engineer** — React portal
- **1 platform/infra engineer** — Bicep, AKS, networking, CI/CD
- **1 tech lead / architect** — design, ADO/GitHub integration, AI copilot

> Scale the team as phases progress. Phase 1–2 can start with 3 people minimum.

---

## Phases Overview

| Phase | Name | Goal | Duration |
|---|---|---|---|
| 0 | Foundation | Infrastructure + Auth + Catalog v1 | 6–8 weeks |
| 1 | Core Catalog | Full entity model + ingestion + portal | 8–10 weeks |
| 2 | Self-Service | Actions engine + Day-2 ops | 10–12 weeks |
| 3 | Standards & Metrics | Scorecards + DORA + Runbooks | 8–10 weeks |
| 4 | AI & FinOps | AI Copilot + Cost management | 10–12 weeks |
| 5 | Developer Tools | CLI + VS Code + Advanced integrations | Ongoing |

---

## Phase 0 — Foundation
**Goal:** Platform boots. Engineers can log in and see a basic catalog.

### Infrastructure
- [ ] Provision all Azure resources via Bicep (Cosmos DB, Container Apps, Redis, Key Vault, AI Search, Service Bus, Event Grid, Front Door, Static Web Apps, APIM)
- [ ] Azure DevOps CI/CD pipeline for all services (build → test → deploy)
- [ ] Environment setup: `dev`, `staging`, `prod`
- [ ] Secrets wiring via Key Vault references (no plain-text secrets anywhere)
- [ ] Azure Monitor + Application Insights configured for all services
- [ ] Network isolation: VNet, private endpoints for all data services

### Identity & Auth
- [ ] Entra ID app registration (delegated + application permissions)
- [ ] MSAL-based login in the React SPA (Authorization Code + PKCE)
- [ ] Backend token validation middleware (JWT, issuer, audience)
- [ ] Four base roles: `Developer`, `PlatformEngineer`, `TeamLead`, `Admin`
- [ ] Group-based role assignment from Entra ID groups
- [ ] Managed Identity for all Container Apps → Azure service calls

### Catalog Core (v1)
- [ ] Cosmos DB Gremlin schema for entity vertices + edges
- [ ] Entity types in scope: `Service`, `Repository`, `Pipeline`
- [ ] CRUD REST API for catalog entities (Catalog Service)
- [ ] Entity ownership model: resolved from tags, Entra groups, CODEOWNERS
- [ ] Basic entity-level RBAC (read/write/admin per entity)

### Portal (v1 shell)
- [ ] React SPA scaffold with route structure
- [ ] Login/logout flow
- [ ] Catalog browser: list + search + detail page for the 3 entity types
- [ ] Personal dashboard shell ("My Services", empty states for future widgets)

### Ingestion (bootstrap)
- [ ] GitHub App installation + webhook receiver
- [ ] Azure Resource Graph polling (Azure Resource entities seeded)
- [ ] ADO Service Hooks receiver for pipeline events
- [ ] Manual `catalog-info.yaml` import from repos

**Phase 0 exit criteria:** Any engineer can log in, see their services/repos/pipelines, and the catalog is self-managing (updates on push/pipeline events).

---

## Phase 1 — Full Catalog
**Goal:** Complete entity model. Everything is discoverable. Org has >80% catalog coverage.

### New Entity Types
- [ ] `AzureResource` — type, SKU, region, cost (stub), health, tags
- [ ] `Environment` — stage (dev/staging/prod), region, subscription, linked services
- [ ] `Team` — members (from Entra group), owned services, on-call schedule
- [ ] `API/Endpoint` — version, consumers, SLA, auth scheme
- [ ] `Package/Library` — version, license, consumers, CVEs
- [ ] `Incident` — from Azure Monitor alerts; severity, status, MTTR
- [ ] `ADOWorkItem` — type, status, sprint, assignee; linked to services

### Ingestion Expansion
- [ ] IaC sync: Bicep/Terraform state parsing → Azure Resource entities
- [ ] GitHub dependency graph → Package entities + CVE links
- [ ] PagerDuty/Opsgenie webhook receiver → Incident entities
- [ ] ADO Work Item sync → ADOWorkItem entities
- [ ] Change feed processor: Cosmos DB change feed → Event Grid fan-out
- [ ] Delta tracking to avoid full re-scans

### Catalog Portal Pages
- [ ] Entity detail pages for all 7 new entity types
- [ ] Relationship graph view (dependency visualizer)
- [ ] Unified search across all entity types (Azure AI Search backed)
- [ ] Team page: members, owned services, on-call
- [ ] Service detail: health, last deployed version, linked ADO items, GitHub repo, cost stub, compliance score stub

### User State Engine
- [ ] Per-user materialized view: owned resources, team memberships, recent actions, open PRs, active environments
- [ ] Live query composition: Azure Resource Graph + GitHub API + ADO REST
- [ ] Pre-computed state with sub-100ms response target
- [ ] Real-time updates via Azure Web PubSub (WebSocket)
- [ ] Personal dashboard fully populated: My Services, My Deployments, My PRs, My Alerts, My Costs (stub)

**Phase 1 exit criteria:** Any engineer can discover every service, resource, team, and dependency in the org from one search box. No orphaned resources.

---

## Phase 2 — Self-Service Actions
**Goal:** Developers stop filing tickets. They execute Day-2 operations from the portal.

### Actions Engine
- [ ] YAML action manifest spec + parser + schema validator
- [ ] Action registry stored in Git (version-controlled)
- [ ] Execution router: ADO Pipeline trigger, GitHub Actions trigger, Azure Function invoke, Terraform Cloud API
- [ ] Approval workflow engine: single approver, multi-stage, time-boxed auto-approval
- [ ] Approval notifications via Teams + Email
- [ ] Full audit log: every action invocation → Azure Monitor (immutable, 90-day retention)
- [ ] Rollback support: rollback plan field in action manifest + trigger
- [ ] Action policy enforcement: only allowed roles can invoke specific actions

### Built-in Actions — Priority Order

**Tier 1 (ship in Phase 2):**
- [ ] AKS: scale deployment replicas, rolling restart, view pod logs, exec into pod (audited), cordon/drain node
- [ ] App Service: swap deployment slots, restart, update app settings (Key Vault linked)
- [ ] Pipelines: trigger ADO pipeline with params, approve pending gate, cancel run, re-run failed jobs
- [ ] GitHub: trigger GitHub Actions workflow, create branch from template, open PR
- [ ] Secrets: rotate Key Vault secret, rotate storage access key
- [ ] Onboarding: provision dev environment, scaffold new service (repo + pipeline + RG + tags + catalog entity)

**Tier 2 (stretch goals Phase 2 / early Phase 3):**
- [ ] VMSS: scale up/down, restart VM, deallocate, enable/disable auto-scale
- [ ] Databases: scale DTU/vCores, failover to replica, create/restore backup, update firewall rules
- [ ] Networking: update NSG rules, enable/disable DDoS, update DNS record
- [ ] Cost/Governance: apply resource tag, move resource to RG, schedule stop/start, resize to cost-optimal SKU

### Day-2 Operations Hub
- [ ] Resource health dashboard per service (live Azure Resource Health API)
- [ ] Historical SLA availability tracking
- [ ] Alert correlation: Azure Monitor alerts → catalog entities (surface on entity detail page)
- [ ] Unified change log per service: commits, config changes, pipeline runs, Azure resource changes
- [ ] Dependency impact analysis: when incident fires, show upstream/downstream services affected
- [ ] Deployment ring status tracker + canary analysis results view
- [ ] Scheduled operations: stop/start policies, maintenance windows, patch schedules

**Phase 2 exit criteria:** A developer can scale their AKS service, swap a deployment slot, rotate a secret, and provision a dev environment — all without a ticket, with full audit trail.

---

## Phase 3 — Standards & Engineering Intelligence
**Goal:** Engineering leaders have visibility. Teams know where they stand. Quality improves measurably.

### Scorecards Engine
- [ ] Rule evaluation engine (evaluate catalog properties, Azure Policy results, GitHub checks, ADO test results)
- [ ] Weighted scoring per rule, configurable pass/fail thresholds
- [ ] Score trend tracking (daily snapshots)
- [ ] Minimum threshold gate: block promotion to production if score below threshold

**Built-in Scorecard Templates:**
- [ ] **Production Readiness:** health probes configured, alerts set, runbook linked, on-call owner assigned, SLO documented
- [ ] **Security Posture:** Defender for Cloud score, no public endpoints, secrets in Key Vault, Managed Identity in use, vulnerability scan passing
- [ ] **Cost Optimization:** proper tagging, no orphaned resources, right-sized SKUs, budget alerts active
- [ ] **DevOps Maturity:** branch protection on, PR reviews required, automated tests present, DORA metrics tracked
- [ ] **Compliance:** Azure Policy assignments applied, audit logging enabled, data residency correct, encryption enforced, backup policy active

**Custom Scorecard Builder:**
- [ ] Drag-and-drop rule builder in portal
- [ ] Rule sources: catalog properties, Azure Policy, GitHub checks, ADO results
- [ ] Weighted rules, thresholds, trend graphs

**Leadership Dashboards:**
- [ ] Org-wide scorecard heatmap (team × scorecard)
- [ ] Team rankings + score distribution histograms
- [ ] Score trends over time

### DORA Metrics
- [ ] **Lead time for changes:** time from commit to production deploy (ADO/GitHub data)
- [ ] **Deployment frequency:** deploys per service per day/week (ADO/GitHub pipeline data)
- [ ] **MTTR:** mean time to recovery from incidents (Incident entity data)
- [ ] **Change failure rate:** % deploys that caused an incident (correlated pipeline + incident data)
- [ ] Per-team + per-service breakdown
- [ ] Personal DORA metrics on user dashboard
- [ ] Trend charts (weekly/monthly/quarterly)

### Runbook Library
- [ ] Markdown runbook storage in GitHub (org-managed)
- [ ] Runbook ingestion → catalog entities (linked to services)
- [ ] Contextual surfacing: runbook appears next to related alert or resource
- [ ] Runbook search + tagging

**Phase 3 exit criteria:** Engineering leaders can see team health, DORA metrics, and scorecard scores. Engineers know exactly what they need to fix to pass production readiness gates.

---

## Phase 4 — AI Copilot & FinOps
**Goal:** Reduce toil through AI. Make cost visible and actionable.

### AI Copilot (Nexus Intelligence)
- [ ] Azure OpenAI (GPT-4o) deployment in org's subscription (no data egress)
- [ ] RAG pipeline: embed catalog entities using `text-embedding-3`, store in Azure AI Search vector index
- [ ] Grounded context: copilot only sees structured graph data (not source code)
- [ ] Chat UI embedded in portal sidebar

**Copilot Capabilities:**
- [ ] Natural language resource queries ("show me all AKS clusters without health probes")
- [ ] Incident triage: "what changed in the last 2 hours near this service?"
- [ ] Cost explanation: "why did our Azure spend increase 30% this week?"
- [ ] Runbook generation from service metadata
- [ ] Code scaffolding: Azure Functions, Service Bus consumers, Cosmos DB clients
- [ ] Policy explanation in plain English
- [ ] On-call assistant: incident history, related runbooks, suggested actions
- [ ] Prompt + completion logging to Azure Monitor (auditable)

### FinOps / Cost Management
- [ ] Azure Cost Management API integration
- [ ] Cost allocation per service, per team, per environment
- [ ] Cost anomaly detection (threshold-based alerts)
- [ ] "My Costs This Month" on personal dashboard (real data)
- [ ] Right-sizing analysis: compare current SKU to recommended
- [ ] Reserved instance tracking
- [ ] Budget alerts configured and surfaced in portal
- [ ] AI copilot cost explanation queries

**Phase 4 exit criteria:** Engineers can ask the copilot why their costs went up, get a runbook generated for a new service, and see cost allocation by team.

---

## Phase 5 — Developer Tools & Advanced Integrations
**Goal:** Meet developers where they work. Extend platform reach.

### CLI Tool (`nexus`)
- [ ] Auth via device flow (Entra ID)
- [ ] `nexus catalog search <query>`
- [ ] `nexus action run <action-name> --service <service>`
- [ ] `nexus env create / destroy`
- [ ] `nexus scorecard show <service>`
- [ ] `nexus dora show <team>`

### VS Code Extension
- [ ] Login via extension (reuse CLI auth token)
- [ ] Open service in dev container
- [ ] Trigger actions without leaving IDE
- [ ] Surface scorecard results inline
- [ ] Alert/notification panel

### Advanced Integrations
- [ ] Azure Chaos Studio integration: define experiments from portal, view blast radius, trigger chaos runs
- [ ] ServiceNow ITSM integration: sync incidents, change requests
- [ ] Slack integration: action approvals, alert notifications, copilot queries from Slack
- [ ] Azure API Management integration: API entities auto-populated, rate limit / auth surfaced
- [ ] Multi-org support: multiple Entra tenants, multiple ADO organizations

---

## Non-Functional Requirements (All Phases)

| Requirement | Target |
|---|---|
| Catalog query latency | < 100ms (materialized views) |
| Real-time update lag | < 5s (Event Grid → WebSocket) |
| Portal load time | < 2s (CDN-backed SPA) |
| Uptime | 99.9% (Azure SLA-backed) |
| Concurrent users | 1,000+ (Container Apps auto-scale) |
| Audit log retention | 90 days minimum |
| Data encryption at rest | AES-256 (Cosmos DB, Blob Storage) |
| Data encryption in transit | TLS 1.3 |
| Secrets management | Key Vault only — zero plain-text secrets |
| Zero Trust | All service-to-service via Managed Identity |

---

## Feature Priority Matrix

| Feature | Phase | Impact | Effort | Priority |
|---|---|---|---|---|
| Entra ID auth + RBAC | 0 | Critical | Low | P0 |
| Catalog v1 (Service, Repo, Pipeline) | 0 | Critical | Medium | P0 |
| GitHub + ADO ingestion | 0–1 | Critical | Medium | P0 |
| Full entity model (10 types) | 1 | High | High | P1 |
| User state / personal dashboard | 1 | High | Medium | P1 |
| Actions engine + approval workflow | 2 | Critical | High | P1 |
| AKS / App Service actions | 2 | High | Medium | P1 |
| Service scaffolding / onboarding | 2 | High | Medium | P1 |
| Day-2 ops hub | 2 | High | Medium | P1 |
| Scorecards engine | 3 | High | High | P2 |
| DORA metrics | 3 | High | Medium | P2 |
| Runbook library | 3 | Medium | Low | P2 |
| AI Copilot | 4 | High | High | P3 |
| FinOps / cost management | 4 | Medium | Medium | P3 |
| CLI tool | 5 | Medium | Medium | P3 |
| VS Code extension | 5 | Medium | High | P4 |
| Chaos Studio integration | 5 | Low | High | P4 |
| ServiceNow integration | 5 | Medium | Medium | P4 |

---

## Backlog (Not Scoped in Initial Phases)

- Nexus Enterprise self-hosted Bicep distribution
- Partner/plugin marketplace
- GitHub Enterprise Server support
- EU data residency configuration
- Advanced ABAC (attribute-based access control)
- Time-travel state (30-day entity history replay)
- API developer portal for internal API consumers
- Sprint planning widget (ADO velocity/capacity)
- Copilot usage analytics per team (GitHub Copilot metrics)
- Environment cloning with anonymized prod-like data

---

## Success Metrics

| Metric | Target |
|---|---|
| Catalog coverage | >80% of org resources cataloged within 30 days of Phase 1 launch |
| Self-service adoption | >50% of Day-2 ops executed via portal (no ticket) by end of Phase 2 |
| Developer WAU/MAU | >0.6 (active weekly use) |
| Scorecard pass rate | >70% of services pass Production Readiness by end of Phase 3 |
| DORA improvement | Lead time reduced by >20% within 6 months of Phase 3 |
| AI copilot resolution rate | >60% of queries answered without escalation (Phase 4) |
| On-call ticket reduction | >30% fewer "where is this?" tickets post Phase 1 |
