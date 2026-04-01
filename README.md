# Asset Intelligence Platform

A CMS-agnostic AI metadata governance service
that evaluates AI-generated metadata before
it is applied to digital assets at scale.

## The Problem

AI metadata generation is widely available.
Enterprise governance of that metadata is not.

When a CMS or DAM generates tags for digital
assets, enterprises in regulated industries need:

- Confidence-based routing before tags are applied
- Brand-specific validation against taxonomy
- Human review workflows for uncertain outputs
- Audit trails for compliance and accountability
- Control over thresholds and exclusive brand knowledge

This platform provides that governance layer —
a service consumed by Adobe AEM, Contentful,
Sitecore, or any DAM exposing a metadata API.

## How It Works

```
CMS generates tags via its own AI
         ↓
POST /api/governance/evaluate
{asset_id, asset_url, generated_tags, callback_url}
         ↓
Governance service queries RAG namespaces
(brand guidelines, taxonomy, product catalogue,
 exclusive customer knowledge)
         ↓
LLM evaluates tags against retrieved context
Confidence score generated per tag
         ↓
Decision routing:
> 0.85  → auto-approve → POST back to CMS
0.70–0.85 → human review task created
< 0.70  → reject → reason returned to CMS
         ↓
Audit log written (every decision)
         ↓
[Optional] C2PA provenance watermark applied
```

## Key Benefits

**Customer-controlled governance**
Define confidence thresholds per asset type,
campaign, and risk level. Conservative thresholds
for regulated markets, permissive for high-volume
low-risk content. No code changes required —
configuration only.

**Exclusive knowledge injection**
Index brand knowledge that exists nowhere in
your CMS — legal guidelines, regional compliance
rules, historical brand decisions, competitor
blocklists. Your RAG layer becomes the single
source of truth for governance context that no
AI tagging vendor has access to.

**Predictable infrastructure cost**
Estimated $300–500/month at typical enterprise
asset volumes. Runs asynchronously — no impact
on asset upload or delivery performance.
ROI positive within 2–3 months versus manual
review at equivalent scale.

**CMS-agnostic**
No lock-in to any CMS, AI provider, or vector
database. Each component is configurable and
swappable via config.yaml.

## Architecture

### Core Components

**Governance API**
- CMS-agnostic REST endpoint
- Accepts tag payloads from any source system
- Returns confidence scores and routing decisions
- Configurable thresholds per asset type and risk level

**Tag Evaluation Layer**
- Queries RAG namespaces for brand context
- LLM evaluates each tag against retrieved context
- Returns per-tag confidence scores and issue evidence
- Configurable LLM provider: OpenAI, Anthropic, Ollama

**RAG Context Layer**
- Brand guidelines namespace
- Approved taxonomy namespace
- Product catalogue namespace
- Exclusive customer knowledge namespace
- Approved examples namespace (golden dataset)
- Configurable vector DB: Pinecone, pgvector, Weaviate

**Human Review Task Adapter**
- Configurable notification adapter per deployment
- AEM Inbox (reference implementation)
- Extensible to: Jira, Slack, email, any webhook

**Audit Trail**
- Every decision logged: model, context retrieved,
  confidence score, routing decision, approver, timestamp
- REST API for compliance queries
- Supports regulatory review and brand audits

**C2PA Provenance (optional)**
- Watermarks AI-generated metadata
- Enables downstream verification of provenance
- Designed for regulated industries

### Data Flow

```
CMS Webhook → Governance API
→ RAG Query → LLM Evaluation
→ Confidence Score → Decision Router
→ [Auto-approve | Human Review | Reject]
→ Audit Log → Callback to CMS
```

## Technical Stack

- **API:** Python 3.11, FastAPI
- **Orchestration:** LangGraph
- **LLM:** Configurable (OpenAI GPT-4 default)
- **Vector DB:** Configurable (Pinecone default)
- **Embeddings:** OpenAI text-embedding-ada-002
- **Audit Store:** PostgreSQL
- **Infrastructure:** Docker, AWS Sydney (planned)

## Reference Implementation

Adobe AEM is the reference CMS implementation.
The governance service integrates via AEM workflow
steps and writes results back via AEM Assets API.
The notification adapter uses AEM Inbox for
human review task creation.

The architecture is portable to any CMS exposing
metadata read/write APIs and webhook capabilities.

## Configuration

```yaml
# config.yaml
llm_provider: openai          # openai | anthropic | ollama
vector_db: pinecone           # pinecone | pgvector | weaviate
notification_adapter: aem     # aem | jira | slack | email
confidence_thresholds:
  auto_approve: 0.85
  human_review: 0.70
  reject: 0.70
asset_type_overrides:
  hero_images:
    auto_approve: 0.92
  stock_photos:
    auto_approve: 0.75
```

## Current Status

**Completed:**
- ✅ FastAPI foundation and core endpoints
- ✅ Governance layer architecture defined
- ✅ CMS-agnostic API design

**In Progress:**
- 🚧 Tag evaluation endpoint (LLM + RAG)
- 🚧 RAG namespace setup (Pinecone)

**Planned:**
- ⏳ Confidence-based decision routing
- ⏳ Human review task adapter
- ⏳ Audit trail (PostgreSQL)
- ⏳ AEM reference implementation
- ⏳ C2PA provenance integration
- ⏳ Production deployment (AWS Sydney)

## Infrastructure Cost Estimate

| Component | Monthly Cost |
|---|---|
| LLM API (10K assets) | ~$100–300 |
| Vector DB (Pinecone) | ~$70 |
| Governance API (AWS Fargate) | ~$50–100 |
| Audit Store (RDS PostgreSQL) | ~$25 |
| **Total** | **~$300–500** |

Compared to manual review at equivalent scale: $40,000–100,000/year.

## Running Locally

```bash
git clone https://github.com/rupeshaec/asset-intelligence-platform
cd asset-intelligence-platform
cp .env.example .env
docker-compose up -d
curl http://localhost:8000/health
```

See [GOVERNANCE_LAYER.md](./GOVERNANCE_LAYER.md)
for the full ideation and validation plan.
