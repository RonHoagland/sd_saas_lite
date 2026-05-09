# ServizDesk Numbering Service Specification V1

**Date:** March 2026
**Scope:** SDTA — Human-Readable Number Generation & Assignment
**Status:** Working Draft
**Adapted From:** Desktop Version `numbering/` module
**Replaces:** SequenceTracker model in Data Models V6 Section 1.9
**Cross-References:** Data Models V6, TenantPreference (numbering prefix/start fields), Database Specification V2

---

## 1. Overview

This specification defines the numbering service that generates human-readable, collision-free numbers for all numbered entities in SDTA (Customer, Asset, Work Order, Quote, Invoice, Payment, Task, InventoryItem, Employee, Service Request, Vendor, Purchase Order, and others). The full list of numbered entity types is defined in Section 6.1 and matches the entity types seeded in Tenant Provisioning Seed Data V2 Section 5.

The current implementation uses a minimal `SequenceTracker` model (Data Models V6 Section 1.9) with a `last_value` counter. This specification replaces SequenceTracker with a richer system that adds configurable formatting, yearly/monthly reset, atomic concurrency-safe generation, and an immutable assignment audit trail.

---

## 2. Architecture

### 2.1 Three-Model Pattern

1. **NumberingRule** — Defines how numbers are formatted for each entity type (prefix, year inclusion, delimiter, padding, reset behavior).
2. **NumberSequence** — Atomic sequence counter for each rule (the current value and last reset date).
3. **AssignedNumber** — Immutable record of every number assigned to a specific entity instance.

### 2.2 Design Principles

- **Collision-free.** Sequence values are incremented atomically using `SELECT FOR UPDATE` database locking. No two concurrent requests can receive the same number.
- **Deterministic.** Given a rule configuration and sequence value, the resulting number is always the same.
- **Immutable assignment.** Once a number is assigned to an entity, it cannot be changed, reused, or deleted.
- **Tenant-scoped.** Each tenant has its own set of rules, sequences, and assignments. Numbers are unique within a tenant, not globally.
- **Configurable (tier-gated).** Administrators can customize prefixes, delimiters, year format, and reset behavior via TenantPreference (which seeds the NumberingRule on provisioning). **This customization is Plus+ only.** On **Lite**, tenants receive the system defaults seeded at provisioning and do not have UI access to edit prefixes or other numbering settings. The underlying TenantPreference fields and NumberingRule records still exist for Lite tenants, but they are admin-read-only in the Lite Company Settings UI. See `Architecture & Planning/LITE_DECISIONS.md` §B for rationale.

---

## 3. Data Models

### 3.1 `NumberingRule`

Defines the formatting and behavior for number generation of a specific entity type within a tenant. One rule per (tenant_id, entity_type).

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → TenantState | |
| `entity_type` | CharField(50) | Machine key identifying the numbered entity. Must match one of the registered entity types in the seed data table (Section 6.1). Examples: `customer`, `work_order`, `invoice`, `inventory_item`. |
| `is_enabled` | BooleanField | Default True. If False, `generate_number()` raises `NumberingDisabledError`. |
| `prefix` | CharField(20) | Prefix string (e.g., `C`, `W`, `I`, `SR`, `YU`). Sourced from TenantPreference on provisioning. For most entities this is static; for `inventory_item` it is dynamically computed using the reverse-alphabet year encoding (see Section 6.1). |
| `include_year` | BooleanField | Default True. Whether to include the year component in the number. |
| `year_format` | Enum | `YY` (2-digit, e.g., `26`) or `YYYY` (4-digit, e.g., `2026`). Default `YY`. Only applies if `include_year = True`. |
| `include_month` | BooleanField | Default False. Whether to include the 2-digit month (`MM`) in the number. |
| `sequence_length` | PositiveIntegerField | Default 4. Number of digits in the sequence portion (zero-padded). A value of 4 produces `0001`, `0042`, `9999`. |
| `delimiter` | CharField(5) | Default `-`. Character(s) separating format components (e.g., `WO-26-0001`). |
| `reset_behavior` | Enum | `none` — Never reset. `yearly` — Reset to 0 on January 1. `monthly` — Reset to 0 on the 1st of each month. Default `yearly`. |
| `description` | TextField, blank | Documentation about this rule. |
| `created_by` | CharField | |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | |
| `updated_on` | DateTimeField | |

