# BrixaWares SaaS  
# Lite Edition – MVP V1 Specification (Locked Draft)

---

# 1. Product Identity

## Target Market
General service businesses:
- HVAC
- Plumbing
- Electrical
- Repair/service shops
- 1–10 users

## Core Promise
Simple service execution with structured data that stays organized as the company grows.

## Design Principles
- Manual-first (no automation)
- Operational simplicity
- Structured long-term integrity
- Transparent data ownership
- Storage-controlled (not artificially crippled)
- Competitive feature parity where required

---

# 2. Plan Limits (Lite)

- Max Users: 10
- Attachment Storage: 3GB
- Storage Warnings:
  - 70% notice
  - 85% strong warning
  - 100% block uploads only
- CSV export allowed (all tables)
- No API access
- No SMS
- No automation
- No multi-location
- No inventory automation

## Add-Ons Available
- +5GB storage
- +10GB storage

---

# 3. Core Modules Included

---

# 3.1 Dashboard (Operational Overview)

Not analytics-heavy.

Displays:
- Work Orders Today
- Open Work Orders
- Open Invoices
- Overdue Invoices
- Revenue This Month
- Storage Usage Meter

No charts required.

---

# 3.2 Companies

## Capabilities
- Create / Edit / Delete
- Status lifecycle enforced
- Embedded Sections - Limited record count
  - Contacts (2)
  - Addresses (billing (required), Shipping (optional))
  - Phone Numbers (Fax, Phone1, Phone2)
  - Social Info (email, facebook, Linkedin, )
- Linked to:
  - Service Items
  - Quotes
  - Work Orders
  - Invoices
  - Notes
  - Documents
  - Tasks

## Features
- Search
- Filters
- List view
- CSV export

---

# 3.3 People

## Types
- Contacts (linked to Company)
- Employees (system users)

## Capabilities
- Create/Edit contacts
- Assign Work Orders
- Role-based access

---

# 3.4 Products & Services (Catalog Only)

Lite is catalog-only.

## Fields
- Name
- Type (Part / Service)
- SKU
- Unit Price
- Unit Cost (optional)
- Manual Quantity (informational only)
- Active/Inactive

## Not Included
- Auto-decrement
- Inventory movement
- Adjustments
- Transfers
- Locations
- Purchase Orders

---

# 3.5 Service Items (Customer Assets)

Core differentiator.

## Required Fields
- Company (required)
- Asset Name
- Make/Model
- Serial Number
- Install Date
- Warranty Start/End
- Status (Active / Retired / Decommissioned)

## Capabilities
- View service history (Quotes, WOs, Invoices)
- Attach documents
- Add typed notes
- CSV export

No maintenance automation.

---

# 3.6 Quotes

Required for competitive parity.

## Relationships
- Company (required)
- Service Item (optional but encouraged)
- Line items
- Assigned user (optional)

## Status Flow
Draft → Sent → Accepted → Rejected → Expired → Converted

## Capabilities
- Create/Edit
- Send (email or PDF)
- Convert to Work Order
- Convert to Invoice
- Attach documents
- Typed notes
- CSV export

## Not Included
- E-signature
- Approval workflows
- Version history
- Automation reminders
- Advanced analytics

---

# 3.7 Work Orders

Primary operational object.

## Required Relationships
- Company (required)
- Service Item (required)
- Assigned User
- Line items

## Status Flow
Draft → Scheduled → In Progress → On Hold → Completed → Closed / Cancelled

## Capabilities
- Create/Edit
- Schedule date/time (set inside WO)
- Calendar reflects scheduled items
- Add parts/labor
- Convert to Invoice
- Attach documents
- Typed notes
- CSV export

---

# 3.8 Scheduling (Calendar View)

- Calendar is display-based
- Scheduling occurs inside Work Order
- Drag-and-drop to reschedule
- Filter by assigned user

No dispatch board.
No routing.
No optimization.

---

# 3.9 Invoices

## Relationships
- Company (required)
- Service Item (optional if standalone)
- Line items
- Payments (embedded)

