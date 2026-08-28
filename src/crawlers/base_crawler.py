import asyncio
import aiohttp
from typing import Optional, Dict, Any
from ..utils.anti_bot import AntiBotManager
from ..utils.logger import get_logger
from ..llm.rate_limiter import AsyncRateLimiter

logger = get_logger("BaseCrawler")

class BaseCrawler:
    def __init__(self, concurrency: int = 15, rate_limit_per_sec: int = 10):
        self.semaphore = asyncio.Semaphore(concurrency)
        self.rate_limiter = AsyncRateLimiter(max_rate=rate_limit_per_sec, time_window=1.0)
        self.session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30.0, connect=10.0)
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch_text(self, url: str, headers: Optional[Dict[str, str]] = None, retries: int = 3) -> Optional[str]:
        session = await self.get_session()
        req_headers = headers or AntiBotManager.get_stealth_headers(url)

        for attempt in range(1, retries + 1):
            try:
                await self.rate_limiter.acquire()
                async with self.semaphore:
                    async with session.get(url, headers=req_headers) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status in [429, 503]:
                            wait_time = attempt * 1.5
                            await asyncio.sleep(wait_time)
                        else:
                            return None
            except Exception as e:
                if attempt == retries:
                    logger.debug(f"Error fetching {url}: {e}")
                await asyncio.sleep(0.5 * attempt)
        return None

    async def fetch_json(self, url: str, headers: Optional[Dict[str, str]] = None, retries: int = 3) -> Optional[Dict[str, Any]]:
        session = await self.get_session()
        req_headers = headers or AntiBotManager.get_api_headers()

        for attempt in range(1, retries + 1):
            try:
                await self.rate_limiter.acquire()
                async with self.semaphore:
                    async with session.get(url, headers=req_headers) as response:
                        if response.status == 200:
                            return await response.json(content_type=None)
                        elif response.status in [429, 503]:
                            await asyncio.sleep(attempt * 1.5)
                        else:
                            return None
            except Exception as e:
                if attempt == retries:
                    logger.debug(f"Error fetching JSON from {url}: {e}")
                await asyncio.sleep(0.5 * attempt)
        return None
