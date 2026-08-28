import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from ..config import settings
from ..schemas import (
    StartupEntity, ProductEntity, ResearchPaperEntity, JobEntity, NewsEntity, EntityMappingRecord
)
from ..utils.logger import get_logger

logger = get_logger("DatabaseManager")
Base = declarative_base()

class StartupModel(Base):
    __tablename__ = "startups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(10), default="1.0")
    record_type = Column(String(20), default="STARTUP")
    source_name = Column(String(255))
    source_url = Column(Text)
    entity_name = Column(String(255), index=True)
    employee_count = Column(Integer, nullable=True)
    collected_at = Column(String(50))

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(10), default="1.0")
    record_type = Column(String(20), default="PRODUCT")
    source_name = Column(String(255))
    source_url = Column(Text)
    startup_name = Column(String(255), index=True)
    pricing_model = Column(String(50), default="FREEMIUM")
    collected_at = Column(String(50))

class ResearchPaperModel(Base):
    __tablename__ = "research_papers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(10), default="1.0")
    record_type = Column(String(20), default="RESEARCH_PAPER")
    title = Column(Text)
    authors_json = Column(Text)
    paper_url = Column(Text, unique=True)
    github_url = Column(Text, nullable=True)
    github_stars = Column(Integer, nullable=True)
    published_date = Column(String(50))

class JobModel(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(10), default="1.0")
    record_type = Column(String(20), default="JOB")
    company = Column(String(255), index=True)
    date = Column(String(50))
    is_remote = Column(Boolean, default=True)
    role_family = Column(String(100), default="Engineering")

class NewsModel(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, autoincrement=True)
    schema_version = Column(String(10), default="1.0")
    record_type = Column(String(20), default="NEWS")
    title = Column(Text)
    url = Column(Text, unique=True)
    source = Column(String(255))
    published_date = Column(String(50))
    summary = Column(Text, nullable=True)
    entities_mentioned_json = Column(Text)
    collected_at = Column(String(50))

class EntityMappingModel(Base):
    __tablename__ = "entity_mapping_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_name = Column(String(255))
    canonical_name = Column(String(255))
    confidence_score = Column(Float)
    method = Column(String(50))
    entity_type = Column(String(50))
    timestamp = Column(String(50))

class DatabaseManager:
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.DATABASE_URL
        # Sync engine for fast bulk inserts / table creation
        sync_url = self.db_url.replace("+aiosqlite", "").replace("+asyncpg", "")
        self.engine = create_engine(sync_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.init_db()

    def init_db(self):
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized with schema tables: {list(Base.metadata.tables.keys())}")

    def save_startups(self, startups: List[StartupEntity]):
        with self.Session() as session:
            for s in startups:
                m = StartupModel(
                    schema_version=s.schemaVersion,
                    record_type=s.recordType,
                    source_name=s.source.name,
                    source_url=s.source.url,
                    entity_name=s.content.entityName,
                    employee_count=s.content.data.employeeCount,
                    collected_at=s.collectedAt
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(startups)} startups to database.")

    def save_products(self, products: List[ProductEntity]):
        with self.Session() as session:
            for p in products:
                m = ProductModel(
                    schema_version=p.schemaVersion,
                    record_type=p.recordType,
                    source_name=p.source.name,
                    source_url=p.source.url,
                    startup_name=p.content.startupName,
                    pricing_model=p.content.pricingModel.value,
                    collected_at=p.collectedAt
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(products)} products to database.")

    def save_research_papers(self, papers: List[ResearchPaperEntity]):
        with self.Session() as session:
            for p in papers:
                m = ResearchPaperModel(
                    schema_version=p.schemaVersion,
                    record_type=p.recordType,
                    title=p.content.title,
                    authors_json=json.dumps(p.content.authors),
                    paper_url=p.content.paper_url,
                    github_url=p.content.github_url,
                    github_stars=p.content.github_stars,
                    published_date=p.content.published_date
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(papers)} research papers to database.")

    def save_jobs(self, jobs: List[JobEntity]):
        with self.Session() as session:
            for j in jobs:
                m = JobModel(
                    schema_version=j.schemaVersion,
                    record_type=j.recordType,
                    company=j.content.company,
                    date=j.content.date,
                    is_remote=j.content.is_remote,
                    role_family=j.content.role_family
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(jobs)} jobs to database.")

    def save_news(self, news: List[NewsEntity]):
        with self.Session() as session:
            for n in news:
                m = NewsModel(
                    schema_version=n.schemaVersion,
                    record_type=n.recordType,
                    title=n.content.title,
                    url=n.content.url,
                    source=n.content.source,
                    published_date=n.content.published_date,
                    summary=n.content.summary,
                    entities_mentioned_json=json.dumps(n.content.entities_mentioned),
                    collected_at=n.collectedAt
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(news)} news articles to database.")

    def save_entity_mappings(self, mappings: List[EntityMappingRecord]):
        with self.Session() as session:
            for em in mappings:
                m = EntityMappingModel(
                    raw_name=em.raw_name,
                    canonical_name=em.canonical_name,
                    confidence_score=em.confidence_score,
                    method=em.method,
                    entity_type=em.entity_type,
                    timestamp=em.timestamp
                )
                session.add(m)
            session.commit()
            logger.info(f"Persisted {len(mappings)} entity mapping logs to database.")
