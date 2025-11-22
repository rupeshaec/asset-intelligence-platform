# Asset Intelligence Platform

Semantic search and automated classification system for digital assets using vector embeddings and large language models.

## Overview

Traditional asset management relies on manual tagging and keyword-based search, which breaks down at scale. This project implements semantic search using vector embeddings, enabling natural language queries across image and document libraries.

**Key capabilities:**
- Natural language search ("sunset photos with mountains" vs. keyword matching)
- Automated visual tagging using GPT-4 Vision
- Multi-modal search (combine text queries with image similarity)
- Real-time asset indexing pipeline

## Architecture

### Core Components

**Ingestion Layer**
- Adobe AEM Assets API integration for metadata extraction
- Authentication and connection pooling for API reliability
- Batch processing for bulk asset migration

**Embedding Pipeline**
- OpenAI Embeddings API for text and image vectorization
- Embedding dimension: 1536 (OpenAI ada-002 model)
- Processing rate: ~500 assets/minute

**Vector Database**
- Evaluating: Pinecone (managed) vs. Weaviate (self-hosted)
- Trade-off: Operational simplicity vs. infrastructure control
- Index structure: Flat index for <1M vectors, HNSW for scale

**Search API**
- FastAPI for low-latency query processing
- Query → embedding → vector search → ranked results
- Sub-100ms p95 latency target for cached queries

**AI Tagging Service**
- GPT-4 Vision for automated image analysis
- Generates: tags, descriptions, alt-text, contextual metadata
- Fallback strategy: CLIP embeddings when GPT-4V unavailable

### Data Flow

```
Asset Upload → Metadata Extraction → Embedding Generation → 
Vector DB Storage → Indexed & Searchable  → AI Tagging (async)
```

### Multi-Modal Search Architecture

Combining text and image queries requires weighted embedding fusion:
- Text query embedding (weight: 0.7)
- Image similarity embedding (weight: 0.3)
- Cosine similarity for ranking

**Current challenge:** Optimizing weight distribution based on query intent. Exploring learned weighting vs. fixed ratios.

## Technical Stack

- **Backend:** Python 3.11, FastAPI
- **Vector Database:** Pinecone (primary evaluation), Weaviate (secondary)
- **AI/ML:** OpenAI Embeddings API, GPT-4 Vision API
- **Content Source:** Adobe AEM Assets API
- **Infrastructure:** Docker, AWS (planned deployment)
- **Observability:** Structured logging (structlog), Prometheus metrics

## Current Status

**Completed:**
- ✅ AEM Assets API integration
- ✅ Embedding pipeline (OpenAI integration)
- ✅ Vector database setup (Pinecone)
- ✅ Basic semantic search API
- ✅ GPT-4V automated tagging

**In Progress:**
- 🚧 Multi-modal search implementation
- 🚧 Real-time indexing pipeline for new assets
- 🚧 Performance optimization (caching, batch processing)

**Planned:**
- ⏳ Production deployment (AWS ECS)
- ⏳ Monitoring and alerting (Prometheus + Grafana)
- ⏳ Vector database cost optimization analysis

## Technical Decisions & Trade-offs

### Vector Database Selection

**Pinecone (currently using):**
- ✅ Managed service (zero ops overhead)
- ✅ Fast setup and iteration
- ❌ Higher cost at scale
- ❌ Vendor lock-in

**Weaviate (evaluating):**
- ✅ Self-hosted (infrastructure control)
- ✅ Lower cost at scale
- ❌ Operational complexity
- ❌ Requires Kubernetes/container orchestration

**Decision:** Pinecone for development/MVP, evaluate Weaviate migration if cost becomes prohibitive at scale.

### Embedding Model Choice

Using OpenAI `text-embedding-ada-002`:
- 1536 dimensions (good balance of accuracy vs. storage)
- $0.0001 per 1K tokens (acceptable for prototype scale)
- Alternative considered: Cohere embeddings (similar performance, slightly cheaper)

### Real-Time vs. Batch Indexing

**Trade-off:** Low latency (real-time) vs. cost efficiency (batch)

Current approach: Hybrid
- Real-time indexing for user-uploaded assets (immediate searchability)
- Batch processing for bulk migrations (cost-optimized)
- Event-driven architecture using message queue (future: SQS/Kafka)

## Observability

**Metrics tracked:**
- Embedding generation latency (p50, p95, p99)
- Vector search query time
- Cache hit rate (planned)
- AI tagging accuracy (manual spot-check, ~95% satisfactory rate observed)

**Logging strategy:**
- Structured logs (JSON format) for query patterns and error analysis
- Correlation IDs for request tracing
- Log sampling for high-volume operations

## Open Questions

**Performance:**
- What's the optimal batch size for embedding generation? (currently 50 assets/batch)
- How to handle embedding model version upgrades without re-indexing everything?

**Architecture:**
- Event-driven indexing vs. polling for new assets?
- Caching strategy for frequently searched queries (Redis vs. in-memory)?

**Cost:**
- At what scale does self-hosted Weaviate become cost-effective vs. Pinecone?

## Running Locally
```bash
# Clone and setup
git clone https://github.com/yourusername/asset-intelligence-platform
cd asset-intelligence-platform

# Environment setup
cp .env.example .env
# Add your API keys: OPENAI_API_KEY, PINECONE_API_KEY, AEM_ASSETS_API_KEY

# Docker setup
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

