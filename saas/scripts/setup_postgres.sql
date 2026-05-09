-- =============================================================================
-- ServizDesk SDTA — PostgreSQL setup script
-- =============================================================================
-- Run this ONCE as a PostgreSQL superuser (e.g. postgres) against the SDTA
-- database server. Passwords MUST be supplied via psql variables — no
-- credentials are committed to source.
--
-- Required variables:
--   sdta_app_password       — runtime/RLS-bound role
--   sdta_migration_password — migrations + Django admin (BYPASSRLS, CREATEDB)
--   sdta_support_password   — vault-locked support role (BYPASSRLS)
--
-- Optional variables:
--   sdta_readonly_password  — reporting/analytics (SELECT only). When omitted,
--                             the role is not created.
--
-- Recommended invocation (passwords sourced from your secrets store):
--
--   psql -h 127.0.0.1 -U postgres \
--        -v sdta_app_password="$SDTA_APP_PASSWORD" \
--        -v sdta_migration_password="$SDTA_MIGRATION_PASSWORD" \
--        -v sdta_support_password="$SDTA_SUPPORT_PASSWORD" \
--        -v sdta_readonly_password="$SDTA_READONLY_PASSWORD" \
--        -f scripts/setup_postgres.sql
--
-- After running this script, create the database (cannot run in a transaction):
--   createdb -h 127.0.0.1 -U postgres -O sdta_migration servizdesk_sdta
--
-- Then run Django migrations (they connect as sdta_migration via the worker
-- DB alias):
--   python manage.py migrate --database=worker
--
-- Then apply RLS policies:
--   psql -h 127.0.0.1 -U sdta_migration -d servizdesk_sdta -f scripts/setup_rls.sql
--
-- Per Database Specification V2 §4 the four roles map as:
--   sdta_app       LOGIN, RLS-bound        — every web request
--   sdta_migration LOGIN, BYPASSRLS        — schema migrations, Django admin,
--                                            background tasks needing cross-tenant reads
--   sdta_support   LOGIN, BYPASSRLS        — break-glass support; checked out
--                                            of a vault per incident, rotated after
--   sdta_readonly  LOGIN, RLS-bound        — read-only reporting; reserved use
--
-- Implementation note: psql variable substitution (`:'var'`) is suppressed
-- inside dollar-quoted blocks. We therefore create the roles in DO blocks
-- without a password, then set/rotate passwords with plain ALTER ROLE
-- statements where `:'var'` substitutes correctly.
-- =============================================================================

-- Fail loud if required variables are missing. ON_ERROR_STOP makes psql exit
-- non-zero on the first error so callers (CI, ops scripts) notice immediately.
\set ON_ERROR_STOP on

\if :{?sdta_app_password}
\else
    \echo 'ERROR: -v sdta_app_password=... is required.'
    \quit
\endif

\if :{?sdta_migration_password}
\else
    \echo 'ERROR: -v sdta_migration_password=... is required.'
    \quit
\endif

\if :{?sdta_support_password}
\else
    \echo 'ERROR: -v sdta_support_password=... is required.'
    \quit
\endif


-- ─── Roles ────────────────────────────────────────────────────────────────────
--
-- Create roles idempotently (no password inside the DO block — substitution
-- is suppressed there). Passwords are set in the ALTER ROLE block below.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_migration') THEN
        CREATE ROLE sdta_migration LOGIN BYPASSRLS CREATEDB;
        RAISE NOTICE 'Role sdta_migration created.';
    ELSE
        ALTER ROLE sdta_migration WITH LOGIN BYPASSRLS CREATEDB;
        RAISE NOTICE 'Role sdta_migration already existed — flags reset.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_app') THEN
        CREATE ROLE sdta_app LOGIN;
        RAISE NOTICE 'Role sdta_app created.';
    ELSE
        ALTER ROLE sdta_app WITH LOGIN NOBYPASSRLS;
        RAISE NOTICE 'Role sdta_app already existed — flags reset.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_support') THEN
        CREATE ROLE sdta_support LOGIN BYPASSRLS NOINHERIT;
        RAISE NOTICE 'Role sdta_support created.';
    ELSE
        ALTER ROLE sdta_support WITH LOGIN BYPASSRLS NOINHERIT;
        RAISE NOTICE 'Role sdta_support already existed — flags reset.';
    END IF;
