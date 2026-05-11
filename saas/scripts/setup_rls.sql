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
--   psql -h 127.0.0.1 -U sdta_migration -d servizdesk_sdta \
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
        -- automation
        'automation_checkinout',
        'automation_communicationtemplate',
        'automation_communicationtrigger',
        'automation_creditcard',
        'automation_employeepurchase',
        'automation_equipment',
        'automation_milestone',
        'automation_milestonetask',
        'automation_portfolio',
        'automation_portfoliomember',
        'automation_portfolioproject',
        'automation_safetyform',
        'automation_sprint',
        'automation_sprintmember',
        'automation_sprinttask',
        'automation_territoryzone',
        'automation_triggerlog',
        'automation_triggertemplate',
        'automation_wfinventory',
        'automation_wfsafetyform',
        'automation_wfstep',
        'automation_wfsteptodo',
        'automation_wftool',
        'automation_workflow',
        'automation_wosfanswer',
        -- crm
        'crm_account',
        'crm_address',
        'crm_contact',
        'crm_customer',
        'crm_lead',
        'crm_opportunity',
        'crm_opportunitycontacts',
        'crm_person',
        'crm_phone',
        'crm_social',
        -- documents
        'documents_document',
        'documents_file_upload_log',
        'documents_filedownloadlog',
        -- fleet
        'fleet_mileagelog',
        'fleet_vehicle',
        'fleet_vehicleinventory',
        'fleet_vehiclemaintenance',
        -- infrastructure
        'infrastructure_dataexportlog',
        'infrastructure_emaildeliverylog',
        'infrastructure_emailusagetracker',
        'infrastructure_issueserrors',
        'infrastructure_navigationaudit',
        'infrastructure_notification',
        'infrastructure_onboardingstate',
        'infrastructure_processtransaction',
        'infrastructure_smsusagetracker',
        'infrastructure_storagetracker',
        'infrastructure_stripeapirequestlog',
        'infrastructure_stripeconnection',
        'infrastructure_stripeconnectionlog',
        'infrastructure_stripelog',
        'infrastructure_striperesponse',
        'infrastructure_systemaudits',
        'infrastructure_tenantsynclog',
        'infrastructure_webhooklog',
        -- inventory
        'inventory_invpricehistory',
        'inventory_kititem',
        'inventory_pricebook',
        'inventory_pricebookentry',
        'inventory_product',
        -- lifecycle
        'lifecycle_lifecyclestatedef',
        'lifecycle_lifecycletransitionaudit',
        'lifecycle_lifecycletransitionrule',
        -- maintenance
        'maintenance_agreement',
        'maintenance_asset',
        'maintenance_customeragreement',
        'maintenance_preventativemaintenance',
        'maintenance_subasset',
        -- notes
        'notes_note',
        -- numbering
        'numbering_assignednumber',
        'numbering_numberingrule',
        'numbering_numbersequence',
        -- procurement
        'procurement_lotinfo',
        'procurement_purchaseorder',
        'procurement_purchaseorderline',
        'procurement_receiving',
        'procurement_requisition',
        'procurement_requisitionline',
        'procurement_rma',
        'procurement_vendor',
        'procurement_vendoraccount',
        'procurement_vendorbill',
        -- service
        'service_accounting',
        'service_bank',
        'service_invoice',
        'service_invoiceasset',
        'service_invoiceline',
        'service_invoicesnapshot',
        'service_ledger',
        'service_payments',
        'service_quote',
        'service_quoteasset',
        'service_quoteline',
        'service_quotesnapshot',
        'service_servicerequest',
        'service_workinvoice',
        'service_workorder',
        'service_workorderline',
        'service_workorderteam',
        -- tasks
        'tasks_associatedtask',
        'tasks_task',
        'tasks_tasktime',
        'tasks_tasktodo',
        'tasks_timeentry',
        -- users
        'users_department',
        'users_employeeposition',
        'users_employeepreference',
        'users_employeerole',
        'users_employeezone',
        'users_loginattemptlog',
        'users_position',
        'users_role',
        'users_rolepermission',
        'users_sessionlog',
        'users_tenantpreference',
        -- value_lists
        'value_lists_valuelist',
        'value_lists_valuelistitem',
        -- warehouse
        'warehouse_inventorycount',
        'warehouse_inventorytransfer',
        'warehouse_location',
        'warehouse_locationassignedinventory',
        'warehouse_sublocation',
        'warehouse_warehouse',
        -- workforce
        'workforce_employeeskill',
        'workforce_skill',
        'workforce_wgdivision',
        'workforce_wgtrole',
        'workforce_workgroup',
        'workforce_workgroupasset',
        'workforce_workgroupteam'
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
