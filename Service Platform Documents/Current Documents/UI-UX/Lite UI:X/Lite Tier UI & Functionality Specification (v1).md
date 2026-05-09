# 📘 Lite Tier UI & Functionality Specification (v1)

**Handoff index:** see **`README.md`** in this folder (canonical entry point for agents and developers).

---

# 🎯 1. Objective

Define the **Lite Tier experience** as a fully self-contained product layer that:

* Competes directly with Jobber / Housecall Pro
* Prioritizes speed and simplicity
* Enforces clean operational workflows
* Hides all enterprise complexity
* Preserves data integrity for future upgrades

---

# 🧠 2. Core Philosophy

Lite is NOT a reduced Pro system.

It is a **simplified operational experience built on a full system backend**.

### Design Rules

* Hide complexity, don’t disable it
* Enforce real-world workflows
* Eliminate ambiguity
* Minimize user decisions

---

# 🧭 3. Navigation Structure (Sidebar)

## Primary Navigation

* Dashboard
* Customers
* Assets
* Jobs
* Schedule
* Quotes
* Invoices
* Payments

## Secondary Navigation

* Tasks
* Time Tracking
* Products & Services

## Settings

* Company Settings
* Users

### Critical Rule

* “Jobs” replaces “Work Orders” completely in Lite
* No internal terminology leakage

---

## Information architecture and entry points

### Service Requests (SR) vs Jobs

* **Service Request** is a first-class intake object (see **§17**). It is **not** a separate top-level sidebar item.
* **Jobs** is the primary operational hub for execution and scheduling (see **§3** primary nav and **§19**).

### Where users create and find Service Requests

* **New SR / intake:** A persistent primary action in the **app header** on every screen — label e.g. **New request** or **New intake** — opens the **single-screen intake** defined in **§16** (full-page route; suggested path `/intake`).
* **Secondary entry:** A prominent **same action** on the **Dashboard** is recommended for discoverability.
* **Finding open SRs:** The **Jobs** area must include a clear way to list **Open** and **Assigned** SRs (tabs, filters, or sub-nav such as **Requests** vs **Jobs**). Users must not need to open a Customer record as the only path to triage intake.

### Suggested routes (implementation may vary)

* `/intake` — intake
* `/jobs` — workflow hub (requests + jobs as above)
* `/jobs/:jobId` — job detail
* `/schedule` — scheduling
* `/customers`, `/customers/:id`, `/assets`, `/quotes`, `/invoices`, `/payments`, `/tasks`, `/time`, `/products`, `/settings/company`, `/settings/users`

Exact paths are not normative; behavior and discoverability are.

---

# 📊 4. Dashboard Definition

### Display ONLY

* Today’s Jobs
* Upcoming Schedule
* Open Invoices
* Recent Payments

### KPIs

* Jobs Today
* Revenue Today
* Outstanding Balance

### Explicitly Excluded

* Advanced reporting
* Custom dashboards
* Complex charts

---

# 📅 5. Lite Scheduling View

## 🎯 Purpose

Provide a simple scheduling workspace that allows users to organize Jobs by day, week, or month.

---

## 🧭 Views

* Day View
* Week View
* Month View
* Ordered Job List (for selected date range)

---

## 📊 Display Requirements

Each scheduled Job must display:

* Scheduled Time
* Customer Name
* Assigned User
* Job Status
* Short Description
* Asset reference (if present)

---

## ⚙️ Behavior Rules

* Jobs displayed in chronological order
* Users can quickly switch date ranges
* Users can open Jobs directly from the schedule
* Basic drag-and-drop scheduling allowed
* Reordering within a day allowed

---

## 📦 Unscheduled Jobs

System must provide a visible list of:

* Jobs without a scheduled date/time

Purpose:

* Prevent Jobs from being lost
* Allow quick assignment into schedule

---

## 🚫 Explicitly Excluded (Lite)

* Route optimization
* Advanced dispatch logic
* Multi-tech scheduling

---

## 🔒 Upgrade Hints (Contextual Only)

* "Advanced Scheduling (Plus)" — disabled
* "Route Optimization (Plus)" — disabled
* "Multi-Tech Scheduling (Plus)" — disabled

Tooltip: "Available in Plus"

---

## 🎯 UX Rules

* Must be usable without training
* Minimal controls only
* No complex filtering
* Should feel like a daily organizer, not a dispatch system

---

# 🔄 6. Core Workflow Model (FINALIZED)

## Primary Flow

Quote → Job → Invoice → Payment

## FINAL RULES

### Quotes

* Can ONLY convert to Jobs
* Cannot convert directly to Invoices

### Jobs

* Can exist WITHOUT a Quote
* Central object in the system
* REQUIRED for all Invoices

### Invoices

* MUST be created FROM a Job
* Cannot exist independently

### Payments

* MUST be applied to an Invoice

## Critical clarifications

1. **Quote directly to Invoice?** **No.** Invoices must come from Jobs so execution data stays tied to field work.

2. **Workflow backwards?** **No.** Forward-only transitions reduce inconsistent states.

3. **Invoice without a Job?** **No.** Jobs anchor all billing.

4. **Job without a Quote?** **Yes.** Supports emergency and direct service.

## Why this matters

This structure:

* Mirrors real-world operations
* Forces clean data
* Prevents edge-case logic explosion later

---

# 🧩 7. Feature Behavior

