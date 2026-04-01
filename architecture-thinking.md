# Asset Intelligence Platform — Architecture

## Overview

The Asset Intelligence Platform is a CMS-agnostic governance service
that evaluates AI-generated metadata before it is applied to digital
assets at scale.

It operates as a quality gate — consumed by any CMS or DAM that
generates AI metadata — providing confidence scoring, brand validation,
human review routing, and compliance-grade audit trails.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CMS / DAM                                │
│         (Adobe AEM, Contentful, Sitecore, or any DAM)           │
│                                                                 │
│   Asset processed → AI tags generated → Webhook fired           │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ POST /api/governance/evaluate
                              │ {asset_id, asset_url,
                              │  generated_tags, callback_url}
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE API (FastAPI)                     │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  Tag Evaluation Layer                   │   │
│   │                                                         │   │
│   │   RAG Query → LLM Evaluation → Confidence Score         │   │
│   │                                                         │   │
│   │   Per-tag output:                                       │   │
│   │   {"tag": "run-for-the-oceans",                         │   │
│   │    "confidence": 0.43,                                  │   │
│   │    "issue": "incorrect campaign association",           │   │
│   │    "evidence": "campaign_brief.pdf page 3"}             │   │
│   └─────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│                             ↓                                   │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                  Decision Router                        │   │
│   │                                                         │   │
│   │   score > 0.85  → auto-approve                          │   │
│   │   score 0.70–0.85 → human review task                   │   │
│   │   score < 0.70  → reject + reason                       │   │
│   └──────┬─────────────────────┬──────────────────┬─────────┘   │
│          │                     │                  │             │
│          ↓                     ↓                  ↓             │
│   ┌─────────────┐   ┌──────────────────┐  ┌────────────────┐    │
│   │  Auto       │   │  Task Adapter    │  │  Reject +      │    │
│   │  Approve    │   │  (Configurable)  │  │  Reason        │    │
│   │             │   │  AEM Inbox       │  │  returned      │    │
│   │  Callback   │   │  Jira            │  │  to CMS        │    │
│   │  to CMS     │   │  Slack           │  │                │    │
│   └─────────────┘   │  Email           │  └────────────────┘    │
│                     └──────────────────┘                        │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │                    Audit Logger                         │   │
│   │  Runs after every decision — approve, review, reject    │   │
│   │  Logs: model, context, score, routing, approver,        │   │
│   │        timestamp, C2PA hash                             │   │
│   └─────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          │                         │
          ↓                         ↓
┌──────────────────┐     ┌──────────────────────────────────────┐
│   RAG Layer      │     │         LLM Provider                 │
│                  │     │  (Configurable)                      │
│  Namespaces:     │     │                                      │
│  - brand_guidelines    │  openai   → GPT-4 Vision             │
│  - taxonomy      │     │  anthropic → Claude 3.5 Sonnet       │
│  - product_catalogue   │  ollama   → Llama 3 (self-hosted)    │
│  - customer_exclusive  │                                      │
│  - golden_dataset│     └──────────────────────────────────────┘
│                  │
│  Vector DB:      │
│  (Configurable)  │
│  - Pinecone      │
│  - pgvector      │
│  - Weaviate      │
└──────────────────┘
```

---

## Core Data Flow

```
1. CMS fires webhook after asset processing
   POST /api/governance/evaluate
   {
     "asset_id": "dam/brand/shoes/ub22.psd",
     "asset_url": "https://...",
     "generated_tags": ["shoes", "blue", "sport"],
     "source_cms": "aem",
     "callback_url": "https://cms/webhook/result"
   }

2. Governance API queries RAG namespaces
   → Retrieves brand guidelines, taxonomy,
     product catalogue, customer-specific rules

3. LLM evaluates each tag against retrieved context
   → Confidence score per tag
   → Issue evidence where applicable

4. Decision router applies configured thresholds
   → Auto-approve / Human review / Reject

5. Audit log written regardless of decision

6. Result posted back to CMS via callback_url
   {
     "asset_id": "...",
     "decision": "human_review",
     "tags": [
       {"tag": "shoes", "confidence": 0.94, "status": "approved"},
       {"tag": "sport", "confidence": 0.71, "status": "review"},
       {"tag": "blue",  "confidence": 0.91, "status": "approved"}
     ],
     "review_task_id": "TASK-1234",
     "audit_id": "aud_abc123"
   }
