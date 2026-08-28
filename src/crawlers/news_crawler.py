import asyncio
import xml.etree.ElementTree as ET
import html
import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from .base_crawler import BaseCrawler
from ..schemas.news import NewsEntity, NewsContent
from ..utils.date_normalizer import DateNormalizer
from ..utils.logger import get_logger
from ..llm.chunker import ContentChunker

logger = get_logger("NewsCrawler")

class NewsCrawler(BaseCrawler):
    """
    Phase II: High-Fidelity Signal Ingestion (News)
    Monitors 5 distinct AI news sources:
    1. TechCrunch AI News (RSS)
    2. VentureBeat AI (RSS)
    3. MIT Technology Review (RSS)
    4. Hacker News AI Stories (Firebase REST API)
    5. ArXiv AI Daily Highlights (RSS)
    
    Guarantees strict 24-hour freshness window and date normalization.
    """
    def __init__(self, concurrency: int = 10):
        super().__init__(concurrency=concurrency, rate_limit_per_sec=10)

    async def crawl_news(self) -> List[NewsEntity]:
        logger.info("Starting High-Fidelity AI News Crawler (24h Freshness Window)...")
        all_news: List[NewsEntity] = []
        collected_at = datetime.now(timezone.utc).isoformat()

        # Source 1: TechCrunch AI Feed
        all_news += await self._crawl_rss_feed(
            url="https://techcrunch.com/category/artificial-intelligence/feed/",
            source_name="TechCrunch AI",
            collected_at=collected_at
        )

        # Source 2: VentureBeat AI Feed
        all_news += await self._crawl_rss_feed(
            url="https://venturebeat.com/category/ai/feed/",
            source_name="VentureBeat AI",
            collected_at=collected_at
        )

        # Source 3: MIT Technology Review AI Feed
        all_news += await self._crawl_rss_feed(
            url="https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            source_name="MIT Technology Review",
            collected_at=collected_at
        )

        # Source 4: ArXiv AI RSS
        all_news += await self._crawl_rss_feed(
            url="https://rss.arxiv.org/rss/cs.AI",
            source_name="ArXiv AI News Feed",
            collected_at=collected_at
        )

        # Source 5: Hacker News Top AI Stories (REST API)
        all_news += await self._crawl_hackernews_ai(collected_at=collected_at)

        logger.info(f"AI News crawling completed. Total 24-hr fresh articles acquired: {len(all_news)}")
        return all_news

    async def _crawl_rss_feed(self, url: str, source_name: str, collected_at: str) -> List[NewsEntity]:
        news_items = []
        try:
            xml_text = await self.fetch_text(url)
            if not xml_text:
                return news_items

            root = ET.fromstring(xml_text)
            items = root.findall('.//item')
            now = datetime.now(timezone.utc)

            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                pub_date_elem = item.find('pubDate')
                desc_elem = item.find('description')

                title = title_elem.text.strip() if title_elem is not None and title_elem.text else "AI Update"
                link = link_elem.text.strip() if link_elem is not None and link_elem.text else url
                raw_date = pub_date_elem.text.strip() if pub_date_elem is not None and pub_date_elem.text else ""
                iso_date = DateNormalizer.parse_to_iso(raw_date)

                # Check 24-hr freshness
                if not DateNormalizer.is_within_24_hours(iso_date):
                    continue

                raw_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                summary = ContentChunker.clean_html(raw_desc)[:500]

                # Extract entities mentioned heuristic
                entities = self._extract_entities_heuristic(f"{title} {summary}")

                news_items.append(NewsEntity(
                    schemaVersion="1.0",
                    recordType="NEWS",
                    content=NewsContent(
                        title=title,
                        url=link,
                        source=source_name,
                        published_date=iso_date,
                        summary=summary,
                        entities_mentioned=entities
                    ),
                    collectedAt=collected_at
                ))
        except Exception as e:
            logger.warning(f"Error fetching/parsing RSS feed {source_name} ({url}): {e}")
        return news_items

    async def _crawl_hackernews_ai(self, collected_at: str) -> List[NewsEntity]:
        hn_items = []
        try:
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            story_ids = await self.fetch_json(top_stories_url)
            if not story_ids or not isinstance(story_ids, list):
                return hn_items

            # Check first 50 top stories for AI keywords
            ai_keywords = ["ai", "llm", "gpt", "claude", "deepseek", "openai", "anthropic", "mistral", "neural", "gpu", "model"]
            now_ts = datetime.now(timezone.utc).timestamp()

            for sid in story_ids[:60]:
                item_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                item = await self.fetch_json(item_url)
                if not item:
                    continue

                title = item.get("title", "")
                title_lower = title.lower()
                
                # Check if matches AI topic
                if any(re.search(r'\b' + re.escape(kw) + r'\b', title_lower) for kw in ai_keywords):
                    time_created = item.get("time", 0)
                    # Must be within 24 hours (86400 seconds)
                    if (now_ts - time_created) > 86400:
                        continue

                    dt = datetime.fromtimestamp(time_created, timezone.utc)
                    iso_date = dt.isoformat()
                    url = item.get("url") or f"https://news.ycombinator.com/item?id={sid}"

                    entities = self._extract_entities_heuristic(title)

                    hn_items.append(NewsEntity(
                        schemaVersion="1.0",
                        recordType="NEWS",
                        content=NewsContent(
                            title=title,
                            url=url,
                            source="Hacker News AI",
                            published_date=iso_date,
                            summary=f"Score: {item.get('score', 0)} points | Comments: {item.get('descendants', 0)}",
                            entities_mentioned=entities
                        ),
                        collectedAt=collected_at
                    ))
        except Exception as e:
            logger.warning(f"Error fetching Hacker News AI items: {e}")
        return hn_items

    def _extract_entities_heuristic(self, text: str) -> List[str]:
        known_keywords = [
            "OpenAI", "Anthropic", "Mistral AI", "Google", "DeepMind", "Meta", "NVIDIA",
            "Microsoft", "Cohere", "Scale AI", "Hugging Face", "Perplexity", "DeepSeek",
            "Groq", "Databricks", "Runway", "ElevenLabs", "Suno", "Cursor", "Apple"
        ]
        found = []
        for kw in known_keywords:
            if re.search(r'\b' + re.escape(kw) + r'\b', text, re.IGNORECASE):
                found.append(kw)
        return found