END
$$;

-- Optional readonly role.
\if :{?sdta_readonly_password}
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sdta_readonly') THEN
        CREATE ROLE sdta_readonly LOGIN;
        RAISE NOTICE 'Role sdta_readonly created.';
    ELSE
        ALTER ROLE sdta_readonly WITH LOGIN NOBYPASSRLS;
        RAISE NOTICE 'Role sdta_readonly already existed — flags reset.';
    END IF;
END
$$;
\else
\echo 'sdta_readonly_password not set — sdta_readonly role skipped (optional).'
\endif


-- ─── Set/rotate passwords ────────────────────────────────────────────────────
--
-- Plain ALTER ROLE statements outside any dollar-quoted block, so psql
-- variable substitution (`:'var'`) works as a quoted SQL literal.

ALTER ROLE sdta_migration WITH ENCRYPTED PASSWORD :'sdta_migration_password';
ALTER ROLE sdta_app       WITH ENCRYPTED PASSWORD :'sdta_app_password';
ALTER ROLE sdta_support   WITH ENCRYPTED PASSWORD :'sdta_support_password';

\if :{?sdta_readonly_password}
ALTER ROLE sdta_readonly  WITH ENCRYPTED PASSWORD :'sdta_readonly_password';
\endif


-- ─── Database existence check ────────────────────────────────────────────────
--
-- CREATE DATABASE cannot run inside a transaction block. The script only
-- reports whether the DB exists and reminds the operator of the createdb
-- command if it does not.

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'servizdesk_sdta') THEN
        RAISE NOTICE 'Database servizdesk_sdta does not exist. Create it with:';
        RAISE NOTICE '  createdb -h 127.0.0.1 -U postgres -O sdta_migration servizdesk_sdta';
        RAISE NOTICE 'Then re-run this script with -d servizdesk_sdta to apply schema grants.';
    ELSE
        RAISE NOTICE 'Database servizdesk_sdta exists — proceeding with schema grants.';
    END IF;
END
$$;


-- =============================================================================
-- Schema grants — must run connected TO servizdesk_sdta.
-- The \c below switches the connection. If the database does not yet exist,
-- the script will stop here (per ON_ERROR_STOP).
-- =============================================================================

\c servizdesk_sdta


-- ─── sdta_app: full CRUD, RLS-bound ──────────────────────────────────────────

GRANT USAGE ON SCHEMA public TO sdta_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdta_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sdta_app;

ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdta_app;
ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sdta_app;


-- ─── sdta_migration: full ownership ──────────────────────────────────────────

GRANT ALL PRIVILEGES ON SCHEMA public TO sdta_migration;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sdta_migration;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sdta_migration;


-- ─── sdta_support: full CRUD, BYPASSRLS ──────────────────────────────────────

GRANT USAGE ON SCHEMA public TO sdta_support;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sdta_support;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sdta_support;

ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sdta_support;
ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO sdta_support;


-- ─── sdta_readonly: SELECT only, RLS-bound ───────────────────────────────────

\if :{?sdta_readonly_password}
GRANT USAGE ON SCHEMA public TO sdta_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sdta_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO sdta_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT SELECT ON TABLES TO sdta_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE sdta_migration IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO sdta_readonly;
\endif


-- ─── Search path ──────────────────────────────────────────────────────────────

ALTER ROLE sdta_app       SET search_path TO public;
ALTER ROLE sdta_migration SET search_path TO public;
ALTER ROLE sdta_support   SET search_path TO public;

\if :{?sdta_readonly_password}
ALTER ROLE sdta_readonly  SET search_path TO public;
\endif


\echo 'Setup complete. Apply RLS policies next with scripts/setup_rls.sql.'
