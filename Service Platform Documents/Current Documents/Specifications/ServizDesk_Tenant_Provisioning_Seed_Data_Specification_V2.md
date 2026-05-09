# ServizDesk Tenant Provisioning Seed Data Specification (SDTA)
**Document Version:** V2
**Status:** Working Draft
**Supersedes:** V1

## 1. Overview
This document specifies the exact "Seed Data" created by the SDTA when a new tenant is provisioned via the internal `/provision-tenant/` endpoint. This data must be initialized within a single atomic database transaction.

## 2. Infrastructure & State Records

### 2.1 `TenantState`
*   `id`: `tenant_id` from payload
*   `status`: `Active`
*   `tier`: From payload
*   `seat_limit`: From payload
*   `storage_limit_bytes`: From payload
*   `email_points_included`: From payload (tier-based; Lite = 400, Plus = 1,600, Pro = 4,000, Enterprise = 12,000)
*   `email_period_start`: Provisioning date (billing anniversary)
*   `sms_points_included`: From payload (tier-based; Lite = 100, Plus = 350, Pro = 750)
*   `sms_period_start`: Provisioning date (billing anniversary)
*   `onboarding_wizard_completed`: `False`

### 2.2 `StorageTracker`
*   `id`: New UUID
*   `tenant_id`: `tenant_id` from payload
*   `total_bytes_used`: 0
*   `pending_bytes`: 0

### 2.3 `EmailUsageTracker`
*   `id`: New UUID
*   `tenant_id`: `tenant_id` from payload
*   `email_points_used`: 0
*   `email_points_overage`: 0

### 2.4 `SMSUsageTracker`
*   `id`: New UUID
*   `tenant_id`: `tenant_id` from payload
*   `sms_points_used`: 0
*   `sms_points_overage`: 0

### 2.5 `OnboardingState`
*   `id`: New UUID
*   `tenant_id`: `tenant_id` from payload
*   `checklist_items`: JSON with all items set to `False`
*   `is_completed`: `False`

## 3. System Roles (The "Identity Foundation")
Every tenant is initialized with exactly three immutable (Non-Custom) roles as the foundation for RBAC.

| Role Name | `is_custom` | Purpose |
|---|---|---|
| **Administrator** | `False` | Full system access. Owns the billing relationship. |
| **User** | `False` | Daily operational access (Quotes, Work Orders, Customers). |
| **Read-Only** | `False` | View-only access across all modules. |

## 4. Default Tenant Preferences
The following defaults are applied to the `TenantPreference` record unless otherwise specified in the provisioning payload.

| Field | Default Value | Note |
|---|---|---|
| **company_name** | From Payload | |
| **mfa_required** | `False` | Administrator-controlled. Off by default; UI recommends enabling. |
| **session_timeout_minutes** | `30` | Min: 15, Max: 480. Administrator-configurable. |
| **default_currency** | `USD` | |
| **currency_symbol** | `$` | |
| **decimal_precision** | `2` | |
| **timezone** | `UTC` | Recommended to prompt for this in Onboarding |
| **date_format** | `MM/DD/YYYY` | |
| **default_tax_rate** | `0.00` | User must configure local tax |
| **tax_label** | `Sales Tax` | |
| **default_payment_terms** | `Due on Receipt` | |
| **default_quote_expiry** | `30` | Days |
| **fiscal_year_start** | `1` | January |
| **numbering_reset** | `Never` | |
| **customer_prefix** | `C` | |
| **asset_prefix** | `A` | |
| **work_order_prefix** | `W` | |
| **quote_prefix** | `Q` | |
| **invoice_prefix** | `I` | |
| **payment_prefix** | `P` | |
| **task_prefix** | `T` | |
| **inventory_item_prefix** | *(computed)* | Reverse-alphabet year encoding — see Numbering Service V1 Section 6.1 for the cipher table. Computed at provisioning from the current year (e.g., `YU` for 2026, `YT` for 2027). |
| **employee_prefix** | `E` | |
| **service_request_prefix** | `SR` | |
| **vendor_prefix** | `V` | Plus+ |
| **po_prefix** | `PO` | Plus+ |
| **vendor_bill_prefix** | `VB` | Plus+ |
| **rma_prefix** | `RMA` | Plus+ |
| **requisition_prefix** | `RQ` | Plus+ |
| **work_group_prefix** | `WG` | Plus+ |
| **agreement_prefix** | `AG` | Plus+ |
| **pm_prefix** | `PM` | Plus+ |
| **lead_prefix** | `LD` | Plus+ |
| **opportunity_prefix** | `OP` | Pro+ |
| **workflow_prefix** | `WF` | Pro+ |
| **equipment_prefix** | `EQ` | Pro+ |
| **vehicle_prefix** | `VS` | Fleet Add-On |

## 5. Numbering Service Initializers

> **Migration Note:** This section previously referenced `SequenceTracker` rows. As of the Numbering Service Specification V1, `SequenceTracker` is replaced by a three-model pattern: `NumberingRule`, `NumberSequence`, and `AssignedNumber`. See Numbering Service Specification V1 for the full model definitions. The tables below now define the `NumberingRule` and `NumberSequence` records seeded at provisioning.