**Constraints:**

- `UNIQUE (tenant_id, entity_type)` — One rule per entity type per tenant.

**Indexes:**

- `(tenant_id, entity_type)`
- `(tenant_id, is_enabled)`

---

### 3.2 `NumberSequence`

Atomic sequence counter for a NumberingRule. One sequence per rule. This is the counter that gets incremented on every number generation.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `rule` | OneToOneField FK → NumberingRule | CASCADE on delete. Each rule has exactly one sequence. |
| `current_value` | PositiveIntegerField | Default 0. Incremented atomically via `SELECT FOR UPDATE`. |
| `last_reset_date` | DateField, nullable | Tracks when the sequence was last reset. Used by `check_reset_needed()`. |

**No tenant_id field.** Tenant scoping is inherited through the FK to NumberingRule.

**No audit fields.** This is an internal counter, not a user-facing record.

**No permissions.** Internal use only — `Meta.permissions = []`.

---

### 3.3 `AssignedNumber`

Immutable record of a number assigned to a specific entity instance. Created by `assign_number()` and never modified or deleted.

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → TenantState | |
| `rule` | FK → NumberingRule | PROTECT on delete (cannot delete a rule that has assigned numbers). |
| `entity_type` | CharField(50) | Denormalized from rule for query convenience. |
| `entity_id` | UUID | ID of the entity that received this number. |
| `number` | CharField(100) | The generated human-readable number (e.g., `W-26-0042`). Immutable. |
| `assigned_at` | DateTimeField | auto_now_add, editable=False. When the number was assigned. |
| `assigned_by` | CharField(200) | User email or `System` for background task assignments. Not an FK — survives user deletion. |

**Constraints:**

- `UNIQUE (tenant_id, entity_type, number)` — No duplicate numbers per entity type per tenant.
- `UNIQUE (tenant_id, entity_type, entity_id)` — Each entity instance gets exactly one number.

**Indexes:**

- `(tenant_id, entity_type)`
- `(tenant_id, entity_id)`
- `(tenant_id, number)`
- `(assigned_at)`

**Immutability Enforcement:**

- `save()` raises `ValidationError` if `self.pk is not None` (prevents updates).
- `delete()` raises `ValidationError` (prevents deletion).

---

## 4. Service Layer

### 4.1 `generate_number(tenant_id, entity_type, user_display="System")`

Generates a new formatted number for an entity type. Does NOT create an AssignedNumber record — that happens in `assign_number()`.

**Steps:**

1. Look up NumberingRule for `(tenant_id, entity_type)`. Raise `NoRuleDefinedError` if not found.
2. Check `is_enabled`. Raise `NumberingDisabledError` if False.
3. Call `get_next_sequence_value(rule)` to atomically increment the sequence.
4. Call `format_number(rule, sequence_value)` to produce the formatted string.
5. Return the formatted number string.

### 4.2 `get_next_sequence_value(rule)`

Atomically increments the sequence counter using database-level locking.

**Steps:**

1. Get or create the NumberSequence for this rule.
2. Call `check_reset_needed(sequence)` to handle yearly/monthly resets.
3. Within `transaction.atomic()`:
   a. `SELECT FOR UPDATE` on the NumberSequence row (locks it from concurrent access).
   b. Double-check reset after lock (another thread may have reset between steps 2-3).
   c. Increment `current_value` by 1.
   d. Save and return the new value.

### 4.3 `check_reset_needed(sequence)`

Checks whether the sequence should be reset based on the rule's `reset_behavior` and the current date.