## Assets (CORE DIFFERENTIATOR)

Assets are a first-class entity in the system.

### Purpose

* Track all work performed on a specific asset
* Provide full service history independent of jobs

### Behavior

* Assets are linked to Customers
* Jobs are linked to Assets (optional but strongly encouraged)
* Each Asset maintains:

  * Service history (all related jobs)
  * Notes
  * Basic identifying information (type, model, serial, etc.)

### Key Rules

* Users can view all past work by Asset
* Jobs should be selectable/filterable by Asset

### UX Goal

* Users should think:
  "What has been done to this unit?"
  not just
  "What jobs have we done?"

### Why this matters

* Differentiates from job-centric systems
* Supports maintenance, repeat service, and long-term tracking

---

## Customers

* Create / Edit
* Basic contacts
* No segmentation or tagging systems

### Asset Integration

* Customers have associated Assets
* View all Assets linked to a Customer
* Ability to:

  * Add new Asset
  * Link existing Asset
  * View Asset service history

### UI Layout (Equal Weight Design)

Customer view must present:

* Customer Information
* Assets

With equal visual importance.

Recommended layout:

* Split view OR
* Tabbed view with:

  * Customer Details
  * Assets (default or co-equal prominence)

### UX Expectation

* Users should immediately understand that Assets are a core part of the Customer
* Navigation should feel natural:
  Customer → Assets → Service History
* Assets should never feel secondary or hidden

## Jobs

* Statuses: Open, Scheduled, In Progress, On Hold, Complete, Voided (see **§19** for transitions)
* No workflows exposed
* No automation rules

## Schedule

* Calendar + dispatch board
* Drag-and-drop only
* No optimization logic

## Quotes

* Built from Products & Services only
* Must convert to Job before invoicing
* No margin or cost visibility

## Invoices

* Generated from Jobs ONLY
* Simple totals
* No accounting logic

## Payments

* Record payment
* Link to invoice
* No reconciliation

---

# 🧾 8. Products & Services (MANDATORY SYSTEM)

## Rules

* ALL line items must come from Products & Services
* NO free-text entries allowed

## Behavior

Selecting a product auto-fills:

* Name
* Price
* Description

## Allowed

* Price override (enabled for flexibility)

## Hidden Fields

* Cost
* Vendor
* Inventory levels
* Warehousing

---

## Tax (Lite)

* Each **Products & Services** master row may carry a **taxable** flag (see **§24**).
* **Tax rate** is **not** entered on line items. It comes from **Tenant Settings** (single tenant default rate; see **§27**).
* On **Quotes** and **Invoices**, line tax amounts use that tenant rate applied to each **taxable** line’s extended amount (see **§18**, **§20**). **Users cannot override tax rate per line in Lite.**

---

# 🧠 9. Tasks & Time Tracking

## Tasks

* Basic create / assign / complete
* No dependencies
* No workflow integration

## Time Tracking

* Start / stop timer
* Attach to Job

---

# 🚫 10. Explicitly Hidden Features

The following MUST NOT appear anywhere in Lite:

* Pricebook
* Inventory (as a concept)
* Warehousing
* Procurement
* Vendors
* Purchase Orders
* Accounting (Ledger, COA, Banks)
* Financial Reports
* Workflow Engine
* Safety Forms
* Projects (Add-on locked)
* Fleet (Add-on locked)

---

# ⚙️ 11. UX Rules

* Max 5 fields per section
* No nested modals
* Default values wherever possible
* Use plain language only

---

# 🎯 12. Success Criteria

A new user MUST be able to:

1. Create a customer
2. Create a job
3. Schedule the job
4. Optionally create a quote
5. Convert quote → job (if used)
6. Move job through statuses
7. Generate invoice from job
8. Record payment

→ Without training

---

# ⚠️ 13. Risks

* Overexposing advanced concepts
* Allowing data inconsistencies
* Introducing unnecessary configuration

---

# 🧠 14. Strategic Role

Lite is the **customer acquisition engine**.

It must feel:

* Faster than Jobber
* Simpler than Housecall Pro

If it fails here, higher tiers become harder to sell.

---

# 🔥 15. Summary

Lite is:

* A clean, enforced workflow system
* A simplified UI over a powerful backend
* A foundation for seamless upgrades

---

# 📥 16. Service Request Intake Specification (Lite)

## 🎯 Objective

Define a **single-screen intake system** that:

* Captures real-world service requests quickly
* Resolves Customers and Assets intelligently
* Prevents duplicate data
* Keeps user fully in control

---

## 🧭 Layout Overview

The intake is a **single unified screen**:

### LEFT SIDE → User Input

### RIGHT SIDE → System Suggestions

No multi-step wizard.
No page transitions.

---

## 🧩 LEFT SIDE: USER INPUT

### Customer Information

* Customer Name (required)
* Phone (primary identifier)
* Secondary Phone (optional)
* Email (optional)
* Preferred Contact Method

### Location

* Service Address (required)

### Asset / Issue

* Asset Type (optional)
* Problem Category (required)
* Existing Issue Toggle (Yes/No)

### Details

* Problem Description (required)
* Internal Notes (optional)

### Priority

* Normal
* Urgent

---

## 🔍 RIGHT SIDE: SYSTEM SUGGESTIONS

Suggestions update **live as user types**.

### Matching Strategy (Hybrid Model)

* Strong matches shown at top
* Additional matches available via expansion

