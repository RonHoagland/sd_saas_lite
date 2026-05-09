# ServizDesk Lifecycle Framework Specification V1

**Date:** March 2026
**Scope:** SDTA — Data-Driven State Machine for Entity Lifecycles
**Status:** Working Draft
**Adapted From:** Desktop Version `lifecycle/` module
**Cross-References:** System Status Specification V3, Data Models V6, Database Specification V2

---

## 1. Overview

This specification defines a generic, data-driven lifecycle framework that enforces valid status transitions for all major entities in SDTA. Rather than relying on application code to validate state changes, the framework uses database records to define which states exist, which transitions are allowed, and what permissions or justifications are required. Every transition is logged to an immutable audit trail.

The framework is **tenant-scoped** — each tenant inherits a system-default set of states and transitions (seeded from System Status V3), and Pro/Enterprise tiers may customize states and transitions for their business processes.

---

## 2. Architecture

### 2.1 Three-Model Pattern

The framework consists of three models:

1. **LifecycleStateDef** — Registers allowed states per entity type
2. **LifecycleTransitionRule** — Defines which state-to-state transitions are permitted
3. **LifecycleTransitionAudit** — Immutable log of every executed transition

### 2.2 Design Principles

- **Deny by default.** If a transition is not explicitly defined in LifecycleTransitionRule, it is denied.
- **Self-transitions are blocked.** A record cannot transition from a state to the same state.
- **Final states have no outbound transitions.** Once an entity reaches a final state (e.g., `Closed`, `Void`), no further transitions are allowed without an administrative override.
- **Locked states block record edits.** When an entity is in a locked state (e.g., `Issued` for invoices), the entity record is read-only. Only the status field can change (via a valid transition).
- **Immutable audit.** LifecycleTransitionAudit records cannot be modified or deleted.

### 2.3 Relationship to System Status V3

System Status V3 defines the **business rules** for each entity's lifecycle (which statuses exist, what transitions are valid, what triggers them). This specification defines the **technical framework** that enforces those rules. The states and transitions from System Status V3 are seeded as LifecycleStateDef and LifecycleTransitionRule records during tenant provisioning.

---

## 3. Data Models

### 3.1 `LifecycleStateDef`

Registers an allowed lifecycle state for an entity type within a tenant.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → TenantState | |
| `entity_type` | CharField(50) | Machine key identifying the entity. Must match one of the registered entity types defined in System Status V3. Full list: `customer`, `quote`, `work_order`, `invoice`, `payment`, `purchase_order`, `vendor_bill`, `asset`, `service_request`, `lead`, `opportunity`, `agreement`, `customer_agreement`, `preventative_maintenance`, `work_group`, `requisition`, `rma`, `workflow`, `safety_form`, `equipment`, `vehicle`, `vehicle_maintenance`, `employee`, `inventory_item`, `vendor`, `communication_template`, `communication_trigger`, `pricebook_entry`, `wg_division`, `task` |
| `state_name` | CharField(50) | Machine-readable state value stored on the entity record (e.g., `ACTIVE`, `DRAFT`, `IN_PROGRESS`). Must match the TextChoices value on the entity model. |
| `state_label` | CharField(100) | Human-readable display label (e.g., `Active`, `Draft`, `In Progress`) |
| `state_type` | Enum | `normal` — Standard operating state. `locked` — Entity record becomes read-only while in this state (only status field can change via valid transition). `final` — Terminal state; no outbound transitions allowed (except admin override). |
| `is_default` | BooleanField | If True, this is the initial state for new records of this entity type. Exactly one default per (tenant_id, entity_type) pair — enforced via save() logic. |
| `sort_order` | IntegerField | Display ordering in dropdowns and status selectors. |
| `description` | TextField | Documentation about this state and when it applies. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

**Constraints:**

- `UNIQUE (tenant_id, entity_type, state_name)` — No duplicate states per entity per tenant.
- Single `is_default = True` per `(tenant_id, entity_type)` — Enforced in save() method.

**Indexes:**

- `(tenant_id, entity_type)`
- `(tenant_id, entity_type, is_default)`

---

### 3.2 `LifecycleTransitionRule`

