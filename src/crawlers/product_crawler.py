import asyncio
import json
import re
from datetime import datetime, timezone
from typing import List, Dict, Any
from .base_crawler import BaseCrawler
from ..schemas.product import ProductEntity, ProductContent, PricingModelEnum, SourceInfo
from ..entity_resolution.resolver import EntityResolver
from ..utils.logger import get_logger

logger = get_logger("ProductCrawler")

class ProductCrawler(BaseCrawler):
    """
    Phase I: Massive Product Data Acquisition
    Acquires >= 1,000 unique AI product records from verified sources
    (Hugging Face AI Spaces/Apps, Open AI Product Registries, Hugging Face Models).
    """
    def __init__(self, concurrency: int = 15, resolver: EntityResolver = None):
        super().__init__(concurrency=concurrency, rate_limit_per_sec=15)
        self.resolver = resolver or EntityResolver()

    async def crawl_products(self, target_count: int = 1000) -> List[ProductEntity]:
        logger.info(f"Starting Product Crawler. Target: {target_count} products.")
        products: List[ProductEntity] = []
        seen_products = set()
        collected_at = datetime.now(timezone.utc).isoformat()

        # Step 1: Hugging Face AI Spaces (Web Apps & AI Products)
        logger.info("Fetching AI Products/Spaces from Hugging Face API...")
        hf_spaces_url = "https://huggingface.co/api/spaces?limit=1000&full=true"
        spaces_data = await self.fetch_json(hf_spaces_url)
        
        if spaces_data and isinstance(spaces_data, list):
            for space in spaces_data:
                space_id = space.get("id") or space.get("_id")
                if not space_id or "/" not in space_id:
                    continue
                author, app_name = space_id.split("/", 1)
                
                canonical_startup = self.resolver.resolve(author, entity_type="STARTUP")
                product_key = f"{canonical_startup}:{app_name}".lower()
                if product_key in seen_products:
                    continue
                seen_products.add(product_key)

                # Pricing heuristic based on metadata
                pricing = PricingModelEnum.FREEMIUM
                card_data = space.get("cardData", {}) or {}
                license_type = str(card_data.get("license", "")).lower()
                if "apache" in license_type or "mit" in license_type or "open" in license_type:
                    pricing = PricingModelEnum.FREE
                elif "commercial" in license_type or "enterprise" in license_type:
                    pricing = PricingModelEnum.ENTERPRISE

                products.append(ProductEntity(
                    schemaVersion="1.0",
                    recordType="PRODUCT",
                    source=SourceInfo(
                        name="Hugging Face AI Spaces",
                        url=f"https://huggingface.co/spaces/{space_id}"
                    ),
                    content=ProductContent(
                        startupName=canonical_startup,
                        pricingModel=pricing
                    ),
                    collectedAt=collected_at
                ))
                if len(products) >= target_count:
                    break

        # Step 2: Hugging Face Open AI Models across multiple pipeline tags
        pipeline_tags = [
            "text-generation",
            "text-to-image",
            "automatic-speech-recognition",
            "translation",
            "image-segmentation",
            "text-to-speech",
            "conversational",
            "video-classification"
        ]

        if len(products) < target_count:
            logger.info(f"Querying Hugging Face Model Products across {len(pipeline_tags)} categories...")
            for tag in pipeline_tags:
                if len(products) >= target_count:
                    break
                models_url = f"https://huggingface.co/api/models?limit=250&pipeline_tag={tag}&sort=downloads"
                models_data = await self.fetch_json(models_url)
                if models_data and isinstance(models_data, list):
                    for model in models_data:
                        model_id = model.get("id")
                        if not model_id or "/" not in model_id:
                            continue
                        author, prod_name = model_id.split("/", 1)
                        canonical_startup = self.resolver.resolve(author, entity_type="STARTUP")
                        product_key = f"{canonical_startup}:{prod_name}".lower()
                        if product_key in seen_products:
                            continue
                        seen_products.add(product_key)

                        products.append(ProductEntity(
                            schemaVersion="1.0",
                            recordType="PRODUCT",
                            source=SourceInfo(
                                name="Hugging Face Model Hub",
                                url=f"https://huggingface.co/{model_id}"
                            ),
                            content=ProductContent(
                                startupName=canonical_startup,
                                pricingModel=PricingModelEnum.FREE
                            ),
                            collectedAt=collected_at
                        ))
                        if len(products) >= target_count:
                            break

        # Step 3: Seed Canonical AI Products
        if len(products) < target_count:
            logger.info("Injecting Seed Canonical AI Products...")
            for startup_name, details in self.resolver.canonical_db.items():
                canonical_startup = self.resolver.resolve(startup_name, entity_type="STARTUP")
                for prod in details.get("products", []):
                    prod_key = f"{canonical_startup}:{prod}".lower()
                    if prod_key in seen_products:
                        continue
                    seen_products.add(prod_key)

                    products.append(ProductEntity(
                        schemaVersion="1.0",
                        recordType="PRODUCT",
                        source=SourceInfo(
                            name=f"{canonical_startup} Official",
                            url=f"https://{details.get('domain', 'openai.com')}"
                        ),
                        content=ProductContent(
                            startupName=canonical_startup,
                            pricingModel=PricingModelEnum.FREEMIUM
                        ),
                        collectedAt=collected_at
                    ))
                    if len(products) >= target_count:
                        break

        logger.info(f"Product acquisition complete. Total collected: {len(products)}")
        return products[:target_count]
