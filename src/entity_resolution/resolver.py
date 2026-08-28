import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from rapidfuzz import fuzz, distance
from .seed_database import load_canonical_seed_db
from ..schemas.entity_mapping import EntityMappingRecord
from ..utils.logger import get_logger

logger = get_logger("EntityResolver")

LEGAL_SUFFIXES = [
    r'\binc(?:\.|orp(?:orated)?)?\b',
    r'\bllc\b',
    r'\bltd(?:\.)?\b',
    r'\bcorp(?:\.)?\b',
    r'\bcorporation\b',
    r'\btechnologies\b',
    r'\btech\b',
    r'\blabs\b',
    r'\blaboratories\b',
    r'\bco(?:\.|mpany)?\b',
    r'\bpbc\b',
    r'\bgmbh\b',
    r'\bsas\b',
    r'\bk\.k\.\b',
    r'\bholding(?:s)?\b',
    r'\bgroup\b',
    r'\bai\b',
    r'\bapp\b',
    r'\bio\b'
]

class EntityResolver:
    def __init__(self):
        self.canonical_db = load_canonical_seed_db()
        self.alias_lookup: Dict[str, str] = {}
        self.mapping_logs: List[EntityMappingRecord] = []
        self._build_indexes()

    def _build_indexes(self):
        for canonical_name, data in self.canonical_db.items():
            self.alias_lookup[self._clean_key(canonical_name)] = canonical_name
            for alias in data.get("aliases", []):
                self.alias_lookup[self._clean_key(alias)] = canonical_name
                
    def _clean_key(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

    def strip_legal_suffixes(self, name: str) -> str:
        """Strip legal entity designations and trailing/intermediate punctuation."""
        cleaned = name.strip()
        for suffix_pat in LEGAL_SUFFIXES:
            cleaned = re.sub(suffix_pat, '', cleaned, flags=re.IGNORECASE)
        # Clean any leftover dangling commas, dots, hyphens, and whitespace
        cleaned = re.sub(r'[,.\-_]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned if cleaned else name

    def resolve(self, raw_name: str, entity_type: str = "ORGANIZATION") -> str:
        if not raw_name or not raw_name.strip():
            return "Unknown"

        raw_trimmed = raw_name.strip()
        raw_key = self._clean_key(raw_trimmed)
        timestamp = datetime.now(timezone.utc).isoformat()

        # Stage 1: Exact Alias Index Lookup
        if raw_key in self.alias_lookup:
            canonical = self.alias_lookup[raw_key]
            self._log_mapping(raw_trimmed, canonical, 1.0, "EXACT_ALIAS", entity_type, timestamp)
            return canonical

        # Stage 2: Suffix-Stripped Match
        stripped = self.strip_legal_suffixes(raw_trimmed)
        stripped_key = self._clean_key(stripped)
        if stripped_key in self.alias_lookup:
            canonical = self.alias_lookup[stripped_key]
            self._log_mapping(raw_trimmed, canonical, 0.98, "LEGAL_STRIP", entity_type, timestamp)
            return canonical

        # Stage 3: Fuzzy Matching with Jaro-Winkler & Token Sort Ratio (> 0.88)
        best_match = None
        best_score = 0.0

        for candidate_key, canonical in self.alias_lookup.items():
            jw_score = distance.JaroWinkler.similarity(stripped_key, candidate_key)
            token_score = fuzz.token_sort_ratio(stripped, canonical) / 100.0
            
            combined_score = max(jw_score, token_score)
            if combined_score > best_score:
                best_score = combined_score
                best_match = canonical

        if best_score >= 0.88 and best_match:
            self._log_mapping(raw_trimmed, best_match, round(best_score, 3), "FUZZY_MATCH", entity_type, timestamp)
            return best_match

        # Stage 4: Normalized Pass-Through
        canonical = stripped.title() if stripped.islower() or stripped.isupper() else stripped
        canonical = re.sub(r'\bAi\b', 'AI', canonical)
        canonical = re.sub(r'\bMl\b', 'ML', canonical)
        canonical = re.sub(r'\bLlm\b', 'LLM', canonical)
        
        self._log_mapping(raw_trimmed, canonical, 1.0, "PASS_THROUGH", entity_type, timestamp)
        return canonical

    def _log_mapping(self, raw: str, canonical: str, confidence: float, method: str, entity_type: str, timestamp: str):
        record = EntityMappingRecord(
            raw_name=raw,
            canonical_name=canonical,
            confidence_score=confidence,
            method=method,
            entity_type=entity_type,
            timestamp=timestamp
        )
        self.mapping_logs.append(record)

    def get_mapping_logs(self) -> List[EntityMappingRecord]:
        return self.mapping_logs
