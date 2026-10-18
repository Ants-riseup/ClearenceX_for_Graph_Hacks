"""Additive tables: historical source data is never silently assigned to a user."""
from sqlalchemy import Column, String, Integer, Float, BigInteger, ForeignKey, JSON, Index
from database.models import Base


class Tenant(Base):
    __tablename__ = "cx_tenants"
    id = Column(String(64), primary_key=True)
    name = Column(String(200), nullable=False)
    settings = Column(JSON, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default='active')
    version = Column(Integer, nullable=False, default=1)
    profile = Column(JSON, nullable=False, default=dict)


class User(Base):
    __tablename__ = "cx_users"
    id = Column(String(64), primary_key=True)
    email = Column(String(254), unique=True, nullable=False)
    password_hash = Column(String(512), nullable=False)
    disabled = Column(Integer, nullable=False, default=0)
    platform_admin = Column(Integer, nullable=False, default=0)
    must_change_password = Column(Integer, nullable=False, default=0)


class CompanyEvent(Base):
    __tablename__ = 'cx_company_events'
    id = Column(String(64), primary_key=True)
    company_id = Column(String(64), ForeignKey('cx_tenants.id'), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    action = Column(String(40), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    details = Column(JSON, nullable=False, default=dict)


class Membership(Base):
    __tablename__ = "cx_memberships"
    user_id = Column(String(64), ForeignKey("cx_users.id"), primary_key=True)
    tenant_id = Column(String(64), ForeignKey("cx_tenants.id"), primary_key=True)
    role = Column(String(20), nullable=False)
    disabled = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)


class AccountEvent(Base):
    __tablename__ = 'cx_account_events'
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey('cx_tenants.id'), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    target_id = Column(String(64), nullable=False)
    action = Column(String(40), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    details = Column(JSON, nullable=False, default=dict)


class LoginAttempt(Base):
    __tablename__ = "cx_login_attempts"
    id = Column(String(64), primary_key=True)
    identity = Column(String(64), nullable=False, index=True)
    timestamp = Column(BigInteger, nullable=False)


class Session(Base):
    __tablename__ = "cx_sessions"
    token_hash = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("cx_users.id"), nullable=False)
    tenant_id = Column(String(64), ForeignKey("cx_tenants.id"), nullable=False)
    csrf_hash = Column(String(64), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    last_seen = Column(BigInteger, nullable=False)
    expires_at = Column(BigInteger, nullable=False)


class ContextDossier(Base):
    __tablename__ = "cx_context_dossiers"
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey("cx_tenants.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    revision = Column(Integer, nullable=False, default=1)
    graph_revision = Column(Integer, nullable=False, default=0)
    state = Column(JSON, nullable=False)
    created_at = Column(BigInteger, nullable=False)


class Outbox(Base):
    __tablename__ = "cx_graph_outbox"
    id = Column(String(64), primary_key=True)
    dossier_id = Column(String(64), ForeignKey("cx_context_dossiers.id"), nullable=False)
    revision = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt = Column(BigInteger, nullable=False, default=0)
    error = Column(String(200))


class AgentRun(Base):
    __tablename__ = "cx_agent_runs"
    id = Column(String(64), primary_key=True)
    dossier_id = Column(String(64), ForeignKey("cx_context_dossiers.id"), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    revision = Column(Integer, nullable=False)
    status = Column(String(24), nullable=False)
    question = Column(String(2000), nullable=False)
    result = Column(JSON, nullable=False, default=dict)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class UsageBudget(Base):
    __tablename__ = "cx_usage_budget"
    # One ledger for this application, shared across API processes.
    id = Column(String(32), primary_key=True)
    charged_usd = Column(Float, nullable=False, default=0)
    reserved_usd = Column(Float, nullable=False, default=0)
    input_tokens = Column(BigInteger, nullable=False, default=0)
    output_tokens = Column(BigInteger, nullable=False, default=0)


class ExportArtifact(Base):
    __tablename__ = 'cx_export_artifacts'
    id = Column(String(64), primary_key=True)
    dossier_id = Column(String(64), ForeignKey('cx_context_dossiers.id'), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    source_revision = Column(Integer, nullable=False)
    validity_state = Column(String(20), nullable=False, default='current')
    created_at = Column(BigInteger, nullable=False)
    payload = Column(JSON, nullable=False)
    xml = Column(String, nullable=False)


class BatchJob(Base):
    __tablename__ = 'cx_batch_jobs'
    id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), ForeignKey('cx_tenants.id'), nullable=False, index=True)
    actor_id = Column(String(64), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    status = Column(String(20), nullable=False)
    result = Column(JSON, nullable=False, default=dict)


Index("cx_outbox_ready", Outbox.status, Outbox.next_attempt)