```

---

## Component Design

### Governance API

**POST /api/governance/evaluate**
```python
@app.post("/api/governance/evaluate")
async def evaluate_tags(request: GovernanceRequest):
    """
    Main governance endpoint. CMS-agnostic.
    Accepts tags from any source, returns routing decision.
    """
    # 1. Query RAG for brand context
    context = await rag_client.query(
        namespaces=["brand_guidelines", "taxonomy",
                    "product_catalogue", "customer_exclusive"],
        query=build_context_query(request.generated_tags)
    )

    # 2. LLM evaluates tags against context
    evaluation = await llm_client.evaluate(
        tags=request.generated_tags,
        context=context,
        asset_url=request.asset_url
    )

    # 3. Route based on confidence
    decision = router.decide(
        evaluation=evaluation,
        thresholds=config.confidence_thresholds
    )

    # 4. Create human review task if needed
    if decision.requires_review:
        task_id = await task_adapter.create_task(
            asset_id=request.asset_id,
            issues=evaluation.issues,
            adapter=config.notification_adapter
        )

    # 5. Write audit log
    await audit_logger.log(
        request=request,
        evaluation=evaluation,
        decision=decision,
        task_id=task_id
    )

    # 6. Return result
    return GovernanceResponse(
        asset_id=request.asset_id,
        decision=decision,
        evaluation=evaluation,
        audit_id=audit_log.id
    )
```

**GET /api/governance/audit/{asset_id}**
```python
@app.get("/api/governance/audit/{asset_id}")
async def get_audit_trail(asset_id: str):
    """
    Returns full audit trail for an asset.
    For compliance queries and regulatory review.
    """
    return await audit_store.get_history(asset_id)
```

---

### Data Models

**Governance Request**
```python
class GovernanceRequest(BaseModel):
    asset_id: str
    asset_url: str
    generated_tags: List[str]
    source_cms: str          # "aem" | "contentful" | "sitecore"
    callback_url: str
    asset_type: Optional[str] = "default"  # for threshold override
```

**Tag Evaluation**
```python
class TagEvaluation(BaseModel):
    tag: str
    confidence: float        # 0.0 to 1.0
    status: str              # "approved" | "review" | "rejected"
    issue: Optional[str]     # Description of problem if any
    evidence: Optional[str]  # Source document and page
```

**Audit Record**
```python
class AuditRecord(BaseModel):
    audit_id: str
    timestamp: datetime
    asset_id: str
    source_cms: str
    llm_model: str
    llm_version: str
    rag_namespaces_queried: List[str]
    tags_evaluated: List[TagEvaluation]
    overall_decision: str
    reviewer_assigned: Optional[str]
    reviewer_decision: Optional[str]
    review_timestamp: Optional[datetime]
    c2pa_hash: Optional[str]
```

---

### RAG Layer

**Namespace Structure**
```
vector_db/
├── brand_guidelines/     ← Brand tone, values, visual identity
├── taxonomy/             ← Approved tag vocabulary
├── product_catalogue/    ← Product names, codes, descriptions
├── customer_exclusive/   ← Rules not in any CMS
│   ├── legal_guidelines
│   ├── regional_compliance
│   └── campaign_rules
└── golden_dataset/       ← Human-approved examples
```

**Document Record Schema**
```python
{
    "content": "UltraBoost 22 belongs to the Impossible 
                is Nothing campaign for Spring 2025...",
    "namespace": "product_catalogue",
    "source": "product_brief_2025.pdf",
    "page": 3,
    "last_verified": "2026-03-01",
    "expiry": "2026-09-01",
    "status": "active"
}
```

**Stale Content Guard**
```python
async def query_rag(namespaces: List[str], query: str):
    results = await vector_db.query(namespaces, query)

    # Filter stale documents
    active = [r for r in results if r.metadata["status"] == "active"]

    # Flag approaching expiry
    expiring = [r for r in active
                if days_until_expiry(r) < 30]
    if expiring:
        await notify_document_owners(expiring)

    return active
```

---

### Task Adapter (CMS-Agnostic Human Review)

```python
class TaskAdapter:
    """
    Configurable human review task creation.
    Swap adapter in config.yaml — no code changes.
    """

    async def create_task(self, asset_id, issues, adapter):
        if adapter == "aem":
            return await self._create_aem_inbox_task(asset_id, issues)
        elif adapter == "jira":
            return await self._create_jira_ticket(asset_id, issues)
        elif adapter == "slack":
            return await self._post_slack_message(asset_id, issues)
        elif adapter == "email":
            return await self._send_email(asset_id, issues)

    async def _create_aem_inbox_task(self, asset_id, issues):
        """AEM reference implementation."""
        return await aem_client.create_task({
            "title": f"Tag review required: {asset_id}",
            "assignee": "brand-review-team",
            "payload": {"issues": issues}
        })
```

---

### Configuration

```yaml
# config.yaml — all components configurable, no code changes