| reset_behavior | Reset Condition |
|---|---|
| `none` | Never reset. |
| `yearly` | Reset if `last_reset_date` is null or `last_reset_date.year != current_year`. |
| `monthly` | Reset if `last_reset_date` is null or month/year has changed since `last_reset_date`. |

When reset occurs: set `current_value = 0` and `last_reset_date = today`.

### 4.4 `format_number(rule, sequence_value)`

Formats the number according to the rule definition.

**Format pattern:** `{prefix}{delimiter}{year}{delimiter}{month}{delimiter}{sequence}`

Components are only included if configured. Examples:

| Configuration | Result |
|---|---|
| prefix=`W`, include_year=True, year_format=`YY`, sequence_length=4 | `W-26-0001` |
| prefix=`I`, include_year=True, year_format=`YYYY`, include_month=True, sequence_length=5 | `I-2026-03-00001` |
| prefix=`C`, include_year=True, year_format=`YY`, sequence_length=4 | `C-26-0001` |
| prefix=`SR`, include_year=True, year_format=`YY`, sequence_length=4 | `SR-26-0001` |
| prefix=`YU` *(2026 encoding)*, include_year=False, sequence_length=4 | `YU-0001` |

### 4.5 `assign_number(tenant_id, entity_type, entity_id, user_display="System")`

Generates a number and creates an immutable AssignedNumber record.

**Steps:**

1. Check if entity already has an assigned number. Raise `DuplicateAssignmentError` if so.
2. Call `generate_number()` to get the formatted number.
3. Create AssignedNumber record with all context.
4. Return the AssignedNumber instance.

### 4.6 `get_assigned_number(tenant_id, entity_type, entity_id)`

Returns the assigned number string for an entity, or `None` if not yet assigned.

### 4.7 `has_assigned_number(tenant_id, entity_type, entity_id)`

Returns Boolean indicating whether an entity has an assigned number.

### 4.8 Exceptions

| Exception | When Raised |
|---|---|
| `NumberingError` | Base exception for all numbering errors. |
| `NoRuleDefinedError` | No NumberingRule exists for this (tenant_id, entity_type). |
| `NumberingDisabledError` | NumberingRule exists but `is_enabled = False`. |
| `DuplicateAssignmentError` | Entity already has an assigned number. |
| `SequenceError` | Database error during atomic sequence increment. |

---

## 5. Integration with Entity Models

### 5.1 NumberingMixin

A Python mixin class that provides convenience methods on entity models.

```
class NumberingMixin:
    numbering_entity_type = None  # Subclass must set (e.g., 'work_order')

    def assign_number(self, user_display):
        return assign_number(self.tenant_id, self.numbering_entity_type, self.id, user_display)

    def get_assigned_number(self):
        return get_assigned_number(self.tenant_id, self.numbering_entity_type, self.id)

    def has_assigned_number(self):
        return has_assigned_number(self.tenant_id, self.numbering_entity_type, self.id)
```

### 5.2 When Numbers Are Assigned

