# Phase 01 — Database Schema + Setup

> **Priority:** MUST
> **Estimated Time:** 1–2 hours
> **Dependencies:** None
> **Blocks:** All backend phases

---

## Goal

Create the PostgreSQL database schema for ClearanceX. This is the data foundation that everyone else builds on top of.

## Why

Without the schema, Kaveen can't store uploads and you can't store extractions, discrepancies, or audit logs. This must be done first.

## Tasks

### 1.1 Create Schema SQL

```sql
-- backend/database/schema.sql

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core shipment table
CREATE TABLE shipments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    status VARCHAR(20) DEFAULT 'uploaded',
    -- Status flow: uploaded → processing → completed → error
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual documents within a shipment
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(50),
    classification_confidence FLOAT,
    classification_evidence JSONB DEFAULT '[]',
    file_path VARCHAR(500) NOT NULL,
    page_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Extracted entities from each document
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    raw_value TEXT,
    normalized_value TEXT,
    unit VARCHAR(20),
    page INT DEFAULT 1,
    bbox JSONB,                    -- [x1, y1, x2, y2]
    extraction_confidence FLOAT,
    classification_confidence FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Detected discrepancies across documents
CREATE TABLE discrepancies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    field VARCHAR(50) NOT NULL,
    severity VARCHAR(10) DEFAULT 'medium',
    severity_score FLOAT DEFAULT 0.5,
    sources JSONB NOT NULL,        -- Array of source references
    reasoning_chain JSONB,         -- Layer 2
    confidence JSONB,              -- Layer 3 decomposed
    counterfactual JSONB,          -- Layer 4
    status VARCHAR(20) DEFAULT 'open',
    -- Status: open → resolved → accepted → overridden
    resolved_value TEXT,
    resolved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Immutable audit trail (Layer 5)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id UUID REFERENCES shipments(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    module VARCHAR(50) NOT NULL,   -- 'classifier', 'extractor', 'reconciler', 'user'
    action VARCHAR(100) NOT NULL,
    reasoning TEXT,
    confidence FLOAT,
    outcome VARCHAR(50),
    details JSONB
);

-- Human corrections (for future active learning)
CREATE TABLE corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extraction_id UUID REFERENCES extractions(id) ON DELETE CASCADE,
    original_value TEXT,
    corrected_value TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_documents_shipment ON documents(shipment_id);
CREATE INDEX idx_extractions_document ON extractions(document_id);
CREATE INDEX idx_extractions_entity_type ON extractions(entity_type);
CREATE INDEX idx_discrepancies_shipment ON discrepancies(shipment_id);
CREATE INDEX idx_audit_logs_shipment ON audit_logs(shipment_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
```

### 1.2 Create SQLAlchemy Models

```python
# backend/database/models.py
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class Shipment(Base):
    __tablename__ = 'shipments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), default='uploaded')
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Document(Base):
    __tablename__ = 'documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id'))
    filename = Column(String(255), nullable=False)
    document_type = Column(String(50))
    classification_confidence = Column(Float)
    classification_evidence = Column(JSONB, default=[])
    file_path = Column(String(500), nullable=False)
    page_count = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

class Extraction(Base):
    __tablename__ = 'extractions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id'))
    entity_type = Column(String(50), nullable=False)
    raw_value = Column(Text)
    normalized_value = Column(Text)
    unit = Column(String(20))
    page = Column(Integer, default=1)
    bbox = Column(JSONB)
    extraction_confidence = Column(Float)
    classification_confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

class Discrepancy(Base):
    __tablename__ = 'discrepancies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id'))
    field = Column(String(50), nullable=False)
    severity = Column(String(10), default='medium')
    severity_score = Column(Float, default=0.5)
    sources = Column(JSONB, nullable=False)
    reasoning_chain = Column(JSONB)
    confidence = Column(JSONB)
    counterfactual = Column(JSONB)
    status = Column(String(20), default='open')
    resolved_value = Column(Text)
    resolved_by = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey('shipments.id'))
    timestamp = Column(DateTime, server_default=func.now())
    module = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    reasoning = Column(Text)
    confidence = Column(Float)
    outcome = Column(String(50))
    details = Column(JSONB)

class Correction(Base):
    __tablename__ = 'corrections'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extraction_id = Column(UUID(as_uuid=True), ForeignKey('extractions.id'))
    original_value = Column(Text)
    corrected_value = Column(Text)
    reason = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
```

### 1.3 Create Database Connection

```python
# backend/database/connection.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/clearancex")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from .models import Base
    Base.metadata.create_all(bind=engine)
```

### 1.4 Initialize Database

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE clearancex;"

# Run schema
psql -U postgres -d clearancex -f backend/database/schema.sql

# OR use SQLAlchemy auto-create:
python -c "from database.connection import init_db; init_db()"
```

## Acceptance Criteria

- [ ] All 6 tables created in PostgreSQL
- [ ] SQLAlchemy models match the SQL schema
- [ ] Database connection works from Python
- [ ] Can insert and query a test shipment
- [ ] Indexes created for performance

## Outputs

- `backend/database/schema.sql`
- `backend/database/models.py`
- `backend/database/connection.py`
- Working PostgreSQL database
