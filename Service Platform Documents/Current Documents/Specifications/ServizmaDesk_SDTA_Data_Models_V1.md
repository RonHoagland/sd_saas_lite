# ServizmaDesk Tenant App (SDTA) Data Models
**Document Status:** Working Draft — High-Level Architecture
**Document Version:** V3

---

# 1. Architectural Mandates
1. **Global Mandate:** Every table contains a `tenant_id` (UUID) to isolate data horizontally.
2. **Primary Keys:** Every table uses a `UUIDv4` as its primary key (`id`).
3. **No Generic Foreign Keys (GFKs):** To maintain strict PostgreSQL Row-Level Security (RLS) enforcement, we do not use Django's content-types framework.
4. **Isolated Line Items:** Quotes, Work Orders, and Invoices do not share a generic line item table. Each has its own dedicated line table (`QuoteLine`, `WorkOrderLine`, `InvoiceLine`).
5. **Exclusive Arc (Nullable FKs) for Notes/Docs**: Instead of creating dozens of separate note/document tables or using dangerous GFKs, we use a single `Note` table and a single `Document` table. These tables contain nullable foreign keys pointing to every possible parent entity. A DB constraint ensures exactly one of these FKs is populated per row.
6. **Universal Deletion Policy**: A top-level entity (Customer, Quote, Work Order, etc.) **cannot be deleted** if any related records exist. **Notes are the only exception** and will cascade-delete with the parent. All other records (Documents, Line Items, Assets) must be manually removed before the parent record can be deleted. This ensures absolute data integrity and accurate storage tracking.

---

# 2. Lite Tier Models (The Core MVP)

The foundational models required to execute the core service delivery and billing lifecycle.

### 2.1 Identity, Access & Preferences
*   **`User`**: Represents an employee accessing the tenant app. Holds authentication details (email, hashed password). Linked to the Tenant.
*   **`Role`**: Defines permissions. In higher tiers, supports custom CRUD matrices.
*   **`EmployeeRole`**: Junction table mapping employees to multiple roles (M2M).
*   **`TenantPreference`**: Global settings acting horizontally across the entire tenant. Includes default Tax Rate, Timezone, Currency, Date/Time formats, and Company Legal Name/Logo for invoice headers.
*   **`UserPreference`**: Individualized settings per employee (e.g., UI Theme preference, default landing page).
*   **`SessionLog`**: Tracks active authenticated sessions. Records login time, IP address, user-agent, expiration, and a `permission_snapshot` (JSONB) of the user's rights at login.
*   **`AuditEvent`**: The immutable history log. Records *who* did *what* and *when* (e.g., "User A created Invoice B", "User B deleted Quote C"). Essential for security and dispute resolution.
*   **`PasswordResetToken`**: Stores the time-limited, single-use hashed token generated when an Administrator initiates a password reset for an employee. Contains `user_id`, `token` (hashed), `created_at`, and `expires_at`.

### 2.2 Core CRM (The Triad Architecture)
To preserve historical integrity as humans move between companies without losing their purchasing history, we employ a Triad Architecture for CRM.
*   **`Customer`**: The billing entity/company.
*   **`Person`**: The actual human being. Holds identity logic (First/Last name).
*   **`Contact`**: The bridge table linking a `Person` to a `Customer`. Tracks the role/title. A `Person` can have multiple `Contact` records over their lifetime (e.g., worked at Company A, then moved to Company B), but only **one `Contact` can be active at a given time** for a single Person.
*   **`Address`**: Physical or mailing addresses. Can link to a `Customer`, `Person`, `Contact`, or an `Asset` (Physical site).
*   **`Phone`**: Phone numbers. Can link to a `Customer`, `Person`, `Contact`, or `User`.
*   **`Social`**: Web links, LinkedIn. Links to a **Customer**, **Vendor**, **Person**, or **Contact**.

### 2.3 Assets & Inventory
*   **`InventoryItem`**: (Formerly Product) The base tracking record for Parts, Services, Consumables, and Kits.
*   **`Asset`**: The physical equipment being serviced.
    *   *Relationships:* Belongs to a `Customer`. Links to a physical `Address` and potentially a `Warranty`.

