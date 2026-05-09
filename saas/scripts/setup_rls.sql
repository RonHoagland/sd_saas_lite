-- =============================================================================
-- ServizDesk SDTA — Row-Level Security (RLS) policies
-- =============================================================================
-- Run this AFTER running Django migrations (which create all the tables).
-- Must be run as a superuser or sdta_migration:
--
--   psql -U djangouser -h 127.0.0.1 -d servizdesk_sdta \
--        -f scripts/setup_rls.sql
--
-- How it works:
--   • Every TenantModel table has a tenant_id UUID column.
--   • A PostgreSQL session variable app.current_tenant_id is set by Django's
--     TenantMiddleware at the start of each request.
--   • The RLS SELECT / INSERT / UPDATE / DELETE policies below filter every
--     query made by sdta_app to only rows where tenant_id matches that variable.
--   • sdta_migration has BYPASSRLS, so it always sees all rows.
--
-- The list of tables below must be kept in sync with TenantModel subclasses.
-- Run this script again whenever new TenantModel tables are added.
-- =============================================================================

-- Helper function: returns the current tenant UUID set by Django middleware.
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS UUID AS $$
    SELECT NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
$$ LANGUAGE SQL STABLE;

-- Helper function: returns true if the session is flagged as staff.
CREATE OR REPLACE FUNCTION is_staff() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.is_staff', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;

-- Helper function: returns true if the session is flagged as superuser.
CREATE OR REPLACE FUNCTION is_superuser() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.is_superuser', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;

-- Helper function: returns true if the session has a system bypass flag (e.g. during provisioning).
CREATE OR REPLACE FUNCTION system_bypass() RETURNS BOOLEAN AS $$
    SELECT current_setting('app.system_bypass', TRUE) = 'true';
$$ LANGUAGE SQL STABLE;


-- =============================================================================
-- Macro: enable RLS and create the four standard policies on a table.
-- =============================================================================
-- Usage: call apply_tenant_rls('<table_name>');
-- This is a DO block; repeat for each table or use the bulk section below.
-- =============================================================================

-- ─── Bulk application ─────────────────────────────────────────────────────────
-- Add every tenant-scoped table here.  Tables owned by non-tenant models
-- (TenantState, SubdomainIndex, StaffUser, ErrorCode, etc.) are NOT listed
-- because they are global and should not be RLS-restricted by tenant_id.

