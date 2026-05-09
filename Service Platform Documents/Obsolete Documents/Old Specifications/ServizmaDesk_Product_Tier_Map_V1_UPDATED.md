# ServizmaDesk — ServizmaDesk Product Tier Map

**Document 1 of 3 — Master Project Documents**

> **Document Version:** V1  
> **Status:** Draft — Pending Review  
> **Last Updated:** February 2026  
> **Classification:** Internal — Confidential

---

# 1. Purpose and Scope

This document is the first of three master project documents that govern the design, architecture, and construction of the ServizmaDesk product family. It defines what is being built at each product tier and establishes the boundaries that all subsequent technical and build decisions must respect.

**Document 1 (this document):** Product Tier Map. Defines what each tier includes, excludes, and how tiers relate to each other.

**Document 2:** Technical Architecture and Stack. Defines how the product is built, including technology choices, database design, deployment, and inter-application communication.

**Document 3:** Build Plan. Defines the sequenced, dependency-ordered construction plan with phase completion criteria.

All three documents are living documents. Changes to any one document may trigger updates to the others. No document is considered final until all three are internally consistent.

This document supersedes all prior tier, feature, and pricing references found in legacy ServizmaDesk/ServizmaDesk documentation and earlier ServizmaDesk draft documents. Where conflicts exist between this document and any other source, this document governs.

---

# 2. Product Identity

## 2.1 Company

- **Company Name:** ServizmaDesk LLC
- **Structure:** Minnesota Multi-Member LLC
- **Operations:** US-based (founder relocating to Philippines, Year 2)

## 2.2 Product Family

- **Product Name:** ServizmaDesk
- **Product Type:** Multi-tenant SaaS field service management platform
- **Platform Name:** ServizmaDesk Platform (SDP) — internal operations and billing platform
- **Application Name:** ServizmaDesk Tenant App (SDTA) — customer-facing product

## 2.3 Target Market

Solo and small service businesses currently managing operations with spreadsheets or no system at all. Primary verticals include HVAC, plumbing, electrical, and repair/service shops. The primary target customer is a 1–3 person operation, with plans supporting growth up to 10 users (Lite) and unlimited users (Plus, Pro, Enterprise).

## 2.4 Core Differentiator

ServizmaDesk is built around an asset-centric model. The Asset (customer-owned equipment being serviced) is the center of the data model. All operational activity — quotes, work orders, invoices, maintenance history, documents, and notes — connects through the Asset. This contrasts with competitors (Jobber, Housecall Pro, ServiceTitan) who use workflow-first or job-first approaches where the equipment being serviced is secondary to the job record.

This asset-centric approach provides superior visibility into equipment lifecycle, service history, warranty tracking, and maintenance scheduling — capabilities that are especially valuable for businesses that service the same equipment repeatedly.

---

# 3. Pricing and Billing

All pricing, billing cycles, storage add-ons, and Founding Partner program details are defined in the **ServizmaDesk Pricing & Billing Specification V1**.

**Quick Reference — Standard Tier Pricing (Annual Billing):**
- Lite: $29/seat/month (max 10 seats)
- Plus: $49/seat/month (unlimited seats)
- Pro: $98/seat/month (unlimited seats)
- Enterprise: TBD (future tier)

**Quick Reference — Founding Partner Programs:**
- Founding Partner Lite: $200/seat/year (10 slots available)
- Founding Partner Plus: $400/seat/year (10 slots available)

For complete pricing details, billing rules, storage pricing, trial structure, and competitive positioning rationale, see:
→ **ServizmaDesk Pricing & Billing Specification V1**

---

# 4. Free Trial Structure

ServizmaDesk offers a 14-day free trial with no credit card required. Full trial terms, expiration flow, and conversion process are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 6**.

**Trial Flow Summary:**
- Days 1-14: Full Lite access with countdown timer
- Day 15: Account enters read-only mode (data preserved)
- Day 45: Account flagged for cleanup (60-day grace period begins)
- Day 105: Permanent data deletion

For complete trial structure details, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 6**

---

# 5. Founding Partner Program

ServizmaDesk offers two Founding Partner tiers with exclusive legacy pricing for early adopters:

- **Founding Partner Lite:** $200/seat/year (10 slots available)
- **Founding Partner Plus:** $400/seat/year (10 slots available)

Both programs offer 24-month pricing locks with automatic conversion to standard pricing after expiration.