### 2.4 Service Delivery & Financials
*   **`Quote`**: A proposal provided to a `Customer`. Linked to **Pricebooks** for contract-specific pricing.
*   **`QuoteLine`**: Items from the `Inventory` catalog linked to a `Quote`.
*   **`WorkOrder`**: The execution record.
*   **`WorkOrderLine`**: Parts/labor executed on the job, depleting `Inventory` stock.
*   **`Invoice`**: The billing record.
*   **`InvoiceLine`**: Billed items.
*   **`Payment`**: Records of funds received.
*   **`LedgerEntry`**: Read-only running net balance (Unified AR/AP).

### 2.5 Warehouse & Logistics
*   **`Warehouse`**: Physical buildings or areas for bulk storage.
*   **`StorageLocation`**: Subdivisions (Bins, Racks, Aisles) within a Warehouse.
*   **`StockLevel`**: The junction linking an `InventoryItem` to a `StorageLocation` with specific quantities.

### 2.6 Organization & Task Management
*   **`Task`**: Actionable to-do items.
*   **`TaskTodo`**: Granular checklists within a Task.
*   **`TaskTime`**: Duration/Labor tracking specific to a Task.

### 2.6 Attachments (Exclusive Arc Pattern)
These two tables service the entire Lite tier.
### `Note`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `note_type` | Enum | Internal Note, Call, Email, Site Visit, Customer Comment, Reminder |
| `body` | TextField | |
| `customer_id` | UUID FK → Customer | Nullable |
| `person_id` | UUID FK → Person | Nullable |
| `contact_id` | UUID FK → Contact | Nullable |
| `asset_id` | UUID FK → Asset | Nullable |
| `product_id` | UUID FK → Product | Nullable |
| `quote_id` | UUID FK → Quote | Nullable |
| `work_order_id` | UUID FK → WorkOrder | Nullable |
| `invoice_id` | UUID FK → Invoice | Nullable |
| `payment_id` | UUID FK → Payment | Nullable |
| `task_id` | UUID FK → Task | Nullable |
| `vendor_id` | UUID FK → Vendor | Nullable |
| `purchase_order_id` | UUID FK → PurchaseOrder | Nullable |
| `vehicle_id` | UUID FK → Vehicle | Nullable |
| `user_id` | UUID FK → User | Nullable — employee notes |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### `Document`

| Field | Type | Notes |
|---|---|---|
| `id` | UUIDv4 PK | |
| `tenant_id` | UUID FK → Tenant | |
| `file_name` | CharField | Original filename |
| `file_key` | CharField | Object storage key |
| `file_size_bytes` | BigIntegerField | |
| `mime_type` | CharField | |
| `customer_id` | UUID FK | |
| `contact_id` | UUID FK | |
| `person_id` | UUID FK | |
| `asset_id` | UUID FK | |
| `inventory_id` | UUID FK | |
| `quote_id` | UUID FK | |
| `work_order_id` | UUID FK | |
| `invoice_id` | UUID FK | |
| `payment_id` | UUID FK | |
| `task_id` | UUID FK | |
| `vendor_id` | UUID FK | |
| `warehouse_id` | UUID FK | |
| `fleet_id` | UUID FK | |
| `ledger_id` | UUID FK | |
| `workflow_id` | UUID FK | |
| `trouble_call_id` | UUID FK | |
| `lead_id` | UUID FK | |
| `opportunity_id` | UUID FK | |
| `pm_id` | UUID FK | |
| `purchase_id` | UUID FK | |
| `requisition_id` | UUID FK | |
| `user_id` | UUID FK | |
| `created_by` | CharField | Username snapshot of actor |
| `created_on` | DateTimeField | |
| `updated_by` | CharField | Username snapshot of actor |
| `updated_on` | DateTimeField | |