---

### 1. Customer Matches

Ranking priority:

1. Phone (highest weight)
2. Email
3. Name
4. Address

Each match displayed as a card:

Actions:

* Use This Customer
* Not This Person

Rules:

* Only one customer can be selected
* Selection locks customer identity

---

### 2. Address Matches

Display:

* Existing records tied to address
* Historical occupants

Actions:

* Use This Address
* New Occupant

Rule:

* Do NOT assume address = customer

---

### 3. Asset Matches

Shown when:

* Customer is selected OR
* Strong match exists

Filtered by:

* Asset Type (if provided)

Actions:

* Use This Asset
* Different Asset
* Continue Without Asset

---

## ⚙️ INTERACTION MODEL

### Selection Behavior

* Selecting an item = explicit action
* No checkboxes used
* No multi-select allowed

### UI Response

* Selected section collapses/locks
* Other suggestions update dynamically

---

## 🧠 DATA CREATION LOGIC

At submission:

System ensures existence of:

### Customer

* Use existing OR
* Create new

### Asset (optional)

* Use existing OR
* Create new OR
* Skip

### Service Request (always created)

---

## 🔄 OUTPUT STRUCTURE

Creates:

* Service Request

Linked to:

* Customer (required)
* Asset (optional)

Contains:

* Problem category
* Description
* Priority
* Notes

---

## 🔒 DATA INTEGRITY RULES

* No automatic matching
* User must confirm all matches
* System never overrides user decision
* Duplicate prevention handled via suggestions, not enforcement

---

## 🚫 WHAT IS NOT ALLOWED

* Auto-linking customers or assets
* Multi-selection of entities
* Free-text bypass of structured data
* Multi-step intake flows

---

## 🎯 UX GOALS

The intake should feel:

* Fast
* Intelligent
* Non-blocking
* User-controlled

User should think:

"The system is helping me, not fighting me"

---

## ⚠️ RISKS

* Overloading suggestions panel
* Too many weak matches visible
* Poor ranking of results

---

## 🧠 STRATEGIC VALUE

This intake system becomes:

* Primary system entry point
* Data quality gatekeeper
* Foundation for asset-centric workflows

---

# 🔧 17. Service Request Lifecycle (Technical Specification)

## 🎯 Definition

A Service Request (SR) is a **first-class intake object** responsible for:

* Capturing incoming service demand
* Managing assignment and review
* Controlling transition into Quote or Job

The SR does NOT manage outcomes. It hands off to downstream objects.

---

## 🧩 Core Statuses

Service Request statuses are:

1. Open
2. Assigned
3. Converted
4. Cancelled

---

## 📌 Status Definitions

### Open

* SR has been created
* No technician has taken ownership
* May or may not be assigned

### Assigned

* A technician has accepted responsibility
* Ownership is explicitly assigned

### Converted

* SR has transitioned to downstream object
* Triggered by FIRST occurrence of:

  * Quote creation OR
  * Job creation
* SR becomes LOCKED

### Cancelled

* SR is terminated without Quote or Job
* Requires:

  * Cancel reason
  * Cancel timestamp
* SR becomes LOCKED

---

## 🔄 Status Transition Rules

Allowed transitions:

* Open → Assigned

* Open → Converted

* Open → Cancelled

* Assigned → Converted

* Assigned → Cancelled

NOT allowed:

* Converted → any other state
* Cancelled → any other state

---

## ⏱ Timestamp Requirements

Each SR must record:

* Created DateTime
* Assigned DateTime (if applicable)
* Converted DateTime (first conversion event only)
* Cancelled DateTime (if applicable)

All timestamps must be audit-tracked with user reference.

---

## 🔗 Relationship Rules

### Customer

* REQUIRED
* Must be resolved before SR creation

### Asset

* OPTIONAL
* Can be:

  * Selected
  * Created
  * Added later

### Job

* Maximum: ONE per SR

### Quote

* Multiple allowed (**maximum five (5) per Service Request** in Lite)
* All linked to same SR

---

## 🔄 Conversion Rules

### Conversion Trigger

SR becomes Converted when:

* First Quote is created OR
* Job is created directly

### Conversion Behavior

* Converted timestamp set on FIRST trigger only
* SR becomes LOCKED immediately
* No further SR edits allowed

---

## 🧾 Quote Interaction Rules

Full customer-facing status model (**Draft**, **Sent**, etc.) is in **§18**. The rules below describe how Quotes interact with the **Service Request** regardless of marketing status names.

### Creation

* Multiple Quotes allowed (**maximum five (5)** per SR)
* Can be created until a Job exists

### Statuses (interaction outcomes referenced from §18)

* Accepted
* Declined
* Voided

### Rules

* Accepted Quote:

  * Triggers Job creation
  * All other Quotes automatically set to Declined

* Declined:

  * Set when customer chooses different option

* Voided:

  * Set by internal user decision only
  * Represents invalid/superseded Quote

### Restrictions

* Quotes CANNOT be deleted

---

## 🧱 Job Interaction Rules

### Creation

* Can be created:

  * Directly from SR OR
  * From Accepted Quote

### Constraints

* Only ONE Job per SR
* Once Job exists:

  * No new Quotes may be created from SR

---

## ✏️ Edit Rules

### Before Conversion

Editable fields:

* Customer contact info
* Address
* Asset
* Problem category
* Description
* Internal notes
* Priority
* Assignment

