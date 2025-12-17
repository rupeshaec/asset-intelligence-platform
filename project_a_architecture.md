# Project A: AI-Powered Asset Search - Architecture

## 1. SYSTEM OVERVIEW

### Purpose
Semantic search system for digital assets (images, videos, documents) using natural language queries and AI-powered automated tagging.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                          │
│              (Natural language queries)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Search     │  │  Ingestion   │  │   Tagging    │     │
│  │  Endpoints   │  │  Endpoints   │  │  Endpoints   │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │                  ↓                  ↓
          │         ┌─────────────────┐  ┌─────────────────┐
          │         │  Adobe AEM      │  │  GPT-4 Vision   │
          │         │  Assets API     │  │  API            │
          │         └────────┬────────┘  └────────┬────────┘
          │                  │                     │
          │                  ↓                     │
          │         ┌─────────────────────────────┘
          │         │  Embedding Pipeline
          │         │  (OpenAI API)
          │         └────────┬────────────────────┐
          │                  │                    │
          │                  ↓                    ↓
          │         ┌─────────────────┐  ┌──────────────┐
          └────────→│   Pinecone      │  │  Metadata    │
                    │   Vector DB     │  │  Cache       │
                    └─────────────────┘  └──────────────┘
```

### Core Data Flow

**Ingestion Flow:**
1. Fetch assets from Adobe AEM Assets API (images, metadata)
2. Extract metadata (title, description, tags, file info)
3. Generate embeddings via OpenAI text-embedding-3-small
4. For images: Optional GPT-4 Vision analysis for rich descriptions
5. Store vectors in Pinecone with metadata
6. Cache metadata locally for fast retrieval

**Search Flow:**
1. User submits natural language query
2. Generate query embedding (same OpenAI model)
3. Pinecone cosine similarity search
4. Apply metadata filters (type, date, tags)
5. Return top-k ranked results with scores
6. Log query for analytics

**Tagging Flow:**
1. Receive asset (image/document)
2. Send to GPT-4 Vision with tagging prompt
3. Extract structured tags from response
4. Update asset metadata in AEM
5. Re-embed with new tags

---

## 2. TECHNICAL DECISIONS

### Decision 1: Vector Database - Pinecone

**Options Evaluated:**
- Pinecone (managed, cloud-native)
- Weaviate (open-source, self-hosted)
- pgvector (PostgreSQL extension)
- Milvus (open-source, high-performance)

**Choice: Pinecone**

**Reasoning:**
- **Managed service**: Zero infrastructure overhead - critical for solo learning project
- **Proven scale**: Handles billions of vectors in production
- **Developer experience**: Excellent Python SDK, clear documentation
- **OpenAI integration**: Native support for 1536-dim embeddings
- **Free tier**: 1 index, 100K vectors - sufficient for demo/learning
- **Fast iteration**: Focus on application logic, not database ops

**Trade-offs Accepted:**
- Vendor lock-in (mitigated: standard vector format, can migrate)
- Cost at scale (acceptable for POC; can optimize later)
- Less control vs self-hosted (not a concern for learning)

**Alternative Not Chosen - Weaviate:**
Why not: Requires Docker/K8s setup, database management, monitoring. Adds operational complexity that distracts from core learning goals.

---

### Decision 2: Embedding Model - OpenAI text-embedding-3-small

**Options Evaluated:**
- OpenAI text-embedding-3-small (1536 dims, API)
- OpenAI text-embedding-3-large (3072 dims, API)
- Sentence-transformers (open-source, self-hosted)
- Cohere embeddings (API)

**Choice: OpenAI text-embedding-3-small**

**Reasoning:**
- **Performance**: MTEB benchmark scores comparable to larger models
- **Dimensions**: 1536 - sweet spot between quality and storage cost
- **Cost**: $0.02 per 1M tokens (10x cheaper than ada-002)
- **Latency**: <100ms per request (fast enough for real-time)
- **Ecosystem**: Same vendor as GPT-4V simplifies API management
- **Quality**: Excellent semantic understanding for both text and image descriptions

**Trade-offs Accepted:**
- External dependency (requires API keys, network calls)
- Per-call cost (vs free self-hosted models)
- Rate limits (3,500 RPM on paid tier - sufficient for learning)

**Alternative Not Chosen - Sentence-transformers:**
Why not: Requires hosting ML model, GPU for reasonable speed, more code complexity. Want to focus on system design, not model serving infrastructure.

---

### Decision 3: Backend Framework - FastAPI

**Options Evaluated:**
- FastAPI (async, modern)
- Flask (simple, mature)
- Django (full-featured)
- Express.js (Node.js alternative)

**Choice: FastAPI**

**Reasoning:**
- **Async/await**: Native async support crucial for I/O-bound operations (API calls to OpenAI, Pinecone, AEM)
- **Type safety**: Pydantic models catch bugs at development time
- **Auto-documentation**: Swagger UI generated automatically - essential for API testing
- **Performance**: Comparable to Node.js, faster than Flask
- **Modern patterns**: Dependency injection, middleware, background tasks built-in
- **Growing ecosystem**: Active community, good library support

**Trade-offs Accepted:**
- Steeper learning curve vs Flask (but learning is the goal)
- Less mature than Flask/Django (acceptable risk for new project)

**Why Not Flask:**
No native async support - would need to bolt on with Celery/threading. FastAPI's async is cleaner for this use case.

---

### Decision 4: Image Analysis - GPT-4 Vision API

**Options Evaluated:**
- GPT-4 Vision (multimodal LLM)
- CLIP (open-source, image embeddings)
- Custom CNN (trained model)
- Google Vision API

**Choice: GPT-4 Vision**

**Reasoning:**
- **Rich descriptions**: Generates natural language descriptions, not just labels
- **Context understanding**: Can follow complex instructions ("describe the mood," "identify brand elements")
- **No training required**: Zero-shot learning works out of box
- **Structured output**: Can request JSON format for tags
- **Quality**: State-of-art vision understanding as of late 2024

**Use Case:**
Generate detailed metadata for automated tagging:
- Scene description
- Object identification
- Color palette
- Mood/sentiment
- Text extraction (OCR capability)

**Trade-offs Accepted:**
- Cost: ~$0.01 per image (higher than CLIP/free alternatives)
- Latency: ~2-3 seconds per image (vs <100ms for CLIP)
- API dependency (requires network call)

**Hybrid Approach Considered:**
Use CLIP for embeddings (fast, cheap) + GPT-4V for tagging (rich, accurate). May implement if cost becomes issue.

---

### Decision 5: Content Source - Adobe AEM Assets API

**Options Evaluated:**
- Adobe AEM Assets (enterprise DAM)
- Cloudinary API (media management)
- AWS S3 (simple storage)
- Mock/local filesystem

**Choice: Adobe AEM Assets API**

**Reasoning:**
- **Real-world relevance**: AEM is industry-standard DAM used by enterprises
- **Interview value**: Shows ability to integrate with enterprise systems
- **API maturity**: Well-documented REST API
- **Rich metadata**: AEM stores extensive asset metadata (tags, workflows, versions)
- **Authentication learning**: OAuth 2.0 flow - good learning experience

**Trade-offs Accepted:**
- Setup complexity: Required Adobe developer account, OAuth flow
- Learning curve: AEM-specific concepts (renditions, workflows)
- Not universally accessible (some employers may not use AEM)

**Why Not S3:**
Too simple - doesn't demonstrate enterprise integration skills. S3 is just storage; AEM is a complete content management system.

---

### Decision 6: Deployment Strategy - Docker + AWS ECS (Planned)

**Options Evaluated:**
- Docker Compose (local dev)
- AWS ECS (container orchestration)
- Kubernetes (complex orchestration)
- Heroku/Vercel (PaaS)

**Choice: Docker + AWS ECS**

**Reasoning:**
- **Containerization**: Docker ensures dev/prod parity
- **Managed orchestration**: ECS handles container scheduling, auto-scaling
- **AWS ecosystem**: Easy integration with CloudWatch, ALB, Secrets Manager
- **Learning goals**: Industry-standard deployment pattern
- **Cost**: ECS Fargate free tier available

**Current State:**
- Local dev: Docker Compose
- Production: Planned for ECS (not yet implemented)

**Trade-offs Accepted:**
- More complex than Heroku (but demonstrates infrastructure skills)
- AWS-specific (could be more portable with K8s, but ECS is simpler)

**Why Not Kubernetes:**
Overkill for single-service application. ECS provides sufficient orchestration with less operational overhead.

---

## 3. DETAILED COMPONENT DESIGN

### 3.1 Data Models

**Asset Metadata (Internal)**
```python
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class AssetMetadata(BaseModel):
    asset_id: str  # UUID
    title: str
    description: Optional[str]
    file_type: str  # "image", "video", "document"
    file_url: str
    thumbnail_url: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    file_size_bytes: int
    dimensions: Optional[dict]  # {"width": 1920, "height": 1080}
    aem_path: str  # Original AEM path
    embedding_generated: bool
    ai_tags: Optional[List[str]]  # Tags from GPT-4V