To ensure collision-free record numbering, the following `NumberingRule` records are seeded (one per entity type), each with a companion `NumberSequence` record whose `current_value` is initialized to **0** (so the first generated number uses `0001`).

> **Naming Note:** The internal entity name is `InventoryItem`. In the Lite tier UI only, this is labeled as "Product" for simplicity. All other tiers use "Inventory Item" in the UI.

### 5.1 Core Entities (All Tiers)

| Entity Type (entity_type key) | Prefix | Default Start | include_year | reset_behavior |
|---|---|---|---|---|
| **customer** | `C` | 0001 | Yes (YY) | yearly |
| **asset** | `A` | 0001 | Yes (YY) | yearly |
| **work_order** | `W` | 0001 | Yes (YY) | yearly |
| **quote** | `Q` | 0001 | Yes (YY) | yearly |
| **invoice** | `I` | 0001 | Yes (YY) | yearly |
| **payment** | `P` | 0001 | Yes (YY) | yearly |
| **task** | `T` | 0001 | Yes (YY) | yearly |
| **inventory_item** | *(computed; e.g., `YU` for 2026)* | 0001 | No | none |
| **employee** | `E` | 0001 | No | none |
| **service_request** | `SR` | 0001 | Yes (YY) | yearly |

### 5.2 Plus+ Entities

| Entity Type (entity_type key) | Prefix | Default Start | include_year | reset_behavior |
|---|---|---|---|---|
| **vendor** | `V` | 0001 | Yes (YY) | yearly |
| **purchase_order** | `PO` | 0001 | Yes (YY) | yearly |
| **vendor_bill** | `VB` | 0001 | Yes (YY) | yearly |
| **rma** | `RMA` | 0001 | Yes (YY) | yearly |
| **requisition** | `RQ` | 0001 | Yes (YY) | yearly |
| **work_group** | `WG` | 0001 | No | none |
| **agreement** | `AG` | 0001 | Yes (YY) | yearly |
| **preventative_maintenance** | `PM` | 0001 | Yes (YY) | yearly |
| **lead** | `LD` | 0001 | Yes (YY) | yearly |

### 5.3 Pro/Enterprise Entities

| Entity Type (entity_type key) | Prefix | Default Start | include_year | reset_behavior |
|---|---|---|---|---|
| **opportunity** | `OP` | 0001 | Yes (YY) | yearly |
| **workflow** | `WF` | 0001 | Yes (YY) | yearly |
| **equipment** | `EQ` | 0001 | Yes (YY) | yearly |

### 5.4 Fleet Maintenance Add-On

| Entity Type (entity_type key) | Prefix | Default Start | include_year | reset_behavior |
|---|---|---|---|---|
| **vehicle** | `VS` | 0001 | Yes (YY) | yearly |

> **Seeding Rule:** All NumberingRules are seeded at provisioning regardless of the tenant's tier. Rules for entities above the tenant's current tier are dormant — they exist in the database but are never invoked until the tenant upgrades or activates the relevant add-on. This avoids re-seeding on tier upgrades.

## 5a. Lifecycle Framework Initializers

> **New in Lifecycle Framework Specification V1.** During provisioning, `LifecycleStateDef` and `LifecycleTransitionRule` records are seeded for all entity types defined in System Status Specification V3. These records enforce valid status transitions for all major entities.

The provisioning flow transforms each entity lifecycle from System Status V3 into:

1. **LifecycleStateDef** records — one per status per entity type, with `state_type` set based on business rules:
   - `normal` — standard operating states
   - `locked` — states where the entity record becomes read-only (e.g., Issued invoices, Completed work orders)
   - `final` — terminal states with no outbound transitions (e.g., Closed, Void, Written Off)

2. **LifecycleTransitionRule** records — one per allowed transition per entity type, with `required_role` and `requires_reason` set per System Status V3 rules.

> **Seeding Rule:** Like NumberingRules, all lifecycle records are seeded at provisioning regardless of tier. Records for higher-tier entities are dormant until the tenant upgrades. See Lifecycle Framework Specification V1 Section 5 for representative seed data (Customer, Work Order, Invoice lifecycles) and the full entity type list.

## 6. Initial User (Administrator)
The first user is created using the `admin_...` fields from the provisioning payload.
*   **Person Record**: A `Person` record is created with `first_name` and `last_name` from the payload.
*   **User Record**: Links to the newly created Person via `person_id`.
*   **Role**: Links to the newly created **Administrator** Role via `EmployeeRole` junction.
*   **Status**: `Active`
*   **Employee Number**: Generated using the `E` prefix sequence (E26-0001).
*   **Force Password Change**: `False` (The hash provided by SDP is established by the user during signup).
*   **`mfa_enabled`**: `False` — MFA is off by default until the Administrator enables it for their organization.
*   **`mfa_phone`**: `null` — The Administrator must configure their MFA phone number in Settings before MFA can be activated.
*   **`mfa_exempt`**: `False` — No exemptions at provisioning.