## Status Flow
Draft → Issued → Partially Paid → Paid → Overdue → Void → Written Off

## Capabilities
- Create from Work Order
- Standalone invoice
- Email/send invoice
- Print/PDF
- Stripe payment link
- CSV export

---

# 3.10 Payments (Embedded in Invoice)

## Capabilities
- Manual entry
- Stripe processing
- Partial payments
- Status auto-update
- Payment history per invoice

No standalone payment module required.

---

# 3.11 Notes (Typed)

No separate Interactions object.

## Note Types
- Internal Note
- Call
- Email
- Site Visit
- Customer Comment
- Reminder

Unlimited notes.
Text does not count toward storage.

---

# 3.12 Documents (Attachments)

- Max 10 attachments per record
- Counts toward 3GB storage
- Attach to:
  - Company
  - Service Item
  - Quote
  - Work Order
  - Invoice

Uploads blocked at 100% storage.

---

# 3.13 Tasks (Basic)

- Create/Edit
- Assign to user
- Link to Company / Service Item / Quote / Work Order
- Status tracking
- CSV export

No time tracking required.

---

# 3.14 Reporting (List-Based Only)

List views + filters + search.

## Companies
- Active
- Inactive
- With Open Work Orders
- With Outstanding Balance

## Service Items
- By Company
- By Status

## Quotes
- Open Quotes
- Quotes by Customer
- Expired Quotes

## Work Orders
- Open
- By Status
- By User
- Completed (date range)

## Invoices
- Open
- Overdue
- By Customer
- By Date Range

## Payments
- By Date Range
- By Invoice

CSV export only.

---

# 4. Data Ownership & Export Policy

All Paid Tiers:
- Unlimited CSV export per table
- No restore capability

Lite:
- CSV export only

Structured Account Export reserved for Plus/Pro.

---

# 5. Storage Policy

- 3GB included
- Meter visible in Settings
- Uploads blocked at 100%
- Add-on storage available
- Text records not counted

---

# 6. Security, Sessions, and Audit (Lite)

This section defines the minimum security traceability needed to answer:
- Who logged in?
- Who created/deleted a record?
- Who changed a status?
- Who performed a financial-impact action?
- (Selectively) Who changed a high-integrity field?

