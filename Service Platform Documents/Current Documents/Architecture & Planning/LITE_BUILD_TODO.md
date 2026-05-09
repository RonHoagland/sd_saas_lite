# ServizDesk Lite — Build Todo List

**Generated:** April 18, 2026
**Status:** In Progress
**Scope:** Full Lite MVP build against `sdservice02` codebase and `Lite Tier UI & Functionality Specification (v1).md`

---

## How to use this list

Items are grouped by phase. Complete phases in order — each phase is a prerequisite for the next.
Mark items with ✅ when done.

Status key:
- 🔴 **Phase 1** — Shell & Navigation (blocks everything else — do first)
- 🟠 **Phase 2** — Core Intake & Customer Flow
- 🟠 **Phase 3** — Assets
- 🟡 **Phase 4** — Jobs (Core Execution Object)
- 🟡 **Phase 5** — Quotes
- 🟡 **Phase 6** — Invoices & Payments
- 🟢 **Phase 7** — Catalog & Utility Modules
- 🟢 **Phase 8** — Schedule & Settings
- 🔵 **Phase 9** — Polish & Compliance

---

## Current State Summary

### What exists today
- Login page (`splash_login.html`) + home dashboard shell (`home.html`) + customers overview (`customers_dashboard.html`) — all templates present but KPIs not wired to live data
- Sidebar (`app_sidebar.html`) currently lists cross-tier modules (Leads, Opportunities, Preventative Maintenance, Safety Forms, Workflows, Inventory, Price Book, Equipment, Procurement, RMAs, Vendors, Warehousing). Per LITE_DECISIONS.md §H, keep the tier-aware nav but hide items not available in the tenant's tier.
- **Two conflicting template systems** in the same project — both get replaced in Phase 1:
  - `base.html` currently loads Tailwind via CDN. Per LITE_DECISIONS.md §I, swap to Bootstrap 5.
  - `app_dashboard.html` + `theme.css` (older — retire).
- Backend models exist for Customer, ServiceRequest, WorkOrder, Asset, etc.
- **Zero views or URL routes** for any module beyond home/login — only `config/views.py` is wired
- Only two URL routes exist: `/` (login) and `/home/`

### Spec references
All spec docs live under `/Volumes/SolDev_10/SaaS/Service Platform/Service Platform Documents/Current Documents/`.
- UI spec (canonical): `UI-UX/Lite UI:X/Lite Tier UI & Functionality Specification (v1).md`
- **Visual design authority (prototype):** `UI-UX/UIX Prototypes/lite-shell-prototype.html` — interactive HTML prototype with fully rendered designs for Login, Dashboard, Customer List, New Customer form, and Invoice Detail. Reference this for visual and interaction patterns, but replace the Tailwind classes with Bootstrap 5 equivalents and drop the Stripe "Copy Payment Link" button per LITE_DECISIONS.md.
- Data: `Specifications/ServizDesk_Data_Models_V6.md`
- Architecture: `Architecture & Planning/ARCHITECTURE.md` (codebase reference) + `Specifications/ServizDesk_Technical_Architecture_V2.md` (note: Tech Arch V2 still names Tailwind; superseded for Lite by LITE_DECISIONS.md §I)
- Permissions: `Specifications/ServizDesk_Permission_Management_Specification_V2.md`
- Decisions: `Architecture & Planning/LITE_DECISIONS.md`

### UI Patterns established in the prototype (use consistently)
These patterns are defined in `lite-shell-prototype.html` and must be used across all new templates:
- **Inline edit pattern** — section card with pencil icon top-right; click opens edit mode within the same card; cancel/save buttons in card footer; "Unsaved changes" dirty hint appears on input
- **Drawer edit pattern** — right-side sliding drawer (560px wide) for complex sub-forms like line items; drawer has header, scrollable body, save/cancel footer
- **Activity timeline** — right context panel on detail pages; chronological list of events with icon, description, user + timestamp
- **Context panel** — detail pages use a 2/3 + 1/3 column split; left = main canvas, right = context panel (notes, activity, status actions)
- **Breadcrumb nav** — in topbar, dynamically updated per route
- **Stat strip** — 3–4 stat cards at top of list pages with colored accent bar
- **Topbar** — company name left, breadcrumb center, search + utility icons right