### After Conversion or Cancellation

* SR becomes READ-ONLY

---

## 🧾 Snapshot Rules

SR must store snapshot of:

* Customer info (name, phone, address)
* Asset info (if present)

Snapshots remain unchanged even if master records change later.

---

## 👥 Assignment Rules

* SR may exist unassigned
* Assignment is optional
* Any user can assign or reassign before conversion

---

## 👁 Visibility Rules

* All users can view all SRs

---

## 🧠 Priority Rules

* Priority is informational only
* Does not trigger automation in Lite

---

## 🚫 Deletion Rules

* SR cannot be deleted
* Must be Cancelled instead

---

## 🔁 Reuse Rules

* Cancelled SR cannot be reopened
* Cannot be duplicated automatically

---

## ⚠️ Integrity Rules

* No automatic conversion
* No reversal of conversion
* No multi-job creation
* No quote deletion

---

## 🔥 Summary

The Service Request acts as:

* Intake and triage record for new demand
* Parent context for Quotes until a Job exists or the SR is cancelled
* Controlled handoff into Job execution and billing

---

# 🔧 18. Quote Lifecycle (Technical Specification)

## 🎯 Definition

A Quote is the pricing and decision object presented to a Customer. In Lite, Quotes are created in the context of a **Service Request** until that SR is converted or cancelled.

---

## 🧩 Statuses

1. Draft
2. Sent
3. Accepted
4. Declined
5. Voided

---

## 🔄 Transitions

* Draft → Sent (including customer send per **§26**)
* Draft → Voided
* Sent → Accepted
* Sent → Declined

---

## 🧾 Rules

* Quotes **cannot** be deleted.
* **Maximum five (5) Quotes per Service Request** in Lite. No new Quotes once a **Job** exists for that SR (see **§17**).
* **Accepted** Quote creates **exactly one** Job; all other Quotes on that SR become **Declined** automatically.
* Quote lifecycle must remain consistent with **§17** (SR lock on conversion).

---

## ✏️ Edit Rules

* **Draft:** fully editable (line items, customer-facing notes where applicable).
* **Sent** and later: **locked** for structural edits; only allowed status transitions apply.

---

## 🔒 Lite constraints

* "Duplicate Quote (Plus)" is disabled with upgrade tooltip (see **§21**).

---

## 💵 Tax and totals (Lite)

Quotes use the **same tenant tax rate, rounding, and currency rules** as Invoices (**§27**, **§20**).

* **Per line:** For each **taxable** line, compute tax from the line extended amount and the **Tenant Settings** tax rate (users cannot change rate per line in Lite).
* **Document:** Show **subtotal** (sum of extended line amounts), **tax total** (sum of line taxes), and **grand total**.
* **Checkbox (Draft only):** **Include tax in total** (or equivalent plain-language label) — when **checked**, **grand total = subtotal + tax total**; when **unchecked**, **grand total = subtotal** only, while the **tax total** row remains visible so the customer still sees the tax figure.
* **Sent:** Tax amounts and the **applied tenant tax rate** are **snapshotted** on the document (see **§20** snapshot pattern).

---

# 🔧 19. Job Lifecycle (Technical Specification)

## 🎯 Definition

A Job represents **execution of work** for a Customer, optionally linked to **one Asset**, and tied to **at most one** Service Request in Lite.

---

## 🧩 Statuses

1. Open
2. Scheduled
3. In Progress
4. On Hold
5. Complete
6. Voided

---

## 🔄 Transitions

* Open → Scheduled
* Scheduled → In Progress
* In Progress → Complete
* Any non-terminal → On Hold
* Any non-terminal → Voided (**void reason required**)

---

## 🧾 Rules

* **One Job per Service Request** in Lite.
* **One Asset per Job** in Lite (see **§22**).
* **Invoice must be created from a Job** (see **§6** and **§20**).

---

## ✏️ Edit Rules

* Editable until **Complete** or **Voided**.
* **Complete** and **Voided** are terminal and locked.

---

## 🔒 Lite constraints

* Multi-asset per Job and multi-tech dispatch are Plus (disabled hints only).

---

# 🔧 20. Invoice Lifecycle (Technical Specification)

## 🎯 Definition

The Invoice is the billing document created **from a Job**. Customer-facing content and line items are fixed when the document is sent.

---

## 🧩 Statuses (Lite)

1. Draft
2. Sent
3. Paid
4. Voided

**Plus (not reachable in Lite):** Partially Paid — may appear only as a **disabled / upgrade hint**, not as a real state in Lite.

---

## 🔄 Transitions

* Draft → Sent
* Draft → Voided
* Sent → Paid (when payment is recorded per **§25**)
* Sent → Voided (only when **no** payments exist)

---

## 🧾 Rules

* Created **only** from a Job.
* **One active non-voided Invoice per Job** at a time in Lite (Draft or Sent counts as active).
* If an Invoice is **Voided**, a **new** Draft may be created from the same Job **only if** no other Draft or Sent Invoice exists for that Job.
* Invoices cannot be deleted; use **Voided**.

---

## 💵 Tax calculation and invoice total (Lite)

### Source of rate

* **Tenant Settings** defines the **default tax rate** for the tenant. That rate is applied to **each taxable invoice line** (taxability comes from the **Products & Services** taxable flag on the line snapshot — **§24**).
* **Per-line tax rate override is not available in Lite** (Plus may add jurisdictions / multiple rates later).