Lite is **event-level** logging. It does **not** do field-by-field history tracking.  [oai_citation:0‡brixa_wares_state_transition_rules_high_level_v1.md](file-service://file-FMviN1cmA7oss7Zb7W8r55)

---

### 6.1 User Sessions (Lite)

#### Purpose
A **Session** represents an authenticated user context (the “actor”) for a period of activity. Audit events reference a Session.

#### When a Session is created
- A Session record is created on **LOGIN_SUCCESS**.

#### What is captured (recommended Lite fields)
- `session_uuid` (primary identifier)
- `user_uuid`
- `username_snapshot` (optional, but helpful)
- `role_snapshot` (optional; role(s) at login)
- `login_timestamp` (server local time)
- `logout_timestamp` (nullable)
- `ended_flag` or `end_reason` (timeout/logout/admin revoke) (optional in Lite)
- `ip_address` (**required**)
- `user_agent` (recommended)
- `auth_result` (`SUCCESS` / `FAIL`)
- `fail_reason` (nullable; recommended for FAIL)

#### LOGIN_FAIL events
- Lite records **LOGIN_FAIL** events with:
  - timestamp
  - username (attempted) or user reference if known
  - **ip_address**
  - user_agent (recommended)
  - reason if available (optional)

#### Retention
- Sessions are retained on a **rotating 18-month** basis (older sessions are purged).

---

### 6.2 Audit Events (Lite)

#### Purpose
An **Audit Event** records meaningful actions performed by a user during a Session.
Audit Events must be small, queryable, and human-reviewable.  [oai_citation:1‡brixa_wares_state_transition_rules_high_level_v1.md](file-service://file-FMviN1cmA7oss7Zb7W8r55)

#### Core audit event fields (Lite)
- `audit_event_uuid`
- `session_uuid` (required; ties action to session)
- `user_uuid_snapshot` (recommended)
- `timestamp` (server local time)
- `event_type` (see taxonomy)
- `object_type` (e.g., Company, ServiceItem, WorkOrder, Invoice, Product)
- `record_uuid` (target record)
- `human_number` (if the object has one, e.g., `INV25-0001`, `WO25-0001`)  [oai_citation:2‡brixawares_numbering_ids_high_level_v3.md](file-service://file-G6iboS8K924T5tb6mfuRER)
- `summary` (short text)

#### Event taxonomy (Lite)
Lite records the following event types (event-level only):  [oai_citation:3‡brixa_wares_state_transition_rules_high_level_v1.md](file-service://file-FMviN1cmA7oss7Zb7W8r55)
- Authentication:
  - `LOGIN_SUCCESS`
  - `LOGIN_FAIL`
  - `LOGOUT` (optional)
- Data Lifecycle:
  - `CREATE`
  - `DELETE`
- Workflow:
  - `STATUS_CHANGE`
- Financial-impact (Lite must record):
  - `INVOICE_ISSUED`
  - `INVOICE_VOIDED`
  - `INVOICE_WRITEOFF`
  - `PAYMENT_APPLIED`

> Note: Lite does not record generic `UPDATE` events globally.

#### What actions generate Audit Events (Lite rules)
Lite records an Audit Event when any of the following occurs:

1) **Create**
- Any top-tier object creation:
  - Company, Service Item, Quote, Work Order, Invoice, Product, Task (as applicable)
- (Optional) creation of supporting objects if they are significant to traceability

2) **Delete**
- Any delete of top-tier objects
- (If deletes are restricted in Lite, deletions should still be audited when they occur)

3) **Manual Status Change**
- Any manual status change on objects with lifecycles:
  - Work Orders, Invoices, Quotes, Service Items (etc.)  [oai_citation:4‡brixawares_object_lifecycle_definitions_high_level_V2.md](file-service://file-EuSCkRPHA6VM8xw2KcDfxR)

4) **Financial-impact actions**
- Issue/Void/Write-off invoice
- Apply payment to invoice

#### Targeted UPDATE auditing (Lite - selective)
Lite records UPDATE events **only** for a short list of “high-integrity” changes.
This prevents audit noise while preserving traceability where it matters.

**Recommended targeted UPDATE list (Lite):**
- Company:
  - company name changes
  - status changes (already captured via STATUS_CHANGE)
- Service Item:
  - Company link changes (asset ownership)
  - serial number changes
  - status changes (already captured via STATUS_CHANGE)
- Work Order:
  - scheduled date/time changes
  - assigned technician/user changes
  - service item link changes
  - status changes (already captured via STATUS_CHANGE)
- Invoice:
  - due date changes
  - total changes **after Issued**
  - status changes (already captured via STATUS_CHANGE / financial events)
- Product:
  - SKU/Product Number changes (recommended to log as targeted UPDATE in Lite)

> Lite does not store before/after diffs. Pro may add diffs for a targeted list later.  [oai_citation:5‡brixa_wares_state_transition_rules_high_level_v1.md](file-service://file-FMviN1cmA7oss7Zb7W8r55)

#### Retention
- Audit Events are retained on a **rotating 18-month** basis (older events are purged).

---

### 6.3 Lite vs Plus/Pro Notes (scaffold placeholder)
- Lite: event-level only; targeted UPDATE list only; no diffs
- Plus/Pro: may introduce reason-required actions and compact before/after JSON for a short list of objects (to be defined later)  [oai_citation:6‡brixa_wares_state_transition_rules_high_level_v1.md](file-service://file-FMviN1cmA7oss7Zb7W8r55)

---

# 7. Preferences (Lite – Account-Level Configuration)

## 7.1 Purpose

The Preferences record stores global configuration settings for the account.

- One Preferences record exists per account.
- Preferences apply to all users.
- Preferences are editable only by users with the Admin role.
- Preferences are not tied to individual users.

---

## 7.2 Governance Rules

1. Exactly one Preferences record exists per account.
2. Only Admin users may edit Preferences.
3. Preference updates generate an Audit Event.
4. Preferences cannot be deleted.
5. System-enforced values (e.g., storage limits, max users) are read-only.

---

## 7.3 Company Profile Fields

- Company Legal Name
- Display Name
- Address
- Phone
- Email
- Invoice Footer Text
- Logo

---

## 7.4 Localization Fields

- Time Zone
- Date Format
- Time Format
- Currency Code
- Currency Symbol

---

## 7.5 Financial Defaults

- Default Tax Rate
- Default Payment Terms (days)
- Default Quote Expiration Days
- Default Work Order Status
- Default Invoice Status

---

## 7.6 Operational Controls

- Require Service Item on Work Order (boolean)
- Allow Standalone Invoice (boolean)
- Allow Standalone Quote (boolean)

---

## 7.7 Plan & Storage Controls (Read-Only)

These values are system-controlled and not editable by Admin:

- Plan Storage Limit (3GB)
- Current Storage Used
- Max Attachments Per Record (10)
- Max Users (10)

---

# 8. Employee Roles (Lite)

## 8.1 Purpose

Employee Roles define access levels within the Lite system.

Lite includes exactly three system-defined roles:

- Administrator
- User
- Read-Only

Roles are fixed in Lite:
- No new roles may be created
- No roles may be edited
- No roles may be deleted

---

## 8.2 Admin Area (Lite)

The Admin Area exists for system configuration and accountability tools.

Only the **Administrator** role may access the Admin Area.

Admin Area includes:
- Employees
- Roles (view-only in Lite)
- Preferences
- Audit / Sessions
- Export Tools

---

## 8.3 Role Definitions

### Administrator

Administrators can:
- Perform all operational actions (same as User)
- Access the Admin Area

Administrators can:
- Create / Edit / Delete records (where allowed)
- Change status values
- Issue invoices, void invoices, write off invoices
- Apply and manage payments (from within invoices)
- Export data using Export Tools (Admin Area)
- Review accountability using Audit / Sessions (Admin Area)

---

### User

Users can:
- Perform all operational actions

Users cannot:
- Access the Admin Area (Employees, Roles, Preferences, Audit/Sessions, Export Tools)

Operational actions include:
- Create / Edit / Delete records (where allowed)
- Change status values
- Issue invoices, void invoices, write off invoices
- Apply and manage payments (from within invoices)

---

### Read-Only

Read-Only users can:
- Search records
- View records and list views
- View reports (list views)

Read-Only users cannot:
- Create
- Edit
- Delete
- Change status
- Issue/void/write-off invoices
- Apply payments
- Export data

---

## 8.4 Governance Rules (Lite)

1. Roles are system-defined and immutable in Lite.
2. Every Employee must be assigned exactly one role.
3. Role assignments and changes generate an Audit Event.
4. Accountability questions (e.g., "Who voided this invoice?") are answered via Audit/Sessions in the Admin Area.

Permission enforcement required.

---

# . Explicitly Out of Scope (Lite)

- Automation
- Recurring schedules
- Inventory movement
- Purchase Orders
- Receiving
- Multi-location
- API access
- SMS
- Advanced dashboards
- Document version control
- Compliance enforcement
- Cold archive
- Full structured export
- Restore capability

---

# 9. Employees (Lite)

## 9.1 Purpose

Employees represent internal system users.

Employees:
- Are system actors
- Are assigned exactly one Role
- Are referenced by Work Orders, Quotes, Tasks
- Are referenced in Sessions and Audit Events
- Are managed only within the Admin Area

Employees are not customers and are not part of HR management.

---

## 9.2 Admin-Only Access

- Employees are managed behind the Admin Area.
- Only Administrators may:
  - Create Employees
  - Edit Employees
  - Change Role
  - Change Status
- Employees cannot edit their own profile in Lite.

---

## 9.3 Core Fields (Lite)

### Identity
- `employee_uuid` (system identifier)
- `employee_number` (optional human-facing identifier)
- First Name
- Last Name
- `display_name` (calculated: First Name + " " + Last Name)

### Contact Information
- Address, City, State, Zip
- Phone 1
- Phone 2 (optional)
- Company Email (unique; used for login)
- Personal Email (optional)

### Employment Data (Lite Scope)
- Hire Date
- Termination Date (nullable)
- Notes (internal; Admin-only)

### Access Control
- Role (Administrator | User | Read-Only)
- Status (Active | On Leave | Inactive | Terminated)

### Audit Metadata
- Created At
- Updated At
- Created By
- Updated By

Passwords are managed by the authentication system and are never stored in plaintext.

---

## 9.4 Employee Lifecycle (Lite)

Status values:

- Active
- On Leave
- Inactive
- Terminated

Behavior:

Active:
- Can log in
- Can be assigned to records

On Leave:
- Cannot log in
- Not assignable to new records
- Historical assignments remain

Inactive:
- Cannot log in
- Not assignable
- Historical assignments remain

Terminated:
- Cannot log in
- Not assignable
- Record preserved for audit integrity

Employee records are never deleted in Lite.

---

## 9.5 Role Assignment Rules (Lite)

1. Every Employee must have exactly one Role.
2. Roles are fixed and immutable in Lite.
3. Only Administrators may change Role or Status.
4. Role and Status changes generate Audit Events.

---

## 9.6 Login & Session Enforcement (Lite)

- Only Employees with Status = Active may authenticate.
- Successful login creates a Session record.
- Audit Events reference the Session ID.
- Changing Status to Inactive or Terminated invalidates active sessions and blocks future login.

---

## 9.7 Operational Linkages (Lite)

Employees may be referenced in:

- Work Orders (Assigned User)
- Quotes (Assigned User)
- Tasks (Assigned User)
- Audit Events (actor reference)
- Sessions (login tracking)

If an Employee becomes Inactive or Terminated:
- Existing record references remain unchanged.
- Historical integrity is preserved.

---

## 9.8 Employee Seat Limit Enforcement (Lite)

Lite includes a maximum of 10 Employees per account.

### Seat Counting Rules

The following Employee Status values count toward the 10-user limit:

- Active
- On Leave
- Inactive

The following status does NOT count toward the limit:

- Terminated

An Employee must be set to Terminated in order to free a seat.
- Status = Terminated
- Termination Date must be set

An Employee may be reactivated if Terminated
- This will fail if there are no new seats available.
- Admin should be given an option to create a new seat with the increase in price.

---

### Admin Count Notification

- There needs to be some type of counter in the admin section to let the Administrator know how many seats are left
- When adding a new Employee the Admin should get a warning of the cost increase
- In the Employee section show the total number of used seats and it's current cost
   - Show: Seats used (x of 10) , Monthly Seat Cost at current seat rate, Individual Seat Cost if under 10 otherwise show 'Maximum Seats Reached'.
- In the Employee section show the current cost of what a new employee seat is near the 'Add' button.
   - This caps at 10 so once 10 is reached change to the word 'Maximum Seats Reached'.

---

### Enforcement Behavior

- If the account has 10 Employees with status:
  Active, On Leave, or Inactive,
  the system blocks creation of additional Employees.

- The system displays:
  "Maximum employee limit reached for Lite plan."

- Changing an Employee to Terminated:
  - Frees one seat immediately.
  - Does not delete historical references.
  - Preserves audit integrity.

---

### Governance

1. Employee records are never deleted.
2. Status = Terminated and Termination Date is required to release a seat.
3. Termination Date should be populated when Status = Terminated.
4. Reactivating a Terminated Employee requires:
   - Available seat under the plan limit.

---

# . MVP Completion Criteria

Lite is complete when:

1. End-to-end workflow functions:
   Company → Service Item → Quote → Work Order → Invoice → Payment

2. Storage cap operates correctly.

3. CSV export works from all major list views.

4. Roles enforce access properly.

5. No raw DB backup/restore exists in SaaS.

6. System is demo-ready without manual data intervention.

---

**End of Lite V1 Specification**