llm_provider: openai          # openai | anthropic | ollama
llm_model: gpt-4o             # model within provider

vector_db: pinecone           # pinecone | pgvector | weaviate

notification_adapter: aem     # aem | jira | slack | email

confidence_thresholds:
  default:
    auto_approve: 0.85
    human_review: 0.70
    reject: 0.70

  # Asset-type overrides
  hero_images:
    auto_approve: 0.92        # Higher bar for brand-critical assets
  stock_photos:
    auto_approve: 0.75        # Lower bar for low-risk content

audit:
  store: postgresql
  retention_days: 2555        # 7 years — APRA requirement

c2pa:
  enabled: false              # Enable for regulated industries
```

---

## Technical Decisions

**LangGraph for Orchestration**

LangGraph manages the stateful evaluation flow:
- Maintains state across RAG query → LLM evaluation → routing
- Handles retry logic if confidence below threshold
- Conditional branching: approve / review / reject
- Auditable — every state transition logged

```
START
  ↓
query_rag
  ↓
evaluate_tags (LLM)
  ↓
calculate_confidence
  ↓
route_decision ──→ auto_approve ──→ callback_cms ──→ audit ──→ END
                ↓
                human_review ──→ create_task ──→ audit ──→ END
                ↓
                reject ──→ callback_cms ──→ audit ──→ END
```

**Async Processing**

Governance runs asynchronously — no impact on CMS upload performance:

```python
# CMS fires webhook and gets immediate acknowledgement
# Governance runs in background
# Result posted back via callback_url when complete

@app.post("/api/governance/evaluate")
async def evaluate(request: GovernanceRequest, bg: BackgroundTasks):
    bg.add_task(run_governance_pipeline, request)
    return {"status": "accepted", "job_id": generate_id()}
```

**Cold-Start RAG Bootstrap**

No pre-tagged assets required on Day 1.
Governance works from Day 1 using existing brand documents:

```
Week 1: Index brand documents into RAG
        → brand_guidelines.pdf
        → product_catalogue.xlsx
        → approved_tags.csv
        → campaign_briefs/*.pdf

Week 2: Run on 50 sample assets
        Human reviews outputs
        Corrections indexed into golden_dataset namespace

Week 3+: Accuracy improves as golden_dataset grows
         Human review rate drops as confidence increases
```

---

## Deployment Architecture

### Local Development
```yaml
# docker-compose.yml
services:
  governance-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: governance_audit

  redis:
    image: redis:7-alpine
```

### Production (AWS Sydney — Planned)
```
┌──────────────────────────────────────────────────┐
│          Application Load Balancer (HTTPS)        │
└──────────────────────┬───────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────┐
│              ECS Fargate (ap-southeast-2)         │
│   Governance API containers (auto-scaling)        │
│   Data sovereignty: AWS Sydney region             │
└──────┬────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────┐
│   RDS PostgreSQL  │  Pinecone  │  LLM Provider   │
│   (Audit store)   │  (RAG)     │  (Configurable) │
│   AWS Sydney      │            │  Azure OpenAI   │
│   7yr retention   │            │  or Bedrock     │
└──────────────────────────────────────────────────┘
```

**Australian Enterprise Context**

- Deployed in AWS Sydney (ap-southeast-2) for data sovereignty
- Supports APRA CPS 234 compliance requirements
- 7-year audit log retention (APRA standard)
- PII detection before any external LLM API calls
- Azure OpenAI (Australia East) as LLM alternative for APRA-regulated clients

---

## Infrastructure Cost Estimate

| Component | Monthly (10K assets) |
|---|---|
| LLM API (GPT-4) | ~$100–300 |
| Vector DB (Pinecone) | ~$70 |
| Governance API (ECS Fargate) | ~$50–100 |
| Audit Store (RDS PostgreSQL) | ~$25 |
| **Total** | **~$300–500** |

Manual tagging equivalent at 10K assets/month: ~$8,000–12,000.

---

## Current Status

| Component | Status |
|---|---|
| FastAPI foundation | ✅ Complete |
| Governance API design | ✅ Complete |
| CMS-agnostic webhook | 🚧 In progress |
| Tag evaluation (LLM + RAG) | 🚧 In progress |
| RAG namespace setup | ⏳ Planned |
| Decision router | ⏳ Planned |
| Task adapter (AEM Inbox) | ⏳ Planned |
| Audit trail (PostgreSQL) | ⏳ Planned |
| LangGraph orchestration | ⏳ Planned |
| C2PA provenance | ⏳ Planned |
| AWS Sydney deployment | ⏳ Planned |

---

See [GOVERNANCE_LAYER.md](./GOVERNANCE_LAYER.md) for ideation,
validation plan, and go-to-market thinking.