### Per-line calculation

* For each line: **extended amount = quantity × unit price** (after any allowed price override).
* For each **taxable** line: **line tax = extended amount × (tenant tax rate ÷ 100)** using **calculation precision** from **Tenant preferences** (see **§27**; default **3** decimal places internally).
* **Invoice tax total** = sum of line tax amounts (same internal precision, then **display** rules apply).

### Presentation

* The invoice shows **subtotal** (sum of extended amounts), **tax total**, and **grand total**.
* **Checkbox (editable in Draft):** Controls whether tax is **included in the grand total**:
  * **Checked:** **grand total = subtotal + tax total** (tax is added to what the customer owes).
  * **Unchecked:** **grand total = subtotal**; **tax total** row is **still shown** so the document remains transparent, but that tax is **not** added into the amount due.
* **Currency symbol** follows **Tenant preferences** everywhere monetary amounts appear (**§27**).

### Draft vs Sent

* **Draft:** Totals **recalculate** when lines change or when **Tenant Settings** tax rate / rounding preference change (user should see current tenant defaults).
* **Sent** (and later): Tax line amounts, **applied tenant tax rate**, subtotal, tax total, **include-tax-in-total flag**, and grand total are **snapshotted** and **locked** for that document.

---

## ✏️ Edit Rules

* **Draft:** editable.
* **Sent** and **Paid:** locked except **Admin** corrections described under **§25** and **Invoice reopen** below.

---

## Invoice reopen (Lite)

* **Admin only.**
* **Sent → Draft** only when **no Payments** exist.
* If any payment exists, reopen is **blocked**; use void-and-reissue per product policy.

---

## 🔒 Lite constraints

* No partial payments (upgrade hint only; see **§21**).

---

# 🎛 21. Upgrade Hinting Rules (Lite)

## 🎯 Objective

Provide non-intrusive, contextual upgrade hints that:

* Do NOT block core workflows
* Do NOT create frustration
* Clearly communicate higher-tier capabilities

---

## 🧭 General Rules

1. Show hints ONLY at natural friction points
2. Maximum 1–2 hints per screen
3. Use explicit labels with tier callout (e.g., "(Plus)")
4. Disabled controls MUST include tooltip: "Available in Plus"
5. Never disable a core action required to complete work

---

## 🔒 Standard Pattern

* Control visible but disabled (greyed)
* Tooltip on hover: "Available in Plus"

---

## 📌 Implemented Hints in Lite

### Quotes

* "Duplicate Quote (Plus)" — disabled

### Line Items

* "Advanced Edit (Plus)" — disabled

### Invoices

* "Partial Payment (Plus)" — disabled

---

## 🚫 Prohibited

* Multiple disabled controls in same context
* Vague labels (e.g., "Edit") for disabled features
* Blocking completion of core workflows

---

## 🧠 UX Goal

User perception should be:

"This works great—and I can see how it can do more"

NOT:

"This product is missing features"

---

# 🔧 22. Asset Structure and Rules (Technical Specification)

## 🎯 Definition

An Asset represents a **physical piece of equipment owned by a Customer**.

Assets are used to:

* Track service history
* Provide context for Jobs
* Support long-term maintenance tracking (future tiers)

Assets are NOT:

* Required for all workflows
* Shared across customers simultaneously

---

## 🧩 Core Rules

* Asset is OPTIONAL but strongly encouraged
* Asset belongs to ONE Customer at a time
* Asset may transfer ownership over time (history retained)

---

## 📌 Required Fields

Minimum required to create an Asset:

* Asset Type
* Location (Customer Address)

---

## 📌 Optional Fields

Available (simple UI, optional):

* Serial Number
* Model
* Manufacturer
* Install Date
* Warranty Info
* Internal Notes

---

## 🧩 Asset Types

* Fixed predefined list in Lite
* Expanded/custom types available in higher tiers

---

## 🔗 Relationship Rules

### Customer

* REQUIRED

### Job

* One Job may link to ONE Asset
* Jobs without Asset allowed

### Service Request

* Optional Asset link

---

## 📊 Asset History (Core Feature)

Each Asset must display:

* All linked Jobs
* All linked Service Requests
* All linked Quotes
* All linked Invoices
* Internal Notes / Activity log

### Recent Activity (Lite Enhancement)

Display most recent activity items:

* Last Job performed
* Last Service Date
* Last recorded issue

This provides quick visibility without requiring full history navigation.

---

## 🧾 Edit Rules

* Asset is editable after creation
* All edits must be audit-tracked:

  * Field changed
  * Previous value
  * New value
  * User
  * Timestamp

---

## 🚫 Deletion Rules

* Asset can be deleted ONLY if no linked records exist
* Otherwise deletion is blocked

---

## 🔁 Duplicate Handling

* Duplicate Assets allowed in Lite
* No merge functionality in Lite

---

## 📍 Location Rules

* Asset is tied to Customer primary address
* Multi-location asset support reserved for higher tiers

---

## 🧠 Asset Status

Statuses:

* Active
* Inactive

Rules:

* Inactive Assets are hidden from selection lists
* History remains accessible

---

## 🧾 Notes

* Assets support INTERNAL notes only
* Notes follow system-wide note behavior

---

## ⚙️ Workflow Behavior

* Asset selection is optional in SR and Job
* System does not force selection
* UX may suggest assets but does not enforce

