import asyncio
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from .base_crawler import BaseCrawler
from ..schemas.research_paper import ResearchPaperEntity, ResearchPaperContent
from ..utils.date_normalizer import DateNormalizer
from ..utils.logger import get_logger
from ..config import settings

logger = get_logger("ResearchCrawler")

class ResearchPaperCrawler(BaseCrawler):
    """
    Phase I: Massive Research Paper Acquisition
    Acquires AI research papers from Hugging Face Daily Papers API and ArXiv API.
    Correlates papers with GitHub repositories and fetches live GitHub stars.
    """
    def __init__(self, concurrency: int = 20):
        super().__init__(concurrency=concurrency, rate_limit_per_sec=15)
        self.github_token = settings.GITHUB_TOKEN
        self.github_cache: Dict[str, Optional[int]] = {}

    async def crawl_papers(self, target_count: int = 1000) -> List[ResearchPaperEntity]:
        logger.info(f"Starting Research Paper Crawler. Target: {target_count} papers.")
        papers: List[ResearchPaperEntity] = []
        seen_urls = set()

        # Step 1: Hugging Face Daily Papers API (High-velocity AI Papers with ArXiv links & GitHub correlations)
        logger.info("Fetching high-quality AI papers from Hugging Face Daily Papers API...")
        hf_papers_url = "https://huggingface.co/api/daily_papers?limit=500"
        hf_data = await self.fetch_json(hf_papers_url)
        
        if hf_data and isinstance(hf_data, list):
            for item in hf_data:
                paper_obj = item.get("paper", {}) or {}
                arxiv_id = paper_obj.get("id") or item.get("id")
                if not arxiv_id:
                    continue
                paper_url = f"https://arxiv.org/abs/{arxiv_id}"
                if paper_url in seen_urls:
                    continue
                seen_urls.add(paper_url)

                title = paper_obj.get("title") or item.get("title") or "AI Research Paper"
                authors_raw = paper_obj.get("authors") or []
                authors = [a.get("name", "Researcher") if isinstance(a, dict) else str(a) for a in authors_raw]
                if not authors:
                    authors = ["AI Researcher"]

                pub_date = DateNormalizer.parse_to_iso(paper_obj.get("publishedAt") or item.get("publishedAt"))

                # Check for github repo in summary or external links
                github_url = None
                summary = paper_obj.get("summary", "")
                gh_match = re.search(r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)', summary)
                if gh_match:
                    repo_path = gh_match.group(1).rstrip('.')
                    github_url = f"https://github.com/{repo_path}"

                github_stars = None
                if github_url:
                    github_stars = await self._fetch_github_stars(github_url)

                papers.append(ResearchPaperEntity(
                    schemaVersion="1.0",
                    recordType="RESEARCH_PAPER",
                    content=ResearchPaperContent(
                        title=title,
                        authors=authors,
                        paper_url=paper_url,
                        github_url=github_url,
                        github_stars=github_stars,
                        published_date=pub_date
                    )
                ))
                if len(papers) >= target_count:
                    break

        logger.info(f"Acquired {len(papers)} papers from Hugging Face Daily Papers.")

        # Step 2: Query ArXiv API across AI categories
        batch_size = 150
        categories = ["cs.AI", "cs.LG", "cs.CL", "cs.CV", "stat.ML", "cs.RO", "cs.NE"]
        cat_idx = 0
        start = 0

        while len(papers) < target_count and cat_idx < len(categories):
            cat = categories[cat_idx]
            arxiv_url = f"http://export.arxiv.org/api/query?search_query=cat:{cat}&start={start}&max_results={batch_size}&sortBy=submittedDate&sortOrder=descending"
            
            logger.info(f"Fetching ArXiv category: {cat}, start={start}, max={batch_size}...")
            xml_text = await self.fetch_text(arxiv_url)
            if not xml_text:
                cat_idx += 1
                start = 0
                await asyncio.sleep(1.0)
                continue

            extracted = self._parse_arxiv_feed(xml_text)
            if not extracted:
                cat_idx += 1
                start = 0
                continue

            for item in extracted:
                if item["paper_url"] in seen_urls:
                    continue
                seen_urls.add(item["paper_url"])

                github_url = item.get("github_url")
                github_stars = None
                if github_url:
                    github_stars = await self._fetch_github_stars(github_url)

                papers.append(ResearchPaperEntity(
                    schemaVersion="1.0",
                    recordType="RESEARCH_PAPER",
                    content=ResearchPaperContent(
                        title=item["title"],
                        authors=item["authors"],
                        paper_url=item["paper_url"],
                        github_url=github_url,
                        github_stars=github_stars,
                        published_date=item["published_date"]
                    )
                ))
                if len(papers) >= target_count:
                    break

            logger.info(f"Acquired {len(papers)} / {target_count} research papers so far.")
            start += batch_size
            if start >= 600:
                cat_idx += 1
                start = 0
            await asyncio.sleep(0.8)

        logger.info(f"Research Paper acquisition complete. Total collected: {len(papers)}")
        return papers[:target_count]

    def _parse_arxiv_feed(self, xml_text: str) -> List[Dict[str, Any]]:
        results = []
        try:
            root = ET.fromstring(xml_text)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
            
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                title = title_elem.text.strip().replace('\n', ' ') if title_elem is not None else "Untitled"
                title = re.sub(r'\s+', ' ', title)

                summary_elem = entry.find('atom:summary', ns)
                summary = summary_elem.text if summary_elem is not None else ""

                published_elem = entry.find('atom:published', ns)
                raw_pub = published_elem.text if published_elem is not None else ""
                published_date = DateNormalizer.parse_to_iso(raw_pub)

                id_elem = entry.find('atom:id', ns)
                paper_url = id_elem.text.strip() if id_elem is not None else ""

                authors = []
                for author in entry.findall('atom:author', ns):
                    name_elem = author.find('atom:name', ns)
                    if name_elem is not None and name_elem.text:
                        authors.append(name_elem.text.strip())

                github_url = None
                gh_match = re.search(r'https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+)', summary)
                if gh_match:
                    repo_path = gh_match.group(1).rstrip('.')
                    github_url = f"https://github.com/{repo_path}"

                results.append({
                    "title": title,
                    "authors": authors if authors else ["ArXiv Contributor"],
                    "paper_url": paper_url,
                    "github_url": github_url,
                    "published_date": published_date
                })
        except Exception as e:
            logger.error(f"Error parsing ArXiv XML: {e}")
        return results

    async def _fetch_github_stars(self, github_url: str) -> Optional[int]:
        match = re.search(r'github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', github_url)
        if not match:
            return None
        owner, repo = match.group(1), match.group(2).rstrip('.git')
        repo_key = f"{owner}/{repo}".lower()

        if repo_key in self.github_cache:
            return self.github_cache[repo_key]

        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GraphOne-Intelligence-Crawler/1.0"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        data = await self.fetch_json(api_url, headers=headers)
        if data and "stargazers_count" in data:
            stars = int(data["stargazers_count"])
            self.github_cache[repo_key] = stars
            return stars
        
        self.github_cache[repo_key] = None
        return None