```

**Vector Record (Pinecone Schema)**
```python
{
    "id": "asset_uuid",
    "values": [0.123, -0.456, ...],  # 1536 floats
    "metadata": {
        "title": "string",
        "file_type": "image",
        "tags": ["landscape", "sunset"],
        "created_at": "2024-12-17T10:30:00Z",
        "url": "https://...",
        "score": 0.95  # Optional: quality score
    }
}
```

**Search Query**
```python
class SearchRequest(BaseModel):
    query: str  # Natural language query
    filters: Optional[dict] = None  # {"file_type": "image"}
    top_k: int = 10
    include_metadata: bool = True
```

**Search Result**
```python
class SearchResult(BaseModel):
    asset_id: str
    similarity_score: float  # 0.0 to 1.0
    metadata: AssetMetadata
    match_explanation: Optional[str]  # Why this matched
```

---

### 3.2 API Endpoints

**POST /api/v1/search**
```python
@app.post("/api/v1/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest, api_key: str = Depends(verify_api_key)):
    """
    Semantic search across assets using natural language.
    
    Example query: "sunset photos with mountains and warm colors"
    """
    # 1. Generate query embedding
    query_embedding = await openai_client.create_embedding(request.query)
    
    # 2. Search Pinecone
    results = pinecone_index.query(
        vector=query_embedding,
        top_k=request.top_k,
        filter=request.filters,
        include_metadata=True
    )
    
    # 3. Enrich with full metadata
    enriched_results = [
        SearchResult(
            asset_id=match.id,
            similarity_score=match.score,
            metadata=await get_asset_metadata(match.id)
        )
        for match in results.matches
    ]
    
    return SearchResponse(
        results=enriched_results,
        query_time_ms=elapsed_time,
        total_results=len(results)
    )
```

**POST /api/v1/ingest**
```python
@app.post("/api/v1/ingest")
async def ingest_assets(
    aem_folder_path: str,
    background_tasks: BackgroundTasks
):
    """
    Trigger ingestion of assets from Adobe AEM.
    Runs asynchronously in background.
    """
    job_id = generate_job_id()
    
    background_tasks.add_task(
        ingest_pipeline,
        aem_folder_path=aem_folder_path,
        job_id=job_id
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Ingestion started"
    }
```

**POST /api/v1/tag**
```python
@app.post("/api/v1/tag")
async def auto_tag_asset(asset_id: str):
    """
    Generate AI tags for an asset using GPT-4 Vision.
    """
    # 1. Fetch asset from AEM
    asset = await aem_client.get_asset(asset_id)
    
    # 2. Send to GPT-4 Vision
    tags = await gpt4v_client.analyze_image(
        image_url=asset.url,
        prompt="Generate 5-10 descriptive tags for this image. Return JSON array."
    )
    
    # 3. Update metadata
    await update_asset_metadata(asset_id, ai_tags=tags)
    
    # 4. Re-embed with new tags
    await regenerate_embedding(asset_id)
    
    return {"asset_id": asset_id, "tags": tags}
```

**GET /api/v1/similar/{asset_id}**
```python
@app.get("/api/v1/similar/{asset_id}")
async def find_similar_assets(asset_id: str, top_k: int = 10):
    """
    Find assets similar to a given asset.
    """
    # 1. Get asset's embedding from Pinecone
    asset_vector = await pinecone_index.fetch(ids=[asset_id])
    
    # 2. Search for similar vectors
    results = pinecone_index.query(
        vector=asset_vector.vectors[asset_id].values,
        top_k=top_k + 1,  # +1 to exclude self
        include_metadata=True
    )
    
    # 3. Filter out the query asset itself
    similar = [r for r in results.matches if r.id != asset_id]
    
    return {"similar_assets": similar[:top_k]}
```

---

### 3.3 Ingestion Pipeline (Detailed)

```python
async def ingest_pipeline(aem_folder_path: str, job_id: str):
    """
    Complete ingestion workflow.
    """
    try:
        # 1. Fetch assets from AEM
        assets = await aem_client.list_assets(folder_path=aem_folder_path)
        logger.info(f"Found {len(assets)} assets to process")
        
        # 2. Process in batches (avoid rate limits)
        batch_size = 100
        for batch in chunk_list(assets, batch_size):
            
            # 3. For each asset in batch
            for asset in batch:
                try:
                    # a. Extract metadata
                    metadata = extract_metadata(asset)
                    
                    # b. Generate embedding
                    text_for_embedding = f"{metadata.title} {metadata.description} {' '.join(metadata.tags)}"
                    embedding = await openai_client.create_embedding(text_for_embedding)
                    
                    # c. Store in Pinecone
                    await pinecone_index.upsert(
                        vectors=[(
                            metadata.asset_id,
                            embedding,
                            {
                                "title": metadata.title,
                                "file_type": metadata.file_type,
                                "tags": metadata.tags,
                                "url": metadata.file_url
                            }
                        )]
                    )
                    
                    # d. Cache metadata locally
                    await cache_metadata(metadata)
                    
                    logger.info(f"Processed asset {metadata.asset_id}")
                    
                except Exception as e:
                    logger.error(f"Failed to process asset {asset.id}: {e}")
                    continue
            
            # 4. Rate limit pause between batches
            await asyncio.sleep(1)
        
        logger.info(f"Ingestion job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Ingestion job {job_id} failed: {e}")
        raise
```

---

### 3.4 Embedding Generation Strategy

**Text Embeddings:**
- **Model**: text-embedding-3-small (1536 dimensions)
- **Input**: Combined title + description + tags
- **Batching**: Up to 2048 texts per API call (OpenAI limit)
- **Cost**: ~$0.02 per 1M tokens

**Image Embeddings (Hybrid Approach):**

Option 1: Text-based (Current)
```python
# Use GPT-4V to generate description, then embed the description
description = await gpt4v.analyze(image_url)
embedding = await openai.embed(description)
```

Option 2: Vision-native (Future)
```python
# Use CLIP or similar for direct image embeddings
embedding = await clip_model.encode_image(image)
```

**Rationale for Text-based Approach:**
- Reuses existing embedding model (consistency)
- GPT-4V descriptions are semantically rich
- Single vector space for all content types
- Trade-off: Loses some visual nuance vs native image embeddings

---

### 3.5 Error Handling & Resilience

**Rate Limit Handling (OpenAI API):**
```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
async def create_embedding_with_retry(text: str):
    try:
        return await openai_client.create_embedding(text)
    except RateLimitError as e:
        logger.warning(f"Rate limit hit, retrying: {e}")
        raise  # Tenacity will retry
```

**AEM API Failures:**
```python
async def fetch_asset_safe(asset_id: str) -> Optional[Asset]:
    try:
        return await aem_client.get_asset(asset_id)
    except AEMConnectionError:
        logger.error(f"AEM connection failed for {asset_id}")
        return None  # Graceful degradation
    except AEMAuthError:
        logger.critical("AEM authentication expired")
        await refresh_aem_token()
        return await aem_client.get_asset(asset_id)  # Retry once
```

**Pinecone Unavailability:**
```python
async def search_with_fallback(query: str):
    try:
        return await pinecone_index.query(query)
    except PineconeError:
        logger.error("Pinecone unavailable, using cached results")
        return await get_cached_search_results(query)
```

---

### 3.6 Monitoring & Observability

**Structured Logging (structlog):**
```python
import structlog

logger = structlog.get_logger()

# Example log entry
logger.info(
    "search_query_executed",
    query=query_text,
    results_count=len(results),
    latency_ms=elapsed_time,
    user_id=user_id
)
```

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram

# Request metrics
search_requests = Counter('search_requests_total', 'Total search requests')
search_latency = Histogram('search_latency_seconds', 'Search query latency')

# Embedding metrics
embedding_generation_time = Histogram('embedding_generation_seconds', 'Time to generate embedding')
embedding_errors = Counter('embedding_errors_total', 'Failed embedding generations')

# Usage
with search_latency.time():
    results = await execute_search(query)
search_requests.inc()
```

**Key Metrics to Track:**
- Search query latency (p50, p95, p99)
- Embedding generation time
- API error rates (OpenAI, Pinecone, AEM)
- Cache hit rate
- Ingestion throughput (assets/minute)

---

### 3.7 Performance Optimization

**Caching Strategy:**
```python
from functools import lru_cache
import redis

# In-memory cache for frequently accessed metadata
@lru_cache(maxsize=1000)
async def get_asset_metadata_cached(asset_id: str):
    return await fetch_asset_metadata(asset_id)

# Redis for embedding cache (avoid re-computation)
async def get_or_generate_embedding(text: str) -> List[float]:
    cache_key = f"embedding:{hash(text)}"
    
    # Check cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Generate and cache
    embedding = await openai_client.create_embedding(text)
    await redis_client.setex(cache_key, 3600, json.dumps(embedding))
    return embedding
```

**Batch Processing:**
```python
# Batch embeddings to reduce API calls
async def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    # OpenAI allows up to 2048 inputs per call
    embeddings = await openai_client.create_embeddings(texts)
    return embeddings
```

---

### 3.8 Security Considerations

**API Authentication:**
```python
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    if credentials.credentials != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials
```

**Input Validation:**
```python
class SearchRequest(BaseModel):
    query: str = Field(..., max_length=500)  # Prevent abuse
    top_k: int = Field(10, ge=1, le=100)  # Limit result size
    
    @validator('query')
    def validate_query(cls, v):
        # Sanitize input
        if len(v.strip()) == 0:
            raise ValueError("Query cannot be empty")
        return v.strip()
```

**Secrets Management:**
```python
# Environment variables (never commit)
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
AEM_CLIENT_ID=...
AEM_CLIENT_SECRET=...

# In production: AWS Secrets Manager
import boto3

def get_secret(secret_name: str) -> str:
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']
```

---

### 3.9 Scalability Considerations

**Current Bottlenecks:**
1. OpenAI API rate limits (3,500 RPM paid tier)
2. Pinecone free tier query limits
3. Single-instance FastAPI (no horizontal scaling)

**Solutions for Scale:**

**Async Processing:**
```python
# Use background tasks for ingestion
from fastapi import BackgroundTasks

@app.post("/ingest")
async def ingest(path: str, bg: BackgroundTasks):
    bg.add_task(ingest_pipeline, path)
    return {"status": "queued"}
```

**Horizontal Scaling:**
- Deploy multiple FastAPI instances behind ALB
- Use Redis for shared state/caching
- Pinecone handles vector index scaling automatically

**Cost Optimization at Scale:**
- Cache frequent queries (reduce Pinecone calls)
- Batch embeddings (reduce OpenAI calls)
- Consider self-hosted embeddings at high volume (>10M calls/month)

---

## 4. DEPLOYMENT ARCHITECTURE

### Local Development
```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - PINECONE_API_KEY=${PINECONE_API_KEY}
    volumes:
      - ./app:/app
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

### Production (AWS ECS - Planned)
```
┌─────────────────────────────────────────────┐
│         Application Load Balancer            │
│              (HTTPS/TLS)                     │
└──────────────┬──────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────┐
│              ECS Fargate                     │
│  ┌────────────┐  ┌────────────┐            │
│  │  FastAPI   │  │  FastAPI   │ (Auto-scale)│
│  │ Container 1│  │ Container 2│            │
│  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────┘
               │
               ↓
┌──────────────┬──────────────┬───────────────┐
│   Pinecone   │   OpenAI     │   AEM Assets  │
│   (Vector DB)│   (Embeddings│   (Content)   │
└──────────────┴──────────────┴───────────────┘
```

**Infrastructure as Code (Planned):**
- Terraform for AWS resources
- GitHub Actions for CI/CD
- CloudWatch for logs/metrics

---

## 5. TESTING STRATEGY

**Unit Tests:**
```python
# test_embeddings.py
async def test_embedding_generation():
    text = "sample image description"
    embedding = await generate_embedding(text)
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)

async def test_similarity_search():
    results = await search("sunset photos")
    assert len(results) > 0
    assert all(r.similarity_score >= 0 and r.similarity_score <= 1 for r in results)
```

**Integration Tests:**
```python
# test_api.py
from fastapi.testclient import TestClient

def test_search_endpoint():
    response = client.post("/api/v1/search", json={
        "query": "mountain landscape",
        "top_k": 5
    })
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 5
```

---

## 6. FUTURE ENHANCEMENTS

**Phase 2 (If Time Permits):**
- [ ] Multi-modal search (text + image query)
- [ ] Fine-tuned embeddings on domain-specific data
- [ ] Real-time indexing (webhook from AEM on asset upload)
- [ ] Recommendation engine (collaborative filtering)
- [ ] A/B testing framework for embedding models

**Technical Debt:**
- Move to async AEM client (current is sync)
- Implement proper job queue (Celery/RQ)
- Add comprehensive test coverage (target: 80%+)
- Set up staging environment

---

## SUMMARY

**What Makes This Architecture Interview-Ready:**
1. ✅ Clear separation of concerns (ingestion, search, tagging)
2. ✅ Justified technical decisions with trade-offs
3. ✅ Production considerations (monitoring, error handling, scaling)
4. ✅ Real-world integrations (AEM, not toy datasets)
5. ✅ Modern stack (async Python, vector DBs, LLMs)

**Key Talking Points for Interviews:**
- "I chose Pinecone over self-hosted to focus on system design rather than ops"
- "Used hybrid approach: GPT-4V for tagging, embeddings for search"
- "Implemented retry logic with exponential backoff for API resilience"
- "Designed for horizontal scaling with stateless containers"