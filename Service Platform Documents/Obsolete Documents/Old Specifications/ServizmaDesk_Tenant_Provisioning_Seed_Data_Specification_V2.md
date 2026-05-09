# ServizmaDesk Tenant Provisioning Seed Data Specification (SDTA)
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
*   `onboarding_wizard_completed`: `False`

### 2.2 `StorageTracker`
*   `id`: New UUID
*   `tenant_id`: `tenant_id` from payload
*   `total_bytes_used`: 0

### 2.3 `OnboardingState`
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
| **inventory_item_prefix** | `XT` | Reverse alphabet year encoding |
| **employee_prefix** | `E` | |
| **trouble_call_prefix** | `TC` | |
| **vendor_prefix** | `V` | Plus+ |
| **po_prefix** | `PO` | Plus+ |
| **vendor_bill_prefix** | `VB` | Plus+ |
| **rma_prefix** | `RMA` | Plus+ |
| **requisition_prefix** | `RQ` | Plus+ |
| **work_group_prefix** | `WG` | Plus+ |
| **agreement_prefix** | `AG` | Plus+ |
| **pm_prefix** | `PM` | Plus+ |
| **lead_prefix** | `LD` | Plus+ |
| **opportunity_prefix** | `OP` | Plus+ |
| **workflow_prefix** | `WF` | Pro+ |
| **equipment_prefix** | `EQ` | Pro+ |
| **vehicle_prefix** | `VS` | Fleet Add-On |

## 5. Sequence Tracker Initializers
To ensure collision-free record numbering, the following `SequenceTracker` rows are seeded. All `last_value` fields are initialized to **0**.

> **Naming Note:** The internal entity name is `InventoryItem`. In the Lite tier UI only, this is labeled as "Product" for simplicity. All other tiers use "Inventory Item" in the UI.

### 5.1 Core Entities (All Tiers)

| Entity Type | Prefix | Default Start |
|---|---|---|
| **Customer** | `C` | 0001 |
| **Asset** | `A` | 0001 |
| **WorkOrder** | `W` | 0001 |
| **Quote** | `Q` | 0001 |
| **Invoice** | `I` | 0001 |
| **Payment** | `P` | 0001 |
| **Task** | `T` | 0001 |
| **InventoryItem** | `XT` | 0001 |
| **Employee** | `E` | 0001 |
| **TroubleCall** | `TC` | 0001 |

### 5.2 Plus+ Entities

| Entity Type | Prefix | Default Start |
|---|---|---|
| **Vendor** | `V` | 0001 |
| **PurchaseOrder** | `PO` | 0001 |
| **VendorBill** | `VB` | 0001 |
| **RMA** | `RMA` | 0001 |
| **Requisition** | `RQ` | 0001 |
| **WorkGroup** | `WG` | 0001 |
| **Agreement** | `AG` | 0001 |
| **PreventativeMaintenance** | `PM` | 0001 |
| **Lead** | `LD` | 0001 |
| **Opportunity** | `OP` | 0001 |

### 5.3 Pro/Enterprise Entities

| Entity Type | Prefix | Default Start |
|---|---|---|
| **WorkFlow** | `WF` | 0001 |
| **Equipment** | `EQ` | 0001 |

### 5.4 Fleet Management Add-On

| Entity Type | Prefix | Default Start |
|---|---|---|
| **Vehicle** | `VS` | 0001 |

> **Seeding Rule:** All sequence trackers are seeded at provisioning regardless of the tenant's tier. Trackers for entities above the tenant's current tier are dormant — they exist in the database but are never incremented until the tenant upgrades or activates the relevant add-on. This avoids re-seeding on tier upgrades.

## 6. Initial User (Administrator)
The first user is created using the `admin_...` fields from the provisioning payload.
*   **Person Record**: A `Person` record is created with `first_name` and `last_name` from the payload.
*   **User Record**: Links to the newly created Person via `person_id`.
*   **Role**: Links to the newly created **Administrator** Role via `EmployeeRole` junction.
*   **Status**: `Active`
*   **Employee Number**: Generated using the `E` prefix sequence (E26-0001).
*   **Force Password Change**: `False` (The hash provided by SDP is established by the user during signup).