### Sidebar nav — resolved per LITE_DECISIONS.md §H
Nav is tier-aware: the full cross-tier nav exists, and items not available in the current tenant's tier are hidden. For Lite, this means the user sees: Dashboard, Customers, Assets, Jobs, Schedule, Quotes, Invoices, Payments, Tasks, Time Tracking, Products & Services, Company Settings, Users. Higher-tier items (Leads, Opportunities, Workflows, Inventory, Price Book, Procurement, etc.) are hidden for Lite tenants.

Note: this supersedes spec §3's prescription of a flat Lite-only nav. Flag the conflict in the spec update pass (see LITE_DECISIONS.md follow-ups).

### Backend systems already built (do not rebuild)
The following are fully implemented and tested in `sdservice02` per `ARCHITECTURE.md`:
- Multi-tenancy: `TenantModel`, `TenantManager`, `TenantMiddleware`, RLS (all models already have tenant_id)
- Numbering: `NumberingMixin`, `NumberingRule`, `NumberSequence`, `AssignedNumber` — numbers are assigned by explicit call, not auto-save
- Lifecycle state machine: `LifecycleMixin`, `LifecycleStateDef`, `LifecycleTransitionRule`, `LifecycleTransitionAudit`
- Notes system: `Note` model, `create_note()` / `get_notes_for_entity()` services
- Documents/file storage: `Document`, `FileUploadLog`, `FileDownloadLog`, scan status, dual backends (local/S3)
- Background tasks: `TenantAwareTask` base class, Celery integration
- Value lists: `ValueList`, `ValueListItem` — tenant-configurable picklists already seeded

---

## 🔴 Phase 1 — Shell & Navigation

> These items block everything else. No other page can be built consistently until the shell is correct.

- [ ] **1.1 — Rewrite `base.html` on Bootstrap 5 and fix the sidebar** (`templates/base.html`, `templates/includes/app_sidebar.html`)
  - Remove the Tailwind CDN script; include Bootstrap 5.3 CSS + bundle JS (via CDN or vendored into `static/`).
  - Replace the hand-written CSS classes in `base.html` (`btn-primary`, `stat-card`, `nav-item`, `section-card`, etc.) with Bootstrap classes + a small `static/css/site.css` for ServizDesk branding.
  - Keep Lucide icons.
  - Sidebar: use Bootstrap's collapse/nav components; render the full cross-tier nav, but hide items not in the current tenant's tier (per LITE_DECISIONS.md §H). For Lite the visible items are: Dashboard, Customers, Assets, Jobs, Schedule, Quotes, Invoices, Payments, Tasks, Time Tracking, Products & Services, Company Settings (Admin only), Users (Admin only).

- [ ] **1.2 — Add "New Request" intake button to the app header**
  Persistent on every screen. Label: "New Request" or "New Intake". Opens `/intake`. Per spec §3 critical rule.

- [x] **1.3 — Retire the legacy template system** *(done 2026-04-24)*
  Deleted: `templates/layouts/app_dashboard.html`, `templates/customers_dashboard.html`, `static/css/theme.css`, `static/css/home.css`, `static/css/splash_login.css`.

- [ ] **1.5 — Rewrite `users/*.html` templates on Bootstrap** *(deferred to Phase 8.3)*
  The existing `templates/users/*.html` (employees, employee_detail, tenant_preferences, departments, positions, roles) were written against Tailwind. With the Tailwind CDN removed in Phase 1.1, these pages render on bare Bootstrap/browser defaults — functionally usable but visually unstyled. Rewrite them as part of Phase 8.2 (Company Settings) and Phase 8.3 (User Management), which specify the final Lite-spec layouts for these admin pages.