Defines an allowed state-to-state transition for an entity type within a tenant.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → TenantState | |
| `entity_type` | CharField(50) | Must match a registered entity_type in LifecycleStateDef. |
| `from_state` | CharField(50) | Starting state. Must match a state_name in LifecycleStateDef for this (tenant_id, entity_type). |
| `to_state` | CharField(50) | Destination state. Must match a state_name in LifecycleStateDef for this (tenant_id, entity_type). |
| `required_role` | CharField(100), blank | If set, the user must hold this role to execute the transition (e.g., `administrator`). Empty means any authenticated user can execute it. |
| `requires_reason` | BooleanField | If True, the transition must include a reason text. Maps to System Status V3 rules like "Requires a `hold_reason`" or "Admin override requires a `reason`." |
| `is_admin_override` | BooleanField | If True, this transition represents an admin override path (e.g., unlocking a Completed Work Order back to In Progress). Default False. |
| `description` | TextField | Documentation about when this transition is valid and any business context. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

**Constraints:**

- `UNIQUE (tenant_id, entity_type, from_state, to_state)` — No duplicate transition rules.
- `CHECK (from_state != to_state)` — Self-transitions are not permitted.

**Indexes:**

- `(tenant_id, entity_type)`
- `(tenant_id, entity_type, from_state)`

**Validation (clean method):**

- `from_state` must exist as a state_name in LifecycleStateDef for this (tenant_id, entity_type).
- `to_state` must exist as a state_name in LifecycleStateDef for this (tenant_id, entity_type).
- `from_state` must not be a `final` state_type (unless `is_admin_override = True`).

---

### 3.3 `LifecycleTransitionAudit`

Immutable audit record created for every executed state transition.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID | Not an FK — preserved even if tenant is deleted. |
| `timestamp` | DateTimeField | auto_now_add, editable=False. When the transition occurred. |
| `user_id` | UUID | The user who performed the transition. Not an FK — preserved after user deletion. |
| `user_display` | CharField(200) | Snapshot of user email/name at time of transition (denormalized for display without joins). |
| `entity_type` | CharField(50) | Type of entity that changed state. |
| `entity_id` | UUID | ID of the entity that changed state. |
| `from_state` | CharField(50) | Previous state. |
| `to_state` | CharField(50) | New state. |
| `reason` | TextField, blank | Justification for the transition (required when `requires_reason = True` on the rule). |
| `is_override` | BooleanField | Whether this was an administrative override transition. |
| `ip_address` | GenericIPAddressField, nullable | Client IP address at the time of transition. |

**Immutability Enforcement:**

- `save()` raises `ValidationError` if `self.pk is not None` (prevents updates).
- `delete()` raises `ValidationError` (prevents deletion).
- `Meta.permissions = []` (no Django admin change/delete permissions).

**Indexes:**

- `(tenant_id, entity_type, entity_id)` — Look up transition history for a specific record.
- `(tenant_id, entity_type)` — Look up all transitions for an entity type.
- `(tenant_id, timestamp)` — Chronological audit trail per tenant.
- `(user_id)` — Look up all transitions by a specific user.

---

## 4. Service Layer

### 4.1 `execute_transition(entity, to_state, user, reason="", ip_address=None)`

This is the primary function that all status changes must go through. No entity should change its status field directly — all changes must call `execute_transition`.

**Steps:**

1. **Read current state** from entity's status field.
2. **Look up LifecycleTransitionRule** for `(tenant_id, entity_type, from_state=current, to_state=target)`.
3. **If no rule exists → deny.** Raise `TransitionDeniedError`.
4. **Check role requirement.** If `required_role` is set, verify the user holds that role. Raise `PermissionDeniedError` if not.
5. **Check reason requirement.** If `requires_reason = True` and reason is empty, raise `ReasonRequiredError`.
6. **Update entity status** to `to_state`. Save entity.
7. **Create LifecycleTransitionAudit** record with all context (user, timestamp, from/to states, reason, override flag, IP).
8. **Return** the audit record.

### 4.2 `get_available_transitions(entity, user)`

Returns the list of valid next states for an entity given the current user's role.

**Steps:**

1. Read current state from entity.
2. Query LifecycleTransitionRule for all rules where `(tenant_id, entity_type, from_state=current)`.
3. Filter by user's role (include rules where `required_role` is blank or matches the user's role).
4. Return list of `(to_state, state_label, requires_reason, is_admin_override)` tuples.