For complete Founding Partner program details, qualification criteria, conversion rules, and revenue projections, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 5**

---

# 6. Tier Definitions

## 6.1 ServizmaDesk Lite

Lite is the entry-level tier designed for solo operators and small teams (1–10 users) who need structured service management without complexity. Lite is manual-first with no automation. The UI and feature set are intentionally constrained to keep the experience simple while building on a data structure that supports seamless upgrades to higher tiers.

### Core Workflow

Company → Asset → Quote → Work Order → Invoice → Payment (manual recording)

### Modules Included

- **Dashboard:** Work Orders Today, Open Work Orders, Open Invoices, Overdue Invoices, Revenue This Month, Storage Usage Meter, Top 5 Active Tasks.
- **Companies:** Create, edit, delete with status lifecycle. Embedded contacts (2), addresses (billing required, shipping optional), phone numbers (fax, phone1, phone2), social info. Customer-only — no vendor capability. Linked to all operational modules.
- **People:** Contacts (linked to companies) and Employees (system users). Role-based access (Administrator, Standard User). Max 10 seats.
- **Products & Services:** Catalog only. Name, type (Part/Service), SKU, unit price, unit cost, manual quantity (informational only), active/inactive status. No inventory tracking, no auto-decrement.
- **Assets:** The core differentiator. Company-linked assets with make/model, serial number, install date, warranty start/end, status. Full service history visible (quotes, work orders, invoices). Documents and notes attachable. CSV export.
- **Quotes:** With line items. Status lifecycle (Draft, Sent, Accepted, Rejected, Expired). Linkable to work orders for conversion.
- **Work Orders:** With line items. Date and optional time. Status lifecycle. Maintenance flag for manual tagging. Assignable to employees. Linkable to invoices.
- **Invoices:** With line items. Auto-calculated subtotal, tax, total. Status lifecycle (Open, Paid, Cancelled). Auto-lock when not Open.
- **Payments:** Online payment processing via Stripe Payment Links (OAuth integration), plus manual record-keeping (cash, check). Linked to invoices. Multiple payments per invoice. Auto-close invoice when paid in full.
- **Simple Ledger:** Auto-generated, read-only. Debit entry on invoice creation, credit entry on payment recording. Running balance per company. No manual entries.
- **Notes:** Attached to all objects. Typed (Phone Call, Email, Letter, Meeting, Internal). Unlimited. Text does not count toward storage.
- **Documents:** Attachments on all major objects. 3 GB storage cap with add-on options (+5 GB, +10 GB). Max 10 attachments per record. Uploads blocked at 100% storage.
- **Tasks:** Basic create, assign, link to records, status tracking. Top 5 active tasks on Dashboard. Full task list view with My Tasks filter and sort options.
- **Preferences:** Company info, tax rate, currency, date format, timezone, basic configuration.
- **User/Role Management:** Administrator and Standard User roles. Max 10 seats.
- **Session Logging:** Login/logout tracking with SDP address. 18-month rolling retention.
- **Audit Events:** Event-level logging (not field-level). Record creation, deletion, status changes, financial-impact actions.

### UI and Export

- List views with search, sort, and filters acting as reports.
- Show Total checkbox on financial list views (invoices, payments, ledger).
- CSV export from all list views.
- Browser print only — no system PDF generation. (Note: Developers must build robust CSS Print Styles to ensure clean, stripped-down output for quotes and invoices when the user prints from the browser).
- Responsive web design (desktop, tablet, phone).
- No system email sending — users send from their own email client.

### Explicitly Not Included in Lite

- Automation of any kind
- Recurring or auto-generated schedules
- Inventory tracking (system-managed quantities)
- Purchase orders, receiving, or procurement
- Vendor capability on companies
- Leads or opportunities
- Calendar view
- Dispatch board
- SMS
- System email sending
- PDF generation
- API access
- Multi-location
- Maintenance agreements
- Advanced reporting or dashboards
- Task Manager (dedicated workspace)
- Interactions / Activity Log

---

## 6.2 ServizmaDesk Plus

Plus is the growth tier for established teams that need automation, scheduling, procurement, and communication tools. Plus builds on the complete Lite feature set and adds capabilities that enable operational efficiency at scale. Unlimited seats.

### Everything in Lite, Plus

