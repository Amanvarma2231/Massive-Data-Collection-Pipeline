from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from pathlib import Path

def create_architecture_pdf(filename="architecture.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#2563EB'),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=4
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceBefore=5,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#1E293B'),
        leftIndent=10,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )

    elements = []

    # PAGE 1: Executive Summary & Scale Strategy
    elements.append(Paragraph("GraphOne / FrontierAtlas Intelligence Graph", title_style))
    elements.append(Paragraph("Phase VI: Technical Architecture & Production Design Document", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=8))

    elements.append(Paragraph("1. Executive Architecture Overview", h1_style))
    elements.append(Paragraph(
        "GraphOne / FrontierAtlas powers the global Intelligence Graph for the artificial intelligence "
        "and venture capital ecosystem. The platform ingests, resolves, normalizes, and enriches entities across startups, "
        "products, research papers with GitHub metrics, 24-hour job signals, and real-time news feeds. "
        "The architecture is designed for fault tolerance, anti-bot resilience, zero hallucination, and horizontal scalability.",
        body_style
    ))

    elements.append(Paragraph("2. Scale Strategy: Acquiring 500,000+ Records Automatically", h1_style))
    elements.append(Paragraph(
        "Scaling from thousands to 500,000+ records without manual intervention or architectural refactoring is achieved via "
        "a decoupled, event-driven distributed system:",
        body_style
    ))

    elements.append(Paragraph("? <b>Distributed Partitioned Queues (Kafka / RabbitMQ)</b>: Crawl tasks are partitioned by domain hash (hash(domain) % partitions). This prevents thundering herds on individual web hosts while maximizing parallel throughput across independent domains.", bullet_style))
    elements.append(Paragraph("? <b>Stateless Async Workers (Ray / Celery on Kubernetes)</b>: Independent crawler nodes run asyncio + aiohttp / Playwright Async. Cluster size automatically expands via Kubernetes HPA based on queue backpressure.", bullet_style))
    elements.append(Paragraph("? <b>Distributed Bloom Filters (Redis O(1) Lookups)</b>: Scalable Redis Bloom filters verify in sub-millisecond time whether a URL or entity has been processed, eliminating redundant network hops and socket exhaustion.", bullet_style))
    elements.append(Paragraph("? <b>Micro-Batch Bulk Ingestion</b>: Extracted records stream into persistent storage in micro-batches (500 records per transaction), eliminating database memory spikes.", bullet_style))

    scale_table_data = [
        [Paragraph("<b>Component</b>", code_style), Paragraph("<b>1,000 Records (Trial)</b>", code_style), Paragraph("<b>500,000+ Records (Production Scale)</b>", code_style)],
        [Paragraph("Worker Pool", body_style), Paragraph("Async Local Pool (25 workers)", body_style), Paragraph("Ray Distributed Cluster (128 Pods)", body_style)],
        [Paragraph("Task Distribution", body_style), Paragraph("Asyncio In-Memory Queue", body_style), Paragraph("Apache Kafka (32 Partitions)", body_style)],
        [Paragraph("Deduplication", body_style), Paragraph("In-Memory Set + SQLite Unique", body_style), Paragraph("Redis Scalable Bloom Filters + Sharded PostgreSQL", body_style)],
        [Paragraph("Anti-Bot / Proxy", body_style), Paragraph("Stealth UA + Header Rotation", body_style), Paragraph("Residential Proxy Pool + Camoufox Headless Fleet", body_style)]
    ]
    t_scale = Table(scale_table_data, colWidths=[110, 180, 240])
    t_scale.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(Spacer(1, 4))
    elements.append(t_scale)

    # PAGE 2: Resilient LLM Orchestration & Freshness
    elements.append(PageBreak())
    elements.append(Paragraph("3. Managing Context Windows (413s) & Rate Limits (429s)", h1_style))
    elements.append(Paragraph(
        "LLM-based entity extraction at scale faces two critical operational hurdles: token payload overflows (413) and rate limits (429).",
        body_style
    ))

    elements.append(Paragraph("A. 413 Payload Too Large Elimination Strategy:", h2_style))
    elements.append(Paragraph("? <b>Boilerplate Stripping</b>: The ContentChunker removes DOM clutter, scripts, styles, and navigation tags, condensing raw web pages by 75-85% while preserving dense semantic data.", bullet_style))
    elements.append(Paragraph("? <b>Head-and-Tail Truncation (70/30 Rule)</b>: For lengthy technical papers and articles, the engine retains the top 70% (abstract, introduction, metadata) and bottom 30% (conclusions, pricing, contact), capping context to 10,000 characters.", bullet_style))
    elements.append(Paragraph("? <b>Deterministic NLP Fallback</b>: If raw payloads exceed model limits, Tier 4 deterministic heuristic extraction parses structured data with zero model latency.", bullet_style))

    elements.append(Paragraph("B. 429 Rate Limit Handling & Fallback Routing Chain:", h2_style))
    elements.append(Paragraph("? <b>Multi-Tier Fallback Chain</b>: Automatic cascading failover: Gemini 1.5 Flash -> Groq Llama 3 -> DeepSeek Chat -> Deterministic Rule Parser.", bullet_style))
    elements.append(Paragraph("? <b>Full Jitter Exponential Backoff</b>: Retries use randomized jitter to prevent synchronous re-try floods.", bullet_style))
    elements.append(Paragraph("? <b>Leaky Bucket Rate Limiters</b>: Client-side token buckets throttle requests before hitting provider rate limits.", bullet_style))

    elements.append(Spacer(1, 4))
    elements.append(Paragraph("4. Freshness Tracking: Guarantees for 24-Hour Real-Time Signals", h1_style))
    elements.append(Paragraph(
        "To ensure all ingested job and news signals are strictly published within the last 24 hours without duplicate processing:",
        body_style
    ))
    elements.append(Paragraph("? <b>Strict UTC ISO-8601 Normalization</b>: Relative dates ('2 hours ago', 'yesterday') and missing meta tags are normalized to UTC ISO-8601 timestamps and filtered with 0 <= (now - pub_date) <= 24h.", bullet_style))
    elements.append(Paragraph("? <b>Distributed Redlock Synchronization</b>: Atomic Redis locks prevent multiple crawler nodes from fetching the same fresh article or job URL simultaneously.", bullet_style))
    elements.append(Paragraph("? <b>HTTP ETag / Last-Modified Caching</b>: Polling feeds use conditional HTTP headers, skipping re-downloads when servers return 304 Not Modified.", bullet_style))
    elements.append(Paragraph("? <b>Content Fingerprinting</b>: SHA-256 checksums on canonical title + company ensure identical postings with differing tracking URLs are deduped.", bullet_style))

    # PAGE 3: Storage Strategy & Entity Resolution
    elements.append(PageBreak())
    elements.append(Paragraph("5. Storage Strategy: Polyglot Persistence for Knowledge Graphs", h1_style))
    elements.append(Paragraph(
        "No single database fulfills high-write transactional ingestion, deep multi-hop graph traversals, and semantic vector similarity search. The architecture deploys a polyglot storage layer:",
        body_style
    ))

    storage_table_data = [
        [Paragraph("<b>Storage Layer</b>", code_style), Paragraph("<b>Technology</b>", code_style), Paragraph("<b>Operational Responsibility & Rationale</b>", code_style)],
        [Paragraph("Primary ACID Store", body_style), Paragraph("PostgreSQL 16", body_style), Paragraph("Stores raw & normalized entity tables, enforces JSON Schema validations, manages audit logs, provides transactional consistency.", body_style)],
        [Paragraph("Knowledge Graph", body_style), Paragraph("Neo4j Enterprise", body_style), Paragraph("Models venture & AI graph: (Startup)-[:MAKES]->(Product), (Author)-[:AUTHORED]->(Paper)-[:HAS_REPO]->(GitHub). Enables sub-second multi-hop graph queries.", body_style)],
        [Paragraph("Vector Search", body_style), Paragraph("Qdrant / pgvector", body_style), Paragraph("Indexes embeddings of paper abstracts, startup descriptions, and product value propositions for semantic discovery and deduplication.", body_style)],
        [Paragraph("Cache & Locks", body_style), Paragraph("Redis Cluster", body_style), Paragraph("Distributed locks (Redlock), token bucket rate limiting, and global Bloom filter deduplication.", body_style)]
    ]
    t_storage = Table(storage_table_data, colWidths=[110, 100, 320])
    t_storage.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(Spacer(1, 4))
    elements.append(t_storage)

    elements.append(Spacer(1, 5))
    elements.append(Paragraph("6. Deterministic Entity Resolution Pipeline", h1_style))
    elements.append(Paragraph(
        "The entity resolution engine normalizes noisy scraped organization names (e.g., 'OpenAI Inc', 'Open AI', 'OpenAI OpCo LLC' -> 'OpenAI') through a 4-tier deterministic pipeline:",
        body_style
    ))
    elements.append(Paragraph("1. <b>Exact Alias Indexing</b>: Sub-millisecond dictionary lookup against 50+ canonical seed organizations and known aliases.", bullet_style))
    elements.append(Paragraph("2. <b>Legal Suffix Stripping</b>: Regex-based stripping of designations (Inc, LLC, Ltd, Corp, Technologies, Labs, PBC, GmbH, SAS).", bullet_style))
    elements.append(Paragraph("3. <b>Fuzzy Similarity Matching</b>: RapidFuzz Jaro-Winkler and Token Sort Ratio matching with a strict confidence threshold (score >= 0.88).", bullet_style))
    elements.append(Paragraph("4. <b>Audit Logging</b>: Every single normalization transformation is recorded in the Entity Mapping Log with raw name, canonical name, confidence score, and resolution method.", bullet_style))

    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceAfter=5))
    elements.append(Paragraph("<b>GraphOne / FrontierAtlas Confidential</b> ? Built for Production Scale Intelligence Pipelines", ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=7.5, textColor=colors.HexColor('#64748B'), alignment=1)))

    doc.build(elements)
    print(f"Successfully generated 3-page production architecture PDF at: {filename}")

if __name__ == "__main__":
    create_architecture_pdf()