### 4.3 `get_transition_history(entity_type, entity_id, tenant_id)`

Returns the chronological list of LifecycleTransitionAudit records for a specific entity.

### 4.4 Exceptions

| Exception | When Raised |
|---|---|
| `TransitionDeniedError` | No LifecycleTransitionRule exists for this from_state → to_state. |
| `PermissionDeniedError` | User lacks the required_role for this transition. |
| `ReasonRequiredError` | Transition requires a reason but none was provided. |
| `FinalStateError` | Attempting to transition out of a final state without an admin override rule. |

---

## 5. Seed Data

During tenant provisioning, the following states and transitions are seeded from System Status V3. This is a representative subset — the full list covers all entity types defined in System Status V3.

### 5.1 Customer Lifecycle (System Status V3 Section 2)

**States:**

| state_name | state_label | state_type | is_default |
|---|---|---|---|
| `ACTIVE` | Active | normal | Yes |
| `INACTIVE` | Inactive | normal | No |
| `HOLD` | Hold | locked | No |
| `CLOSED` | Closed | final | No |

**Transitions:**

| from_state | to_state | required_role | requires_reason | is_admin_override |
|---|---|---|---|---|
| `ACTIVE` | `INACTIVE` | administrator | No | No |
| `INACTIVE` | `ACTIVE` | administrator | No | No |
| `ACTIVE` | `HOLD` | administrator | Yes (hold_reason) | No |
| `HOLD` | `ACTIVE` | administrator | Yes (release_reason) | No |
| `ACTIVE` | `CLOSED` | administrator | Yes (closed_reason) | No |
| `INACTIVE` | `CLOSED` | administrator | Yes (closed_reason) | No |

### 5.2 Work Order Lifecycle (System Status V3 Section 4)

**States:**

| state_name | state_label | state_type | is_default |
|---|---|---|---|
| `DRAFT` | Draft | normal | Yes |
| `SCHEDULED` | Scheduled | normal | No |
| `IN_PROGRESS` | In Progress | normal | No |
| `ON_HOLD` | On Hold | locked | No |
| `COMPLETED` | Completed | locked | No |
| `CLOSED` | Closed | locked | No |
| `CANCELLED` | Cancelled | final | No |

**Transitions:**

| from_state | to_state | required_role | requires_reason | is_admin_override |
|---|---|---|---|---|
| `DRAFT` | `SCHEDULED` | | No | No |
| `SCHEDULED` | `IN_PROGRESS` | | No | No |
| `IN_PROGRESS` | `ON_HOLD` | | Yes | No |
| `ON_HOLD` | `IN_PROGRESS` | | Yes | No |
| `IN_PROGRESS` | `COMPLETED` | | No | No |
| `COMPLETED` | `CLOSED` | | No | No |
| `DRAFT` | `CANCELLED` | | Yes | No |
| `SCHEDULED` | `CANCELLED` | | Yes | No |
| `COMPLETED` | `IN_PROGRESS` | administrator | Yes | Yes |
| `CLOSED` | `IN_PROGRESS` | administrator | Yes | Yes |

### 5.3 Invoice Lifecycle (System Status V3 Section 5.1)

**States:**

| state_name | state_label | state_type | is_default |
|---|---|---|---|
| `DRAFT` | Draft | normal | Yes |
| `ISSUED` | Issued | locked | No |
| `VIEWED` | Viewed | locked | No |
| `PARTIALLY_PAID` | Partially Paid | locked | No |
| `PAID` | Paid | final | No |
| `OVERDUE` | Overdue | locked | No |
| `VOID` | Void | final | No |
| `WRITTEN_OFF` | Written Off | final | No |