- **Companies — Vendor Capability:** Company records gain a company_type field (Customer, Vendor, Both). Single Companies table — vendor-specific UI elements appear only on vendor-flagged records.
- **Products — Inventory Tracking:** Products gain system-managed quantity on hand. Quantities update automatically on PO receipt. Single location assignment per item.
- **Locations:** Locations table introduced. Tenant can define unlimited location records (rack, shelf, bin, truck, etc.). Each inventory item is assigned to exactly one location.
- **Basic Procurement:** Vendor assignment on products. Purchase order creation. Receiving against POs with automatic inventory update.
- **Leads:** Basic lead tracking with status, follow-up date, source, ranking, conversion percentage, score. Editable only while active. Journalized notes.
- **Maintenance Scheduling:** User selects a Asset, duration (1–5 years), and frequency (yearly, monthly, bi-weekly, etc.). System auto-generates all work orders for the schedule in Scheduled status. Individual generated work orders are fully editable and deletable.
- **Maintenance Agreements:** Light version — scope to be defined in detail during Plus specification.
- **Calendar View:** Month, week, and day views for work orders and scheduled maintenance. Basic scheduler.
- **SMS:** Point-based system. One point equals one outbound SMS. Monthly allotment included with Plus. Additional point tiers available for purchase.
- **System Email:** Two modes available. Mode 1: ServizmaDesk-managed sending with limited daily count, sent through ServizmaDesk infrastructure. Mode 2: Bring Your Own SMTP with no limit, sent through tenant's own email provider. Tenant selects mode in Preferences.
- **PDF Generation:** Available for Quotes, Invoices, Work Orders, and Payment receipts. No quantity limit.
- **Advanced Payment Processing:** Tenant unlocks deep embedded payment APIs (custom card forms, split-payments, recurring subscriptions) rather than just the standard Stripe Payment Links provided in Lite. ServizmaDesk never holds card data.
- **QuickBooks-Formatted CSV Export:** CSV export formatted to match QuickBooks import templates. Available as an extra.
- **External Integrations:** Available as extras. No live API integrations built in.

### Not Included in Plus

- Multiple locations per inventory item
- Inventory transfers or adjustments
- Warehousing
- Opportunities
- Interactions / Activity Log
- Task Manager (dedicated workspace)
- Dispatch board
- Advanced procurement
- REST API access
- Multi-location support (system-wide)
- Advanced reporting / dashboards

---

## 6.3 ServizmaDesk Pro

Pro is the full-featured tier for larger teams managing complex operations across multiple locations. Pro unlocks advanced inventory, dispatch, CRM, reporting, and API capabilities. Pro builds on the complete Plus feature set.

### Everything in Plus, Plus

- **Inventory — Multi-Location:** Items can exist at multiple locations with separate quantity tracked at each location.
- **Inventory Transfers:** Move inventory between locations with full audit trail.
- **Inventory Adjustments:** Manual quantity corrections with reason tracking.
- **Advanced Procurement:** Full vendor management. Full purchase order workflow with advanced features.
- **Opportunities:** Project-level sales objects with unlimited quotes, work orders, and invoices attached. Full sales pipeline tracking.
- **Interactions / Activity Log:** Unified chronological feed of all activity on a record. Auto-tracked events (status changes, record creation, document uploads) combined with manual notes.
- **Task Manager:** Dedicated user-centric workspace showing all tasks assigned to the user across all modules.
- **Dispatch Board:** Visual assignment view for work orders and technicians. Drag-and-drop scheduling.
- **Signals/Notifications:** Automated notifications to users and customers for scheduling events, status changes, and dispatch assignments.
- **SMS — Increased Allotment:** Significantly higher monthly point allotment than Plus. Same purchasable add-on tiers.
- **System Email — Higher Limits:** Same two modes as Plus. Higher daily limits on ServizmaDesk-managed sending.
- **PDF Generation:** Unrestricted across all record types.
- **Multi-Location (System-Wide):** Full multi-location support. Work orders, employees, and reporting can be scoped by location.
- **REST API Access:** Full REST API layer for external integrations. Scope and rate limits to be defined.
- **Advanced Reporting:** Enhanced dashboards and reporting capabilities. Scope to be defined during Pro specification.
- **Advanced Maintenance:** Same scheduling as Plus. Potential additions include auto-notify customer before scheduled maintenance and auto-generate invoice on work order completion.

### Not Included in Pro

- Warehousing (multiple buildings with locations within each)
- Projects, Epics, Use Cases
- Offline mobile application

---

## 6.4 ServizmaDesk Enterprise

