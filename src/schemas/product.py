from pydantic import BaseModel, Field
from enum import Enum
from .common import SourceInfo

class PricingModelEnum(str, Enum):
    FREE = "FREE"
    FREEMIUM = "FREEMIUM"
    PAID = "PAID"
    ENTERPRISE = "ENTERPRISE"

class ProductContent(BaseModel):
    startupName: str
    pricingModel: PricingModelEnum = Field(default=PricingModelEnum.FREEMIUM)

class ProductEntity(BaseModel):
    schemaVersion: str = Field(default="1.0")
    recordType: str = Field(default="PRODUCT")
    source: SourceInfo
    content: ProductContent
    collectedAt: str # ISO-8601 string
