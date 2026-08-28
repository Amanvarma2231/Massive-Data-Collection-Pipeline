import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from ..config import settings
from ..schemas import (
    StartupEntity, ProductEntity, ResearchPaperEntity, JobEntity, NewsEntity, EntityMappingRecord
)
from ..utils.logger import get_logger

logger = get_logger("DataExporter")

class DataExporter:
    """
    Generates Deliverables:
    1. Multi-Tab Excel Workbook (`intelligence_graph_dataset.xlsx`) with 6 required sheets:
       - Startups
       - Products
       - Research Papers
       - Jobs
       - News
       - Entity Mapping Log
    2. Individual CSV files in `data/output/` for direct Google Sheets / BigQuery import.
    """
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or settings.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_all(
        self,
        startups: List[StartupEntity],
        products: List[ProductEntity],
        papers: List[ResearchPaperEntity],
        jobs: List[JobEntity],
        news: List[NewsEntity],
        mapping_logs: List[EntityMappingRecord]
    ) -> Dict[str, str]:
        logger.info("Exporting all pipeline entities to 6-tab Excel and CSV files...")

        # 1. Prepare DataFrames conforming strictly to Expected Schemas
        df_startups = pd.DataFrame([
            {
                "schemaVersion": s.schemaVersion,
                "recordType": s.recordType,
                "source.name": s.source.name,
                "source.url": s.source.url,
                "content.entityName": s.content.entityName,
                "content.data.employeeCount": s.content.data.employeeCount,
                "collectedAt": s.collectedAt
            } for s in startups
        ])

        df_products = pd.DataFrame([
            {
                "schemaVersion": p.schemaVersion,
                "recordType": p.recordType,
                "source.name": p.source.name,
                "source.url": p.source.url,
                "content.startupName": p.content.startupName,
                "content.pricingModel": p.content.pricingModel.value,
                "collectedAt": p.collectedAt
            } for p in products
        ])

        df_papers = pd.DataFrame([
            {
                "schemaVersion": r.schemaVersion,
                "recordType": r.recordType,
                "content.title": r.content.title,
                "content.authors": ", ".join(r.content.authors) if isinstance(r.content.authors, list) else str(r.content.authors),
                "content.paper_url": r.content.paper_url,
                "content.github_url": r.content.github_url or "",
                "content.github_stars": r.content.github_stars if r.content.github_stars is not None else "",
                "content.published_date": r.content.published_date
            } for r in papers
        ])

        df_jobs = pd.DataFrame([
            {
                "schemaVersion": j.schemaVersion,
                "recordType": j.recordType,
                "content.company": j.content.company,
                "content.date": j.content.date,
                "content.is_remote": j.content.is_remote,
                "content.role_family": j.content.role_family
            } for j in jobs
        ])

        df_news = pd.DataFrame([
            {
                "schemaVersion": n.schemaVersion,
                "recordType": n.recordType,
                "content.title": n.content.title,
                "content.url": n.content.url,
                "content.source": n.content.source,
                "content.published_date": n.content.published_date,
                "content.summary": n.content.summary,
                "content.entities_mentioned": ", ".join(n.content.entities_mentioned),
                "collectedAt": n.collectedAt
            } for n in news
        ])

        df_mappings = pd.DataFrame([
            {
                "raw_name": m.raw_name,
                "canonical_name": m.canonical_name,
                "confidence_score": m.confidence_score,
                "method": m.method,
                "entity_type": m.entity_type,
                "timestamp": m.timestamp
            } for m in mapping_logs
        ])

        # 2. Write Multi-Tab Excel Workbook
        excel_path = self.output_dir / "intelligence_graph_dataset.xlsx"
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df_startups.to_excel(writer, sheet_name="Startups", index=False)
            df_products.to_excel(writer, sheet_name="Products", index=False)
            df_papers.to_excel(writer, sheet_name="Research Papers", index=False)
            df_jobs.to_excel(writer, sheet_name="Jobs", index=False)
            df_news.to_excel(writer, sheet_name="News", index=False)
            df_mappings.to_excel(writer, sheet_name="Entity Mapping Log", index=False)
        logger.info(f"Generated 6-tab Excel dataset at: {excel_path}")

        # 3. Write Individual CSV files
        csv_files = {
            "startups": self.output_dir / "startups.csv",
            "products": self.output_dir / "products.csv",
            "research_papers": self.output_dir / "research_papers.csv",
            "jobs": self.output_dir / "jobs.csv",
            "news": self.output_dir / "news.csv",
            "entity_mapping_log": self.output_dir / "entity_mapping_log.csv"
        }

        df_startups.to_csv(csv_files["startups"], index=False, encoding="utf-8")
        df_products.to_csv(csv_files["products"], index=False, encoding="utf-8")
        df_papers.to_csv(csv_files["research_papers"], index=False, encoding="utf-8")
        df_jobs.to_csv(csv_files["jobs"], index=False, encoding="utf-8")
        df_news.to_csv(csv_files["news"], index=False, encoding="utf-8")
        df_mappings.to_csv(csv_files["entity_mapping_log"], index=False, encoding="utf-8")

        logger.info(f"All 6 CSV files successfully generated in {self.output_dir}")
        return {
            "excel": str(excel_path),
            **{k: str(v) for k, v in csv_files.items()}
        }
