import os
import json
import re
import httpx
from typing import Dict, Any, Optional
from ..config import settings
from .chunker import ContentChunker
from .rate_limiter import execute_with_backoff
from ..utils.logger import get_logger

logger = get_logger("LLMOrchestrator")

class MultiTierLLMOrchestrator:
    """
    Phase III: Multi-Tier LLM Extraction Engine
    Fallback Chain: Tier 1 (Gemini Flash) -> Tier 2 (Groq Llama 3) -> Tier 3 (DeepSeek) -> Tier 4 (Deterministic Rule Parser)
    Handles 413 Payload Too Large (via ContentChunker) and 429 Rate Limits (via backoff).
    """
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
        self.groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY")
        self.deepseek_key = settings.DEEPSEEK_API_KEY or os.getenv("DEEPSEEK_API_KEY")

    async def extract_structured_json(self, raw_content: str, schema_description: str, fallback_defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured JSON according to schema through the fallback chain."""
        # 1. Truncate payload to protect against 413 errors
        clean_text = ContentChunker.clean_html(raw_content)
        truncated_text = ContentChunker.truncate_payload(clean_text, max_chars=10000)

        prompt = f"""You are an expert AI data extraction engine.
Given the following raw text content, extract and format the data strictly into valid JSON matching this schema:
{schema_description}

Rules:
1. Return ONLY valid JSON, enclosed in a ```json codeblock.
2. Do not invent or hallucinate data not supported in the text.
3. If an optional field is missing, use null or appropriate default.

Raw Content:
{truncated_text}
"""

        # Tier 1: Gemini Flash
        if self.gemini_key:
            try:
                res = await execute_with_backoff(lambda: self._call_gemini_flash(prompt))
                parsed = self._parse_json_response(res)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Tier 1 (Gemini Flash) failed: {e}. Falling back to Tier 2...")

        # Tier 2: Groq (Llama 3)
        if self.groq_key:
            try:
                res = await execute_with_backoff(lambda: self._call_groq_llama(prompt))
                parsed = self._parse_json_response(res)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Tier 2 (Groq Llama 3) failed: {e}. Falling back to Tier 3...")

        # Tier 3: DeepSeek
        if self.deepseek_key:
            try:
                res = await execute_with_backoff(lambda: self._call_deepseek(prompt))
                parsed = self._parse_json_response(res)
                if parsed:
                    return parsed
            except Exception as e:
                logger.warning(f"Tier 3 (DeepSeek) failed: {e}. Falling back to Tier 4...")

        # Tier 4: Deterministic NLP/Rule-based Fallback Parser
        logger.info("Executing Tier 4 deterministic heuristic extraction fallback.")
        return self._deterministic_extract(clean_text, fallback_defaults)

    async def _call_gemini_flash(self, prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048}
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Gemini API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _call_groq_llama(self, prompt: str) -> str:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"Groq API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _call_deepseek(self, prompt: str) -> str:
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.deepseek_key}", "Content-Type": "application/json"}
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code != 200:
                raise Exception(f"DeepSeek API returned status {resp.status_code}: {resp.text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            # Check for ```json block
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
            # Check for naked JSON
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except Exception:
            pass
        return None

    def _deterministic_extract(self, text: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic regex & heuristic extractor guaranteeing valid output without hallucination."""
        result = dict(defaults)
        
        # Heuristic for employee count
        emp_match = re.search(r'(\d+[\d,]*)\s*(?:\+|plus)?\s*(?:employees|team members|staff|people)', text, re.IGNORECASE)
        if emp_match:
            try:
                result["employeeCount"] = int(emp_match.group(1).replace(",", ""))
            except Exception:
                pass

        # Heuristic for pricing model
        text_lower = text.lower()
        if "enterprise" in text_lower or "contact sales" in text_lower or "custom pricing" in text_lower:
            result["pricingModel"] = "ENTERPRISE"
        elif "freemium" in text_lower or "free tier" in text_lower or "free plan" in text_lower:
            result["pricingModel"] = "FREEMIUM"
        elif "free" in text_lower or "open source" in text_lower or "apache 2.0" in text_lower or "mit license" in text_lower:
            result["pricingModel"] = "FREE"
        elif "paid" in text_lower or "$/mo" in text_lower or "pricing" in text_lower or "subscription" in text_lower:
            result["pricingModel"] = "PAID"

        # Remote boolean heuristic
        if "remote" in text_lower or "anywhere" in text_lower or "distributed" in text_lower or "work from home" in text_lower:
            result["is_remote"] = True

        return result
