import asyncio
import random
import time
from typing import Callable, Any
from ..utils.logger import get_logger

logger = get_logger("RateLimiter")

class AsyncRateLimiter:
    def __init__(self, max_rate: int = 10, time_window: float = 1.0):
        """Token bucket rate limiter."""
        self.max_rate = max_rate
        self.time_window = time_window
        self.tokens = max_rate
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.tokens = min(self.max_rate, self.tokens + elapsed * (self.max_rate / self.time_window))
                self.last_update = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                # Sleep till next token
                wait_time = (1.0 - self.tokens) * (self.time_window / self.max_rate)
                await asyncio.sleep(max(0.01, wait_time))

async def execute_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 30.0
) -> Any:
    """Execute an async callable with exponential backoff and randomized full jitter for 429 & 5xx errors."""
    attempt = 0
    while True:
        try:
            return await func()
        except Exception as e:
            attempt += 1
            err_str = str(e).lower()
            is_rate_limit = "429" in err_str or "rate" in err_str or "quota" in err_str or "too many requests" in err_str
            
            if attempt > max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for operation. Error: {e}")
                raise e

            # Full Jitter backoff: random_between(0, min(max_delay, base_delay * 2 ** attempt))
            calculated_delay = min(max_delay, base_delay * (2 ** attempt))
            jittered_delay = random.uniform(calculated_delay * 0.5, calculated_delay * 1.5)

            if is_rate_limit:
                logger.warning(f"Rate limit encountered (429). Retrying in {jittered_delay:.2f}s (Attempt {attempt}/{max_retries})...")
            else:
                logger.warning(f"Transient error encountered: {e}. Retrying in {jittered_delay:.2f}s (Attempt {attempt}/{max_retries})...")

            await asyncio.sleep(jittered_delay)
