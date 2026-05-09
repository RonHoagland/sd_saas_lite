# ServizmaDesk Tenant Provisioning Seed Data Specification (SDTA)
**Document Version:** V1
**Status:** Working Draft (Resolves Gap 3.8 & 3.9)

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

## 5. Sequence Tracker Initializers
To ensure collision-free record numbering, the following `SequenceTracker` rows are seeded. All `last_value` fields are initialized to **0**.

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
| **Vendor** | `V` | 0001 |
| **PurchaseOrder** | `PO` | 0001 |
| **VendorBill** | `VB` | 0001 |
| **RMA** | `RMA` | 0001 |

## 6. Initial User (Administrator)
The first user is created using the `admin_...` fields from the provisioning payload.
*   **Role**: Links to the newly created **Administrator** Role.
*   **Status**: `Active`
*   **Force Password Change**: `False` (The hash provided by SDP is established by the user during signup).