- [ ] **1.4 — Wire the Dashboard KPI cards (`home.html`) to real data**
  - "Requests" card → count of open ServiceRequests for tenant
  - "Quotes" card → count of open (Draft + Sent) Quotes
  - "Jobs" card (rename from "Work Orders") → count of open Jobs
  - "Invoices" card → count of unpaid (Draft + Sent) Invoices
  - "Today's Schedule" list → Jobs scheduled for today

---

## 🟠 Phase 2 — Core Intake & Customer Flow

- [ ] **2.1 — Service Request Intake page** (`/intake`)
  Single-screen split layout per spec §16. No wizard, no page transitions.
  - **Left side (user input):** Customer Name, Phone (primary), Secondary Phone, Email, Preferred Contact Method, Service Address, Asset Type (optional), Problem Category (required), Existing Issue toggle (Yes/No), Problem Description (required), Internal Notes (optional), Priority (Normal / Urgent)
  - **Right side (system suggestions):** Live-updating customer matches ranked by Phone → Email → Name → Address; each match shown as a card with "Use This Customer" / "Not This Person" actions; address matches; asset matches when customer selected
  - Selection locks that section; only one customer/asset can be selected
  - On submit: resolve or create Customer, optionally resolve or create Asset, always create ServiceRequest
  - URL: `/intake` — add to `config/urls.py`, create view, create template

- [ ] **2.2 — Customers list page** (`/customers`)
  - Filterable by status (Active / Inactive); search by name and phone
  - Each row links to customer detail
  - "Add Customer" button → customer create page
  - URL + view + template

- [ ] **2.3 — Customer detail page** (`/customers/<id>`)
  Per spec §23 layout rules. Use prototype's 2/3 + 1/3 layout and inline edit pattern:
  - Left (2/3): Customer information sections using **inline edit pattern** (pencil icon → edit mode in-card)
  - Right (1/3): Asset list (with "Add Asset" shortcut) + Activity timeline
  - Summary strip: Last Job, Last Service Date, Last Issue
  - Tab set: Service Requests | Quotes | Jobs | Invoices | Assets
  - Deletion blocked if any linked records exist

- [ ] **2.4 — Customer create / edit page**
  Required fields: Name, Primary Phone, Billing Address
  Optional: Secondary Phone, Primary Email, Secondary Email, Customer Type (Residential/Commercial), Shipping Address
  - Block save if primary phone exactly matches an existing Active Customer (duplicate rule per §23)
  - Warn on near-duplicate matches (phone, address, name)

---

## 🟠 Phase 3 — Assets

- [ ] **3.1 — Assets list page** (`/assets`)
  - Filter by customer, filter by status (Active / Inactive)
  - Inactive assets hidden by default (toggle to show)
  - Row → asset detail

- [ ] **3.2 — Asset detail page** (`/assets/<id>`)
  Fields per spec §22: Asset Type, Location, Serial Number, Model, Manufacturer, Install Date, Warranty Info, Internal Notes, Status (Active/Inactive)
  - **Service history section:** all linked Jobs, SRs, Quotes, Invoices
  - **Recent activity strip:** Last Job performed, Last Service Date, Last recorded issue
  - Deletion blocked if any linked records exist
  - All edits audit-tracked: field, previous value, new value, user, timestamp

- [ ] **3.3 — Asset create / edit form**
  Required: Asset Type (from `ValueList`), Customer, Location (customer address)
  Optional: Serial Number, Model, Manufacturer, Install Date, Warranty Info, Notes
  - Asset Type is a **tenant-controlled `ValueList`** per LITE_DECISIONS.md §A. On tenant provisioning, seed with: HVAC Unit, Furnace, Water Heater, Boiler, Electrical Panel, Plumbing Fixture, Appliance, Generator, Other. Tenants can add/remove types via the ValueList admin.