Enterprise is the long-term vision for ServizmaDesk as a full-featured ERP for larger service organizations. Enterprise is not in active development and will not enter planning until Pro is stable and generating revenue. The following represents the directional scope and is subject to change.

### Everything in Pro, Plus

- **Warehousing:** Multiple warehouses (buildings), each with its own set of locations. Items tracked across warehouses and locations within them.
- **Projects:** Full project management module.
- **Epics:** Project sub-components. Must belong to a project.
- **Use Cases:** Global intake objects. Approved Use Cases convert into Epics within a Project.
- **Enhanced Automation:** Advanced automation rules across all modules.
- **Extended Reporting:** Advanced reporting dashboards.
- **Priority Support:** Dedicated support channel.
- **Offline Mobile App:** Downloadable tablet application with offline capability and manual sync. Planned as a paid feature. Architecture and scope to be defined post-Pro launch.

Enterprise pricing, seat structure, and detailed feature scope will be defined in a separate specification when Enterprise enters the planning phase.

---

# 7. Feature Comparison Matrix

A checkmark (✓) indicates the feature is included. An em dash (—) indicates the feature is not available at that tier.

### Core Modules

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Companies (Customers) | ✓ | ✓ | ✓ | ✓ |
| Companies (Vendor Flag) | — | ✓ | ✓ | ✓ |
| People (Contacts + Employees) | ✓ | ✓ | ✓ | ✓ |
| Products & Services (Catalog) | ✓ | ✓ | ✓ | ✓ |
| Assets (Assets) | ✓ | ✓ | ✓ | ✓ |
| Quotes (with Line Items) | ✓ | ✓ | ✓ | ✓ |
| Work Orders (with Line Items) | ✓ | ✓ | ✓ | ✓ |
| Invoices (with Line Items) | ✓ | ✓ | ✓ | ✓ |
| Payments (Manual Recording) | ✓ | ✓ | ✓ | ✓ |
| Simple Ledger (Read-Only) | ✓ | ✓ | ✓ | ✓ |
| Notes (Typed, All Objects) | ✓ | ✓ | ✓ | ✓ |
| Documents (Attachments) | ✓ | ✓ | ✓ | ✓ |
| Tasks (Basic) | ✓ | ✓ | ✓ | ✓ |
| Preferences | ✓ | ✓ | ✓ | ✓ |
| User/Role Management | ✓ | ✓ | ✓ | ✓ |
| Session + Audit Logging | ✓ | ✓ | ✓ | ✓ |

### Financial & Payments

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| Online Payment Links (Stripe Connect) | ✓ | ✓ | ✓ | ✓ |
| Advanced Payment APIs (Embedded, Split) | — | ✓ | ✓ | ✓ |
| PDF: Quotes, Invoices, WOs, Payments | — | ✓ | ✓ | ✓ |
| PDF: All Record Types | — | — | ✓ | ✓ |
| Maintenance Agreements (Light) | — | ✓ | ✓ | ✓ |
| Maintenance Agreements (Full) | — | — | ✓ | ✓ |

### Sales & CRM

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| Leads | — | ✓ | ✓ | ✓ |
| Opportunities (Project-Level) | — | — | ✓ | ✓ |
| Interactions / Activity Log | — | — | ✓ | ✓ |

### Inventory & Procurement

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| Inventory Tracking (System-Managed) | — | ✓ | ✓ | ✓ |
| Locations (Single per Item) | — | ✓ | ✓ | ✓ |
| Locations (Multiple per Item) | — | — | ✓ | ✓ |
| Warehousing (Multiple Buildings) | — | — | — | ✓ |
| Basic Procurement (POs, Receiving) | — | ✓ | ✓ | ✓ |
| Advanced Procurement | — | — | ✓ | ✓ |
| Inventory Transfers | — | — | ✓ | ✓ |
| Inventory Adjustments | — | — | ✓ | ✓ |

### Scheduling & Dispatch

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| WO Scheduling (List-Based, Sort/Filter) | ✓ | ✓ | ✓ | ✓ |
| Calendar View (Month/Week/Day) | — | ✓ | ✓ | ✓ |
| Maintenance Scheduling (Auto-Generate WOs) | — | ✓ | ✓ | ✓ |
| Dispatch Board | — | — | ✓ | ✓ |
| Signals/Notifications to Users + Customers | — | — | ✓ | ✓ |

