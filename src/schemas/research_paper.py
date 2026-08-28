from pydantic import BaseModel, Field
from typing import List, Optional

class ResearchPaperContent(BaseModel):
    title: str
    authors: List[str]
    paper_url: str
    github_url: Optional[str] = None
    github_stars: Optional[int] = None
    published_date: str # ISO-8601 publication date

class ResearchPaperEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="RESEARCH_PAPER")
    content: ResearchPaperContent
