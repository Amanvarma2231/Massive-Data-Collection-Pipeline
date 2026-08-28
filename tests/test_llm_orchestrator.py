import pytest
import asyncio
from src.llm.chunker import ContentChunker
from src.llm.orchestrator import MultiTierLLMOrchestrator
from src.llm.rate_limiter import execute_with_backoff

def test_content_chunker_html_clean():
    html_raw = "<html><head><script>alert('x')</script><style>.a{}</style></head><body><h1>Title</h1><p>Text here.</p></body></html>"
    cleaned = ContentChunker.clean_html(html_raw)
    assert "alert" not in cleaned
    assert "Title Text here." in cleaned

def test_payload_truncation():
    long_text = "A" * 20000
    truncated = ContentChunker.truncate_payload(long_text, max_chars=8000)
    assert len(truncated) < 10000
    assert "[... Content condensed" in truncated

@pytest.mark.asyncio
async def test_deterministic_llm_fallback():
    orchestrator = MultiTierLLMOrchestrator()
    sample_text = "Anthropic is an AI safety startup with 500 employees offering Claude on an enterprise pricing tier with remote work."
    
    res = await orchestrator.extract_structured_json(
        raw_content=sample_text,
        schema_description="Extract entityName, employeeCount, pricingModel, is_remote",
        fallback_defaults={"entityName": "Anthropic", "employeeCount": None, "pricingModel": "FREEMIUM", "is_remote": False}
    )
    assert res["employeeCount"] == 500
    assert res["pricingModel"] == "ENTERPRISE"
    assert res["is_remote"] is True
