import os
import asyncio
from pathlib import Path
import pandas as pd
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from .config import settings
from .pipeline import GlobalIntelligencePipeline

app = FastAPI(
    title="GraphOne / FrontierAtlas Intelligence Pipeline API",
    description="Global AI Intelligence Data Ingestion, Entity Resolution, and Signal Extraction Engine.",
    version="1.0.0"
)

pipeline_running = False

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "GraphOne-Intelligence-Pipeline", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse)
def index():
    out_dir = settings.OUTPUT_DIR
    counts = {}
    csvs = {
        "startups": out_dir / "startups.csv",
        "products": out_dir / "products.csv",
        "research_papers": out_dir / "research_papers.csv",
        "jobs": out_dir / "jobs.csv",
        "news": out_dir / "news.csv",
        "entity_mapping_log": out_dir / "entity_mapping_log.csv",
    }
    for k, p in csvs.items():
        if p.exists():
            try:
                df = pd.read_csv(p)
                counts[k] = len(df)
            except Exception:
                counts[k] = "Available"
        else:
            counts[k] = 0

    excel_exists = (out_dir / "intelligence_graph_dataset.xlsx").exists()
    pdf_exists = (settings.BASE_DIR / "architecture.pdf").exists()

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>GraphOne / FrontierAtlas Intelligence Pipeline</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .card {{ background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 20px; }}
            .stat-number {{ font-size: 2.2rem; font-weight: 700; color: #38bdf8; }}
            .badge-custom {{ background-color: #0284c7; color: white; padding: 6px 12px; border-radius: 20px; font-size: 0.85rem; }}
            .btn-action {{ background: linear-gradient(135deg, #0284c7, #2563eb); border: none; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 600; text-decoration: none; display: inline-block; }}
            .btn-action:hover {{ background: linear-gradient(135deg, #0369a1, #1d4ed8); color: white; }}
            .hero {{ padding: 40px 0 20px 0; border-bottom: 1px solid #334155; margin-bottom: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero text-center">
                <span class="badge-custom">GraphOne / FrontierAtlas Global Pipeline</span>
                <h1 class="mt-3 fw-bold">AI Intelligence Graph Ingestion Engine</h1>
                <p class="text-secondary mt-2">Production-grade distributed crawler, multi-tier LLM extractor, deterministic entity resolver, and polyglot persistence.</p>
            </div>

            <div class="row g-4 mb-4">
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">AI Startups</div>
                        <div class="stat-number mt-2">{counts.get('startups', 0):,}</div>
                        <div class="text-secondary small mt-1">Verified Organizations</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">AI Products</div>
                        <div class="stat-number mt-2">{counts.get('products', 0):,}</div>
                        <div class="text-secondary small mt-1">Classified by Pricing Tier</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">Research Papers</div>
                        <div class="stat-number mt-2">{counts.get('research_papers', 0):,}</div>
                        <div class="text-secondary small mt-1">With Live GitHub Stars</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">24h Fresh News</div>
                        <div class="stat-number mt-2">{counts.get('news', 0):,}</div>
                        <div class="text-secondary small mt-1">5 AI News Feeds</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">24h Fresh Jobs</div>
                        <div class="stat-number mt-2">{counts.get('jobs', 0):,}</div>
                        <div class="text-secondary small mt-1">5 AI Job Boards</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card p-4 text-center">
                        <div class="text-secondary text-uppercase fw-semibold" style="font-size: 0.85rem;">Entity Mappings</div>
                        <div class="stat-number mt-2">{counts.get('entity_mapping_log', 0):,}</div>
                        <div class="text-secondary small mt-1">Audit Trail Transformations</div>
                    </div>
                </div>
            </div>

            <div class="card p-4">
                <h4 class="fw-bold mb-3">Deliverables & Downloads</h4>
                <div class="d-flex flex-wrap gap-3">
                    <a href="/api/download/excel" class="btn-action">?? Download 6-Tab Excel Dataset (.xlsx)</a>
                    <a href="/api/download/architecture-pdf" class="btn btn-outline-info px-3 py-2 fw-semibold">?? Architecture PDF (Phase VI)</a>
                    <a href="/docs" class="btn btn-outline-secondary px-3 py-2 fw-semibold">? Interactive API Documentation (Swagger)</a>
                </div>
            </div>
            
            <div class="card p-4 mt-3">
                <h5 class="fw-bold">JSON API Endpoints</h5>
                <ul class="list-unstyled mb-0">
                    <li class="mb-2"><code>GET /api/startups</code> ? View startups payload</li>
                    <li class="mb-2"><code>GET /api/products</code> ? View products payload</li>
                    <li class="mb-2"><code>GET /api/papers</code> ? View research papers with GitHub metrics</li>
                    <li class="mb-2"><code>GET /api/jobs</code> ? View 24h fresh jobs</li>
                    <li class="mb-2"><code>GET /api/news</code> ? View 24h fresh news signals</li>
                    <li class="mb-0"><code>POST /api/pipeline/run</code> ? Trigger asynchronous crawler run</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return html_content

@app.get("/api/startups")
def get_startups(limit: int = 100):
    p = settings.OUTPUT_DIR / "startups.csv"
    if p.exists():
        df = pd.read_csv(p)
        return df.head(limit).to_dict(orient="records")
    return []

@app.get("/api/products")
def get_products(limit: int = 100):
    p = settings.OUTPUT_DIR / "products.csv"
    if p.exists():
        df = pd.read_csv(p)
        return df.head(limit).to_dict(orient="records")
    return []

@app.get("/api/papers")
def get_papers(limit: int = 100):
    p = settings.OUTPUT_DIR / "research_papers.csv"
    if p.exists():
        df = pd.read_csv(p)
        return df.head(limit).to_dict(orient="records")
    return []

@app.get("/api/jobs")
def get_jobs(limit: int = 100):
    p = settings.OUTPUT_DIR / "jobs.csv"
    if p.exists():
        df = pd.read_csv(p)
        return df.head(limit).to_dict(orient="records")
    return []

@app.get("/api/news")
def get_news(limit: int = 100):
    p = settings.OUTPUT_DIR / "news.csv"
    if p.exists():
        df = pd.read_csv(p)
        return df.head(limit).to_dict(orient="records")
    return []

@app.get("/api/download/excel")
def download_excel():
    excel_path = settings.OUTPUT_DIR / "intelligence_graph_dataset.xlsx"
    if excel_path.exists():
        return FileResponse(
            path=excel_path,
            filename="intelligence_graph_dataset.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    raise HTTPException(status_code=404, detail="Excel dataset not yet generated.")

@app.get("/api/download/architecture-pdf")
def download_pdf():
    pdf_path = settings.BASE_DIR / "architecture.pdf"
    if pdf_path.exists():
        return FileResponse(
            path=pdf_path,
            filename="architecture.pdf",
            media_type="application/pdf"
        )
    raise HTTPException(status_code=404, detail="Architecture PDF not found.")

async def _run_pipeline_bg(target_count: int):
    global pipeline_running
    pipeline_running = True
    try:
        pipeline = GlobalIntelligencePipeline(target_count=target_count)
        await pipeline.run_pipeline()
    finally:
        pipeline_running = False

@app.post("/api/pipeline/run")
def trigger_pipeline(background_tasks: BackgroundTasks, target_count: int = 1000):
    global pipeline_running
    if pipeline_running:
        return {"status": "already_running", "message": "Pipeline execution is currently in progress."}
    background_tasks.add_task(_run_pipeline_bg, target_count)
    return {"status": "started", "message": f"Pipeline launched asynchronously with target quota {target_count}."}