> **Note:** The remaining entity lifecycles follow the same pattern — each is derived from System Status V3 and loaded during provisioning. The full list of entity lifecycles seeded per tenant is:
>
> **Core (All Tiers):** Customer (§2), Quote (§3), Work Order (§4), Invoice (§5.1), Payment (§5.2), Asset (§8), Service Request (§9), Task (implied from Work Order), Employee (§18), InventoryItem (§19)
>
> **Plus+:** Purchase Order (§6.1), PO Line Item (§6.2), Vendor Bill (§7), Lead (§10.1), Opportunity (§10.2), Agreement (§11.1), CustomerAgreement (§11.3), PreventativeMaintenance (§11.2), WorkGroup (§12), Requisition (§13), RMA (§14), Vendor (§20)
>
> **Pro/Enterprise:** WorkFlow (§15.1), SafetyForm (§15.2), Equipment (§16), Communication Template (§21), Communication Trigger (§22), PricebookEntry (§23), WGDivision (§24)
>
> **Fleet Add-On:** Vehicle (§17.1), VehicleMaintenance (§17.2)
>
> The provisioning flow reads each entity's status definitions and transition rules from System Status V3, maps `state_type` based on locking and finality rules (locked statuses → `locked`, terminal statuses → `final`, others → `normal`), and creates LifecycleStateDef and LifecycleTransitionRule records within the atomic provisioning transaction.

---

## 6. Integration with Existing Models

### 6.1 Entity Model Changes

No changes to existing entity models are required. Each entity already has a `status` CharField with TextChoices. The lifecycle framework reads and writes this field via `execute_transition()`. The TextChoices values must match the `state_name` values in LifecycleStateDef.

### 6.2 Where Transitions Are Called

All status changes must go through `execute_transition()`. This includes:

- **View layer** — When a user changes status via the UI (HTMX form submission).
- **Background tasks** — When Celery tasks change status (e.g., `manage_trial_lifecycle`, auto-expiration of quotes).
- **Internal API** — When SDP pushes status changes via `/internal/api/v1/update-account-status/`.
- **Admin** — When staff change status via the Django admin (TenantModelAdmin).

### 6.3 Admin Interface

LifecycleStateDef and LifecycleTransitionRule are registered in the staff admin via TenantModelAdmin. Staff can view all tenants' state configurations.

For Lite tier, states and transitions are system-managed and read-only.

For Pro/Enterprise tier (future), tenants may customize states and transitions via the SDTA admin area.

LifecycleTransitionAudit is read-only in all cases — no edit or delete actions are exposed.

---

## 7. Multi-Tenancy

### 7.1 Model Inheritance

- LifecycleStateDef extends TenantModel (filtered by tenant_id via TenantManager).
- LifecycleTransitionRule extends TenantModel.
- LifecycleTransitionAudit extends TenantModel but with immutability enforcement (no update/delete).

### 7.2 RLS

All three models are protected by PostgreSQL Row-Level Security per the standard `app.current_tenant_id` pattern. The `setup_rls.sql` script must include policies for these tables.

### 7.3 Worker Alias

Staff admin uses the `'worker'` Django database alias (which connects as the `sdta_migration` PostgreSQL role with BYPASSRLS) to view lifecycle configurations across tenants. See Database Specification V2 Section 3 for alias configuration.

---

## 8. Governance Rules

1. All entity status changes must go through `execute_transition()`. Direct status field updates are prohibited.
2. If no LifecycleTransitionRule exists for a from_state → to_state pair, the transition is denied.
3. Self-transitions (same from and to state) are blocked at the database level.
4. Final states have no outbound transitions unless an `is_admin_override = True` rule exists.
5. Locked states make the entity record read-only (except status field changes via valid transitions).
6. LifecycleTransitionAudit records are immutable — they cannot be updated or deleted.
7. Every successful transition generates exactly one audit record.
8. Seed data is loaded during tenant provisioning and matches System Status V3.
9. Lite tier: States and transitions are system-managed. Tenants cannot add, remove, or modify them.
10. Pro/Enterprise tier (future): Tenants may customize states and transitions within guard rails.

---

## 9. Cross-References

| Topic | Document |
|---|---|
| Entity status definitions and business rules | ServizDesk System Status Specification V3 |
| Entity field definitions | ServizDesk Data Models V6 |
| Multi-tenancy and RLS | ServizDesk Multi-Tenancy Specification V1 |
| Database roles (`'worker'` alias, `sdta_migration` role) | ServizDesk Database Specification V2, Sections 3–4 |
| Background task status changes (must use `execute_transition()`) | ServizDesk Background Tasks Specification V2 |
| Internal API status changes | ServizDesk Platform (SDP) Specification V2, Section 4 |
| Seed data provisioning flow | ServizDesk Tenant Provisioning Seed Data V2 |
| Tier-based entity availability | ServizDesk Product Tier Map V2 |
