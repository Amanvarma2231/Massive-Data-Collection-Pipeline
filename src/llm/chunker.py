import re
from bs4 import BeautifulSoup
from typing import List

class ContentChunker:
    @staticmethod
    def clean_html(raw_html: str) -> str:
        """Strip HTML tags, scripts, styles, extra whitespaces using BeautifulSoup."""
        if not raw_html:
            return ""
        try:
            soup = BeautifulSoup(raw_html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
                tag.decompose()
            text = soup.get_text(separator=" ")
            text = re.sub(r'\s+', ' ', text).strip()
            return text
        except Exception:
            cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', ' ', raw_html, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
            return re.sub(r'\s+', ' ', cleaned).strip()

    @staticmethod
    def truncate_payload(text: str, max_chars: int = 12000) -> str:
        """Prevent 413 Payload Too Large by truncating while preserving dense semantic head and tail."""
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_chars:
            return text

        head_len = int(max_chars * 0.70)
        tail_len = int(max_chars * 0.30)
        return text[:head_len] + "\n\n[... Content condensed for LLM context budget ...]\n\n" + text[-tail_len:]

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 4000, overlap: int = 200) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            if end == len(text):
                break
            start += (chunk_size - overlap)
        return chunks