Numbers are assigned on entity creation (in the model's `save()` method or the view layer), not on `generate_number()`. This ensures the number is only persisted when the entity is successfully saved.

### 5.3 Entity Number Fields

Each entity model retains its existing number field (e.g., `wo_number`, `invoice_number`, `customer_number`). The `assign_number()` function generates the number and the entity stores it on its own field. The AssignedNumber record is the authoritative audit trail.

---

## 6. Seed Data

During tenant provisioning, NumberingRules are seeded from the TenantPreference model's prefix and start_number fields.

### 6.1 Default Numbering Rules

#### Core Entities (All Tiers)

| entity_type | prefix | include_year | year_format | sequence_length | reset_behavior | Source (TenantPreference field) |
|---|---|---|---|---|---|---|
| `customer` | `C` | Yes | `YY` | 4 | yearly | `customer_prefix`, `customer_start_number` |
| `asset` | `A` | Yes | `YY` | 4 | yearly | `asset_prefix`, `asset_start_number` |
| `work_order` | `W` | Yes | `YY` | 4 | yearly | `work_order_prefix`, `work_order_start_number` |
| `quote` | `Q` | Yes | `YY` | 4 | yearly | `quote_prefix`, `quote_start_number` |
| `invoice` | `I` | Yes | `YY` | 4 | yearly | `invoice_prefix`, `invoice_start_number` |
| `payment` | `P` | Yes | `YY` | 4 | yearly | `payment_prefix`, `payment_start_number` |
| `task` | `T` | Yes | `YY` | 4 | yearly | `task_prefix`, `task_start_number` |
| `inventory_item` | `YU` *(2026; see encoding note below)* | No | — | 4 | none | `inventory_item_prefix`, `product_start_number` |
| `employee` | `E` | No | — | 4 | none | `employee_prefix`, `employee_start_number` |
| `service_request` | `SR` | Yes | `YY` | 4 | yearly | `service_request_prefix`, `service_request_start_number` |

> **InventoryItem Prefix Note — Reverse-Alphabet Year Encoding:**
>
> The default `inventory_item` prefix uses the ServizDesk reverse-alphabet year encoding. Each digit of the year's last two digits is individually substituted using a reversed-alphabet cipher:
>
> | Digit | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
> |---|---|---|---|---|---|---|---|---|---|---|
> | Letter | Q | Z | Y | X | W | V | U | T | S | R |
>
> **Encoding example:** The year 2026 → last two digits `26` → digit `2` = `Y`, digit `6` = `U` → prefix `YU`. The year 2027 → `27` → `Y` + `T` → prefix `YT`. A full InventoryItem number in 2026 would be `YU-0086` (prefix + delimiter + sequence).
>
> Because the year is already encoded in the prefix, `inventory_item` does not include a separate year component (`include_year = False`, `reset_behavior = none`). The prefix value stored in `TenantPreference.inventory_item_prefix` is the **current year's computed prefix** (e.g., `YU` for 2026). When a new calendar year begins, the system updates the stored prefix to the new encoded value.
>
> The administrator may override this prefix to any static string, which disables the automatic year encoding.

#### Plus+ Entities

| entity_type | prefix | include_year | year_format | sequence_length | reset_behavior | Source (TenantPreference field) |
|---|---|---|---|---|---|---|
| `vendor` | `V` | Yes | `YY` | 4 | yearly | `vendor_prefix`, `vendor_start_number` |
| `purchase_order` | `PO` | Yes | `YY` | 4 | yearly | `po_prefix`, `po_start_number` |
| `vendor_bill` | `VB` | Yes | `YY` | 4 | yearly | `vendor_bill_prefix`, `vendor_bill_start_number` |
| `rma` | `RMA` | Yes | `YY` | 4 | yearly | `rma_prefix`, `rma_start_number` |
| `requisition` | `RQ` | Yes | `YY` | 4 | yearly | `requisition_prefix`, `requisition_start_number` |
| `work_group` | `WG` | No | — | 4 | none | `work_group_prefix`, `work_group_start_number` |
| `agreement` | `AG` | Yes | `YY` | 4 | yearly | `agreement_prefix`, `agreement_start_number` |
| `preventative_maintenance` | `PM` | Yes | `YY` | 4 | yearly | `pm_prefix`, `pm_start_number` |
| `lead` | `LD` | Yes | `YY` | 4 | yearly | `lead_prefix`, `lead_start_number` |

#### Pro/Enterprise Entities

| entity_type | prefix | include_year | year_format | sequence_length | reset_behavior | Source (TenantPreference field) |
|---|---|---|---|---|---|---|
| `opportunity` | `OP` | Yes | `YY` | 4 | yearly | `opportunity_prefix`, `opportunity_start_number` |
| `workflow` | `WF` | Yes | `YY` | 4 | yearly | `workflow_prefix`, `workflow_start_number` |
| `equipment` | `EQ` | Yes | `YY` | 4 | yearly | `equipment_prefix`, `equipment_start_number` |

#### Fleet Maintenance Add-On

| entity_type | prefix | include_year | year_format | sequence_length | reset_behavior | Source (TenantPreference field) |
|---|---|---|---|---|---|---|
| `vehicle` | `VS` | Yes | `YY` | 4 | yearly | `vehicle_prefix`, `vehicle_start_number` |

> **Seeding Rule:** All NumberingRules are seeded at provisioning regardless of the tenant's tier. Rules for entities above the tenant's current tier are dormant — they exist in the database but are never invoked until the tenant upgrades or activates the relevant add-on. This avoids re-seeding on tier upgrades. This matches the seeding rule for SequenceTracker (Seed Data V2 Section 5).

### 6.2 Start Number Seeding

When a NumberingRule is seeded, the `NumberSequence.current_value` is set to `start_number - 1` (from TenantPreference). This ensures the first generated number uses the configured start value.

---

## 7. Multi-Tenancy

### 7.1 Model Inheritance

- NumberingRule extends TenantModel.
- NumberSequence does NOT extend TenantModel (tenant scoping is via FK to NumberingRule).
- AssignedNumber extends TenantModel.

### 7.2 RLS

NumberingRule and AssignedNumber are protected by PostgreSQL RLS. NumberSequence is protected indirectly via its FK to NumberingRule (and by `SELECT FOR UPDATE` scoping).

### 7.3 Concurrency

The `SELECT FOR UPDATE` lock in `get_next_sequence_value()` ensures that concurrent requests within the same tenant cannot produce duplicate numbers. The lock is per-row (per NumberSequence), so different entity types and different tenants do not block each other.

---

## 8. Migration from SequenceTracker

### 8.1 Data Migration

For existing tenants that have SequenceTracker records:

1. Create NumberingRule from SequenceTracker + TenantPreference data (prefix, pad_length → sequence_length).
2. Create NumberSequence with `current_value = SequenceTracker.last_value`.
3. SequenceTracker can be dropped after migration is verified.

### 8.2 Backward Compatibility

Entity models' number fields (e.g., `wo_number`) are unchanged. The only change is where the number generation logic lives — from inline code to the numbering service.

---

## 9. Governance Rules

1. Numbers are generated atomically via `SELECT FOR UPDATE`. Concurrent requests are serialized.
2. Numbers are assigned once and never changed. AssignedNumber records are immutable.
3. Numbers are never reused. Even after entity deletion, the AssignedNumber record persists.
4. Each entity instance receives exactly one number (enforced by unique constraint).
5. Each number is unique within its (tenant_id, entity_type) scope (enforced by unique constraint).
6. Reset behavior (yearly/monthly/none) is applied automatically on the next generation after the period boundary.
7. NumberingRules are configured per tenant during provisioning and can be updated by administrators.
8. Deleting a NumberingRule is blocked if any AssignedNumber records reference it (PROTECT).

---

## 10. Cross-References

| Topic | Document |
|---|---|
| SequenceTracker (being replaced) | ServizDesk Data Models V6, Section 1.9 |
| TenantPreference numbering prefix/start fields | ServizDesk Data Models V6, Section 1.1 |
| Entity number field definitions | ServizDesk Data Models V6 (per entity) |
| SequenceTracker seed data (being replaced) | ServizDesk Tenant Provisioning Seed Data V2, Section 5 |
| Number format examples (C-26-0001, YU-0001, etc.) | ServizDesk Top-Down Specifications V4, Section 10.3 |
| Reverse-alphabet year encoding (XT prefix) | ServizDesk Top-Down Specifications V4, Section 4 (Products) |
| Multi-tenancy and RLS | ServizDesk Multi-Tenancy Specification V1 |
| Database roles and locking | ServizDesk Database Specification V2 |
| Provisioning flow (context bootstrap) | ServizDesk Multi-Tenancy Specification V1, Section 8 |
