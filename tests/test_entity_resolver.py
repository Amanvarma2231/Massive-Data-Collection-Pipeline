import pytest
from src.entity_resolution.resolver import EntityResolver

def test_entity_resolver_exact_and_aliases():
    resolver = EntityResolver()
    
    # Exact and alias matches from canonical seed DB
    assert resolver.resolve("OpenAI") == "OpenAI"
    assert resolver.resolve("OpenAI, Inc.") == "OpenAI"
    assert resolver.resolve("Open AI") == "OpenAI"
    assert resolver.resolve("OpenAI OpCo LLC") == "OpenAI"
    
    assert resolver.resolve("Anthropic PBC") == "Anthropic"
    assert resolver.resolve("Mistral AI SAS") == "Mistral AI"
    assert resolver.resolve("Cohere Inc.") == "Cohere"
    assert resolver.resolve("Scale Labs, Inc.") == "Scale AI"

def test_legal_suffix_stripping():
    resolver = EntityResolver()
    assert resolver.strip_legal_suffixes("Acme Technologies, Inc.") == "Acme"
    assert resolver.strip_legal_suffixes("DeepTech Labs LLC") == "DeepTech"
    assert resolver.strip_legal_suffixes("GenAI Corp.") == "GenAI"

def test_fuzzy_resolution():
    resolver = EntityResolver()
    # Slight typos or spacing variations
    assert resolver.resolve("Open-AI") == "OpenAI"
    assert resolver.resolve("Huggingface") == "Hugging Face"
    assert resolver.resolve("Databricks AI Inc") == "Databricks"

def test_mapping_log_generation():
    resolver = EntityResolver()
    resolver.resolve("OpenAI, Inc.")
    resolver.resolve("Anthropic PBC")
    resolver.resolve("BrandNewAIStartup LLC")
    
    logs = resolver.get_mapping_logs()
    assert len(logs) == 3
    assert logs[0].raw_name == "OpenAI, Inc."
    assert logs[0].canonical_name == "OpenAI"
    assert logs[0].confidence_score >= 0.95
