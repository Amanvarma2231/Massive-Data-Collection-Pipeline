from pydantic import BaseModel, Field

class EntityMappingRecord(BaseModel):
    raw_name: str
    canonical_name: str
    confidence_score: float
    method: str  # EXACT, ALIAS, LEGAL_STRIP, FUZZY, LLM, PASS_THROUGH
    entity_type: str = Field(default="ORGANIZATION")
    timestamp: str # ISO-8601