DO $$
DECLARE
    tbl TEXT;
    tenant_tables TEXT[] := ARRAY[
        -- users
        'users_user', 'users_role', 'users_rolepermission', 'users_position',
        'users_employeerole', 'users_employeeposition', 'users_department',
        'users_tenantpreference', 'users_employeepreference',
        'users_sessionlog', 'users_loginattemptlog',
        -- crm
        'crm_customer', 'crm_person', 'crm_contact', 'crm_address',
        'crm_phone', 'crm_social', 'crm_lead', 'crm_opportunity',
        'crm_opportunitycontacts',
        -- inventory
        'inventory_product', 'inventory_kititem', 'inventory_pricebook',
        'inventory_pricebookentry', 'inventory_invpricehistory',
        -- warehouse
        'warehouse_warehouse', 'warehouse_sublocation',
        'warehouse_inventorycount', 'warehouse_inventorytransfer',
        'warehouse_locationassignedinventory',
        -- procurement
        'procurement_vendor', 'procurement_vendorbill', 'procurement_lotinfo',
        'procurement_requisition', 'procurement_requisitionline',
        'procurement_purchaseorder', 'procurement_purchaseorderline',
        'procurement_receiving',
        -- service
        'service_workorder', 'service_workorderline', 'service_workorderteam',
        'service_workorderinvoice', 'service_servicerequest',
        'service_quote', 'service_quoteline', 'service_quoteasset',
        'service_invoice', 'service_invoiceline', 'service_invoiceasset',
        'service_payments', 'service_accounting', 'service_bank', 'service_ledger',
        -- maintenance
        'maintenance_asset', 'maintenance_subasset', 'maintenance_agreement',
        'maintenance_customeragreement', 'maintenance_preventativemaintenance',
        -- tasks
        'tasks_task', 'tasks_associatedtask', 'tasks_tasktime',
        'tasks_tasktodo', 'tasks_timeentry',
        -- workforce
        'workforce_wgdivision', 'workforce_workgroup', 'workforce_wgtrole',
        'workforce_workgroupteam', 'workforce_workgroupasset',
        -- automation
        'automation_communicationtrigger', 'automation_communicationtemplate',
        'automation_triggertemplate', 'automation_triggerlog',
        -- fleet
        'fleet_vehicle', 'fleet_vehiclemaintenance', 'fleet_mileagelog',
        'fleet_vehicleinventory',
        -- numbering (Phase 1 — Numbering Service Specification V1)
        'numbering_numberingrule', 'numbering_assignednumber', 'numbering_numbersequence',
        -- lifecycle (Phase 1 — Lifecycle Framework Specification V1)
        'lifecycle_lifecyclestatedef', 'lifecycle_lifecycletransitionrule',
        'lifecycle_lifecycletransitionaudit',
        -- notes (Phase 1 — Note & Document Implementation Specification V1)
        'notes_note', 'notes_document', 'notes_fileuploadlog',
        -- NOTE: notes_filedownloadlog does NOT have tenant_id FK (raw UUID for immutability)
        -- infrastructure (tenant-scoped subset)
        'infrastructure_storagetracker',
        'infrastructure_emailusagetracker', 'infrastructure_smsusagetracker',
        'infrastructure_onboardingstate', 'infrastructure_notification',
        'infrastructure_navigationaudit', 'infrastructure_systemaudits',
        'infrastructure_tenantsynclog', 'infrastructure_dataexportlog',
        'infrastructure_emaildeliverylog', 'infrastructure_issueserrors',
        'infrastructure_stripelog', 'infrastructure_striperesponse',
        'infrastructure_stripeapirequestlog', 'infrastructure_stripeconnection',
        'infrastructure_stripeconnectionlog', 'infrastructure_webhooklog',
        'infrastructure_processtransaction'
    ];
BEGIN
    FOREACH tbl IN ARRAY tenant_tables LOOP
        -- Enable RLS on the table
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', tbl);
        EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', tbl);

        -- Drop existing policies (idempotent re-run)
        EXECUTE format('DROP POLICY IF EXISTS tenant_select  ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_insert  ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_update  ON %I', tbl);
        EXECUTE format('DROP POLICY IF EXISTS tenant_delete  ON %I', tbl);

        -- SELECT — only rows for the current tenant OR staff bypass
        EXECUTE format(
            'CREATE POLICY tenant_select ON %I FOR SELECT USING (tenant_id = current_tenant_id() OR is_staff() OR is_superuser() OR system_bypass())',
            tbl
        );

        -- INSERT — tenant_id must match OR system bypass
        EXECUTE format(
            'CREATE POLICY tenant_insert ON %I FOR INSERT WITH CHECK (tenant_id = current_tenant_id() OR is_staff() OR is_superuser() OR system_bypass())',
            tbl
        );

        -- UPDATE — restrict to current tenant's rows OR staff bypass
        EXECUTE format(
            'CREATE POLICY tenant_update ON %I FOR UPDATE USING (tenant_id = current_tenant_id() OR is_staff() OR is_superuser() OR system_bypass())',
            tbl
        );

        -- DELETE — restrict to current tenant's rows OR staff bypass
        EXECUTE format(
            'CREATE POLICY tenant_delete ON %I FOR DELETE USING (tenant_id = current_tenant_id() OR is_staff() OR is_superuser() OR system_bypass())',
            tbl
        );

        RAISE NOTICE 'RLS enabled on %', tbl;
    END LOOP;
END
$$;