- [ ] **3.4 — Disabled upgrade hint on Asset detail**
  "Add Multiple Assets per Job (Plus)" control visible but disabled with tooltip per spec §22

---

## 🟡 Phase 4 — Jobs

- [ ] **4.1 — Jobs list page** (`/jobs`)
  - Sub-nav or filter tabs: **Requests** (open SRs) | **Jobs** (active jobs)
  - Job list filterable by status: Open, Scheduled, In Progress, On Hold, Complete, Voided
  - Users must not need to open a Customer record as the only path to find open SRs (per spec §3)
  - "New Job" button (creates job directly, without SR)

- [ ] **4.2 — Job create page**
  Can be created directly (no SR) or from an accepted Quote or from an SR.
  Fields: Customer (required), Asset (optional), Description, Assigned To, Scheduled Date/Time
  Status starts at **Open** automatically.
  One Job per SR maximum in Lite.

- [ ] **4.3 — Job detail page** (`/jobs/<id>`)
  - Status transition buttons per spec §19 state machine:
    - Open → Scheduled → In Progress → Complete
    - Any non-terminal → On Hold
    - Any non-terminal → Voided (void reason required)
    - Complete and Voided are terminal and locked
  - **Line items panel:** add lines from Products & Services catalog only (no free-text); quantity (default 1), price override allowed; user-reorderable while job is editable; display order snapshotted when Job is Complete
  - Link to Invoice ("Create Invoice" when job is Complete)
  - Link back to source SR (if any)
  - Disabled upgrade hint: "Multi-Asset per Job (Plus)"

---

## 🟡 Phase 5 — Quotes

- [ ] **5.1 — Quotes list page** (`/quotes`)
  Filter by status: Draft, Sent, Accepted, Declined, Voided

- [ ] **5.2 — Quote create**
  Created in context of a Service Request (SR must exist first).
  Maximum **5 Quotes per SR** — enforce this limit.
  No new Quotes once a Job exists for that SR.
  - Line items from P&S catalog only; no free-text
  - Subtotal / Tax Total / Grand Total per spec §18
  - "Include tax in total" checkbox (Draft only — controls whether tax is added to grand total or shown separately)
  - Tax rate comes from Tenant Settings (not editable per line in Lite)

- [ ] **5.3 — Quote detail / status transitions**
  - Draft → Sent (includes customer email send — requires customer email, else block with message)
  - Draft → Voided
  - Sent → Accepted (auto-creates Job; all other Quotes on that SR become Declined; SR becomes Converted and locked)
  - Sent → Declined
  - Quotes cannot be deleted
  - Sent locks structural edits; only status transitions allowed
  - **PDF generation:** subtotal, tax total, grand total, currency symbol, include-tax treatment per §26
  - Disabled upgrade hint: "Duplicate Quote (Plus)"

- [ ] **5.4 — Quote Sent snapshot**
  On transition to Sent, snapshot: applied tenant tax rate, subtotal, tax total, include-tax-in-total flag, grand total, all line amounts, line tax amounts

---

## 🟡 Phase 6 — Invoices & Payments

- [ ] **6.1 — Invoices list page** (`/invoices`)
  Filter by status: Draft, Sent, Paid, Voided

- [ ] **6.2 — Invoice create**
  Created from a Job only (not from a Quote directly).
  One active (non-voided) Invoice per Job at a time — enforce this.
  - Line items pre-populated from Job lines (snapshotted); editable in Draft
  - Tax calculation per spec §20: per-taxable-line tax using tenant default rate
  - "Include tax in total" checkbox (Draft only)
  - Grand total = subtotal + tax total (if checkbox checked) or subtotal only (tax still displayed)
  - Currency symbol from Tenant Settings

