from pydantic import BaseModel, Field
from typing import Optional
from .common import SourceInfo

class StartupContentData(BaseModel):
    employeeCount: Optional[int] = None

class StartupContent(BaseModel):
    entityName: str
    data: StartupContentData = Field(default_factory=StartupContentData)

class StartupEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="STARTUP")
    source: SourceInfo
    content: StartupContent
    collectedAt: str # ISO-8601 string