### Communication & Messaging

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| SMS (Point-Based) | — | ✓ | ✓ | ✓ |
| System Email (ServizmaDesk-Managed, Limited) | — | ✓ | ✓ | ✓ |
| System Email (Bring Your Own SMTP) | — | ✓ | ✓ | ✓ |
| Task Manager (Dedicated Workspace) | — | — | ✓ | ✓ |

### Technical & Integrations

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| CSV Export (All List Views) | ✓ | ✓ | ✓ | ✓ |
| Show Totals on Financial Lists | ✓ | ✓ | ✓ | ✓ |
| Multi-Location Support (System-Wide) | — | — | ✓ | ✓ |
| REST API Access | — | — | ✓ | ✓ |
| QuickBooks-Formatted CSV Export | — | ✓ | ✓ | ✓ |
| External Integrations (Extras) | — | ✓ | ✓ | ✓ |

### UI & Access

| Feature / Capability | Lite | Plus | Pro | Entp |
|---|:---:|:---:|:---:|:---:|
| Responsive Web (Desktop/Tablet/Phone) | ✓ | ✓ | ✓ | ✓ |
| Browser Print | ✓ | ✓ | ✓ | ✓ |
| Advanced Reporting / Dashboards | — | — | ✓ | ✓ |
| Offline Mobile App (Future) | — | — | Future | Future |

---

# 8. Database Architecture Summary

This section provides a high-level summary of the database architecture as it relates to tier design. Full technical details will be defined in Document 2 (Technical Architecture and Stack).

## 8.1 Two-Database Model

- **ServizmaDesk Platform Database (SDP):** Holds all account-level data: tenant records, plan status, billing history, security credentials, staff accounts, audit logs. Operated by ServizmaDesk internally.
- **ServizmaDesk Application Database (SDTA):** Holds all tenant operational data: companies, assets, quotes, work orders, invoices, payments, notes, documents, tasks, and all other business records. Shared by all tenants across all tiers.

## 8.2 Shared Schema Multi-Tenancy

All tenants share the same SDTA database and the same tables. Every table includes a tenant_id (UUID) field that scopes all data to a specific tenant. This model was chosen because it supports seamless upgrades and downgrades without data migration.

## 8.3 Tier Enforcement Through Distinct UIs & Controllers

The SDTA database contains all tables required for all tiers. However, tier boundaries are rigorously enforced at both the UI and backend controller levels. 

To eliminate any "spillover" features between tiers and prevent hackable manipulation, **there are three completely distinct UI parts built for SDTA (one for Lite, one for Plus, and one for Pro).** The application routes the user to the specific UI frontend corresponding to their active plan. 

Backend controllers explicitly reject any write request to a higher-tier feature if the tenant's current plan does not allow it. When a tenant upgrades from Lite to Plus, no database migration occurs—the application simply directs them to the Plus UI part and permits access to Plus controllers. When a tenant downgrades, they are pushed back to the Lite UI, restricting access but leaving the underlying data intact.

This means the SDTA schema must be designed upfront to accommodate the complete feature set across Lite, Plus, and Pro. Tables for Plus and Pro features (such as Locations, Purchase Orders, Leads, and Opportunities) exist in the database from day one, even though Lite's distinct UI does not expose them.

## 8.4 Three-Layer Tenant Isolation

- **Layer 1 — Database field constraint:** tenant_id is non-nullable on all tenant-scoped tables.
- **Layer 2 — Django middleware:** injects tenant_id filter into all querysets on every request.
- **Layer 3 — PostgreSQL Row Level Security (RLS):** database-level safety net ensuring queries can only return rows matching the active tenant.

## 8.5 SDP to SDTA Communication

SDTA reads tenant plan status directly from the SDP database via a read-only database connection. This is a direct server-side connection between two Django applications on the same PostgreSQL server. No external API is involved. This approach will be evolved to an internal API only if and when the applications need to run on separate servers.

---

# 9. Cross-Tier Design Principles

### 9.1 UI is the Limiting Factor

All tiers share the same underlying data structure. The user interface controls what the customer sees and what functionality they can access. Upgrading or downgrading a tier changes the UI experience without modifying the database.

### 9.2 Asset-Centric Design

The Asset is the center of the data model across all tiers. Every operational object (quotes, work orders, invoices, notes, documents) connects through the Asset. This principle must be preserved as new modules and tiers are added.

### 9.3 Foundation Tables First