---

## 🔒 UI Constraints (Lite vs Plus)

### Multiple Assets per Job

* Lite: ONE Asset only
* "Add Multiple Assets (Plus)" control is visible but DISABLED
* Tooltip: "Available in Plus"

---

## 🧠 Future Hooks (Not Active in Lite)

Assets are designed to support:

* Recurring maintenance scheduling
* Asset lifecycle tracking
* Performance analytics

These features are hidden in Lite but structure must support them.

---

## 🔥 Summary

The Asset acts as:

* Service history anchor
* Context layer for Jobs and Requests
* Foundation for future maintenance features

---

# 🔧 23. Customer Structure and Rules (Technical Specification)

## 🎯 Definition

A Customer represents a **company or household entity** that owns work, assets, and financial transactions within the system.

Customers are the **root entity** for:

* Service Requests
* Quotes
* Jobs
* Invoices
* Assets

---

## 🧩 Core Structure

### Contact Model (Lite)

* One primary contact
* One secondary contact
* Implemented as fields on the Customer record (no separate contact entity in Lite)

---

## 📌 Required Fields

Minimum required to create a Customer:

* Name
* Primary Phone
* Address (Billing)

---

## 📌 Address Structure

Lite supports:

* One Billing Address (required)
* One Shipping Address (optional)

Rules:

* Managed as fields on Customer record
* No separate address entity in Lite

---

## 📌 Communication Fields

* Primary Phone (required)
* Secondary Phone (optional)
* Primary Email (optional)
* Secondary Email (optional)

---

## 🧩 Customer Type

Supported types:

* Residential
* Commercial

---

## 🔗 Relationship Rules

### Assets

* Customer may have zero or many Assets
* Assets are optional but encouraged

### Service Requests

* Must link to Customer

### Quotes

* Must link to Customer

### Jobs

* Must link to Customer

### Invoices

* Must link to Customer

---

## 📊 Customer Record View

Customer screen layout:

* LEFT: Customer information
* RIGHT: Asset list

### Summary Section

Display:

* Recent Activity

  * Last Job
  * Last Service Date
  * Last Issue

---

## 🧾 Customer History (Full View)

Customer record must display:

* Service Requests
* Jobs
* Quotes
* Invoices
* Assets

---

## ✏️ Edit Rules

* Customer is fully editable
* Changes are NOT field-level audited in Lite

---

## 🚫 Deletion Rules

* Customer can be deleted ONLY if no linked records exist
* Otherwise deletion is blocked

---

## ⚠️ Duplicate Handling

* System must:

  * Attempt duplicate detection
  * Warn user of potential duplicates
  * **BLOCK** creation when **primary phone** exactly matches an existing **Active** Customer (exact match rule for Lite)

Matching priority:

1. Phone
2. Address
3. Name

---

## 🧠 Status Rules

Customer statuses:

* Active
* Inactive

Rules:

* Inactive Customers are hidden from selection lists
* Historical records remain accessible

---

## 🧾 Notes

* Customers support INTERNAL notes only
* Notes follow system-wide behavior and flow through related records

---

## 🧾 Snapshot Rules

All downstream objects must store a snapshot of Customer data at time of creation.

Changes to Customer do NOT retroactively affect:

* Service Requests
* Quotes
* Jobs
* Invoices

---

## 🔁 Ownership and History Integrity

* Customer remains tied to all historical records
* Address changes do NOT affect historical linkage
* New occupants at same address must be treated as new Customers

---

## ⚙️ Creation Points

Customer may be created from:

* Intake
* Customer screen
* Any workflow requiring a Customer

---

## 🔥 Summary

The Customer acts as:

* Root ownership entity
* Anchor for all transactional records
* Context provider for Assets and Service history

---

# 🧾 24. Products & Services Rules (Technical Specification)

## 🎯 Definition

Products & Services (P&S) are the **master line-item catalog** used on Quotes, Jobs, and Invoices. Transactional documents store **snapshots** of line data (see **§8** and **Snapshot Rules** below).

---

## 📌 Required fields (master record)

* Name
* Type
* Default Price
* Description
* Status (Active / Inactive)

---

## 📌 Optional fields (master record)

* SKU / Item Code
* Taxable flag
* Default labor / time indicator (if used in UI)

---

## 👥 Permissions

### Admin

* Create, edit, activate/deactivate P&S
* Delete **only** if the record has **never** been used on any Quote, Job, or Invoice

### User

* Select P&S on Quotes, Jobs, and Invoices
* **Price override** on the transactional line only (does not change the master record)

Users **cannot** edit master P&S records.

---

## Line items (Quotes, Jobs, Invoices)

* Users may **add and remove** line rows while the parent document is **editable** (Quote Draft; Job not terminal; Invoice Draft).
* **Quantity:** positive numeric; default **1**.
* **Display order:** user-reorderable while editable; order is **snapshotted** when the parent becomes locked (e.g. Quote Sent, Invoice Sent, Job Complete — exact lock points follow parent lifecycle sections).
* **Price override:** allowed on the line; audit per system rules.
* **No free-text-only lines** — every line must reference a P&S row (see **§8**).
* **Tax:** Taxability follows the **taxable** flag on the line (from P&S at add time). **Tax rate** always comes from **Tenant Settings** on **Quote** and **Invoice**; **not editable per line in Lite**. **Job** line items in Lite store **amounts only**; formal tax totals and customer documents follow **Quote** / **Invoice** (**§18**, **§20**).

