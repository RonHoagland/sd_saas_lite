"""
Regenerate scripts/setup_rls.sql from the live model registry.

Why this exists
---------------
The hand-maintained RLS script drifted out of sync with the TenantModel
registry — multiple models had been added (procurement.RMA,
procurement.VendorAccount, value_lists.*, users.EmployeeZone, most of
automation.*) but never had their tables added to the bulk RLS list.
At least one entry referenced a stale Django app name
(`notes_document` vs the real `documents_document`).

The fix isn't to chase the drift forever; it's to derive the script
mechanically from `apps.get_models()` so it can never go stale.

Usage
-----
    # Write the file:
    python manage.py regenerate_rls_sql

    # Dry-run / drift detection (CI):
    python manage.py regenerate_rls_sql --check

A tests/ test exercises --check so a PR that adds a TenantModel
without regenerating the SQL fails the suite.
"""

from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

from config.base_models import TenantModel


# Models that are NOT TenantModel subclasses but carry a `tenant_id`
# UUIDField column (typically immutable audit logs that intentionally use
# a raw UUID rather than a real FK so audit records survive entity
# deletion). They must still be RLS-protected.
NON_TENANTMODEL_TENANT_ID_TABLES = [
    'documents_filedownloadlog',
    'lifecycle_lifecycletransitionaudit',
    'numbering_numbersequence',
]


HEADER = """\
-- =============================================================================
-- ServizDesk SDTA — Row-Level Security (RLS) policies
-- =============================================================================
--
--   ⚠️  GENERATED FILE — do not edit by hand.
--   Re-run `python manage.py regenerate_rls_sql` if a TenantModel is added
--   or removed; CI runs the same command with --check to catch drift.
--
-- Run this AFTER Django migrations have created the tables. The script
-- assumes the four PostgreSQL roles created by setup_postgres.sql.
--
--   psql -h 127.0.0.1 -U sdta_migration -d servizdesk_sdta \\
--        -f scripts/setup_rls.sql
--
-- How it works
-- ------------
-- Every TenantModel table has a tenant_id UUID column. Django's
-- TenantMiddleware issues `SET LOCAL app.current_tenant_id = '<uuid>'`
-- inside the request transaction. The four standard policies below
-- (tenant_select / tenant_insert / tenant_update / tenant_delete) filter
-- queries from sdta_app to rows where tenant_id matches that variable.
--
-- sdta_migration / sdta_support have BYPASSRLS, so they always see
-- everything. sdta_app is RLS-bound.
-- =============================================================================

-- Helper functions ------------------------------------------------------------

CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
    SELECT NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION is_staff() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.is_staff', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION is_superuser() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.is_superuser', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION system_bypass() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.system_bypass', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;


-- Bulk policy application -----------------------------------------------------

DO $$
DECLARE
    tbl TEXT;
    tenant_tables TEXT[] := ARRAY[
__TABLE_LIST__
    ];
BEGIN
    FOREACH tbl IN ARRAY tenant_tables LOOP
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tbl);

        EXECUTE format('DROP POLICY IF EXISTS tenant_select ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_insert ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_update ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_delete ON %I', tbl);

        EXECUTE format(
            'CREATE POLICY tenant_select ON %I FOR SELECT USING ('
            'tenant_id = current_tenant_id() OR is_staff() OR '
            'is_superuser() OR system_bypass())',
            tbl
        );
        EXECUTE format(
            'CREATE POLICY tenant_insert ON %I FOR INSERT WITH CHECK ('
            'tenant_id = current_tenant_id() OR is_staff() OR '
            'is_superuser() OR system_bypass())',
            tbl
        );
        EXECUTE format(
            'CREATE POLICY tenant_update ON %I FOR UPDATE USING ('
            'tenant_id = current_tenant_id() OR is_staff() OR '
            'is_superuser() OR system_bypass())',
            tbl
        );
        EXECUTE format(
            'CREATE POLICY tenant_delete ON %I FOR DELETE USING ('
            'tenant_id = current_tenant_id() OR is_staff() OR '
            'is_superuser() OR system_bypass())',
            tbl
        );

        RAISE NOTICE 'RLS enabled on %', tbl;
    END LOOP;
END
$$;
"""


class Command(BaseCommand):
    help = "Regenerate scripts/setup_rls.sql from the TenantModel registry."

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help="Don't write the file; exit non-zero if it would change.",
        )
        parser.add_argument(
            '--output',
            default=None,
            help="Output path. Default: <BASE_DIR>/scripts/setup_rls.sql.",
        )

    def handle(self, *args, **options):
        target = Path(options['output']) if options['output'] else (
            Path(settings.BASE_DIR) / 'scripts' / 'setup_rls.sql'
        )

        tenant_tables = self._discover_tenant_tables()
        sql = self._render_sql(tenant_tables)

        if options['check']:
            current = target.read_text() if target.exists() else ''
            if current == sql:
                self.stdout.write(self.style.SUCCESS(
                    f'OK — {target.name} matches the current TenantModel registry '
                    f'({sum(len(v) for v in tenant_tables.values())} tables).'
                ))
                return
            self.stderr.write(self.style.ERROR(
                f'DRIFT DETECTED: {target} is out of date.\n'
                f'Re-run `python manage.py regenerate_rls_sql` and commit '
                f'the result.'
            ))
            raise SystemExit(1)

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(sql)
        total = sum(len(v) for v in tenant_tables.values())
        self.stdout.write(self.style.SUCCESS(
            f'Wrote {target} covering {total} tenant-scoped tables across '
            f'{len(tenant_tables)} apps.'
        ))

    def _discover_tenant_tables(self):
        """Return {app_label: [db_table, ...]} for every tenant-scoped table.

        Sources:
          1. apps.get_models() filtered to TenantModel subclasses (not
             abstract, not proxy, not TenantModel itself).
          2. NON_TENANTMODEL_TENANT_ID_TABLES — hand-curated list of
             tables that bear `tenant_id` despite not subclassing
             TenantModel (immutable audit logs, etc.).
        """
        seen = set()
        tables_by_app: dict[str, list[str]] = {}

        for model in apps.get_models():
            if model is TenantModel:
                continue
            meta = model._meta
            if meta.abstract or meta.proxy:
                continue
            if not issubclass(model, TenantModel):
                continue
            table = meta.db_table
            if table in seen:
                continue
            seen.add(table)
            tables_by_app.setdefault(meta.app_label, []).append(table)

        for table in NON_TENANTMODEL_TENANT_ID_TABLES:
            if table in seen:
                continue
            seen.add(table)
            app_label = table.split('_', 1)[0]
            tables_by_app.setdefault(app_label, []).append(table)

        # Deterministic order so re-runs produce stable diffs.
        for tables in tables_by_app.values():
            tables.sort()
        return dict(sorted(tables_by_app.items()))

    def _render_sql(self, tables_by_app):
        lines = []
        for app_label, tables in tables_by_app.items():
            lines.append(f"        -- {app_label}")
            for i, table in enumerate(tables):
                comma = ',' if not (
                    app_label == list(tables_by_app)[-1]
                    and i == len(tables) - 1
                ) else ''
                lines.append(f"        '{table}'{comma}")
        return HEADER.replace('__TABLE_LIST__', '\n'.join(lines))