- [ ] **6.3 — Invoice detail / status transitions**
  Use prototype's Invoice Detail layout: 2/3 main canvas + 1/3 context panel. Implement all established patterns:
  - **Metadata card** — inline edit pattern (Bill To, Invoice #, Issued Date, Payment Terms, Linked Job)
  - **Line items card** — drawer edit pattern ("Edit line items" button → right-side drawer with per-line Product/Service selector, qty, unit price, line total, add/remove rows, totals summary in drawer footer)
  - **Payment card** — "Record Manual Payment" button only. Per LITE_DECISIONS.md §F, Lite is manual-logging only; the prototype's "Copy Payment Link" (Stripe) button is removed entirely, not disabled.
  - **Terms & Notes card** — inline edit pattern (customer-facing message)
  - **Right panel:** Internal Notes (add note), Activity timeline
  - **"Client View" toggles:** Skip per LITE_DECISIONS.md §G. The PDF is the customer view.
  - Draft → Sent (customer email send — requires customer email; locks document; snapshots all amounts and tax rate)
  - Draft → Voided
  - Sent → Paid (when full payment is recorded)
  - Sent → Voided (only when no payments exist)
  - Invoices cannot be deleted
  - **Admin only:** Sent → Draft reopen (only when no payments exist)
  - If voided, a new Draft may be created from the same Job (if no other active invoice exists)
  - **PDF generation** per spec §26
  - Disabled upgrade hint: "Partial Payment (Plus)"

- [ ] **6.4 — Invoice Sent snapshot**
  On transition to Sent, snapshot: applied tenant tax rate, subtotal, tax total, include-tax-in-total flag, grand total, all line amounts, line tax amounts

- [ ] **6.5 — Payment record** (`/payments`)
  One full payment per Invoice only (no partial payments in Lite).
  Fields: Amount (must equal invoice grand total), Date, Payment Method (Cash / Check / Credit Card / ACH / Bank Transfer / Other), Reference/Notes (optional)
  - Recording payment transitions Invoice → Paid
  - Admin may correct Payment Method, Reference/Notes, and Date after save (with audit)
  - Amount is not editable after save

---

## 🟢 Phase 7 — Catalog & Utility Modules

- [ ] **7.1 — Products & Services** (`/products`)
  - **Admin:** Full CRUD; activate/deactivate; delete only if never used on any Quote, Job, or Invoice
  - **User:** Read/select only
  - Required fields: Name, Type, Default Price, Description, Status (Active/Inactive)
  - Optional: SKU/Item Code, Taxable flag, Labor/time indicator
  - Inactive P&S records hidden from selection lists
  - Edits to master records are forward-looking only; historical documents do not change

- [ ] **7.2 — Tasks** (`/tasks`)
  - List view grouped by: Overdue / Today / Upcoming / No Date
  - Create task: Title, Assigned To, Due Date, Description
  - Complete task action
  - No dependencies, no workflow engine

- [ ] **7.3 — Time Tracking** (`/time`)
  - Start / stop timer (attaches to a Job)
  - Manual time entry (Job, date, duration, notes)
  - List of time entries for current user

---

## 🟢 Phase 8 — Schedule & Settings

- [ ] **8.1 — Schedule** (`/schedule`)
  - Views: Day, Week, Month; Ordered Job List for selected date range
  - Each scheduled Job displays: Scheduled Time, Customer Name, Assigned User, Job Status, Short Description, Asset reference (if present)
  - Jobs in chronological order; switch date ranges quickly
  - Click Job on calendar → Job detail
  - Basic drag-and-drop reordering within a day
  - **Unscheduled Jobs list** — visible panel of Jobs with no scheduled date/time (prevent jobs from being lost)
  - Disabled upgrade hints: "Route Optimization (Plus)", "Multi-Tech Scheduling (Plus)"

- [ ] **8.2 — Company Settings** (`/settings/company`) — Admin only
  Per LITE_DECISIONS.md §B. Lite tenants do NOT control numbering prefixes; those are fixed to system defaults seeded at tenant creation.
  - Identity: company name, from-email identity, logo upload
  - Financial (per spec §27): default tax rate (%), currency code, currency symbol, calculation precision (default 3), display precision (default 2)
  - Operations: business hours, timezone

- [ ] **8.3 — User Management** (`/settings/users`) — Admin only
  - List of active users with role (Admin / User)
  - Create user: name, email, role assignment
  - Deactivate user (does not delete — preserves history)
  - Seat count enforcement: max 10 active users per Lite plan
  - Display current seat usage vs limit

---

## 🔵 Phase 9 — Polish & Compliance

- [ ] **9.1 — Upgrade hints audit**
  Verify all disabled upgrade controls are in place per spec §21:
  - "Duplicate Quote (Plus)" on Quote detail
  - "Advanced Edit (Plus)" on line items
  - "Partial Payment (Plus)" on Invoice detail
  - "Add Multiple Assets per Job (Plus)" on Job detail
  - "Route Optimization (Plus)" on Schedule
  - "Multi-Tech Scheduling (Plus)" on Schedule
  All disabled controls must show tooltip "Available in Plus" on hover.
  Maximum 1–2 hints per screen. Never block a core workflow action.

- [ ] **9.2 — Storage quota enforcement**
  - 70% usage → notice banner in app
  - 85% usage → strong warning banner
  - 100% usage → block new file/attachment uploads only (rest of app works)
  - 3GB default limit for Lite; add-ons: +5GB, +10GB

- [ ] **9.3 — CSV export on all tables**
  Every list view (Customers, Assets, Jobs, Quotes, Invoices, Payments, Tasks, Time Entries, Products & Services) must have a "Export CSV" action.

- [ ] **9.4 — Asset edit audit trail**
  Every field change on an Asset must log: field name, previous value, new value, user, timestamp.

- [ ] **9.5 — Document send audit log**
  When a Quote or Invoice is sent to a customer, record: sent by (user), timestamp, recipient email, document type.

- [ ] **9.6 — Snapshot integrity verification**
  Confirm that Quote and Invoice Sent transitions correctly lock and snapshot:
  - Applied tenant tax rate
  - Subtotal, tax total, include-tax-in-total flag, grand total
  - All line amounts and line tax amounts
  - Customer snapshot on SR/Quote/Job/Invoice at time of creation (name, phone, address)

- [ ] **9.7 — Duplicate customer detection**
  Enforce: block creation when primary phone exactly matches an existing Active Customer.
  Warn (but allow) on near-matches by address and name.

---

## Open Decisions — resolved

All eight spec §29 open decisions (A–H) plus tooling (I–L) are resolved in `LITE_DECISIONS.md` (2026-04-24). Summary:

| # | Decision | Resolution |
|---|---|---|
| A | Asset Type list | Tenant-controlled ValueList, seeded at provisioning |
| B | Company Settings fields | Identity + financial + operations; NO numbering prefix control in Lite |
| C | Quote/Invoice void reasons | Optional free-text |
| D | Global search scope | Customers + Jobs + Invoices, prefix match |
| E | Accessibility | WCAG 2.1 AA informal, spot-check per phase |
| F | Payment processor | Manual logging only; Stripe starts in Plus |
| G | Invoice Client View toggle | Skip (PDF is the customer view) |
| H | Sidebar structure | Full tier-aware nav; hide items not available in tenant's tier |
| I | CSS framework | Bootstrap 5 |
| J | Frontend JS | HTMX + Django templates |
| K | Email | Postmark |
| L | PDF | WeasyPrint |

See `LITE_DECISIONS.md` for the rationale and spec-alignment follow-ups.

---

## Notes

- Spec authority: If this document and the Lite Tier UI spec conflict, **the spec wins**.
- "Jobs" replaces "Work Orders" everywhere in the Lite UI — no internal terminology leakage per spec §3.
- Service Requests are **not** a top-level sidebar item — they live inside the Jobs hub and are accessible from the header intake button.
- All monetary display uses 2 decimal places; internal tax calculation uses 3 (or tenant-configured precision).
- All users see all company records in Lite — no territory or per-user data hiding.
