from pydantic import BaseModel, Field
from typing import List, Optional

class NewsContent(BaseModel):
    title: str
    url: str
    source: str
    published_date: str # ISO-8601 publication date
    summary: Optional[str] = None
    entities_mentioned: List[str] = Field(default_factory=list)

class NewsEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="NEWS")
    content: NewsContent
    collectedAt: str # ISO-8601 string
