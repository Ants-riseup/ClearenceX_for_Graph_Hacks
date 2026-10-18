"""Ordered, transactional PostgreSQL upgrades; never silently downgrade data."""
from sqlalchemy import text


def initial_schema(connection):
    from database.models import Base
    from context_app import models  # register the initial additive model set
    Base.metadata.create_all(connection)


def queue_and_listing_indexes(connection):
    for statement in (
        'CREATE INDEX IF NOT EXISTS cx_dossiers_tenant_created ON cx_context_dossiers (tenant_id, created_at DESC, id)',
        'CREATE INDEX IF NOT EXISTS cx_runs_dossier_created ON cx_agent_runs (dossier_id, created_at DESC)',
        'CREATE INDEX IF NOT EXISTS cx_sessions_expiry ON cx_sessions (expires_at)',
    ):
        connection.execute(text(statement))


def workspace_settings(connection):
    connection.execute(text("ALTER TABLE cx_tenants ADD COLUMN IF NOT EXISTS settings JSON NOT NULL DEFAULT '{}'"))


def export_records(connection):
    from context_app.models import ExportArtifact, BatchJob
    ExportArtifact.__table__.create(connection, checkfirst=True)
    BatchJob.__table__.create(connection, checkfirst=True)


def reviewed_goods_provenance(connection):
    for definition in ('source_document_id VARCHAR(64)', 'source_revision INTEGER', 'source_row_id VARCHAR(255)',
            "validity_state VARCHAR(24) NOT NULL DEFAULT 'unverified'", "details JSONB NOT NULL DEFAULT '{}'::jsonb"):
        connection.execute(text('ALTER TABLE cusdec_line_items ADD COLUMN IF NOT EXISTS ' + definition))
    connection.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS cx_goods_source_identity ON cusdec_line_items (shipment_id, source_row_id) WHERE source_row_id IS NOT NULL'))
    # Earlier artifacts were prepared without the new completeness/provenance
    # gates. Preserve their history, but require a newly reviewed export.
    connection.execute(text("UPDATE cx_export_artifacts SET validity_state='stale' WHERE validity_state='current'"))


UPGRADES = [(1, 'initial_additive_schema', initial_schema), (2, 'queue_and_listing_indexes', queue_and_listing_indexes), (3, 'workspace_settings', workspace_settings), (4, 'export_records', export_records), (5, 'reviewed_goods_provenance', reviewed_goods_provenance)]


def upgrade(engine):
    # A database transaction and advisory lock serialize startup/admin upgrades.
    # Existing records and tables are preserved. Future schema changes must add
    # an explicit numbered upgrade rather than mutate an applied revision.
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(467831209)'))
        connection.execute(text('CREATE TABLE IF NOT EXISTS cx_schema_migrations '
            '(version INTEGER PRIMARY KEY, name VARCHAR(120) NOT NULL, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())'))
        applied = dict(connection.execute(text('SELECT version, name FROM cx_schema_migrations')).all())
        known = dict((version, name) for version, name, _ in UPGRADES)
        if any(known.get(version) != name for version, name in applied.items()):
            raise RuntimeError('Unknown database migration revision; use the matching application release.')
        for version, name, migrate in UPGRADES:
            if version not in applied:
                migrate(connection)
                connection.execute(text('INSERT INTO cx_schema_migrations (version, name) VALUES (:v, :n)'), {'v': version, 'n': name})


def status(engine):
    with engine.connect() as connection:
        return [dict(r._mapping) for r in connection.execute(text('SELECT version, name, applied_at FROM cx_schema_migrations ORDER BY version'))]