### 2.7 System Utilities & Operations
Crucial behind-the-scenes tables running the infrastructure of the tenant account.
*   **`SequenceTracker`**: Manages the tenant-scoped auto-incrementing counters (e.g., the `0001` in `26-0001`) to guarantee collision-free record number generation for Quotes, Work Orders, Invoices, and Inventory.
*   **`Notification`**: In-app dismissible banner alerts for Administrators (e.g., "Stripe Payment Failed"). Contains an `is_dismissed` flag.
*   **`StripeConnection`**: Holds the live Stripe account ID, encrypted OAuth access token, and current `is_active` connection status. Read locally to determine if the "Generate Payment Link" button renders.
*   **`StripeConnectionLog`**: Audit table tracking when a tenant connects, disconnects, or experiences an OAuth token revocation with Stripe Connect.
*   **`StripeAPIRequestLog`**: Tracks outgoing API requests made to Stripe (e.g., generating Payment Links) for debugging HTTP timeouts or payload failures.
*   **`WebhookLog`**: Idempotency tracker for incoming Stripe events. Stores external event IDs to prevent duplicate payment processing.
*   **`EmailDeliveryLog`**: Tracks internal transactional emails sent to `User` accounts via Postmark (e.g., Password Resets, Welcome Invites) to capture delivery status and hard bounces.
*   **`SystemErrorLog`**: Server-side capture of exceptions and system errors scoped to the UI action, providing developer triage without exposing stack traces to the user.

### 2.8 Tenant Infrastructure (SDTA Local)
These tables manage the tenant's exact state within the SDTA database to ensure performance and enforce limits without constantly polling the SDP platform.
*   **`TenantProxy` / `TenantState`**: A local cache residing in SDTA that stores the tenant's current active Tier (Lite), Seat Limit (10), and Status (Active/Suspended/Read-Only). Automatically synced from the SDP REST API via webhooks or background workers.
*   **`StorageTracker`**: A utility table maintaining a running tally of total bytes consumed by a tenant's `Document` uploads. Eliminates the need to query Object Storage deeply to enforce the 3 GB Lite storage cap.
*   **`DataExportLog`**: Audit tracking of whenever a tenant requests a CSV export of any major list view (Customers, Invoices, etc.) for data exfiltration security reviews.
*   **`TenantSyncLog`**: Tracks successful and failed synchronization attempts between SDTA and SDP (e.g., updating a subscription status or logging a failed connection).
*   **`TenantPreference`**: Stores tenant-scoped operational settings (prefixes, start numbers, timezone).
*   **`SequenceTracker`**: Stores the atomic counter for per-tenant human-readable record numbering.
*   **`TenantAddOn`**: Stores individual feature or limit overrides active for the tenant (e.g., Fleet Management, Extra Storage).
    | Field | Type | Notes |
    |---|---|---|
    | `id` | UUIDv4 PK | |
    | `tenant_id` | UUID FK → Tenant | |
    | `addon_type` | Enum | Fleet, SMS_Extra, Storage_+5GB, Storage_+10GB, QB_CSV_Export |
    | `status` | Enum | Active, Cancelled, Expired |
    | `unit_limit` | Integer | Nullable — for capacity-based add-ons |
    | `purchased_on` | DateTimeField | |
    | `created_by` | CharField | 'System' — updated by SDP sync |
    | `created_on` | DateTimeField | |
    | `updated_by` | CharField | 'System' — updated by SDP sync |
    | `updated_on` | DateTimeField | |
*   **`OnboardingState`**: Transient operational state tracking weather the first-login wizard has been completed, and the active status of the dashboard onboarding checklist items (per-tenant).

---

# 3. Plus & Enterprise Tier Extensions
These models represent the advanced operational logic required for medium-to-large service enterprises.

- **SOP Workflows**: Templates (`WFSteps`, `WFTools`, `WFInventory`) providing standard plans for Work Orders and variance auditing.
- **WorkGroup Management**: Regional and specialty grouping (`WorkGroup`, `WGDivision`, `WorkGroupTeam`).
- **Workforce Optimization**: Skills-based capability tracking (`Skills`, `EmployeeSkills`).
- **AP Loop**: Full Accounts Payable lifecycle (`VendorBills`, `RMA`, `Receiving`).
- **Equipment Accountability**: Management of durable shop tools (`Equipment`, `CheckIn/Out`).
- **Fleet Tracking**: Mobile inventory and maintenance for the `Vechicles` fleet.
- **Safety Compliance**: Field-service auditing (`SafetyForms`, `WOSFAnswers`).
- **Exclusive Note/Document Arc**: Universal relational storage covering 25+ distinct entities.
- **Maintenance Schedule**: Recurring Work Order rules for Assets and Preventive Maintenance.
- **Warranty**: Entitlements for Assets or InventoryItems.
- **Vehicle Logistics**: Mileage, fuel tracking, and mobile stock (`VechicleInventory`).
...*(To be fully defined post-MVP)*

---
**End of Document**