Companies, People, Products, Assets, Notes, Documents, and Tasks are foundation objects that exist across all tiers. All business modules (procurement, CRM, scheduling, etc.) attach to these foundation objects. New modules never recreate foundation functionality.

### 9.4 Progressive Enhancement

Each tier adds capabilities on top of the previous tier. No tier removes features available in a lower tier. A Plus customer has everything a Lite customer has, plus more. A Pro customer has everything a Plus customer has, plus more.

### 9.5 Single Companies Table

Companies are stored in a single table with a company_type field (Customer, Vendor, Both). In Lite, all companies are implicitly customers and vendor-related UI elements are hidden. In Plus and above, vendor capability is enabled through conditional UI rendering.

### 9.6 Data Preservation on Downgrade

When a tenant downgrades, their data is not deleted. The UI restricts access to higher-tier features, but the underlying data remains. If the tenant upgrades again, their data reappears. This is a key benefit of the shared-schema, UI-gated architecture.

### 9.7 No Raw Card Data

ServizmaDesk never stores raw payment card data at any layer. All card collection uses Stripe Checkout (for ServizmaDesk billing) or Stripe Connect (for tenant payment processing). This is a non-negotiable security and compliance requirement.

---

# 10. Open Decisions and Dependencies

The following items are identified but not yet resolved. They will be addressed in Document 2 (Technical Architecture) or during individual tier specification work.

### Technical Architecture (Document 2)

- Exact Django and PostgreSQL version numbers
- HTMX version and supporting JavaScript libraries
- Stripe SDK version
- Transactional email provider selection (for ServizmaDesk-to-tenant communications from SDP)
- System email architecture for tenant-to-customer communications (ServizmaDesk-managed mode details)
- WSGI server selection (Gunicorn configuration)
- Production hosting configuration on Digital Ocean
- Development and staging environment setup for SaaS
- SMS provider selection (Twilio or alternative)
- Tier-gating implementation pattern in Django (middleware, decorators, template conditionals)
- PDF generation library selection
- File/document storage strategy for SaaS (cloud object storage vs filesystem)

### Feature Specification (During Tier Development)

- Maintenance Agreements — detailed scope for light version (Plus) and full version (Pro)
- SMS point allotments and purchasable tier pricing
- System email daily limits for ServizmaDesk-managed mode
- REST API scope and rate limits (Pro)
- Dispatch board detailed functionality (Pro)
- Advanced reporting scope (Pro)
- Opportunities detailed specification (Pro)
- Interactions/Activity Log event taxonomy (Pro)
- Enterprise tier detailed specification (future)

### Business Decisions

- Annual billing discount percentage (currently approximately 15–17% vs monthly)
- SMS add-on tier pricing
- Enterprise monthly pricing

---

# 11. Document Relationships

### This Document Supersedes

- All tier and feature references in ServizmaDesk/ServizmaDesk legacy documentation
- All prior ServizmaDesk SaaS Operational Plan versions (pricing and tier structure sections only — financial projections and business planning sections remain valid in the current operational plan)
- ServizmaDesk Product Structure High-Level V5 (replaced by the tier definitions and feature matrix in this document)

### This Document Depends On

- ServizmaDesk Platform (SDP) V1 Specification — for platform architecture, provisioning, and billing details
- ServizmaDesk Lite MVP V3 Specification — for detailed Lite module specifications

### Legacy Reference Documents (Not Superseded, Used for Reference)

The following ServizmaDesk/ServizmaDesk documents contain module-level detail that remains largely applicable to the SaaS version. They should be consulted during module development but must be reconciled with the SaaS architecture, multi-tenancy model, and tier boundaries defined in this document and Document 2.

- ServizmaDesk Customers MVP Functionality
- ServizmaDesk Products MVP Functionality
- ServizmaDesk Quotes MVP Functionality
- ServizmaDesk Work Orders MVP Functionality
- ServizmaDesk Invoices MVP Functionality
- ServizmaDesk Payments MVP Functionality
- ServizmaDesk Simple Ledger MVP Functionality
- ServizmaDesk Notes MVP Functionality
- ServizmaDesk Documents MVP Functionality
- ServizmaDesk Leads MVP Functionality
- ServizmaDesk Assets MVP Functionality
- ServizmaDesk Preferences Functionality
- ServizmaDesk Reports Functionality
- ServizmaDesk Admin Access MVP Functionality
- ServizmaDesk User Management
- ServizmaDesk Sequence Management System
- ServizmaDesk Service Offerings

---

**End of Document**
