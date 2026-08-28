import asyncio
import argparse
import sys
import time
from datetime import datetime, timezone
from typing import Dict, Any

from .config import settings
from .utils.logger import get_logger
from .entity_resolution.resolver import EntityResolver
from .crawlers.research_crawler import ResearchPaperCrawler
from .crawlers.startup_crawler import StartupCrawler
from .crawlers.product_crawler import ProductCrawler
from .crawlers.news_crawler import NewsCrawler
from .crawlers.jobs_crawler import JobsCrawler
from .storage.database import DatabaseManager
from .storage.exporter import DataExporter

logger = get_logger("PipelineOrchestrator")

class GlobalIntelligencePipeline:
    """
    Master Orchestrator for GraphOne / FrontierAtlas Intelligence Graph Ingestion.
    Coordinates Phase I (Massive Acquisition), Phase II (Signal Ingestion),
    Phase III (LLM Fallbacks), Phase IV (Entity Resolution), and Phase VI Storage/Export.
    """
    def __init__(self, target_count: int = 1000):
        self.target_count = target_count
        self.resolver = EntityResolver()
        self.db = DatabaseManager()
        self.exporter = DataExporter()

    async def run_pipeline(
        self,
        crawl_startups: bool = True,
        crawl_products: bool = True,
        crawl_papers: bool = True,
        crawl_signals: bool = True
    ) -> Dict[str, Any]:
        start_time = time.time()
        logger.info("================================================================================")
        logger.info("  STARTING GRAPHONE / FRONTIERATLAS GLOBAL INTELLIGENCE INGESTION PIPELINE")
        logger.info(f"  Target Quota per Vertical: {self.target_count} records")
        logger.info(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
        logger.info("================================================================================")

        results = {
            "startups": [],
            "products": [],
            "research_papers": [],
            "jobs": [],
            "news": [],
            "mapping_logs": []
        }

        # ----------------------------------------------------------------------
        # Phase I: Massive One-Time Data Acquisition
        # ----------------------------------------------------------------------
        startup_crawler = StartupCrawler(concurrency=settings.MAX_CONCURRENT_REQUESTS, resolver=self.resolver)
        product_crawler = ProductCrawler(concurrency=settings.MAX_CONCURRENT_REQUESTS, resolver=self.resolver)
        paper_crawler = ResearchPaperCrawler(concurrency=settings.MAX_CONCURRENT_REQUESTS)

        async def run_phase_1():
            tasks = []
            if crawl_startups:
                tasks.append(startup_crawler.crawl_startups(target_count=self.target_count))
            else:
                tasks.append(asyncio.sleep(0, result=[]))

            if crawl_products:
                tasks.append(product_crawler.crawl_products(target_count=self.target_count))
            else:
                tasks.append(asyncio.sleep(0, result=[]))

            if crawl_papers:
                tasks.append(paper_crawler.crawl_papers(target_count=self.target_count))
            else:
                tasks.append(asyncio.sleep(0, result=[]))

            return await asyncio.gather(*tasks)

        s_list, p_list, r_list = await run_phase_1()
        results["startups"] = s_list
        results["products"] = p_list
        results["research_papers"] = r_list

        await startup_crawler.close()
        await product_crawler.close()
        await paper_crawler.close()

        # ----------------------------------------------------------------------
        # Phase II: High-Fidelity Signal Ingestion (24h Freshness)
        # ----------------------------------------------------------------------
        if crawl_signals:
            news_crawler = NewsCrawler(concurrency=10)
            jobs_crawler = JobsCrawler(concurrency=10, resolver=self.resolver)

            news_list, jobs_list = await asyncio.gather(
                news_crawler.crawl_news(),
                jobs_crawler.crawl_jobs()
            )
            results["news"] = news_list
            results["jobs"] = jobs_list

            await news_crawler.close()
            await jobs_crawler.close()

        # ----------------------------------------------------------------------
        # Phase IV: Entity Resolution Logs
        # ----------------------------------------------------------------------
        results["mapping_logs"] = self.resolver.get_mapping_logs()

        # ----------------------------------------------------------------------
        # Phase VI: Real-time Persistence & Multi-Tab Export
        # ----------------------------------------------------------------------
        logger.info("Persisting entities to database...")
        self.db.save_startups(results["startups"])
        self.db.save_products(results["products"])
        self.db.save_research_papers(results["research_papers"])
        self.db.save_jobs(results["jobs"])
        self.db.save_news(results["news"])
        self.db.save_entity_mappings(results["mapping_logs"])

        logger.info("Exporting 6-tab spreadsheet and CSV deliverables...")
        export_paths = self.exporter.export_all(
            startups=results["startups"],
            products=results["products"],
            papers=results["research_papers"],
            jobs=results["jobs"],
            news=results["news"],
            mapping_logs=results["mapping_logs"]
        )

        elapsed = time.time() - start_time
        logger.info("================================================================================")
        logger.info("  PIPELINE EXECUTION SUMMARY")
        logger.info(f"  - Startups Acquired:        {len(results['startups'])}")
        logger.info(f"  - Products Acquired:        {len(results['products'])}")
        logger.info(f"  - Research Papers Acquired: {len(results['research_papers'])}")
        logger.info(f"  - 24h News Signals:         {len(results['news'])}")
        logger.info(f"  - 24h Job Signals:          {len(results['jobs'])}")
        logger.info(f"  - Entity Mappings Logged:   {len(results['mapping_logs'])}")
        logger.info(f"  - Excel Dataset:            {export_paths['excel']}")
        logger.info(f"  - Elapsed Time:             {elapsed:.2f} seconds")
        logger.info("================================================================================")
        return results

def main():
    parser = argparse.ArgumentParser(description="GraphOne / FrontierAtlas Intelligence Pipeline CLI")
    parser.add_argument("--all", action="store_true", help="Run full pipeline across all 6 phases")
    parser.add_argument("--target-count", type=int, default=1000, help="Target count for Startups, Products, Papers (Default: 1000)")
    parser.add_argument("--only-papers", action="store_true", help="Run only Research Paper crawler")
    parser.add_argument("--only-startups", action="store_true", help="Run only Startup crawler")
    parser.add_argument("--only-products", action="store_true", help="Run only Product crawler")
    parser.add_argument("--only-signals", action="store_true", help="Run only News & Job Signals (24h)")
    args = parser.parse_args()

    pipeline = GlobalIntelligencePipeline(target_count=args.target_count)

    if args.only_papers:
        asyncio.run(pipeline.run_pipeline(crawl_startups=False, crawl_products=False, crawl_papers=True, crawl_signals=False))
    elif args.only_startups:
        asyncio.run(pipeline.run_pipeline(crawl_startups=True, crawl_products=False, crawl_papers=False, crawl_signals=False))
    elif args.only_products:
        asyncio.run(pipeline.run_pipeline(crawl_startups=False, crawl_products=True, crawl_papers=False, crawl_signals=False))
    elif args.only_signals:
        asyncio.run(pipeline.run_pipeline(crawl_startups=False, crawl_products=False, crawl_papers=False, crawl_signals=True))
    else:
        asyncio.run(pipeline.run_pipeline(crawl_startups=True, crawl_products=True, crawl_papers=True, crawl_signals=True))

if __name__ == "__main__":
    main()