---

## ✏️ Edit rules (master)

* Edits to master P&S are **forward-looking**; historical documents do not change.

---

## 🧾 Snapshot rules (transactional)

When a P&S row is added to a document, the line must snapshot at minimum:

* Name
* Description
* Unit price (after any override at add time)
* Quantity
* Taxable flag (if used)

When a **Quote** or **Invoice** is **Sent**, each line must additionally snapshot **line tax amount** (computed per **§18** / **§20**), and the document header must snapshot **applied tenant tax rate**, **subtotal**, **tax total**, **include-tax-in-total** checkbox value, and **grand total**.

---

## 🧠 Audit rules (master)

Audit applies to creation, status changes, and material field changes (including default price).

---

## 🚫 Deletion rules (master)

* Cannot delete if referenced on any Quote, Job, or Invoice.

---

# 💳 25. Payment Rules (Technical Specification)

## 🎯 Definition

Payments are financial records **applied to an Invoice** (see **§6**).

---

## 🧾 Fields

* Amount (must equal the Invoice **grand total** in Lite — the total defined in **§20**, respecting **include tax in total**; single full payment)
* Date
* Payment Method
* Reference / Notes (optional)

---

## Payment methods (Lite)

System-defined selectable values (labels may be localized):

* Cash
* Check
* Credit Card
* ACH / Bank transfer
* Other

---

## ⚙️ Behavior

* **One payment per Invoice** in Lite; paying the **full** total sets Invoice to **Paid** (see **§20**).
* No partial payments, no overpayments.

---

## ✏️ Edit rules

* **Admin** may correct **Payment Method**, **Reference / Notes**, and **Date** (correction only), with audit.
* **Amount** is **not** editable after save; void payment / void invoice / re-enter per controlled process (product may require support workflow — out of Lite scope).

---

# 📧 26. Notification and Communication Rules (Technical Specification)

## 🎯 Definition

How Quote and Invoice delivery works in Lite. **Lite is manual-delivery only — the system does NOT originate emails to customers.** Users deliver documents via their own email client (Outlook, Gmail, Apple Mail, etc.). The app provides the state transition, snapshot, lock, and a printable document; the user handles the actual email send.

---

## Quote "Send" action

* The Send action transitions status **Draft → Sent** (see **§18**).
* This triggers the snapshot and lock per §18.
* **Requirement:** Customer must have **at least one** email on record (used for reference and to pre-fill delivery helpers); otherwise Send is **blocked** with a clear validation message.
* **The system does NOT send an email.** The user is responsible for delivering the Quote to the customer via their own email client.

---

## Invoice "Send" action

* The Send action transitions **Draft → Sent** (see **§20**).
* Triggers snapshot and lock per §20.
* **Requirement:** Customer must have **at least one** email on record.
* **The system does NOT send an email.** The user is responsible for delivery.

---

## Delivery format (Lite)

* **No server-side PDF generation.** The user prints the Quote or Invoice from the browser using the browser's built-in Print command. The app ships robust `@media print` CSS so the printed output is clean 8.5x11 with no UI chrome, no navigation, no buttons. See Tech Arch V2 §3.2.
* The printed document reflects **subtotal**, **tax total**, **grand total**, **currency symbol**, and the **include tax in total** treatment per **§18** / **§20** (snapshotted values locked at Sent).
* The user attaches the printed PDF to a message in their own email client and sends it to the customer.
* The app **may** provide a `mailto:` helper link that pre-fills the To address and subject; message body, attachment, and actual send are the user's responsibility.
* **No customer portal** in Lite.

---

## Reply handling

* Replies go directly to the user's own email client (since that is what originated the message). Lite **does not** ingest, thread, or log replies. Users track correspondence in their own email.

---

## Evolution to Plus

Plus introduces system-originated customer emails via Postmark, with server-generated PDF attachments (WeasyPrint), automated reminders, and tracked delivery. Lite's manual-delivery pattern remains available in Plus+ as a fallback. See Tech Arch V2 §3.2 and Email Specification V1 §4.1.

---

## 🚫 Excluded in Lite

* Automated reminders, ETA texts, workflow-driven messaging, and in-app customer chat.

---

## 🧾 Content rules

* Customer-facing notes may be included; **internal notes are never** included.

---

## 🧠 Audit

System must record: sent by (user), timestamp, recipient email, document type (Quote or Invoice).

---

# 🖥 27. Navigation, Permissions, and Screen-Level Behavior

## 🎯 Role model (Lite)

Two roles: **Admin** and **User**.

---

## 🏢 Tenant preferences (financial) — Lite

These settings live in **Tenant / Company Settings** (and related **preferences**). They drive **§8**, **§18**, **§20**, **§24**, and **§25**.

### Tax rate

* **Admin** maintains a **single default tax rate** (percent) for the tenant.
* It is applied to **taxable** line items on **Quotes** and **Invoices** per **§18** and **§20**.
* **Users cannot override** this rate per line in Lite.

### Currency

* **Currency** (and display of the **currency symbol**) is set in tenant preferences.
* Show the symbol **wherever monetary amounts appear** (lists, detail, Quote, Invoice, PDFs, payments).

### Rounding and display precision

