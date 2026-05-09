-- =============================================================================
-- ServizDesk SDTA — PostgreSQL setup script
-- =============================================================================
-- Run this ONCE as a PostgreSQL superuser (e.g. djangouser or postgres) against
-- the same PostgreSQL instance that service01 uses:
--
--   psql -U djangouser -h 127.0.0.1 -f scripts/setup_postgres.sql
--
-- What this script does:
--   1. Creates two application roles: sdta_app (RLS-bound) and sdta_migration
--      (BYPASSRLS — used by Django admin and background tasks).
--   2. Creates the servizdesk_sdta database owned by sdta_migration.
--   3. Grants the minimum privileges each role needs.
--   4. Adds a search_path so both roles find the public schema automatically.
--
-- After running this script, run Django migrations:
--   python manage.py migrate --database=worker
--
-- Then apply RLS policies:
--   psql -U djangouser -h 127.0.0.1 -d servizdesk_sdta \
--        -f scripts/setup_rls.sql
-- =============================================================================


-- ─── Roles ────────────────────────────────────────────────────────────────────

-- sdta_migration: superuser-lite for schema migrations and staff admin access.
-- BYPASSRLS means PostgreSQL Row-Level Security policies do not apply to it.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_migration') THEN
        CREATE ROLE sdta_migration
            LOGIN
            PASSWORD 'buddA123'
            BYPASSRLS
            CREATEDB;          -- needs CREATEDB to create/drop the test database
        RAISE NOTICE 'Role sdta_migration created.';
    ELSE
        RAISE NOTICE 'Role sdta_migration already exists — skipping.';
    END IF;
END
$$;

-- sdta_app: normal application user.  RLS policies filter rows to the current
-- tenant (set via SET app.current_tenant_id = '<uuid>' in the connection).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_app') THEN
        CREATE ROLE sdta_app
            LOGIN
            PASSWORD 'buddA123';
        RAISE NOTICE 'Role sdta_app created.';
    ELSE
        RAISE NOTICE 'Role sdta_app already exists — skipping.';
    END IF;
END
$$;


-- ─── Database ─────────────────────────────────────────────────────────────────

-- Create the database owned by sdta_migration (allows it to manage objects).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'servizdesk_sdta') THEN
        -- Cannot run CREATE DATABASE inside a transaction block; executed via
        -- a separate connection in the shell wrapper below if needed.
        RAISE NOTICE 'Database servizdesk_sdta does not exist — create it manually:';
        RAISE NOTICE '  createdb -U djangouser -O sdta_migration servizdesk_sdta';
    ELSE
        RAISE NOTICE 'Database servizdesk_sdta already exists — skipping.';
    END IF;
END
$$;


-- =============================================================================
-- Run the rest of this script connected TO servizdesk_sdta
-- (\c servizdesk_sdta  in psql, or pass -d servizdesk_sdta on the CLI)
-- =============================================================================

\c servizdesk_sdta


-- ─── Schema & Sequence Privileges for sdta_app ───────────────────────────────

-- Full CRUD on all existing tables.
GRANT USAGE ON SCHEMA public TO sdta_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdta_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sdta_app;

-- Full CRUD on tables created in the future (by migrations via sdta_migration).
ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdta_app;

ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sdta_app;


-- ─── Schema & Sequence Privileges for sdta_migration ─────────────────────────

GRANT ALL PRIVILEGES ON SCHEMA public TO sdta_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdta_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdta_migration;


-- ─── Search path ──────────────────────────────────────────────────────────────

ALTER ROLE sdta_app       SET search_path TO public;
ALTER ROLE sdta_migration SET search_path TO public;
