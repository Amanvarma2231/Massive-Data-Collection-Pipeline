# GraphOne / FrontierAtlas Intelligence Graph Architecture
## Global Multi-Dimensional AI & Venture Ingestion Pipeline (Production Design)

---

### Executive Architecture Overview

GraphOne / FrontierAtlas powers the global Intelligence Graph for the artificial intelligence and venture capital ecosystem. The infrastructure continuously ingests, normalizes, resolves, and enriches multi-dimensional entities?including AI startups, foundation model products, research papers with code correlations, 24-hour job market shifts, and real-time news signals.

The ingestion architecture is divided into five core decoupled subsystems:
1. **Distributed Async Crawling & Anti-Bot Engine**
2. **Deterministic & Fuzzy Entity Resolution Subsystem**
3. **Multi-Tier Resilient LLM Extraction Orchestrator**
4. **Freshness Tracking & State Reconciliation Layer**
5. **Polyglot Storage & Intelligence Knowledge Graph Layer**

---

### 1. Scale Strategy: Acquiring 500,000+ Startups, Products, and Papers

Scaling from 1,000 to 500,000+ records without code alterations relies on horizontal distributed worker partitioning, event-driven task distribution, and backpressure-regulated queues.

```text
[ Seed URLs / Scheduled Cron / RSS Feeds ]
                 ?
                 ?
      ???????????????????????
      ?  Kafka / RabbitMQ   ? ??? Partitioned by domain/source
      ???????????????????????
                 ?
  ???????????????????????????????
  ?              ?              ?
????????????   ????????????   ????????????
? Crawler  ?   ? Crawler  ?   ? Crawler  ? (Celery / Ray Actors running
? Worker 1 ?   ? Worker 2 ?   ? Worker N ?  Playwright Async + aiohttp)
????????????   ????????????   ????????????
      ?              ?              ?
      ???????????????????????????????
                     ?
          ???????????????????????
          ? Redis Bloom Filter  ? ??? O(1) Global URL & entity deduplication
          ???????????????????????
                     ?
          ???????????????????????
          ?  Extraction Buffer  ?
          ???????????????????????
```

#### Key Scale Mechanisms:
* **Partitioned Work Queues (Apache Kafka / RabbitMQ)**: Ingestion tasks are partitioned by target domain hash (`hash(domain) % partitions`). This guarantees per-domain rate limit enforcement and connection pooling isolation without cross-worker race conditions.
* **Stateless Distributed Workers (Ray / Celery / Kubernetes Pods)**: Crawler workers run asynchronously using `asyncio` and `aiohttp` / `Playwright Async`. Node scaling is handled dynamically via Kubernetes Horizontal Pod Autoscaler (HPA) pegged to queue lag.
* **Distributed Bloom Filters (Redis O(1) Lookups)**: With 500k+ records and millions of crawled URLs, Redis-backed scalable Bloom filters (false positive probability < 0.001) check whether an article, paper ID, or entity has already been fetched before opening a socket.
* **Bulk Streaming Pipelines**: Ingestion pipelines stream records in micro-batches (e.g., 500 records per database bulk insert) to avoid memory starvation.

---

### 2. Handling 413s (Payloads) & 429s (Rate Limits) Across Thousands of Concurrencies

#### A. 413 Payload Too Large Mitigation
* **Semantic Density Condenser**: Raw HTML contains >80% non-informative boilerplate (navbars, scripts, tracking pixels, footer links). The `ContentChunker` strips HTML markup and applies structural extraction.
* **Head-and-Tail Truncation**: For long documents (e.g., full research papers or long articles), the system retains the top 70% (abstract, introduction, metadata, key properties) and bottom 30% (conclusions, affiliations, pricing tiers, links), truncating the middle section while staying strictly within a token budget (< 10,000 characters).
* **Sliding Window Chunking**: For multi-section texts requiring deep analysis, text is partitioned into overlapping chunks (4,000 characters with 200 character overlap) and processed with map-reduce extraction.

#### B. 429 Rate Limit Handling & Tiered Fallback Chain
* **Tiered Dynamic Fallback**:
  Tier 1 (Gemini Flash) -> Tier 2 (Groq Llama 3) -> Tier 3 (DeepSeek) -> Tier 4 (Deterministic Rule Engine)
* **Exponential Backoff with Full Jitter**:
  `wait = uniform(0, min(max_delay, base_delay * 2^attempt))`
  Randomized jitter prevents the "thundering herd" problem across concurrent workers.
* **Token Bucket Concurrency Gates**: Distributed rate limiters in Redis track per-minute token consumption and dynamically throttle requests before external API limits are exceeded.

---

### 3. Freshness Tracking & Deduplication Across Distributed Nodes

To guarantee that all 24-hour signals (News and Jobs) are strictly fresh and never processed twice across distributed crawler nodes:

1. **Distributed Locks (Redis Redlock)**: When a candidate URL is discovered by a node, it requests an atomic `SET key lock NX EX 300`. Only the winning node proceeds to crawl.
2. **ETag & `If-Modified-Since` Caching**: HTTP conditional requests ensure that unchanged feeds return `304 Not Modified`, saving 95%+ bandwidth on recurring crawler runs.
3. **Date Normalization & Rolling 24-Hour Sliding Window**: All published timestamps?whether relative ("2 hours ago", "yesterday") or RFC/ISO format?are converted to strict UTC ISO-8601 strings and verified against `0 <= (now - pub_date) <= 86,400 seconds`.
4. **State Reconciliation Engine**: Processed items have their cryptographic content hashes (`SHA-256(canonical_title + canonical_entity)`) stored in a persistent database index with a TTL equal to the retention window.

---

### 4. Storage Strategy: Polyglot Persistence Architecture

#### 1. Primary ACID Store: PostgreSQL
* Stores normalized entity tables with strict JSON Schema constraints.
* Provides ACID guarantees, indexing on canonical names, and relational joins for high-throughput transactional writes.

#### 2. Intelligence Graph: Neo4j
* Models high-order venture ecosystem relationships:
  * `(:Startup {name: "OpenAI"})-[:DEVELOPS]->(:Product {name: "ChatGPT"})`
  * `(:Author {name: "Vaswani"})-[:AUTHORED]->(:Paper)-[:HAS_REPO]->(:GitHubRepo {stars: 35000})`
  * `(:Startup)-[:POSTED]->(:Job {role_family: "Engineering"})`
* Allows N-hop path traversal for venture intelligence, investor signal discovery, and competitive analysis.

#### 3. Vector Engine: Qdrant / pgvector
* Indexes dense embeddings of startup mission statements, product value propositions, and research paper abstracts.
* Enables semantic deduplication, cross-lingual entity resolution, and similarity recommendations across the intelligence platform.
