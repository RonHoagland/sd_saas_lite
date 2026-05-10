"""
Tests for the `regenerate_rls_sql` management command and the integrity
of the generated `scripts/setup_rls.sql` file.

Goal: catch any drift between the TenantModel registry and the RLS
script before deploy. A model added without a corresponding migration
in the script is a real cross-tenant data exposure.
"""

import io
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.test import SimpleTestCase

from config.base_models import TenantModel
from infrastructure.management.commands.regenerate_rls_sql import (
    NON_TENANTMODEL_TENANT_ID_TABLES,
    Command,
)


SCRIPT_PATH = Path(settings.BASE_DIR) / 'scripts' / 'setup_rls.sql'


def _all_tenant_tables_from_registry():
    """Replica of Command._discover_tenant_tables, flat list."""
    seen = []
    for model in apps.get_models():
        if model is TenantModel:
            continue
        meta = model._meta
        if meta.abstract or meta.proxy:
            continue
        if not issubclass(model, TenantModel):
            continue
        if meta.db_table not in seen:
            seen.append(meta.db_table)
    for table in NON_TENANTMODEL_TENANT_ID_TABLES:
        if table not in seen:
            seen.append(table)
    return sorted(seen)


class RegenerateRlsSqlCheckModeTest(SimpleTestCase):
    """`regenerate_rls_sql --check` must succeed against the committed file."""

    def test_check_mode_passes_against_committed_script(self):
        """Drift detector — fails the suite if a TenantModel was added
        without re-running the command."""
        out = io.StringIO()
        try:
            call_command('regenerate_rls_sql', '--check', stdout=out)
        except SystemExit as exc:
            self.fail(
                f"`regenerate_rls_sql --check` exited {exc.code}. "
                f"Re-run `python manage.py regenerate_rls_sql` and commit "
                f"the resulting scripts/setup_rls.sql.\n"
                f"Output:\n{out.getvalue()}"
            )
        self.assertIn('OK', out.getvalue())


class GeneratedScriptCoversEveryTenantModelTest(SimpleTestCase):
    """Every TenantModel subclass must appear in the generated script."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.script_text = SCRIPT_PATH.read_text()
        cls.expected_tables = _all_tenant_tables_from_registry()

    def test_every_tenantmodel_table_listed(self):
        missing = [
            t for t in self.expected_tables
            if f"'{t}'" not in self.script_text
        ]
        self.assertEqual(
            missing, [],
            msg=(
                f'{len(missing)} tenant-scoped table(s) not found in '
                f'setup_rls.sql: {missing}. Re-run '
                f'`python manage.py regenerate_rls_sql`.'
            ),
        )

    def test_no_unknown_tables_listed(self):
        """Catches stale entries (db_table renames, deleted models)."""
        # Pull every quoted table from the array literal in the file.
        # Lines that look like `        'foo_bar',` are table entries.
        listed = []
        in_array = False
        for line in self.script_text.splitlines():
            stripped = line.strip()
            if stripped.startswith('tenant_tables TEXT[]'):
                in_array = True
                continue
            if in_array:
                if stripped.startswith('];') or stripped.startswith(']'):
                    break
                if stripped.startswith("'"):
                    table = stripped.strip("',")
                    listed.append(table)

        unknown = sorted(set(listed) - set(self.expected_tables))
        self.assertEqual(
            unknown, [],
            msg=(
                f'{len(unknown)} table(s) are listed in setup_rls.sql '
                f'but no TenantModel matches: {unknown}. '
                f'Did a model get renamed or deleted? Re-run '
                f'`python manage.py regenerate_rls_sql`.'
            ),
        )


class PreviouslyMissingTablesAreCoveredTest(SimpleTestCase):
    """Regression: tables the audit flagged as missing must now be present."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.script_text = SCRIPT_PATH.read_text()

    def _assert_listed(self, table):
        self.assertIn(
            f"'{table}'", self.script_text,
            msg=f'{table} missing from setup_rls.sql',
        )

    def test_procurement_rma_listed(self):
        self._assert_listed('procurement_rma')

    def test_procurement_vendoraccount_listed(self):
        self._assert_listed('procurement_vendoraccount')

    def test_value_lists_valuelist_listed(self):
        self._assert_listed('value_lists_valuelist')

    def test_value_lists_valuelistitem_listed(self):
        self._assert_listed('value_lists_valuelistitem')

    def test_users_employeezone_listed(self):
        self._assert_listed('users_employeezone')

    def test_automation_workflow_listed(self):
        self._assert_listed('automation_workflow')

    def test_automation_equipment_listed(self):
        self._assert_listed('automation_equipment')

    def test_automation_safetyform_listed(self):
        self._assert_listed('automation_safetyform')

    def test_documents_document_uses_correct_table_name(self):
        """The audit flagged `notes_document` (wrong); real table is
        `documents_document`."""
        self._assert_listed('documents_document')
        self.assertNotIn(
            "'notes_document'", self.script_text,
            msg='Stale `notes_document` reference still present.',
        )

    def test_file_upload_log_uses_correct_table_name(self):
        """Real db_table is `documents_file_upload_log` (with underscores)."""
        self._assert_listed('documents_file_upload_log')
        self.assertNotIn(
            "'notes_fileuploadlog'", self.script_text,
            msg='Stale `notes_fileuploadlog` reference still present.',
        )

    def test_service_workinvoice_uses_correct_table_name(self):
        """Real db_table on WorkOrderInvoice is `service_workinvoice`."""
        self._assert_listed('service_workinvoice')
        self.assertNotIn(
            "'service_workorderinvoice'", self.script_text,
            msg='Stale `service_workorderinvoice` reference still present.',
        )


class GeneratedScriptIntegrityTest(SimpleTestCase):
    """Sanity checks on the generated SQL structure."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.script_text = SCRIPT_PATH.read_text()

    def test_marked_as_generated(self):
        self.assertIn('GENERATED FILE', self.script_text)
        self.assertIn('regenerate_rls_sql', self.script_text)

    def test_force_row_level_security_present(self):
        self.assertIn('FORCE ROW LEVEL SECURITY', self.script_text)

    def test_failsafe_helper_uses_nullif(self):
        """The current_tenant_id() helper must return NULL on missing
        context (fail-safe), not crash and not match every row."""
        self.assertIn(
            "NULLIF(current_setting('app.current_tenant_id', TRUE), '')",
            self.script_text,
        )

    def test_all_four_policies_created(self):
        for policy in ('tenant_select', 'tenant_insert', 'tenant_update', 'tenant_delete'):
            self.assertIn(
                f'CREATE POLICY {policy}',
                self.script_text,
                msg=f'{policy} policy missing from script.',
            )

    def test_renderer_emits_alphabetised_apps(self):
        """Apps appear in alpha order so re-runs produce stable diffs."""
        cmd = Command()
        rendered = cmd._render_sql(cmd._discover_tenant_tables())
        # App-section comments are emitted as exactly 8-space-indented
        # `-- <app_label>` lines (no other content on the line).
        app_comments = []
        for line in rendered.splitlines():
            if line.startswith('        -- '):
                tail = line[len('        -- '):]
                # App labels are lowercase, may contain underscores, no spaces.
                if tail and ' ' not in tail and tail.replace('_', '').isalnum():
                    app_comments.append(tail)
        self.assertEqual(app_comments, sorted(app_comments))
        # And the test suite proves we actually emit at least 10 apps.
        self.assertGreaterEqual(len(app_comments), 10)
