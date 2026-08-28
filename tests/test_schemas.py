import pytest
from src.schemas import (
    StartupEntity, StartupContent, StartupContentData, SourceInfo,
    ProductEntity, ProductContent, PricingModelEnum,
    ResearchPaperEntity, ResearchPaperContent,
    JobEntity, JobContent,
    NewsEntity, NewsContent,
    EntityMappingRecord
)

def test_startup_schema():
    entity = StartupEntity(
        schemaVersion="1.0",
        recordType="STARTUP",
        source=SourceInfo(name="Test Source", url="https://example.com"),
        content=StartupContent(
            entityName="OpenAI",
            data=StartupContentData(employeeCount=1200)
        ),
        collectedAt="2026-08-29T00:00:00Z"
    )
    assert entity.schemaVersion == "1.0"
    assert entity.recordType == "STARTUP"
    assert entity.content.entityName == "OpenAI"
    assert entity.content.data.employeeCount == 1200

def test_product_schema():
    entity = ProductEntity(
        schemaVersion="1.0",
        recordType="PRODUCT",
        source=SourceInfo(name="Test Source", url="https://example.com"),
        content=ProductContent(
            startupName="Anthropic",
            pricingModel=PricingModelEnum.FREEMIUM
        ),
        collectedAt="2026-08-29T00:00:00Z"
    )
    assert entity.recordType == "PRODUCT"
    assert entity.content.pricingModel == PricingModelEnum.FREEMIUM

def test_research_paper_schema():
    entity = ResearchPaperEntity(
        schemaVersion="1.0",
        recordType="RESEARCH_PAPER",
        content=ResearchPaperContent(
            title="Attention Is All You Need",
            authors=["Vaswani", "Shazeer"],
            paper_url="https://arxiv.org/abs/1706.03762",
            github_url="https://github.com/tensorflow/tensor2tensor",
            github_stars=32000,
            published_date="2017-06-12T00:00:00Z"
        )
    )
    assert entity.recordType == "RESEARCH_PAPER"
    assert entity.content.github_stars == 32000

def test_job_schema():
    entity = JobEntity(
        schemaVersion="1.0",
        recordType="JOB",
        content=JobContent(
            company="Mistral AI",
            date="2026-08-29T00:00:00Z",
            is_remote=True,
            role_family="Engineering"
        )
    )
    assert entity.recordType == "JOB"
    assert entity.content.is_remote is True

def test_news_schema():
    entity = NewsEntity(
        schemaVersion="1.0",
        recordType="NEWS",
        content=NewsContent(
            title="New Breakthrough in LLM Reasoning",
            url="https://techcrunch.com/news/1",
            source="TechCrunch",
            published_date="2026-08-29T00:00:00Z",
            summary="Exciting new model architecture",
            entities_mentioned=["OpenAI", "DeepSeek"]
        ),
        collectedAt="2026-08-29T00:00:00Z"
    )
    assert entity.recordType == "NEWS"
    assert "OpenAI" in entity.content.entities_mentioned