* **Tenant preference** controls **calculation decimal precision**. **Default: 3** decimal places for **internal** tax and money calculations.
* **User interface** displays standard **2** decimal places for currency amounts.
* Implementations **must** use the configured precision **behind the scenes** (e.g. line tax accumulation) and **round for display** to 2 decimals consistently on screen and on customer-facing PDFs unless legal rules require otherwise in a future revision.

---

## 👥 Admin

* Full CRUD on all entities where business rules allow
* **User management** and **Company Settings**
* **Reopen Invoice** (Draft) when allowed by **§20**
* **Edit payments** within **§25** limits
* **Delete** only where entity rules explicitly allow

---

## 👤 User

* Create and manage Customers, Service Requests, Jobs, Quotes, Invoices (within status rules)
* Schedule jobs, record **payments** (full amount per **§25**)
* **View all records** (no per-user data hiding in Lite)

Users **cannot**:

* Manage users or company settings
* Perform restricted **Admin** financial corrections

---

## 👁 Visibility

* **All users see all company records** in Lite (no territory or team segmentation).

---

## 🧭 Navigation behavior

* **Sidebar** matches **§3** for all roles (no feature hiding by role except **Settings** entries may be Admin-only).
* **Intake** is always available from the **header** (see **§3**).

---

## Screen-level expectations

### Tasks (**§9**)

* List + detail: create, assign, complete; no dependencies or workflow engine.

### Time Tracking (**§9**)

* Start/stop timer and manual entry; attach to **Job** where applicable.

### Company Settings (**Admin**)

* Minimum for Lite outbound email/PDF: company name, branding as needed, **from** email identity.
* **Financial:** default **tax rate**, **currency**, **calculation precision** (see **Tenant preferences** above); Quote/Invoice tax behavior per **§18** / **§20**.
* Exact field list may expand; must not contradict **§10** hidden features.

### Record interaction

* Click row → **detail** view; primary actions visible without buried menus.
* Disabled controls follow **§21** upgrade rules.

### Status changes

* Simple controls (dropdown or explicit buttons); no builder or automation.

---

## 🎯 UX goal

A new user answers **“where do I do X?”** from **§3** and this section without training.

---

# ✅ 28. System Completion Status (Lite)

The following are **specified in this document** for Lite UI and behavior:

* Information architecture and intake entry (**§3**, **§16**)
* Dashboard and schedule (**§4**, **§5**)
* Core workflow (**§6**) and feature behavior (**§7**–**§11**)
* Service Request lifecycle (**§17**) and Quote / Job / Invoice lifecycles (**§18**–**§20**)
* Upgrade hinting (**§21**)
* Asset and Customer (**§22**–**§23**)
* Products & Services and line items (**§8**, **§24**)
* Tenant tax, currency, rounding preferences (**§27**)
* Payments (**§25**)
* Customer email/PDF (**§26**)
* Roles and screens (**§27**)

Implementation-ready **UI design** (visual design system, components) and **backend/API** contracts may still be defined in separate artifacts but **must not contradict** this spec.

---

# 📋 29. Implementation backlog and open decisions

Use this section to track gaps **without** silently inventing product behavior.

## Resolved here (formerly ambiguous)

* **Service Request navigation:** Intake from header + Jobs hub lists open SRs (**§3**).
* **Quote cap:** Five Quotes per SR (**§17**, **§18**).
* **Job statuses:** Open through Voided (**§7**, **§19**).
* **Invoice void / re-issue:** One active non-voided Invoice per Job; new Draft after Void allowed when no other active invoice (**§20**).
* **Payments:** One full payment; method enum (**§25**); amount equals invoice grand total per **§20** / **§25**.
* **Tax (Lite):** Single tenant tax rate; per-line tax on taxable Quote/Invoice lines; **include tax in total** checkbox on Quote/Invoice; internal calc precision default **3**, display **2**; currency/symbol from tenant preferences (**§8**, **§18**, **§20**, **§24**, **§27**).

## Resolved on 2026-04-24 (see `Architecture & Planning/LITE_DECISIONS.md`)

* ~~**Company Settings (full field list):** Numbering prefixes, email footer, business hours if shown to customers (beyond tax/currency/precision now in **§27**).~~ → Resolved §B: identity, financial, operations fields. **Numbering prefixes are NOT Lite-editable** — Lite tenants receive system defaults.
* ~~**Asset type list (Lite):** Enumerate allowed asset types or seed data.~~ → Resolved §A: tenant-controlled `ValueList`, seeded at provisioning with common service-trade types.
* ~~**Global search / filters:** Behavior for header search, list filters, and mobile layouts.~~ → Resolved §D: scope = Customers + Jobs + Invoices, prefix match.
* ~~**Void reasons:** Whether Quote/Invoice void require reason codes in addition to Job void (currently Job void requires reason — align UX).~~ → Resolved §C: optional free-text, no structured list.
* ~~**Accessibility and localization:** WCAG target, i18n strategy.~~ → Resolved §E: WCAG 2.1 AA informal (spot-check, no formal audit for MVP). i18n deferred to a future tier.
* ~~**Integrations:** Card processing (if any) vs manual "Credit Card" logging in Lite.~~ → Resolved §F: manual logging only in Lite; card processing begins in Plus.

## Still to specify (recommended next documents)

*(Nothing currently open. Add items here if new gaps surface.)*

---

**Document maintenance:** When you close an item above, move the decision into the relevant numbered section and trim this backlog.
