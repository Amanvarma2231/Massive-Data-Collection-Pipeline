from pydantic import BaseModel, Field

class JobContent(BaseModel):
    company: str
    date: str # ISO-8601 publication date
    is_remote: bool
    role_family: str = Field(default="Engineering")

class JobEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="JOB")
    content: JobContent
