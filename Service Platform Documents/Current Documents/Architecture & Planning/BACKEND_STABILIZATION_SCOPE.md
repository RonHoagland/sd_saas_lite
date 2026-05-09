# Service03 Backend Stabilization Scope

This file documents what is intentionally in scope for the current security hardening phase and what is explicitly deferred.

## In scope now

- Staff vs tenant access boundaries in admin/service backend paths.
- Tenant middleware correctness for tenant-scoped requests.
- Role-scoped staff write permissions and enforcement checks.
- Audit trail coverage for staff cross-tenant write/delete interventions.
- PostgreSQL-backed test coverage for the above.

## Explicitly out of scope now

- New business features.
- Expanding internal API endpoint surface beyond current placeholder wiring.
- Redesigning the staff/tenant identity model.

## Internal API note

`/internal/api/v1/` is intentionally mounted with middleware protection while endpoint implementations remain deferred to a dedicated internal API definition/build phase.
