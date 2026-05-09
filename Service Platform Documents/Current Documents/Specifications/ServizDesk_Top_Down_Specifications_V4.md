# ServizDesk Top-Down Specifications
**Complete Product Structure & Data Model Documentation**

**Date:** March 2026
**Document Status:** Working Draft — V4
**Classification:** Internal — Confidential
**Purpose:** Full functional specification defining ServizDesk's complete product scope across all tiers

---

# Document Purpose

This document provides a complete functional specification of ServizDesk's data model, features, workflows, and system structure. It defines the full product ceiling — the maximum functional scope across all tiers (Lite, Plus, Pro, Enterprise). Individual tier specifications determine which features are available at each plan level.

**Architectural Foundation:** ServizDesk is **asset-centric**. Unlike job-centric competitors where the Work Order is the primary organizing entity, ServizDesk treats the **Asset** (customer-owned equipment) as a first-class data entity. Work Orders, maintenance plans, warranty tracking, and service history are organized *around* Assets, not the other way around. This is the platform's core structural differentiator.

**Naming Conventions (canonical — applies to all ServizDesk documents):**
- **Customer** — The business or individual receiving service
- **Asset** — Customer-owned equipment tracked for service
- **Work Order** — A unit of service work (equivalent to "Job" in competitor platforms)
- **Quote** — A price proposal sent to a customer (equivalent to "Estimate" in competitor platforms)

**Document Scope:** This document covers the ServizDesk Tenant App (SDTA) only — the customer-facing application. It does not cover the ServizDesk Platform (SDP), which is the internal operations and billing platform. SDP is documented separately in the ServizDesk Platform (SDP) Specification V2.

**Single Source of Truth Policy:** Each data domain is owned by exactly one document. This document does not duplicate pricing, billing, trial structure, or technical stack decisions. Those are referenced from their owning documents. See Section 15 for the full document ownership map.

---

# 1. Data Model & Core Entities

## 1.1 Customer Entity

### Customer Record Structure

**Primary Fields:**
- **Customer Number** — Auto-generated (ServizDesk record numbering: C26-0001)
- **Status** — Dropdown
  - Values: Active, Inactive, Hold, Closed
  - **Hold**: Freezes the account — no new Work Orders, Quotes, or Invoices can be created. Existing open records remain accessible but cannot be modified. Requires explicit permission to place on hold. Hold Date and Hold Reason are recorded.
  - **Closed**: Permanently closes the account. All linked records become read-only. Cannot be reopened — a new Customer record must be created if the relationship resumes.
  - **Transitions**: Active ↔ Inactive (reversible), Active → Hold → Active (reversible), Active/Inactive → Closed (terminal).
- **Account Type** — Dropdown
  - Values: Residential, Commercial
- **Assigned To** — Dropdown (employee assignment)
- **Lead Source** — Dropdown (customizable list)
- **Tax Exempt** — Toggle (on/off)
- **Customer Since** — Date picker
- **Account Number** — Text (required)
- **Account Terms** — Dropdown (customizable list)
- **Credit Limit** — Number (required)
- **Credit Status** — Dropdown
  - Values: Good, Fair, Poor

**Company Name:**
- **Company Name** — Text (required for Commercial, optional for Residential)

**Contacts (via Contact Table):**
- Customer has one or more Contact records
- Each Contact links a **Person** record to this Customer (see Section 1.13 — Person Entity)
- **Primary Contact** — One Contact is designated as the primary contact
- Each Contact holds:
  - **Person** — Link to Person record (First Name, Last Name)
  - **Role/Title** — Text (optional)
  - **Department** — Text (optional)
  - **Status** — Dropdown
    - Values: Active (default), Left
  - **Start Date** — Date picker (optional)
  - **Left Date** — Date picker (optional — populated when Status changes to Left)
  - **Socials** — Managed via Socials Table (emails, social media links — linked to Contact)
  - **Phone Numbers** — Managed via Phone Number Table (linked to Contact)
- Can add unlimited Contacts per Customer
- Import capability via CSV template

**Phone Numbers (via Phone Number Table):**
- Phone numbers linked to Customer and/or Contact records
- Supports unlimited phone numbers per Customer and per Contact
- Duplicate numbers permitted to preserve history

**Addresses (via Address Table):**
- **Service Address** — Full address (street, city, state, ZIP)
- **Billing Address** — Full address (optional separate address)
  - Toggle: "Use Separate Billing Address"

**Additional Locations:**
- Can add multiple service locations linked to primary customer
- Each location has: Location Name (user-defined), Full Address
- Assets can be linked to specific locations
- Import capability via CSV template

**Tags:**
- Free-text tags for categorization and filtering
- Multiple tags per customer
- Searchable and filterable across customer list

**Notes:**
- **Internal Notes** — Not visible to customer
- **Files/Attachments** — Upload documents, photos
- **Contracts** — Attach contract documents

**Custom Fields (Pro/Enterprise):**
- Custom fields can be created per tenant
- Field types:
  - Free text
  - Number
  - Date (with calendar picker)
  - Checkbox (toggle)
  - Dropdown (custom options)
- Visibility by role (Administrator, User, Read-Only)

**Related Records (Linked to Customer):**
- Asset records
- Work Order records
- Quote records
- Invoice records
- Payment records
- Notes and documents
- Communication history
- Service history timeline

**Customer Pipeline (Plus+):**
- Pipeline Status — Dropdown (customizable workflow statuses)
  - Default: Lead, Opportunity, Active, Inactive
  - Custom statuses configurable per business
- Lead tracking and conversion metrics

---

## 1.2 Asset Entity

### Asset Record Structure

> **Architectural Note:** The Asset is ServizDesk's primary organizing entity. Unlike competitor platforms where equipment tracking is optional and secondary to job records, ServizDesk treats every Asset as a first-class data entity with its own complete lifecycle — installation, service history, warranty tracking, maintenance schedules, and eventual decommissioning.

**Core Asset Fields:**
- **Asset Number** — Auto-generated (ServizDesk record numbering: A26-0001)
- **Customer** — Link to Customer record (required)
- **Location** — Link to Customer Location (defaults to primary service address)
- **Status** — Dropdown
  - Values: Active, Inactive, Decommissioned
- **Asset Category** — Dropdown (customizable)
  - Examples: HVAC, Plumbing, Electrical, Appliance, Other
- **Asset Type** — Dropdown (customizable per category)
  - Examples (HVAC): Split System, Package Unit, Mini-Split, Furnace, Boiler, Chiller

**Equipment Identification:**
- **Make** — Manufacturer (text or dropdown from managed list)
- **Model** — Model number (text)
- **Serial Number** — Unique identifier (text)
- **Installation Date** — Date picker
- **Age** — Calculated from installation date (display only)
- **Condition** — Dropdown: Excellent, Good, Fair, Poor
- **Refrigerant Type** — Text (HVAC-specific, optional)
- **Capacity / Size** — Text (e.g., "3 Ton", "200 Amp", "50 Gallon")

**Warranty Tracking:**
- **Warranty Start Date** — Date picker
- **Warranty End Date** — Date picker
- **Warranty Status** — Calculated: Active, Expired, N/A
- **Warranty Provider** — Text (manufacturer, extended warranty company)
- **Warranty Notes** — Free text (coverage details, exclusions)

**Asset Grouping (SubAsset Junction — Pro/Enterprise):**
- Assets can be assigned to other assets via the `SubAsset` junction table (many-to-many grouping)
- Supports hierarchical equipment structures and tool/accessory assignment
  - Example: Rooftop HVAC Unit → Compressor, Blower Motor, Control Board (components)
  - Example: CNC Machine → Calibration Tool Kit, Coolant Pump (assigned tools/accessories)
- Each asset in a group retains independent warranty tracking, service history, and lifecycle
- Asset group relationships visible in Asset detail view as a tree structure
- See Data Models V6 `SubAsset` for the full field definition (replaces the former `parent_asset_id` self-FK)

**Asset Relationships:**
- **Customer** — Required relationship
- **Location** — Service location at customer site
- **Service History** — All Work Orders linked to this Asset (chronological timeline)
- **Maintenance Plans** — Recurring maintenance schedules linked to this Asset
- **Documents** — Manuals, warranties, spec sheets, photos
- **Notes** — Asset-specific internal notes

**Custom Fields on Assets (Pro/Enterprise):**
- Custom fields can be created for Asset records
- Same field types as Customer custom fields
- Separate from Customer custom fields

**Attachments:**
- **Photos** — Upload from mobile or desktop
  - Installation photos, nameplate photos, condition photos
- **Files** — PDF manuals, spec sheets, warranty documents
- **QR Code** — System-generated QR code per Asset for field scanning (Pro/Enterprise)

---

## 1.3 Service Request (Call Intake) Entity

> **Naming Note:** The canonical name for this entity is **Service Request** (prefix SR). All internal references, record numbering, URL patterns, and code must use `service_request` / `SR`.

### Service Request Record Structure

**Purpose:** The entry point for all new customer requests before they are converted into scheduled Work Orders or Quotes. This handles triage, incoming web bookings, and call center intake.

**Service Request Fields:**
- **Service Request Number** — Auto-generated (ServizDesk record numbering: SR26-0001)
- **Customer** — Link to Customer record (required)
- **Asset** — Link to Asset record (Nullable — linked when the asset being serviced is identified during triage)
- **Address** — Link to Address record (Nullable — service location)
- **Status** — Dropdown
  - Values: New, Triaged, Converted to Work Order, Converted to Quote, Cancelled
- **Source** — Dropdown
  - Values: Phone, Customer Portal, Web Widget, Email, Referral
- **Issue Category** — Dropdown (e.g., HVAC Repair, Plumbing Leak, Electrical Outage)
- **Urgency** — Dropdown (Low, Normal, High, Emergency)
- **Customer Issue Description** — Text (exact customer wording)
- **Triage Notes** — Internal text (dispatcher/CSR notes on next steps)
- **Requested Date/Time** — Customer's preferred service window (from portal/widget)

**Service Request Relationships:**
- **Customer Portal** — Service Requests are directly created by the customer via the Portal
- **Work Orders** — When triaged successfully, a Service Request converts into a Work Order or Quote; the originating Service Request is linked via FK on the Work Order (`service_request_id`)

---

## 1.4 Work Order Entity

### Work Order Record Structure

**Core Work Order Fields:**
- **Work Order Number** — Auto-generated (ServizDesk record numbering: W26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Asset** — Link to Asset record (one Asset per Work Order; nullable)
  - Multi-asset coordination is handled via WorkGroups (see Section 1.5)
- **Related WorkGroup** — Link to WorkGroup (optional, Plus+)
- **Work Order Status** — Dropdown
  - Default statuses: Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled
  - **Custom Status Workflows (Pro/Enterprise)** — Configurable per business
    - Example: "Permit Pending", "Material Ordered", "Awaiting Inspection"
    - Custom statuses can be created for specific service types
- **Assigned To** — Single employee assignment (FK to Employee/User record)
- **Priority** — Dropdown (Low, Normal, High, Urgent)
- **Scheduled Date/Time** — Date and time picker
- **Estimated Duration** — Time estimate
- **Work Order Type** — Dropdown (customizable service categories)
  - Examples: Service Call, Repair, Installation, Maintenance, Inspection, Diagnostic
- **Location** — Defaults to customer service address, can override

**Work Order Description:**
- **Title/Summary** — Short description
- **Detailed Description** — Long-form text field
- **Internal Notes** — Not visible to customer
- **Customer-Facing Notes** — Visible in customer portal (Plus+)

**Checklists:**
- **Checklist Items** — Ordered list of steps/inspection items per Work Order
- Each checklist item has:
  - Label (text description of the step)
  - Checkbox (complete/incomplete)
  - Optional: Notes field per item
  - Optional: Photo attachment per item
- **Checklist Templates** — Pre-configured checklists that auto-apply by Work Order Type
  - Example: "Annual HVAC Maintenance — 12-Point Inspection"
  - Templates managed in Admin Area
- Completed checklists saved as permanent record of work performed

**Tasks (Subtasks):**
- Can create multiple tasks within a Work Order
- Each task has:
  - Task name
  - Assigned to (employee)
  - Status (Open, In Progress, Completed)
  - Due date
  - Notes
- Task progress tracking

**Recurring Work Orders:**
- Toggle: "Make this Work Order recurring"
- Recurrence options:
  - Daily
  - Weekly
  - Monthly
  - Quarterly
  - Semi-Annual
  - Annual
  - Custom interval
- Auto-generate future Work Orders based on schedule
- Link to Maintenance Plan if applicable

**Time Tracking:**
- **Clock In/Out** — Time tracking per employee per Work Order
- **Time Entries** — View time by Work Order, employee, or date range
- **Arrival/Departure Times** — Logged per visit
- **Total Hours** — Calculated automatically
- **Labor Cost** — Calculated from hours × employee rate

**Custom Fields on Work Orders (Pro/Enterprise):**
- Custom fields can be created for Work Order records
- Same field types as Customer custom fields
- Separate from other entity custom fields

**Attachments:**
- **Photos** — Upload from mobile or desktop
  - Before/After photo capability
- **Files** — PDF, documents, forms
- **Forms** — Custom form attachments (Pro/Enterprise)
- **Signatures** — Customer sign-off capture

**Related Records:**
- **Quotes** — Linked quote(s)
- **Invoices** — Linked invoice(s)
- **Assets** — Linked asset(s) with service context
- **Purchase Orders** — Related PO records (Plus+)
- **WorkGroup** — Parent WorkGroup if applicable (Plus+)

---

## 1.5 WorkGroup Entity (Plus+)

### WorkGroup Structure

> **Naming Note:** The ERD labels this entity WorkGroup(Project) and its sub-grouping WG Division(Epic). In ServizDesk, these are called WorkGroups and WGDivisions. The "Project" and "Epic" labels are reserved for the future ServizmaProjects product, which will build on top of this same schema.

**Purpose:** Group multiple Work Orders under a single umbrella for complex, multi-phase work (e.g., HVAC system replacement, electrical panel upgrade, bathroom remodel). Because ServizDesk enforces one Asset per Work Order, WorkGroups provide the rolled-up multi-asset view across grouped Work Orders.

**WorkGroup Fields:**
- **WorkGroup Number** — Auto-generated (ServizDesk record numbering: WG26-0001)
- **WorkGroup Name** — Text (required; user-defined label, e.g., "HVAC System Replacement - Johnson Residence")
- **Customer** — Link to Customer record (required)
- **Address** — Link to Address record (service location for the group)
- **Status** — Dropdown
  - Values: Open, In Progress, Completed, Cancelled
- **Notes** — Internal notes

**WGDivision (Sub-Grouping):**
- **Purpose:** Subdivide a WorkGroup into logical phases or sections (e.g., "Phase 1: Demo", "Phase 2: Rough-In", "Phase 3: Finish")
- **Division Name** — Text (required)
- **Address** — Link to Address record (division-specific location, if different from WorkGroup)
- A WorkGroup has zero or more WGDivisions
- Work Orders and Tasks can reference a specific WGDivision for phase-level organization

**WorkGroup Team (WorkGroupTeam):**
- **Purpose:** Assign employees to the WorkGroup with defined roles
- Each `WorkGroupTeam` record links one Employee to the WorkGroup with a role
- **WGTRole** — Tenant-configurable role lookup table (e.g., Lead Technician, Helper, Project Manager, Supervisor). Tenants define their own role list in Tenant Preferences. At least one WGTRole must exist before employees can be added to a WorkGroup.

**WorkGroup Assets (WorkGroupAsset):**
- **Purpose:** Rolled-up view of all Assets involved across the WorkGroup's Work Orders
- Each `WorkGroupAsset` record links an Asset to the WorkGroup
- **Population rule:** WorkGroupAsset records are created automatically by the system when a Work Order with a non-null `asset_id` is added to (or removed from) a WorkGroup. They are system-managed, not manually editable. This provides a single place to see every Asset being serviced across the grouped Work Orders without requiring manual maintenance.

**WorkGroup Components:**
- **Grouped Work Orders** — Multiple Work Orders linked to WorkGroup (each WO has its own single Asset)
- **Timeline Tracking** — Visual view of WorkGroup schedule
- **Cost Tracking** — Real-time labor, materials, overhead aggregated from linked Work Orders
- **Profitability Monitoring** — Track margin throughout the WorkGroup

**WorkGroup-Level Features:**
- **Multi-day support** — Work Orders spanning multiple visits/phases
- **Team coordination** — Assign different employees per phase via WGDivisions
- **Progress billing** — Invoice by phase or percentage of completion (Pro/Enterprise)

---

## 1.6 Quote Entity

### Quote Record Structure

**Header Fields:**
- **Quote Number** — Auto-generated (ServizDesk record numbering: Q26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Related Work Order** — Link to Work Order (optional)
- **Related WorkGroup** — Link to WorkGroup (optional, Plus+)
- **Related Asset(s)** — Link to Asset(s) being quoted for service
- **Quote Date** — Date picker (defaults to today)
- **Expiration Date** — Date picker (configurable default in settings)
- **Assigned To** — Employee who created/owns quote

**Quote Status:**
- **Draft** — Being created
- **Sent** — Sent to customer
- **Viewed** — Customer opened quote (tracked)
- **Accepted** — Customer accepted
- **Rejected** — Customer rejected
- **Expired** — Past expiration date
- **Converted** — Converted to Invoice or Work Order

**Line Items:**
- **Add from Product Catalog** — Pull from pre-defined inventory
- **Create New Line Item** — Create on-the-fly
- **Insert Bundle** — Pre-configured bundles of items

**Line Item Fields (per item):**
- **Item Name** — Text
- **Type** — Dropdown
  - Service
  - Product - Inventory
  - Product - Non-Inventory
- **SKU** — Text (optional)
- **Description** — Long-form text
- **Unit Cost** — Currency (internal cost — not visible to customer)
- **Unit Price** — Currency (customer price)
- **Markup** — Percentage or fixed amount
- **Quantity** — Number
- **Taxable** — Toggle (yes/no)
- **Visible to Customer** — Toggle (can hide internal line items)

**Line Item Organization:**
- **Groupings** — Group items with title and subtotal
  - Can hide individual item names/prices from customer
  - Show only group total
- **Bundles** — Pre-configured sets of items (see Product Catalog section)
  - Saved bundles can be inserted with one click
- **Add-On Options** — Optional items customer can select (Pro/Enterprise)
  - Create optional items customers choose when approving

**Good/Better/Best Proposals (Pro/Enterprise):**
- **Multi-Option Quoting** — Create multiple pricing tiers within a single quote
- Customer sees options side-by-side and selects preferred tier
- Each option has its own line items, subtotal, and description
- Increases average ticket by anchoring to middle option

**Subtotal Calculations:**
- **Line Item Subtotal** — Sum of all line items
- **Discounts** — Percentage or fixed amount
- **Surcharges** — Additional fees
- **Tax** — Applied to taxable items only
  - Default tax rate from settings
  - Can override per-quote
- **Grand Total** — Final amount

**E-Signature / Online Approval:**
- **Shareable Approval Link** — URL sent to customer for review and approval
- **Digital Approval** — Customer clicks "Approve" with typed name or signature capture
- **Approval Record** — System records: who approved, when, from what device/IP
- Approval notification sent to assigned employee

**Deposit Collection:**
- **Deposit Amount** — Fixed dollar or percentage of total
- **Deposit Required on Approval** — Toggle
- When enabled, customer is directed to payment after approving
- Deposit collected via Stripe Payment Link
- Deposit tracked against eventual invoice balance

**Notes & Attachments:**
- **Quote Notes** — Visible to customer on PDF/approval page
- **Internal Notes** — Not visible to customer
- **Files** — Attach supporting documents (photos, spec sheets)

**Templates:**
- **Save as Template** — Toggle when creating quote
- Templates include: all line items, groupings, bundles, tags, custom fields, notes
- **Import Template** — Select saved template when creating new quote

**Quote PDF Customization:**
- Company information (logo, address, contact)
- Verbiage customization (call it "Quote", "Estimate", "Proposal", etc.)
- Show/hide fields: SKU, description, unit price, quantity, line subtotals, tax breakdown
- Header/footer customization

**Conversion:**
- **Convert to Invoice** — One-click conversion
  - Transfers all line items, customer info, Work Order link
  - Deposits already collected are applied to invoice balance
- **Convert to Work Order** — Generate Work Order from approved quote
  - Creates Work Order linked to customer and Asset(s)

---

## 1.7 Invoice Entity

### Invoice Record Structure

**Header Fields:**
- **Invoice Number** — Auto-generated (ServizDesk record numbering: I26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Related Work Order** — Link to Work Order (optional)
- **Related WorkGroup** — Link to WorkGroup (optional, Plus+)
- **Related Asset(s)** — Link to Asset(s) serviced
- **Invoice Date** — Date picker (defaults to today)
- **Due Date** — Date picker
  - Auto-populate methods (configurable):
    - Based on Creation Date + N days
    - Based on Sent Date + N days
    - Based on Work Order Completion + N days
    - Manual entry
- **Assigned To** — Employee

**Invoice Status:**
- **Draft** — Being created
- **Issued** — Sent to customer
- **Viewed** — Customer opened invoice (tracked)
- **Partially Paid** — Partial payment received
- **Paid** — Full payment received (auto-updated)
- **Overdue** — Past due date, unpaid
- **Void** — Invoice voided
- **Written Off** — Bad debt write-off

**Line Items:**
- Identical structure to Quotes
- Can pull from Product Catalog or create new
- Bundles and groupings supported
- Visibility controls per line item

**Recurring Invoices (Plus+):**
- **Toggle: Make Recurring**
- Recurrence options:
  - Weekly
  - Monthly
  - Quarterly
  - Annual
  - Custom interval
- Auto-generate and optionally auto-send

**Payment Features:**
- **Record Manual Payment** — Cash, check, bank transfer, other
- **Stripe Payment Link** — Generate payment link for customer
  - Link displayed on Invoice detail view as copyable URL
  - Customer pays via Stripe-hosted payment page
  - Webhook updates Invoice status automatically
- **Partial Payments** — Record multiple payments against invoice
- **Deposits Applied** — Deposits collected on Quotes reduce balance due

**Subtotal Calculations:**
- **Line Item Subtotal**
- **Discounts** — Percentage or fixed amount
- **Surcharges** — Additional fees
- **Tax** — Configurable tax rate
- **Total Due**
- **Deposits Applied** — From quote approval
- **Amount Paid** — Sum of payments received
- **Balance Due** — Calculated remaining

**Commission Tracking (Pro/Enterprise):**
- **Enable Commission Calculations** — Toggle in settings
- Methods:
  - Percentage of gross sales
  - Percentage of gross margin
- Default rate configurable
- Can override per invoice

**Notes & Attachments:**
- **Invoice Notes** — Visible to customer
- **Internal Notes** — Hidden from customer
- **Files** — Supporting documents

**Templates:**
- **Save as Invoice Template** — Toggle when creating
- **Import Template** — Load pre-configured invoice structure

**Invoice PDF Generation:**
- Server-side PDF generation with professional formatting (Plus+)
- Company branding (logo, address, contact)
- Show/hide fields: SKU, description, unit price, quantity, tax breakdown
- Payment terms and due date
- Amount paid / balance due
- Header/footer customization
- Browser print available on all tiers

**Generation from Quotes:**
- **Convert Quote to Invoice** — Transfers all line items and details
- Deposits applied automatically
- Option to preserve quote record

---

## 1.8 Product Catalog (Items & Services)

### Product Repository Structure

**Purpose:** Central catalog of all products and services the business offers. Products are referenced on Quotes, Invoices, and Work Orders as line items.

**Product Fields:**
- **Product Number** — Auto-generated (ServizDesk reverse-alphabet year encoding; e.g., YU-0001 for 2026, YT-0001 for 2027 — see Numbering Service V1 Section 6.1 for the cipher table)
- **Product Name** — Text (required)
- **Type** — Dropdown (required)
  - **Service** — Labor, service work
  - **Product - Inventory** — Physical part, track stock levels (Plus+)
  - **Product - Non-Inventory** — Physical part, don't track stock
- **Category** — Dropdown (customizable)
- **SKU** — Text (optional)
- **Unit Cost** — Currency (what you pay)
- **Unit Price** — Currency (what you charge)
- **Markup** — Calculated (Price - Cost / Cost × 100)
- **Description** — Long-form text
- **Taxable** — Toggle (yes/no)

**Inventory Tracking (Plus+ — Products with type "Product - Inventory"):**
- **Quantity on Hand** — Number
- **Quantity Minimum** — Trigger for low stock alert
- **Quantity Allocated** — How much on Work Ordres
- **Quantity On Order** — How much on purchase orders
- **Quantity Reserved** — How much reserved
- **Quantity Available** — How much available
- **Preferred Vendor** — Link to Vendor (if using vendor management)
- **Location/Hub** — Where item is stored
  - Multiple locations supported (Pro/Enterprise)
  - Track inventory per location
  - Track inventory per truck (Enterprise)

**Serialized Inventory (Pro/Enterprise):**
- **Toggle: Serialized Item**
- Each unit has unique serial number
- Track:
  - Serial number
  - Storage location (hub/truck)
  - Installation date
  - Which technician used it
  - Which customer received it (links to Asset record)
  - Warranty coverage
- Auto-decrement when invoiced by serial number

**Bundles:**
- **Pre-configured sets of items** — Multiple products/services grouped as a reusable package
- Example: "Water Heater Replacement Bundle" = water heater + supply lines + shutoff valves + gas connector + labor
- Bundles can be inserted with one click on Quotes and Invoices
- Individual items within bundle are editable after insertion

**Price Tiers (Pro/Enterprise):**
- **Customer-Specific Pricing** — Create multiple price tiers
  - Examples: Residential Standard, Commercial Standard, Preferred Customer, Contractor Discount
- Two pricing methods:
  - **Markup/Discount from base** — Percentage adjustment from catalog price
  - **Flat price per tier** — Fixed price for tier
- Price tier assigned to Customer record
- Auto-applies tier pricing on Quotes/Invoices
- Can override per line item

**Pricebook Integration (Pro/Enterprise):**
- Pre-built pricebooks for common services
- Flat-rate pricing capability
- Select equipment/service, auto-populates pricing and labor

**Mass Import:**
- Import products via CSV template
- Template includes all standard fields

---

## 1.9 Warehouse / Location Entity (Plus+)

### Warehouse Record Structure

**Purpose:** Defines the physical or mobile locations where inventory (Products) is stored. A warehouse can be a physical building, a storage hub, or a service van/truck.

**Warehouse/Location Fields:**
- **Warehouse Number** — Auto-generated (ServizDesk record numbering: WH26-0001)
- **Warehouse Name** — Text (required — e.g., "Main Hub", "Van 01", "Van 02")
- **Type** — Dropdown
  - Values: Physical Hub, Mobile (Van/Truck)
- **Status** — Active, Inactive
- **Assigned Employee** — Link to Employee (especially for Mobile/Van types)
- **Address** — Full address (for Physical Hubs)
- **Notes** — Internal notes

**Warehouse Relationships:**
- **Sub-Locations** — One Warehouse has many sub-locations
- **Purchase Orders** — POs can be received directly into a specific Warehouse
- **Work Orders** — Inventory used on a Work Order is decremented from the assigned Warehouse (usually the technician's van)

### Sub-Location Record Structure

**Purpose:** Defines granular storage spots within a parent Warehouse, such as a specific shelf, bin, or room.

**Sub-Location Fields:**
- **Location Number** — user-generated (e.g., "A1.B3.C2", "B2.C1.A3", "C3.B2.A1")
- **Parent Warehouse** — Link to Warehouse record (required)
- **Type** — Dropdown (customizable)
  - Default values: Area, Bin, Shelf, Section, Cabinet, Room
- **Description** — Text (e.g., "Back area for extra large items")
- **Status** — Active, Inactive

**Sub-Location Relationships:**
- **Inventory Quantity** — Product quantities are tracked per Sub-Location within the Warehouse
 - These roll up to the Warehouse level, and then to the Product level

---

## 1.10 Payment Entity

### Payment Record Structure

**Payment Types:**
- **Credit/Debit Card** — Via Stripe Payment Links
- **Cash**
- **Check**
- **Bank Transfer**
- **Other** — Custom payment method

**Payment Fields:**
- **Payment Number** — Auto-generated (ServizDesk record numbering: P26-0001, annual reset)
- **Payment Date** — Date received
- **Amount** — Currency
- **Payment Method** — Dropdown (see types above)
- **Reference Number** — For check/transfer tracking
- **Applied To** — Link to Invoice(s)
  - Can split payment across multiple invoices (Pro/Enterprise)
- **Notes** — Internal notes about payment

**Stripe Integration:**
- **Payment Links** — Generated per Invoice for customer self-service payment
- **Webhook Processing** — Automatic payment recording on successful Stripe payment
- **Idempotent Processing** — Duplicate webhook events do not create duplicate records
- **No markup** — ServizDesk passes through Stripe fees with no additional markup

**Consumer Financing (Pro/Enterprise):**
- **Third-party integration** — Wisetack or equivalent
- Offer financing to customers at point of sale
- Financing option presented during Quote approval or Invoice payment
- Full payment received from financing company; customer pays financing company over time
- Approval and terms managed by financing partner

**Payment Tracking:**
- Payment history per customer
- Payment status on invoices
- Aging reports — Track overdue invoices (Plus+)
- Payment reminders — Automated reminders for unpaid invoices (Plus+ automation)

---

## 1.11 Part Requisition Entity (Plus+)

### Part Requisition Structure

**Purpose:** Allows field technicians to request parts from the warehouse or purchasing agent. This explicitly bridges the gap between field demand and inventory/purchasing fulfillment.

**Requisition Fields:**
- **Requisition Number** — Auto-generated (ServizDesk record numbering: RQ26-0001)
- **Requested By** — Link to Employee (Technician)
- **Related Work Order** — Link to Work Order (optional, but typical)
- **Required By Date** — Date picker
- **Status** — Dropdown
  - Values: New, Approved, Partially Fulfilled, Fulfilled, Cancelled
- **Fulfillment Method** — Dropdown
  - Values: Warehouse Transfer, direct Purchase Order

**Requisition Line Items:**
- **Product** — Link to Product Catalog (or free-text for non-catalog items)
- **Quantity Requested** — Number
- **Quantity Fulfilled** — Number (updates as parts arrive)
- **Notes** — E.g., "Need specific brand for consistency with existing panel"

**Requisition Workflow:**
- Technician submits Requisition from mobile app
- Purchasing agent or Warehouse Manager reviews
- Requisition can be converted directly into a Purchase Order (sent to Vendor) or an Inventory Transfer (from Main Hub to Technician Van)

---

## 1.12 Purchase Order Entity (Plus+)

### Purchase Order Structure

**PO Fields:**
- **PO Number** — Auto-generated
- **Vendor** — Link to Vendor record (required)
- **Related Work Order** — Link to Work Order (optional)
- **Related WorkGroup** — Link to WorkGroup (optional, Plus+)
- **Order Date** — Date picker
- **Expected Delivery Date** — Date picker
- **Status** — Draft, Sent, Partially Received, Received, Cancelled

**PO Line Items:**
- **Product** — From Product Catalog or create new
- **Quantity Ordered** — Number
- **Quantity Received** — Number (updated on receipt)
- **Unit Cost** — Cost per unit
- **Total** — Calculated

**PO Creation:**
- Create from web app
- Create from mobile (Pro/Enterprise)
- From Work Order — Technician can flag missing parts and generate PO

**Receiving:**
- Mark line items as received (full or partial)
- Receiving updates inventory quantities automatically
- Variance tracking (ordered vs. received)

---

## 1.13 Vendor Entity (Plus+)

### Vendor Record Structure

> **Standalone Entity:** Vendors are a completely separate entity from Customers. There is no connection between them. In Lite, there is no reference to Vendors in any way.

**Vendor Fields:**
- **Vendor Name** — Text (required)
- **Status** — Dropdown
  - Values: Active, Inactive, Do Not Use
  - Transitions: Active ↔ Inactive (reversible), Inactive → Do Not Use (blocks all new POs; Admin only, requires reason), Do Not Use → Active (Admin only, requires reason). See System Status Specification V3 Section 20.
- **Account Number** — Vendor account reference
- **Notes** — Vendor-specific notes

**Contacts (via Contact Table):**
- Vendor has one or more Contact records
- Each Contact links a **Person** record to this Vendor
- Each Contact holds: Role/Title, Department, Status (Active/Left), Start Date, Left Date
- Socials (emails, social media links) managed via Socials Table (linked to Contact)
- Phone numbers managed via Phone Number Table (linked to Contact)

**Addresses (via Address Table):**
- Vendor addresses managed via shared Address Table

**Phone Numbers (via Phone Number Table):**
- Phone numbers linked to Vendor and/or Contact records

**Vendor Relationships:**
- **Contacts** — People associated with this vendor (via Contact Table)
- **Purchase Orders** — POs sent to this vendor
- **Vendor Bills** — Bills received from this vendor
- **RMAs** — Return Merchandise Authorizations with this vendor
- **Vendor Payments** — Payment records for AP transactions with this vendor

---

## 1.14 Person Entity

### Person Record Structure

> **Architectural Note:** The Person entity represents a permanent human identity, independent of any company or customer relationship. A Person can be linked to multiple Customers (or Vendors) through Contact records. When a person changes companies, their Person record persists — only the Contact relationship changes. This preserves complete transaction and communication history across company transitions.

**Person Fields:**
*(Note: Person has no visible record number since it is handled completely behind the scenes.)*
- **First Name** — Text (required)
- **Last Name** — Text (required)

**Person Relationships:**
- **Contacts** — All Contact records linking this Person to Customers and/or Vendors
- **Socials** — Personal social media profiles and personal emails (via Socials Table, linked to Person)
- A single Person can have multiple active Contacts (e.g., a property manager across several accounts)
- Person record is never deleted when a Contact is removed — history is preserved

---

## 1.15 Socials Entity

### Socials Record Structure

> **Architectural Note:** The Socials table provides a unified way to store emails, social media links, and other digital identities. It links to both **Contact** (for company-assigned emails and professional profiles) and **Person** (for personal emails and social media profiles). The Type field auto-detects emails; users select social media types when entering links.

**Socials Fields:**
- **Type** — Dropdown (required)
  - Values: Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other
  - Auto-detected for email entries
- **URL** — Text (required)
  - For Email type: the email address itself
  - For social media types: the full URL to the profile/page

**Socials Relationships:**
- **Contact** — Link to Contact record (optional — for company-assigned emails and professional profiles)
- **Person** — Link to Person record (optional — for personal emails and social media)
- At least one of Contact or Person is required
- Supports unlimited entries per Contact and per Person

---

## 1.16 Task Entity

### Task Record Structure

**Purpose:** Standalone internal tasks not tied to a specific Work Order. For intra-Work Order tasks, see Work Order subtasks (Section 1.4).

**Task Fields:**
- **Task Number** — Auto-generated (ServizDesk record numbering: T26-0001)
- **Title** — Text (required)
- **Description** — Long-form text
- **Assigned To** — Employee
- **Status** — Open, In Progress, Completed
- **Due Date** — Date picker
- **Priority** — Low, Normal, High, Urgent
- **Related Customer** — Link to Customer (optional)
- **Related Asset** — Link to Asset (optional)
- **Notes** — Internal notes

---

## 1.17 Native Accounting Entity (All Tiers)

### Financial Tier Scalability

> **Architectural Decision:** ServizDesk actively avoids fragile, two-way API syncs with external accounting platforms (like QuickBooks Online) due to historically high failure rates, API deprecations, and support burdens. Instead, ServizDesk utilizes a **"Native Accounting First"** approach that scales with the customer's tier, supported by robust, bulletproof CSV exports for external tax prep.

**Tier 1: Lite (Basic Income Ledger)**
- No true double-entry General Ledger under the hood.
- **Accounts Receivable (AR):** Tracks generated Invoices and applied Payments.
- **Basic Ledger:** A simple list view showing Balance Due per customer and total revenue collected.
- **Tax Handoff:** Relies on the **Standardized Accounting Export** (Section 7.1) for end-of-month CPA handoff.

**Tier 2: Plus (Advanced AR/AP & Expense Tracking)**
- No true double-entry General Ledger under the hood.
- **Advanced AR:** Adds aging reports (Outstanding invoices by 30/60/90 days).
- **Accounts Payable (AP):** Introduces Purchase Orders and the ability to log Vendor Bills against them.
- **Basic Expense Tracking:** Ability to log one-off expenses (e.g., fuel receipts, ad-hoc material purchases) not tied to a PO to calculate basic job costing margin.
- **Tax Handoff:** Standardized Accounting Export + Expense/Bill exports.

**Tier 3: Pro (Native Core Accounting)**
- Introduces the **Chart of Accounts (COA)** (Assets, Liabilities, Equity, Revenue, Expenses).
- Introduces true **Double-Entry General Ledger (GL)**.
  - Completing WO / Generating Invoice → Credits Revenue, Debits AR
  - Receiving Payment → Credits AR, Debits Cash
  - Purchasing Inventory → Credits AP, Debits Inventory Asset
- Functions as a standalone accounting system for day-to-day operations.

**Tier 4: Enterprise (Full ERP Accounting)**
- All Pro features, plus:
- **Journal Entries:** Manual double-entry adjustments.
- **Multi-Location Accounting:** Track revenue/expenses by branch or department.
- **Bank Feed Integration:** Automated transaction importing via Plaid or Finicity for bank reconciliation.
- **Fixed Asset Management:** Depreciation tracking for vehicles and heavy equipment.
- **Complex Tax Liabilities:** Automated tax liability tracking across multiple jurisdictions.

---

## 1.18 Fleet / Vehicle Entity (Add-On — Plus+)

### Vehicle Record Structure

**Purpose:** Tracks the company's rolling assets (service vans, trucks, equipment trailers), managing their assignments, and maintenance schedules directly within the system.

**Vehicle Fields:**
- **Vehicle Number/ID** — Text (e.g., "Van-01")
- **VIN** — Text
- **Make/Model/Year** — Text
- **License Plate** — Text
- **Status** — Active, Out of Service, Decommissioned
- **Current Odometer** — Number (can be updated manually or via telematics integration)
- **Assigned Employee(s)** — Link to Employee

**Fleet Maintenance Features:**
- **Vehicle Maintenance** — Schedule and track preventative maintenance (oil changes, tire rotations)
- **Inspection Logs** — Connects to mobile app for daily/weekly driver inspections
- **Expense Tracking** — Track fuel, tolls, and repair costs per vehicle
- **Warehouse Link** — A Vehicle functions as a "Mobile Warehouse" (see Section 1.9) for inventory tracking purposes

---

## 1.19 WorkFlow Entity (Pro/Enterprise)

### WorkFlow Structure — Standard Operating Procedures

> **Architectural Note:** A WorkFlow is a reusable SOP (Standard Operating Procedure) template. It defines the steps, to-dos, required tools, required parts, and required safety forms for a type of work. WorkFlows are linked to Preventative Maintenance records (defining how recurring service is performed) and can be assigned to individual Work Orders (defining the SOP the technician follows on that job).

**WorkFlow Fields:**
- **WorkFlow Name** — Text (e.g., "Annual HVAC Tune-Up SOP", "Water Heater Installation Procedure")
- **Status** — Active, Inactive
- **Description** — Long-form text describing the purpose and scope of this SOP

**WFSteps (Ordered Steps):**
- Each WorkFlow contains one or more ordered Steps
- **Step Name** — Text (e.g., "Pre-Arrival Prep", "System Inspection", "Cleanup & Sign-Off")
- **Step Order** — Integer (sequence position within the WorkFlow)
- **Step Description** — Long-form text (detailed instructions for this step)

**WFStepToDos (Per-Step Checklist Items):**
- Each WFStep contains zero or more ToDo items
- **ToDo Description** — Text (e.g., "Verify power is disconnected", "Check refrigerant levels")
- **ToDo Order** — Integer (sequence within the step)
- These generate checklist items on the Work Order when the WorkFlow is applied

**WFTools (Required Equipment):**
- Links company-owned Equipment (tools, diagnostic devices) to the WorkFlow
- **Equipment** — Link to Equipment entity
- Defines what tools the technician must have to perform this SOP
- **Runtime behavior:** When a WorkFlow is applied to a Work Order, the required Equipment list is surfaced to the dispatcher and technician as a pre-job checklist. The system does **not** hard-block dispatch if tools are not checked out, but it raises a **soft warning** to the dispatcher when scheduling if any required Equipment item's status is not `Available` or is not currently checked out to the assigned technician. The warning is advisory — the dispatcher can override and proceed.

**WFInventory (Required Parts/Materials):**
- Links Products (inventory items) to the WorkFlow
- **Product** — Link to Product Catalog entity
- **Quantity** — Expected quantity needed
- Defines what parts/materials should be on the truck for this SOP

**WFSafetyForms (Required Safety Forms):**
- Links SafetyForm templates to the WorkFlow
- **SafetyForm** — Link to SafetyForm entity
- Defines which safety forms must be completed as part of this SOP
- Technician is prompted to complete required forms during Work Order execution

**WorkFlow Relationships:**
- **Preventative Maintenance** — PMs link to a WorkFlow (required for Pro+, nullable in Plus) defining how the recurring service is performed
- **Work Orders** — A Work Order can reference a WorkFlow as its assigned SOP
- **Equipment** — Required tools linked via WFTools
- **Products** — Required parts linked via WFInventory
- **Safety Forms** — Required forms linked via WFSafetyForms

---

## 1.20 Lead Entity (Plus+)

> **Architectural Note:** A Lead is a pre-customer record — a person or company that has expressed interest but has not yet been qualified or converted into a Customer. Leads are distinct from Customers. When a Lead is qualified, it is converted: a Customer record is created and the Lead is linked to it (or directly to an Opportunity). The Lead record is retained for history and is not deleted on conversion.

### Lead Record Structure

**Purpose:** Capture and track inbound prospects before they become paying Customers. Leads feed into the CRM pipeline and can be converted into Customers and/or Opportunities.

**Lead Fields:**
- **Lead Number** — Auto-generated (ServizDesk record numbering: L26-0001)
- **First Name** — Text (captured before Customer record exists)
- **Last Name** — Text
- **Phone** — Phone number
- **Email** — Email address
- **Customer** — Link to Customer record (Nullable — populated on conversion)
- **Source** — Dropdown
  - Values: Referral, Website, Advertisement, Trade Show, Cold Call, Other
- **Status** — Dropdown
  - Values: New, Contacted, Qualified, Converted, Lost
- **Notes** — Internal notes field

**Lead Relationships:**
- **Customer** — On conversion, the Lead is linked to the newly created (or matched) Customer record
- **Opportunity** — A qualified Lead may be promoted to an Opportunity; the Opportunity carries a back-link to the originating Lead

**Lead Conversion Workflow:**
1. Lead record created (manually by office staff, or via web widget intake)
2. Lead is contacted and qualified by staff
3. On qualification, status is set to **Qualified**
4. Staff triggers **Convert Lead** action:
   - System creates a new **Customer** record pre-populated from Lead fields (name, phone, email)
   - Lead `customer_id` FK is populated with the new Customer ID
   - Lead status is set to **Converted**
   - Optionally, system simultaneously creates an **Opportunity** linked to the new Customer and this Lead
5. The Lead record is retained as history — it is never deleted on conversion

---

## 1.21 Opportunity Entity (Pro+)

> **Architectural Note:** An Opportunity represents a qualified sales pursuit tied to an existing Customer. Unlike a Lead (which is pre-Customer), an Opportunity always requires a Customer record. Opportunities track the value, timeline, and contacts involved in winning a piece of work.

### Opportunity Record Structure

**Purpose:** Track sales pursuits for existing Customers — new installs, large replacements, upsell agreements, or commercial contracts. Opportunities are the CRM-layer bridge between a Customer relationship and a sold Work Order or CustomerAgreement.

**Opportunity Fields:**
- **Opportunity Number** — Auto-generated (ServizDesk record numbering: OP26-0001)
- **Opportunity Name** — Text (e.g., "HVAC Replacement - Johnson 2026", "Commercial Maintenance Contract - Acme Building")
- **Customer** — Link to Customer record (required)
- **Lead** — Link to Lead record (Nullable — populated if Opportunity originated from a Lead conversion)
- **Status** — Dropdown
  - Values: Open, Won, Lost
- **Estimated Value** — Currency
- **Expected Close Date** — Date picker
- **Assigned To** — Link to Employee (the salesperson or CSR responsible)
- **Notes** — Internal notes

**OpportunityContacts (Opportunity-Contact Assignment):**
- **Purpose:** Link one or more Customer Contacts to this Opportunity with a defined role. This captures *who the decision-makers and influencers are* for this sales pursuit.
- Each assignment record links:
  - **Opportunity** — This Opportunity (required)
  - **Contact** — Link to Contact record on the Customer (required)
  - **Role in Opportunity** — Free text (e.g., "Decision Maker", "Technical Evaluator", "Budget Holder", "Influencer")
- One Opportunity can have many assigned Contacts
- One Contact can be assigned to many Opportunities
- This is a junction table (`OpportunityContacts`) — it is not a direct field on the Opportunity record

**Opportunity Relationships:**
- **Customer** — Required; the Opportunity belongs to this Customer
- **Lead** — Optional back-link to the originating Lead (if converted from one)
- **Contacts** — Many Contacts linked via OpportunityContacts with roles
- **Work Orders** — A Won Opportunity can be linked to the Work Orders generated from it (for revenue attribution)
- **CustomerAgreements** — A Won Opportunity can be linked to the resulting Agreement

---

## 1.22 Equipment Entity (Pro/Enterprise)

> **Architectural Note:** Equipment refers to **company-owned tools** — diagnostic devices, power tools, test equipment, safety gear — that technicians check out for jobs. Equipment is distinct from: (a) **Assets** (customer-owned equipment being serviced) and (b) **Products/InventoryItems** (parts sold to customers). Do not conflate these three concepts.

### Equipment Record Structure

**Purpose:** Track the company's owned tools and equipment — what exists, where it is, who has it, and what condition it's in. Equipment items are linked to WorkFlow SOPs (via WFTools) as required tools for specific types of work.

**Equipment Fields:**
- **Equipment Number** — Auto-generated (ServizDesk record numbering: EQ26-0001)
- **Equipment Name** — Text (e.g., "Fluke 376 FC Clamp Meter", "Fieldpiece SMAN460 Manifold")
- **Category** — Dropdown
  - Values: Power Tool, Hand Tool, Diagnostic, Safety, Other
- **Serial Number** — Text (optional)
- **Status** — System-managed Dropdown
  - Values: Available, Checked Out, In Repair, Decommissioned
  - `Available` ↔ `Checked Out` transitions are driven automatically by CheckInOut records (see below)
  - `In Repair` and `Decommissioned` are set manually by office staff
- **Purchase Date** — Date picker
- **Purchase Cost** — Currency
- **Notes** — Internal notes

**CheckInOut (Equipment Check-In / Check-Out):**
- **Purpose:** Record which employee has which piece of Equipment, when they took it, and what condition it's in at checkout and return.
- Each CheckInOut record represents one checkout event. An open record (null `checked_in_at`) means the item is currently out.
- **CheckInOut Fields:**
  - **Equipment** — Link to Equipment record (required)
  - **Employee** — Link to Employee/User record (required)
  - **Checked Out At** — DateTime (required)
  - **Checked In At** — DateTime (Nullable — null = item is still checked out)
  - **Condition Out** — Dropdown: Good, Fair, Needs Repair
  - **Condition In** — Dropdown: Good, Fair, Damaged (populated on check-in)
  - **Notes** — Free text (damage notes, special circumstances)
- **Status auto-update rule:** When a CheckInOut record is created (checkout), the parent Equipment record's `status` is automatically set to `Checked Out`. When the record is closed (check-in, `checked_in_at` populated), `status` reverts to `Available`. This transition is system-enforced, not manual.

**Equipment Relationships:**
- **WorkFlow (via WFTools)** — Equipment items are linked to WorkFlow SOPs as required tools
- **CheckInOut records** — Full history of all checkout events per Equipment item
- **Employees** — Via CheckInOut; tracks who currently holds each item

---

## 1.23 SafetyForm Entity (Pro/Enterprise)

> **Architectural Note:** SafetyForms are reusable form templates that define what safety questions or compliance acknowledgments a technician must complete. They are linked to WorkFlow SOPs via WFSafetyForms (defining *which forms apply to which type of work*). When a WorkFlow is applied to a Work Order, the required SafetyForms become active for that job, and completed responses are stored in WOSFAnswer records. SafetyForms can also be attached to a Work Order directly without a WorkFlow.

### SafetyForm Record Structure

**Purpose:** Define reusable safety compliance form templates — lockout/tagout checklists, hazard assessments, confined space entry permits, chemical exposure acknowledgments, etc. Templates are defined once and reused across many Work Orders.

**SafetyForm Fields:**
- **Form Name** — Text (e.g., "Lockout/Tagout Pre-Work Checklist", "Electrical Safety Assessment")
- **Description** — Text (scope and intent of the form)
- **Status** — Active, Inactive, Draft
- **Form Definition** — Structured field definitions (stored as JSON). Defines the questions, field types (checkbox, text, signature, date), and order of the form.
- **Required Before Work** — Boolean flag. When `true`, this form must be completed by the assigned technician before the Work Order can advance to `In Progress` status.
  - **Enforcement rule:** If `required_before_work = true` and the technician attempts to advance a Work Order to `In Progress` without completing this form, the system **blocks the status transition** with an error message. This is a hard block, not a soft warning.
  - The assigned technician (the employee assigned to the Work Order) is responsible for completion. If multiple technicians are assigned, any one of them may complete the form.

**WOSFAnswer (Work Order Safety Form Answer):**
- **Purpose:** Record the completed responses to a SafetyForm for a specific Work Order and employee. One WOSFAnswer record is created per completed SafetyForm per Work Order.
- **WOSFAnswer Fields:**
  - **Work Order** — Link to Work Order (required)
  - **Employee** — Link to Employee/User who completed the form (required)
  - **SafetyForm** — Link to SafetyForm template (required)
  - **Answers** — Completed form responses (stored as JSON, matching the structure of `form_definition` on the SafetyForm)
  - **Completed At** — DateTime (when the form was submitted)
  - **Notes** — Free text (optional technician notes)
- **Relationship note:** WOSFAnswer records are created by technicians completing SafetyForms from the mobile/web interface during Work Order execution. They are append-only (no editing after submission).

**SafetyForm Relationships:**
- **WorkFlow (via WFSafetyForms)** — SafetyForms are linked to WorkFlow SOPs as required forms for that type of work
- **Work Orders (via WOSFAnswer)** — Completed SafetyForm responses are stored per Work Order
- **Employees (via WOSFAnswer)** — Records which employee completed which form on which job

---

# 2. Service Agreements & Maintenance Plans

> **Architectural Note:** Service agreements use a three-layer chain: **Agreement** (the template/terms) → **CustomerAgreement** (a specific Customer + Agreement + Asset binding) → **Preventative Maintenance (PM)** (the recurring schedule that generates Work Orders). This structure allows a single Agreement template to be applied to multiple Customers and Assets independently, each with its own PM schedule.

## 2.1 Agreement Entity (Plus+)

### Agreement Structure

**Purpose:** Define reusable service agreement templates with terms, coverage, and pricing tiers. An Agreement is not customer-specific — it is a template that gets linked to specific Customers and Assets via CustomerAgreement records.

**Agreement Fields:**
- **Agreement Name** — Text (e.g., "Annual HVAC Maintenance Agreement", "Quarterly Filter Service Plan")
- **Status** — Active, Inactive, Expired, Cancelled, Pending
- **Description** — Long-form text describing coverage, exclusions, terms
- **Renewal Type** — Manual, Auto-Renew
- **Pricing Amount** — Currency (base price for this agreement template)
- **Pricing Frequency** — Monthly, Quarterly, Annual
- **Plan Tiers (Pro/Enterprise)** — Define multiple service levels within an agreement
  - Example: Silver, Gold, Platinum
  - Different services/inclusions per tier
- **Discounts** — Agreement members receive percentage discount on additional work

## 2.2 CustomerAgreement Entity (Plus+)

### CustomerAgreement Structure

**Purpose:** Three-way junction binding a specific Customer, Agreement, and Asset together. This is where "Customer X has Agreement Y covering Asset Z" is recorded. One Customer can have multiple CustomerAgreement records (different agreements, different assets). One Agreement can apply to multiple Customers.

**CustomerAgreement Fields:**
- **Customer** — Link to Customer record (required)
- **Agreement** — Link to Agreement record (required)
- **Asset** — Link to Asset record (required — asset-centric; each CustomerAgreement covers one specific Asset)
- **Start Date** — Date the agreement coverage begins for this customer/asset
- **End Date** — Date coverage ends (Nullable — null = ongoing)
- **Status** — Active, Expired, Cancelled, Pending

**CustomerAgreement Relationships:**
- One Customer can have many CustomerAgreements
- One Agreement can be referenced by many CustomerAgreements
- One Asset can be covered by many CustomerAgreements (e.g., different agreement types)
- Each CustomerAgreement has one or more Preventative Maintenance (PM) records

## 2.3 Preventative Maintenance (PM) Entity (Plus+)

### PM Structure

**Purpose:** Define the recurring service schedule for a specific CustomerAgreement. PMs generate Work Orders automatically based on their schedule. A CustomerAgreement can have multiple PMs (e.g., a semi-annual A/C tune-up PM and a separate annual duct cleaning PM under the same agreement).

**PM Fields:**
- **PM Status** — Active, Paused, Expired, Cancelled
- **CustomerAgreement** — Link to CustomerAgreement record (required)
- **WorkFlow** — Link to WorkFlow SOP (required for Pro+; nullable in Plus)
- **Start Date** — Date picker
- **End Date** — Date picker (or Ongoing)
- **Renewal** — Manual, Auto-Renew

**Service Schedule:**
- **Frequency** — Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom
- **Visits per Period** — Number of visits included
  - Example: 2 visits/year (Spring A/C + Fall Heating)
- **Assigned To** — Default technician or assignment pool
- **Advance Generation Days** — How many days ahead of the scheduled date to auto-create the Work Order (tenant-configurable integer; e.g., 14 days)

**Auto-Generation Flags (Behavioral Rules):**
- **Auto-Generate Work Orders** — Boolean flag on the PM record. When `true`, the system's background scheduler creates a Work Order automatically per the configured Frequency and Advance Generation Days. When `false`, the PM fires a reminder only — a dispatcher must manually create the Work Order. Default: `true`.
- **Auto-Generate Invoices** — Boolean flag on the PM record (Pro/Enterprise only). When `true`, the system creates a Draft Invoice on each billing cycle date per the parent Agreement's `pricing_amount` and `pricing_frequency`. The Invoice is created in Draft status and must be reviewed/sent by office staff — it is not sent automatically. When `false`, invoicing is manual. Default: `false`.
- These two flags are independent. A PM can auto-generate Work Orders without auto-generating Invoices.

**PM Relationships:**
- Linked to CustomerAgreement (required — inherits Customer, Agreement, and Asset)
- Linked to WorkFlow (optional Plus, required Pro+ — defines the SOP for generated Work Orders)
- Generates Work Orders per schedule (if Auto-Generate Work Orders = true)
- Generates Draft Invoices per billing cycle (Pro/Enterprise only, if Auto-Generate Invoices = true)

**Reminders:**
- Auto-remind customer of upcoming maintenance
- Auto-remind assigned technician of scheduled service
- Reminder timing configurable (X days before scheduled date)

---

# 3. Scheduling & Dispatch

## 3.1 Schedule/Calendar Views

### Calendar Interface

**View Options:**
- **Daily View** — Single day, all employees
- **Weekly View** — Week at a glance
- **Employee View** — Per-employee schedule
- **Map View** — Geographic view of scheduled Work Orders (Pro/Enterprise)

**Drag-and-Drop Scheduling:**
- **Move Work Orders** — Drag to different date/time/employee
- **Resize** — Adjust Work Order duration
- **Color-coding** — By Work Order status, priority, type, or custom tags

**Employee Availability:**
- **Working Hours** — Set per employee
- **Time Off** — Block out unavailable times
- **Skills/Certifications** — Match Work Orders to qualified employees (Pro/Enterprise)

**Real-Time Updates:**
- Changes visible to office and field immediately
- Notifications to employees on schedule changes

## 3.2 Work Order Assignment

### Assignment Methods

**Manual Assignment:**
- **Drag-and-drop** — Assign Work Order to employee via calendar
- **From Work Order record** — Select assigned employee(s)
- **Multiple employees** — Assign multiple employees to one Work Order

**Smart Assignment (Pro/Enterprise):**
- **Skill-based matching** — Don't send a plumber to a high-voltage call
- **Availability-based** — Only show available employees
- **Workload balancing** — Distribute evenly across team

## 3.3 Route Planning (Pro/Enterprise)

### Location Features

**Travel Coordination:**
- **Travel time calculation** — Basic travel time estimates between Work Orders
- **Manual route planning** — Dispatcher arranges Work Orders by geography
- **Route optimization** — Traffic-aware route suggestions (Enterprise)

**Customer Notifications:**
- **"On the Way" Alerts** — Notify customer when employee is dispatched
- **Arrival Window** — Give customer expected arrival time window

---

# 4. Mobile Application

## 4.1 Mobile Access Strategy

### Responsive Web Application

**Platform Approach:**
- ServizDesk uses a **responsive web application** accessible from any modern mobile browser
- Full feature parity between desktop and mobile — every feature works identically on both
- No native iOS/Android app at launch — responsive web-first approach
- Progressive Web App (PWA) capability for home screen installation

> **Design Principle:** By delivering a single responsive web codebase, ServizDesk avoids the mobile parity gaps that plague competitors (FieldPulse: features missing on mobile, HousecallPro: Android 3.3/5 rating, Workiz: Android 3.0/5 rating). Every feature works on every device from Day 1.

## 4.2 Mobile Features

### Core Mobile Capabilities

**Schedule Access:**
- View daily/weekly schedule
- See Work Order details — customer, location, Asset info, notes, attachments
- Update Work Order status
- Clock in/out for time tracking

**Work Order Execution:**
- Access full customer record and Asset service history
- Add notes (internal and customer-facing)
- Capture photos (before/after documentation)
- Complete checklists
- Customer signature capture
- Upload attachments to Work Order record

**Quoting & Invoicing:**
- Create Quotes from mobile — full Quote creation with Product Catalog access
- Insert bundles and groupings
- Convert approved Quote to Invoice
- Create Invoices from mobile
- Generate Stripe Payment Links
- Record manual payments

**Offline Mode (Roadmap):**
- Read-only access to scheduled Work Orders, customer, and Asset data while offline
- Note-taking and photo capture queued for sync
- Data synchronized automatically when connectivity is restored
- Conflict resolution for changes made both offline and online

## 4.3 Mobile Web Parity Requirement

**Mandatory parity items — all features must work identically on mobile:**
- Tax rate application and override
- Discount and surcharge application
- Line item editing (add, remove, reorder)
- Custom field entry
- Photo upload and attachment
- Checklist completion
- Quote and Invoice PDF viewing
- All form submissions and data entry

---

# 5. Customer Communication & Portal

## 5.1 Communication (Plus+)

### Communication Features

**Email Communication:**
- Send Quotes, Invoices, and Payment Links to customers via email
- Email history tracked per customer
- Configurable email templates with business branding

**Automated Communications (Plus+ Automations):**
- **Appointment reminders** — Auto-remind customers of scheduled Work Orders
- **Work Order completion follow-up** — Thank you message after job
- **Payment reminders** — Auto-send reminders for unpaid invoices
- **Maintenance reminders** — Remind customers of upcoming scheduled service
- **Review requests** — Auto-request reviews after Work Order completion (Pro/Enterprise)

**Automation Engine (Plus+):**
- Basic automation rules: "IF [event] THEN [action]"
- Events: Work Order status change, Invoice overdue, Quote approved, Payment received
- Actions: Send email, send notification, update status
- Plus tier: 2–5 automation rules included
- Pro/Enterprise: Unlimited automation rules

## 5.2 Customer Portal (Plus+)

> **⚠️ UNSCOPED — PLACEHOLDER ONLY:** This section describes aspirational Customer Portal functionality that has not been formally scoped, discussed, or validated. The feature list below is a rough sketch carried forward from early planning. A dedicated Customer Portal Specification is required before any development begins on this module. Do not treat this section as authoritative scope.

### Portal Features

**Customer Self-Service:**
- **Request Service (Call Intake)** — Customers submit service or callback requests via web widget or portal
  - Request appears directly in ServizDesk as a **Service Request** (Section 1.3)
- **View Service History** — See past Work Orders and Invoices
- **Quote Review & Approval** — Full suite for Quote interaction
  - Customers can review, discuss (comment/message), approve, or reject Quotes
  - Digital E-signature for acceptance
- **Pay Invoices** — Online payment via Stripe (or integrated processor)
  - Supports both **partial payments** and **full payments**
- **View Asset Information** — See their registered Assets and warranty status
- **Communication** — Message directly with business/dispatcher

**Portal Branding:**
- Business logo and colors
- Custom portal URL (subdomain or custom domain)

**Online Booking Widget (Lite Minimal Version):**
- Simple service request form (embeddable on business website)
- Customer submits: name, email, phone number, issue description
- Appears in ServizDesk as an inbound **Service Request** (Section 1.3)
- No date/time selection — business contacts customer to schedule via the intake process

---

# 6. Reporting & Analytics

## 6.1 Dashboard

### Dashboard Features

**Overview Dashboard:**
- Key metrics at a glance
- Real-time data

**Key Metrics:**
- **Work Orders** — Open, scheduled today, completed, overdue
- **Quotes** — Sent, approved, rejected, conversion rate
- **Invoices** — Outstanding, overdue, paid this period
- **Revenue** — This month, year-to-date
- **Assets** — Total tracked, upcoming maintenance due
- **Employee activity** — Work Orders per employee, hours worked

**Filtering:**
- By date range
- By employee
- By Work Order type
- By customer
- By status

## 6.2 Reports

### Available Reports

**Work Order Reports:**
- **Work Order Summary** — Work Orders by status, type, employee
- **Completion Rate** — On-time vs. late completion
- **Work Order Duration** — Actual vs. estimated time
- **Asset Service Frequency** — Which Assets require the most service

**Financial Reports:**
- **Revenue Reports** — By period, by service type, by customer
- **Expense Reports** — Track costs, compare to budget (Plus+)
- **Profitability Reports** — Margin analysis per Work Order, per customer (Pro/Enterprise)
- **Tax Summary** — Simplified tax reporting
- **Aging Report** — Outstanding invoices by age bracket (Plus+)

**Employee Reports:**
- **Employee Performance** — Work Orders completed, hours worked, revenue generated
- **Time Tracking Reports** — Clock in/out, Work Order duration
- **Commission Reports** — Earnings by employee (Pro/Enterprise)

**Customer Reports:**
- **Customer List** — Exportable customer database
- **Service History** — Per-customer service timeline
- **Payment History** — Customer payment patterns

**Asset Reports:**
- **Asset Inventory** — All tracked Assets by customer, location, category
- **Warranty Expiration** — Assets with expiring warranties
- **Maintenance Compliance** — Planned vs. completed maintenance visits
- **Asset Lifecycle** — Service cost over lifetime of an Asset

**Inventory Reports (Plus+):**
- **Inventory Levels** — Quantity on hand by product
- **Low Stock Alerts** — Products below reorder point
- **Inventory Usage** — Parts used by Work Order, by employee
- **Inventory Value** — Total value of inventory
- **Fleet/Truck Min. Quantity Report** — Alerts for specific mobile warehouses (vans) that have fallen below required minimum stocking levels, generating pull sheets for restock

## 6.3 Exports

**Export Capabilities:**
- **CSV Export** — All major entity lists exportable to CSV
  - Customers, Work Orders, Quotes, Invoices, Payments, Assets, Products
- **PDF Export** — Quotes, Invoices, Work Orders (Plus+)
- **Accounting Export** — Standardized CSV export for CPAs (see Section 7.1)

---

# 7. Integrations

## 7.1 Accounting Exports (All Tiers)

> **Architectural Boundary:** ServizDesk does **not** support live, two-way API syncs with QuickBooks or Xero. Instead, ServizDesk relies on a highly stable **Standardized Accounting Export** format.

### Standardized Accounting Export
**Purpose:** A bulletproof, zero-maintenance method for handing financial data off to external CPAs and bookkeepers, completely immune to third-party API changes.

**Export Features:**
- **Pre-formatted for QuickBooks:** Exports are natively formatted to match the exact column structures required by QuickBooks Online/Desktop import tools.
- **Entities Exported:**
  - Customers / Vendors
  - Invoices (summary or line-item detail)
  - Payments Received
  - Purchase Orders / Bills (Plus+)
- **Automated Delivery:** Tenants can schedule the export (e.g., "1st of the month") to automatically email the CSV package securely to their designated CPA.

### Plaid / Finicity Integration (Enterprise)
- **Purpose:** One-way read-only sync from the user's bank into ServizDesk Enterprise's native General Ledger for Bank Reconciliation. No data is pushed *out* to external systems.

## 7.2 Payment Processing

### Stripe

- **Stripe Connect (Standard)** — Each tenant connects their own Stripe account
- **Payment Links** — Generated per Invoice for customer payment
- **Application fee** — ServizDesk charges a 0.5% application fee on all tenant payment transactions processed through Stripe Connect. See Pricing & Billing Specification V2 Section 9.3.
- **Webhook processing** — Automated payment recording
- **PCI SAQ A** — Card data never touches ServizDesk servers

### Consumer Financing (Pro/Enterprise)
- **Wisetack** or equivalent financing partner integration
- Offer payment plans to customers at point of sale
- Business receives full payment from financing company

## 7.3 Payroll Integration (All Tiers)

> **Architectural Boundary:** ServizDesk treats Payroll as an explicitly offloaded function. The system tracks Employee Time (clock-in/out, job hours) and Commissions, but wage calculation, tax withholding, and direct deposits are pushed to specialized third-party payroll providers.

**Supported Integrations / Exports:**
- **Gusto** (Direct API Sync)
- **ADP** (Export/Sync)
- **QuickBooks Payroll** (Direct API Sync)
- **Standard Payroll Export** (CSV format for manual upload to any provider)

## 7.4 Other Integrations

**Calendar:**
- **Google Calendar** — Sync Work Order schedule (Plus+)

**Communication:**
- **Email Provider** — Platform-managed (point-based, via Postmark) by default. Custom Domain authentication available as a paid add-on (Pro and Enterprise) — see ServizDesk Email Specification V1 and Pricing & Billing Specification V2 Section 11.4.

**Automation (Pro/Enterprise):**
- **Zapier** — Connect to external apps and services
- **Webhooks** — Event-based notifications to external systems
- **REST API** — Programmatic access to ServizDesk data (Pro/Enterprise)

---

# 8. Custom Work Order Statuses & Forms (Pro/Enterprise)

## 8.1 Custom Work Order Statuses

### Status Configuration

**Purpose:** Configure custom Work Order status values specific to business type or service category, beyond the system defaults (Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled).

> **Clarification:** Custom Work Order statuses are a configuration feature on the Work Order entity — they define what statuses a WO moves through. This is separate from the **WorkFlow SOP engine** (Section 1.19), which defines *how* work is performed (steps, to-dos, tools, parts, safety forms).

**Examples:**
- **Plumbing:** "Permit Pending", "Material Ordered", "Awaiting Inspection"
- **Electrical:** "Permit Applied", "Inspection Scheduled", "Inspection Passed"
- **HVAC:** "Equipment Ordered", "System Test", "Warranty Registered"

**Status Enforcement:**
- **Required steps** — Block Work Order closure until mandatory statuses have been reached
- **Guided progression** — Technicians follow status sequence in order
- **Documentation** — Track what status was set, when, by whom

## 8.2 Custom Forms

### Form Builder Features

**Form Types:**
- Service checklists (HVAC maintenance, safety)
- Equipment installation forms
- Customer sign-off forms
- Inspection reports
- Compliance/regulatory forms

**Form Field Types:**
- Text fields
- Date fields (calendar picker)
- Checkboxes (yes/no toggles)
- Dropdown lists
- Signature fields (e-signature capture)
- Photo upload (attach images to form)

**Required Fields:**
- Toggle: "Required Field" — Must be completed before submission

**Form Usage:**
- Fill out on mobile in the field
- Attach to Work Order record as permanent documentation
- Send to customer for e-signature
- PDF generation of completed forms

---

# 9. User Management & Permissions

## 9.1 User Roles

### Role Types

**Administrator:**
- Full access to all features and settings
- Company settings and preferences
- Billing management (via SDP)
- Employee management
- All customer, Asset, and Work Order data

**User:**
- Operational access to day-to-day features
- Create and edit Customers, Assets, Work Orders, Quotes, Invoices
- Record payments
- View schedule and assigned Work Orders
- Limited Admin Area access (no billing, no employee management)

**Read-Only:**
- View-only access to all operational data
- Cannot create, edit, or delete records
- Cannot record payments
- Useful for bookkeepers, office assistants reviewing data

**Custom Roles (Pro/Enterprise):**
- Define custom permission profiles
- Granular control over which entities and actions each role can access
- Field-level visibility controls (e.g., hide cost/margin data from field roles)

## 9.2 Permissions

### Access Controls

**Entity-Level Permissions:**
- Per-entity create, read, update, delete controls
- Configurable per role

**Field-Level Visibility (Pro/Enterprise):**
- Show/hide financial data (cost, margin, markup) by role
- Show/hide internal notes by role
- Custom field visibility by role

**Data Scope:**
- Administrator: sees all data
- User: sees all operational data
- Read-Only: sees all data, cannot modify
- Custom roles can be scoped to assigned Work Orders only (Pro/Enterprise)

## 9.3 User Sessions & Audit Trail

### Access & Activity Logging

> **Scope:** The system maintains a continuous audit trail of user access and specific actions performed within the UI. This ensures accountability and provides a historical record of "who did what, when, and from where."

**Session Logging (On Login Attempt):**
- **Session ID** — Unique identifier for the login session
- **User Details** — User ID, Name, Employee Number
- **Time Tracking** — Login Timestamp, Logout/Expiration Timestamp, Session Duration
- **Environment Data:**
  - **IP Address** — Originating IP
  - **Browser** — User Agent string (parsed)
  - **Operating System**
  - **Device Type** — Mobile vs. Desktop

**Audit Event Logging (During Session):**
- **Event Timestamp** — Exact time of the action
- **Action Performed** — The CRUD operation or major state change (e.g., Created, Updated, Deleted, Approved, Voided)
- **Target Record** — The entity type affected (e.g., Work Order, Quote, Customer, Invoice)
- **Record ID** — The specific identifier of the affected record (e.g., W26-0042)
- **Event Details** — Contextual information about the change (e.g., "Changed status from Draft to Sent", "Updated Line Item Quantity")
- **Relationships** — Every Audit Event is a child record linked to the originating **Session ID**

---

# 10. Tenant Preferences & Settings

## 10.1 Company Information

### Business Identity

> **Scope:** These settings apply at the tenant level. For Lite/Plus/Pro tiers, a single location is assumed. Enterprise tier supports multiple locations with location-specific overrides (see Section 10.5).

**Company Details:**
- **Company Name** — Text (required)
- **Address** — Text
- **City** — Text
- **State/Province** — Text
- **ZIP/Postal Code** — Text
- **Country** — Dropdown (default country for tenant)
- **Phone** — Phone (primary business phone)
- **Fax** — Phone (optional)
- **Email** — Email (primary business email)
- **Website** — URL (optional)

**Branding:**
- **Company Logo** — Image upload
  - Used on all printed forms (Quotes, Invoices, Work Orders)
  - Displayed in system header, Customer Portal, and email templates
  - Recommended dimensions provided during upload

## 10.2 Regional & Locale Settings

### Default Locale Configuration

**Currency & Numbers:**
- **Default Currency** — Dropdown (e.g., USD, CAD, GBP, EUR)
- **Currency Symbol** — Text (auto-populated from currency, can override — e.g., $, £, €)
- **Decimal Precision** — Number (default: 2)

**Date & Time:**
- **Timezone** — Dropdown (IANA timezone list)
- **Date Format** — Dropdown
  - MM/DD/YYYY (US default)
  - DD/MM/YYYY
  - YYYY-MM-DD (ISO)

**Phone Formatting:**
- **Default Phone Country Code** — Dropdown (e.g., +1 for US/Canada)
- **Default Phone Format** — Dropdown
  - (XXX) XXX-XXXX (US default)
  - XXX-XXX-XXXX
  - +X XXX XXX XXXX (international)

## 10.3 Record Numbering

### Entity Numbering Configuration

> **Design Note:** These settings define the default prefix and starting number for auto-generated record numbers. If a user leaves fields blank during setup, the system applies these defaults. The format follows the ServizDesk convention: Prefix + Number (e.g., C26-0001).

**Customer Numbering:**
- **Customer Account Prefix** — Text (default: C)
- **Customer Account Start Number** — Number (default: 0001)

**Asset Numbering:**
- **Asset Prefix** — Text (default: A)
- **Asset Start Number** — Number (default: 0001)

**Work Order Numbering:**
- **Work Order Prefix** — Text (default: W)
- **Work Order Start Number** — Number (default: 0001)

**Quote Numbering:**
- **Quote Prefix** — Text (default: Q)
- **Quote Start Number** — Number (default: 0001)

**Invoice Numbering:**
- **Invoice Prefix** — Text (default: I)
- **Invoice Start Number** — Number (default: 0001)

**Payment Numbering:**
- **Payment Prefix** — Text (default: P)
- **Payment Start Number** — Number (default: 0001)

**WorkGroup Numbering (Plus+):**
- **WorkGroup Prefix** — Text (default: WG)
- **WorkGroup Start Number** — Number (default: 0001)

**Purchase Order Numbering (Plus+):**
- **PO Prefix** — Text (default: PO)
- **PO Start Number** — Number (default: 0001)

**Task Numbering:**
- **Task Prefix** — Text (default: T)
- **Task Start Number** — Number (default: 0001)


**Employee Numbering:**
- **Employee Prefix** — Text (default: E)
- **Employee Start Number** — Number (default: 0001)

**Product Numbering:**
- **Product Prefix** — Text (default: computed via reverse-alphabet year encoding, e.g., `YU` for 2026 — see Numbering Service V1 Section 6.1)
- **Product Start Number** — Number (default: 0001)

**Numbering Reset:**
- **Reset Period** — Dropdown
  - Annual (default — includes 2-digit year in prefix, e.g., W**26**-0001)
  - Never (continuous numbering, no year component)

## 10.4 Financial Defaults

### Tax & Payment Settings

**Tax Configuration:**
- **Default Tax Rate** — Percentage (e.g., 8.25%)
- **Tax Label** — Text (e.g., "Sales Tax", "VAT", "GST")

**Payment & Terms:**
- **Default Payment Terms** — Dropdown
  - Due on Receipt, Net 15, Net 30, Net 45, Net 60, Custom
- **Default Quote Expiration Days** — Number (default: 30)

**Fiscal Year:**
- **Fiscal Year Start Month** — Dropdown (January–December, default: January)
  - Affects reporting periods and year-to-date calculations

## 10.5 Enterprise Multi-Location (Enterprise)

### Multi-Location Configuration

> **Enterprise Only:** Enterprise tier tenants can configure multiple business locations. Each location inherits tenant-level defaults but can override specific settings.

**Location Fields:**
- **Location Name** — Text (required)
- **Address, City, State, ZIP, Country** — Full address per location
- **Phone, Fax, Email** — Location-specific contact information
- **Logo Override** — Optional location-specific logo

**Location-Specific Overrides:**
- **Tax Rate** — Override tenant default per location
- **Timezone** — Override for locations in different time zones
- **Numbering Prefix** — Location-specific prefixes (e.g., W-NYC-0001 vs. W-LA-0001)

**Location Relationships:**
- Employees assigned to location(s)
- Work Orders can be associated with originating location
- Inventory tracked per location (see Section 1.8 — Product Catalog)
- Reporting filterable by location

## 10.6 Custom Domain Email Configuration

### Custom Domain Authentication Setup

> **Scope:** This setting allows Pro and Enterprise tenants to authenticate their own business domain so that platform-managed emails appear to come from their domain (e.g., `quotes@acmehvac.com`) rather than ServizDesk's default sending domain. This is a paid add-on — see Pricing & Billing Specification V2, Section 11.4. Note: Plus tier eligibility is an open decision maintained in ServizDesk Email Specification V1, Section 8.
>
> **BYOS (Bring Your Own SMTP) is not supported.** ServizDesk does not allow tenants to route platform email through their own SMTP credentials. All email delivery runs through Postmark. Custom domain authentication gives tenants the professional result they want (emails from their domain) without the deliverability and support risks of BYOS. See ServizDesk Email Specification V1 for full rationale.

**Domain Setup Fields:**
- **Business Domain** — Text (e.g., `acmehvac.com`)
- **Verification Status** — Read-only (Pending / Verified / Failed)

**DNS Records (generated by ServizDesk, applied by tenant):**
- **SPF record** — Authorises Postmark to send on behalf of the domain
- **DKIM record** — Cryptographic signature for email authenticity
- **DMARC record** — Policy for handling unauthenticated mail

**Sender Information (auto-configured once domain is verified):**
- **From Name** — Tenant's company name (from Tenant Settings)
- **From Address** — `[email-type]@[tenant-domain]` (e.g., `quotes@acmehvac.com`, `invoices@acmehvac.com`)

**Inbound Reply Address (Pro/Enterprise add-on):**
- ServizDesk generates a unique inbound reply address per tenant
- Customer replies route back into ServizDesk and attach to the originating record
- See ServizDesk Email Specification V1 for full inbound processing specification

---

# 11. Workflow Summary

## 11.1 Core Workflows

### Service Call Workflow

**Typical Flow:**
1. **Customer calls / books online** → Create Customer record (if new)
2. **Identify Asset** → Link to existing Asset or create new Asset record
3. **Create Work Order** → Link to Customer and Asset, assign employee, schedule
4. **Dispatch** → Employee sees Work Order on mobile schedule
5. **Travel to site** → "On the Way" notification to customer (Plus+)
6. **Complete work** → Update Work Order status, complete checklist, add notes/photos
7. **Create Quote** (if additional work needed) → On-site quoting via mobile
8. **Customer approves Quote** → E-signature, optional deposit collection
9. **Convert to Invoice** → One-click conversion
10. **Collect payment** → Stripe Payment Link or manual recording
11. **Work Order complete** → Mark complete, service history updates on Asset

### Maintenance Agreement Workflow

**Recurring Service:**
1. **Create Maintenance Plan** → Linked to Customer and Asset(s)
2. **Define schedule** → Frequency, checklist template, assigned employee
3. **Auto-create Work Orders** → System generates Work Orders per schedule
4. **Reminder notifications** → Alert customer and employee of upcoming service
5. **Complete Work Order** → Standard service call workflow
6. **Invoice** → Bill per agreement terms (auto-invoice on Pro/Enterprise)
7. **Renewal** → Auto-renew or manual renewal at plan expiration

### WorkGroup Workflow (Plus+)

**Multi-Phase Work:**
1. **Create WorkGroup** → Link to Customer, assign address/location
2. **Create multiple Work Orders** → Each WO covers one Asset under the WorkGroup
3. **Organize phases** → Use WGDivisions to subdivide into logical phases
4. **Assign team** → Assign employees with roles via WorkGroupTeam
5. **Track progress** → Monitor completion by Work Order status, view all Assets via WorkGroupAssets
6. **Track costs** → Labor hours + materials aggregated from linked Work Orders
7. **Invoice per phase** → Or invoice at WorkGroup completion
8. **Close WorkGroup** → Mark complete when all Work Orders done

### Lead-to-Customer Conversion Workflow (Plus+)

**Lead Capture & Conversion:**
1. **Create Lead** → Office staff creates Lead manually, or inbound web widget creates Lead automatically
2. **Contact Lead** → Staff contacts the prospect; Lead status updated to `Contacted`
3. **Qualify Lead** → Lead assessed as a viable prospect; status set to `Qualified`
4. **Convert Lead** → Staff triggers the Convert action:
   - System creates a new **Customer** record pre-populated from Lead fields (name, phone, email)
   - Lead `customer_id` is linked to the new Customer
   - Lead status is set to `Converted`
   - Staff optionally creates an **Opportunity** linked to the new Customer and this Lead simultaneously
5. **Lead record retained** → The Lead record is never deleted; it serves as acquisition history
6. **Lost Leads** → If the Lead is not viable, status is set to `Lost` — no Customer is created

### Opportunity Workflow (Pro+)

**Sales Pipeline:**
1. **Create Opportunity** → Linked to existing Customer (required); optionally linked to a converted Lead
2. **Assign contacts** → Link relevant Customer Contacts to the Opportunity with roles (Decision Maker, Budget Holder, etc.) via OpportunityContacts
3. **Assign salesperson** → Set Assigned To employee
4. **Set value and timeline** → Enter Estimated Value and Expected Close Date
5. **Work the opportunity** → Notes, follow-up tasks (via Task entity), communication
6. **Outcome:**
   - **Won** → Status set to `Won`; staff creates Work Order(s) or CustomerAgreement linked to this Opportunity
   - **Lost** → Status set to `Lost`; notes capture reason

---

# 12. Data Model Relationships

## 12.1 Entity Relationship Summary

```
ASSET-CENTRIC ARCHITECTURE
============================

Person (1) ←→ (many) Contacts [permanent identity]
Person (1) ←→ (many) Socials [personal emails, social media profiles]

Contact (many) ←→ (1) Person [required]
Contact (many) ←→ (1) Customer or Vendor [required — links person to entity]
Contact (1) ←→ (many) Phone Numbers [via Phone Number Table]
Contact (1) ←→ (many) Socials [company-assigned emails, professional profiles]

Customer (1) ←→ (many) Contacts [via Contact Table — replaces inline person fields]
Customer (1) ←→ (many) Phone Numbers [via Phone Number Table]
Customer (1) ←→ (many) Addresses [via Address Table]
Customer (1) ←→ (many) Assets [primary relationship]
Customer (1) ←→ (many) Locations
Customer (1) ←→ (many) Work Orders
Customer (1) ←→ (many) Quotes
Customer (1) ←→ (many) Invoices
Customer (1) ←→ (many) Payments
Customer (1) ←→ (many) CustomerAgreements [via Agreement chain]
Customer (1) ←→ (many) WorkGroups [Plus+]

Asset (many) ←→ (1) Customer [required]
Asset (many) ←→ (1) Location [optional - defaults to primary]
Asset (1) ←→ (many) Work Orders [service history - core relationship]
Asset (1) ←→ (many) CustomerAgreements [via Agreement chain]
Asset (1) ←→ (many) Documents/Photos
Asset (many) ←→ (many) Assets [via SubAsset junction - Pro/Enterprise]

Work Order (many) ←→ (1) Customer [required]
Work Order (many) ←→ (0..1) Asset [one asset per WO; multi-asset via WorkGroups]
Work Order (many) ←→ (0..1) WorkGroup [optional, Plus+]
Work Order (1) ←→ (many) Quotes [optional]
Work Order (1) ←→ (many) Invoices [optional]
Work Order (1) ←→ (many) Tasks (subtasks)
Work Order (1) ←→ (many) Time Entries
Work Order (1) ←→ (many) Checklist Items
Work Order (1) ←→ (many) Photos/Attachments

WorkGroup (1) ←→ (many) Work Orders [Plus+]
WorkGroup (many) ←→ (1) Customer
WorkGroup (1) ←→ (many) WorkGroupAssets [rolled-up asset view]
WorkGroup (1) ←→ (many) WorkGroupTeam [assigned employees with roles]
WorkGroup (1) ←→ (many) WGDivisions [phase sub-grouping]

Quote (many) ←→ (1) Customer [required]
Quote (many) ←→ (1) Work Order [optional]
Quote (many) ←→ (many) Assets [optional]
Quote (many) ←→ (0..1) WorkGroup [optional, Plus+]
Quote (1) ←→ (many) Quote Lines
Quote (1) ←→ (1) Invoice [on conversion]

Invoice (many) ←→ (1) Customer [required]
Invoice (many) ←→ (1) Work Order [optional]
Invoice (many) ←→ (many) Assets [optional]
Invoice (many) ←→ (0..1) WorkGroup [optional, Plus+]
Invoice (1) ←→ (many) Invoice Lines
Invoice (1) ←→ (many) Payments

Payment (many) ←→ (1) Customer
Payment (many) ←→ (1) Invoice

Agreement (1) ←→ (many) CustomerAgreements [template applied to customers]
CustomerAgreement (many) ←→ (1) Customer [required]
CustomerAgreement (many) ←→ (1) Agreement [required]
CustomerAgreement (many) ←→ (1) Asset [required — asset-centric]
CustomerAgreement (1) ←→ (many) PMs [recurring schedules]
PM (many) ←→ (1) CustomerAgreement [required — inherits Customer, Agreement, Asset]
PM (many) ←→ (0..1) WorkFlow [SOP for generated Work Orders]
PM (1) ←→ (many) Work Orders [auto-generated]

WorkFlow (1) ←→ (many) WFSteps [ordered SOP steps]
WFStep (1) ←→ (many) WFStepToDos [per-step checklist items]
WorkFlow (1) ←→ (many) WFTools [required equipment via Equipment entity]
WorkFlow (1) ←→ (many) WFInventory [required parts via Product entity]
WorkFlow (1) ←→ (many) WFSafetyForms [required safety forms]
WorkFlow (1) ←→ (many) PMs [defines SOP for recurring service]
WorkFlow (1) ←→ (many) Work Orders [assigned SOP for a job]

Vendor (1) ←→ (many) Contacts [via Contact Table — shared with Customers]
Vendor (1) ←→ (many) Phone Numbers [via Phone Number Table]
Vendor (1) ←→ (many) Addresses [via Address Table]

Purchase Order (1) ←→ (many) PO Lines
Purchase Order (many) ←→ (1) Vendor
Purchase Order (many) ←→ (1) Work Order [optional]

Product Catalog (1) ←→ (many) Quote Lines
Product Catalog (1) ←→ (many) Invoice Lines
Product Catalog (1) ←→ (many) PO Lines
Product Catalog (1) ←→ (many) Part Requisition Lines

Warehouse/Location (1) ←→ (many) Sub-Locations [shelves, bins, rooms]
Warehouse/Location (many) ←→ (1) Employee [van assignments]
Warehouse/Location (1) ←→ (many) PO Lines [receiving location]

Sub-Location (1) ←→ (many) Inventory Items [precise stock placement]

Part Requisition (1) ←→ (many) POs [fulfillment]
Part Requisition (many) ←→ (1) Employee [requestor]

Vehicle (1) ←→ (many) Maintenance Records [fleet add-on]
Vehicle (1) ←→ (many) Mileage Log Entries [fleet add-on]
Vehicle (many) ←→ (1) Employee [assigned driver — nullable]
Vehicle (1) ←→ (many) Documents [registration, insurance, inspection]
Work Order (many) ←→ (1) Vehicle [optional — vehicle used on job, fleet add-on]

Lead (many) ←→ (0..1) Customer [nullable — populated on conversion]
Lead (1) ←→ (0..1) Opportunity [optional — created at conversion]

Opportunity (many) ←→ (1) Customer [required]
Opportunity (many) ←→ (0..1) Lead [optional — originating lead]
Opportunity (1) ←→ (many) OpportunityContacts [contacts with roles]
OpportunityContacts (many) ←→ (1) Opportunity [required]
OpportunityContacts (many) ←→ (1) Contact [required — must be a Contact of the Opportunity's Customer]

Equipment (1) ←→ (many) CheckInOut records [checkout history]
Equipment (1) ←→ (many) WFTools [linked to WorkFlow SOPs as required tools]
CheckInOut (many) ←→ (1) Equipment [required]
CheckInOut (many) ←→ (1) Employee [who has the item]

SafetyForm (1) ←→ (many) WFSafetyForms [linked to WorkFlow SOPs as required forms]
SafetyForm (1) ←→ (many) WOSFAnswers [completed responses per Work Order]
WOSFAnswer (many) ←→ (1) Work Order [required]
WOSFAnswer (many) ←→ (1) SafetyForm [required]
WOSFAnswer (many) ←→ (1) Employee [who completed the form]
```

## 12.2 Key Architectural Notes

**Asset-Centric Model:**
- **Primary organizing principle:** Asset (customer equipment)
- Customer → Assets → Work Orders (service history on each asset)
- Work Orders reference Assets, not the other way around
- This is fundamentally different from FieldPulse, Jobber, HousecallPro, and Workiz — all of which are job-centric

**Customer/Person/Contact Triad:**
- **Person** = Permanent human identity (First Name, Last Name only)
- **Contact** = Relationship linking a Person to a Customer or Vendor (holds Role/Title)
- **Socials** = Emails and social media links, linked to Contact (company-assigned) and/or Person (personal)
- **Phone Numbers** = Linked to Customer and Contact via Phone Number Table (duplicates permitted to preserve history)
- A Person can have multiple active Contacts across different Customers/Vendors
- When a person moves companies, a new Contact is created at the new company; the old Contact and all its history remain intact
- Vendors share the same Contact, Person, Address, and Phone Number tables as Customers

**Asset as the Record of Truth:**
- Every piece of equipment a customer owns has a complete, traceable lifecycle
- Installation date, warranty tracking, every service visit, every part replaced, condition history
- When a technician arrives on-site, they pull up the Asset first, then see its full service history
- This enables proactive service recommendations and warranty-aware quoting

**Required vs. Optional Relationships:**
- Work Orders don't require Assets (simple service calls without equipment context)
- Work Orders don't require Quotes or Invoices (can exist independently)
- Quotes don't require Work Orders (can create standalone quotes)
- Invoices don't require Work Orders (can invoice without work order)
- Maintenance Plans REQUIRE Assets (asset-centric design — you maintain equipment, not abstract "jobs")

**Multi-Tenancy:**
- Single database, shared schema, multi-tenant SaaS
- All data scoped by tenant_id (UUID)
- Three-layer isolation: database constraint → Django middleware → PostgreSQL RLS
- No data sharing between tenants

**Add-On Module Architecture:**
- Add-on modules (Fleet Maintenance) use the same shared-schema, tenant-scoped pattern as all other entities
- Add-on tables exist in the database from initial deployment; UI and controllers are gated behind add-on subscription status
- The Vehicle optional field on Work Orders is present in the schema from day one but hidden in the UI when Fleet Maintenance is not active
- Add-on activation/deactivation is handled by SDP updating the tenant's add-on subscription status; SDTA reads this status to gate UI and controllers

---

# 13. Fleet Maintenance (Add-On Module)

## 13.1 Overview

Fleet Maintenance is a **paid add-on module** available to Plus, Pro, and Enterprise tier tenants (Plus+). It is not included in any base tier price. The module activates when the tenant's add-on subscription is active. When inactive, all Fleet Maintenance UI is hidden and all Fleet Maintenance controllers reject write operations.

**Availability:** Plus (add-on), Pro (add-on), Enterprise (add-on)
**Pricing:** $15/vehicle/month (billed per active vehicle record). See Pricing & Billing Specification V2, Section 11.2.

**Design rationale:** Fleet vehicles are operationally distinct from customer-owned equipment (Assets). A service van has a completely different lifecycle, ownership structure, and management needs than the HVAC unit a technician is servicing. Fleet Maintenance is therefore a separate first-class module with its own Vehicle entity, not an extension of the Asset entity.

**Intentionally out of scope:**
- GPS / real-time location tracking (requires third-party hardware integration)
- Fuel card integration (third-party dependency)
- Route optimization (scoped under Enterprise scheduling, not fleet)

---

## 13.2 Vehicle Entity

### Vehicle Record Structure

**Core Vehicle Fields:**
- **Vehicle Number** — Auto-generated (ServizDesk record numbering: V26-0001)
- **Status** — Dropdown
  - Values: Active, Out of Service, Decommissioned
- **Year** — Number (4-digit)
- **Make** — Text (manufacturer)
- **Model** — Text
- **Trim / Description** — Text (optional)
- **VIN** — Text (Vehicle Identification Number, unique per tenant)
- **License Plate** — Text
- **License Plate State** — Dropdown (US states + territories)
- **Color** — Text (optional)
- **Vehicle Type** — Dropdown (customizable)
  - Default values: Van, Truck, Car, Box Truck, Trailer, Other
- **Assigned Driver** — Link to Employee record (optional — nullable when unassigned)
- **Odometer (Current)** — Number (updated via mileage log entries)
- **Purchase Date** — Date picker (optional)
- **Purchase Price** — Currency (optional, internal)
- **Notes** — Internal free-text notes

**Compliance & Registration Fields:**
- **Registration Expiry Date** — Date picker
- **Insurance Policy Number** — Text
- **Insurance Provider** — Text
- **Insurance Expiry Date** — Date picker
- **Last Inspection Date** — Date picker
- **Next Inspection Due Date** — Date picker

**Compliance Alerts:**
- System generates in-app notifications when any compliance date is approaching
- Alert thresholds (configurable in Fleet preferences):
  - 30-day warning
  - 7-day warning
  - Overdue alert (date passed, no update recorded)
- Alerts visible to Administrator role users

**Attachments:**
- **Documents** — Uses existing Document entity
  - Registration documents
  - Insurance certificates
  - Inspection reports
  - Purchase/title documents
  - Photos (vehicle condition photos, damage records)

**Custom Fields on Vehicles (Pro/Enterprise):**
- Custom fields can be created for Vehicle records
- Same field types as other entity custom fields
- Separate from other entity custom fields

---

## 13.3 Vehicle Maintenance Entity

### Maintenance Record Structure

**Purpose:** Tracks all service and maintenance performed on each Vehicle. This is distinct from customer Asset service history — Vehicle Maintenance records belong to the tenant's own fleet, not customer equipment.

**Maintenance Record Fields:**
- **Maintenance Number** — Auto-generated (M26-0001)
- **Vehicle** — Link to Vehicle record (required)
- **Maintenance Type** — Dropdown (customizable)
  - Default values: Oil Change, Tire Rotation, Brake Service, Transmission Service, Battery Replacement, State Inspection, Emissions Test, Scheduled Maintenance, Repair, Other
- **Status** — Dropdown
  - Values: Scheduled, Completed, Overdue, Cancelled
- **Scheduled Date** — Date picker
- **Completed Date** — Date picker (populated when Status = Completed)
- **Odometer at Service** — Number (miles at time of service)
- **Next Service Due — Date** — Date picker (optional)
- **Next Service Due — Odometer** — Number (optional, trigger mileage for next service)
- **Performed By** — Dropdown
  - Values: In-House, External Shop
- **Shop / Vendor Name** — Text (if External Shop)
- **Cost** — Currency (internal cost record)
- **Description / Notes** — Long-form text (work performed details)

**Maintenance Alerts:**
- System generates in-app notifications when next service is approaching
- Alert triggers:
  - Date-based: 14-day and 3-day warnings before Next Service Due date
  - Odometer-based: alert when Current Odometer is within 500 miles of Next Service Due Odometer
- Alerts visible to Administrator role users

**Attachments:**
- Service receipts, invoices from external shops, inspection reports (via Document entity)

---

## 13.4 Mileage Log Entity

**Purpose:** Tracks odometer readings and trip mileage per vehicle. Each entry updates the Vehicle's Current Odometer field.

**Mileage Log Fields:**
- **Log Number** — Auto-generated
- **Vehicle** — Link to Vehicle record (required)
- **Employee** — Link to Employee record (driver logging the entry, required)
- **Date** — Date picker (required)
- **Odometer Start** — Number
- **Odometer End** — Number
- **Miles Driven** — Calculated (Odometer End − Odometer Start)
- **Trip Purpose** — Dropdown (customizable)
  - Default values: Customer Job, Supply Run, Shop Drop-Off, Other
- **Related Work Order** — Link to Work Order (optional)
- **Notes** — Text (optional)

**Odometer Integrity:**
- System validates that Odometer End ≥ Odometer Start
- System validates that new entry Odometer Start ≥ last recorded odometer for that vehicle
- Warnings displayed if entry appears out of sequence (does not block save — accommodates manual/catch-up entry)

---

## 13.5 Fleet Relationships

```
Vehicle (1) ←→ (many) Maintenance Records
Vehicle (1) ←→ (many) Mileage Log Entries
Vehicle (many) ←→ (1) Employee [assigned driver — nullable]
Vehicle (1) ←→ (many) Documents [registration, insurance, inspection, photos]

Mileage Log Entry (many) ←→ (1) Work Order [optional — trip linked to job]
Mileage Log Entry (many) ←→ (1) Employee [driver]
```

**Vehicle ↔ Work Order relationship:**
- Work Orders gain an optional **Vehicle** field when Fleet Maintenance is active (the vehicle dispatched for the job)
- This field is hidden on Work Orders when the Fleet Maintenance add-on is not active
- Vehicle is not required on a Work Order — many jobs are walk-in or the vehicle is not tracked

---

## 13.6 Fleet Maintenance UI Areas

**Fleet Dashboard:**
- Active vehicle count
- Vehicles with overdue compliance (registration, insurance, inspection)
- Vehicles with upcoming maintenance due (next 30 days)
- Recent mileage entries

**Vehicle List View:**
- Searchable, sortable, filterable
- Status filter (Active, Out of Service, Decommissioned)
- Compliance status indicators (green / yellow / red per vehicle)
- CSV export

**Vehicle Detail View:**
- All vehicle fields
- Compliance status summary with alert indicators
- Maintenance history tab (chronological)
- Mileage log tab (chronological, running odometer)
- Documents tab
- Notes tab

**Maintenance List View:**
- All maintenance records across fleet
- Filter by vehicle, type, status, date range
- Overdue and upcoming views

**Mileage Log List View:**
- All mileage entries across fleet
- Filter by vehicle, employee, date range, work order
- Total miles summary per vehicle / per period

---

## 13.7 Fleet Preferences

Configurable per tenant in the Fleet Maintenance preferences area:

- **Compliance alert thresholds** — days before expiry to trigger 30-day and 7-day warnings
- **Maintenance alert thresholds** — days and odometer miles before due date to trigger warnings
- **Default trip purpose options** — customize the mileage log trip purpose dropdown
- **Default vehicle types** — customize the vehicle type dropdown
- **Default maintenance types** — customize the maintenance type dropdown

---

# 14. Technical Architecture Notes

> **Full technical architecture details are maintained in the ServizDesk Technical Architecture V2.** This section provides a summary reference for context within this document. All technical decisions and version specifications are owned by the Technical Architecture document.

## 14.1 Platform Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 6.x |
| Database | PostgreSQL 16+ |
| Frontend Interactions | HTMX v2.x |
| Styling | Tailwind CSS (via Tailwind CLI/PostCSS) |
| Icons | SVG (Heroicons) |
| Web Server | Nginx (reverse proxy + static files) |
| Application Server | Gunicorn (WSGI) |
| Cloud Provider | DigitalOcean |
| Object Storage | DigitalOcean Spaces (S3-compatible) |
| Async Worker | Celery |
| Message Broker | Redis (managed, separate from web server) |

**Access:**
- Web browser (all modern browsers, desktop and mobile)
- Responsive design — full feature parity across screen sizes
- Progressive Web App capable (home screen installation on mobile)

## 14.2 Architectural Mandates

To ensure the MVP (Lite) does not block future growth:

1. **UUIDs Only:** All primary and foreign keys use UUIDv4. Required for future offline-first mobile sync — devices must generate database keys while disconnected. Auto-incrementing integers are prohibited.
2. **Abstracted Pricing:** Products link to intermediate pricing models (Price Tiers / Pricebooks) rather than hardcoded prices, supporting multi-tier commercial pricing in the future.
3. **One Asset per Work Order:** A Work Order links to exactly one Asset via a direct FK (nullable). Multi-asset coordination is handled through WorkGroups. A Work Order can link to multiple Invoices (deposit billing, progress billing, milestone billing) via the `WorkOrderInvoice` junction table — added in V12.
4. **Parent/Child Architecture:** Nested equipment structures for commercial clients are supported via the `SubAsset` junction table (links a child Asset to a parent Asset). See Data Models V6 for the full field definition. The former `parent_asset_id` self-FK on `Asset` was replaced by this junction in ERD V12.
5. **Tenant Isolation:** Three-layer defense — database field constraint → Django middleware → PostgreSQL Row-Level Security.
6. **No Vanilla CSS:** Tailwind CSS is the only permitted styling engine. Vanilla CSS is reserved for extreme edge cases only.
7. **No SQLite:** PostgreSQL is required in all environments including local development. SQLite breaks the required Row-Level Security architecture.

## 14.3 Asynchronous Processing

Background tasks that must not block the web response cycle are handled by Celery workers backed by a Redis message broker. Key async workloads include:

- **Post-cancellation data deletion worker** — permanently deletes tenant data after the full 90-day window expires (30-day `Cancelled (Read Only)` + 60-day `Cancelled` data retention); see Pricing & Billing Specification V2 Section 8
- **Heavy CSV exports** — large export jobs run in background, delivered via notification
- **Stripe Webhook processing** — all incoming Stripe events processed asynchronously
- **PDF generation** (Plus/Pro) — server-side document rendering runs off the web thread
- **Email delivery** — outbound email queued through Celery to prevent request blocking

Redis must run on a separate Droplet or managed Redis instance. Running Redis on the same Droplet as the web server is prohibited.

## 14.4 PDF Generation

> **PDF generation scope per tier is pending final definition. This section will be updated when the per-tier PDF capabilities are formally specified.**

**Architecture decisions locked:**
- **Lite tier:** Browser print via CSS Print Media Queries. No server-side PDF generation. Developers must build robust `@media print` CSS rules to produce clean printable output.
- **Plus/Pro/Enterprise:** Server-side PDF generation via **WeasyPrint** (Python library).

**Scope per tier:**
- **Lite:** Browser Print only (Quotes & Invoices details)
- **Plus:** Quotes, Invoices, Work Orders details, and list views
- **Pro & Enterprise:** Unrestricted PDF generation (any record, list, or custom form)

## 14.5 Communication Architecture

### Email
- **Platform Email (SDP → Tenant):** Transactional emails from ServizDesk to tenant account holders (welcome, password reset, provisioning alerts) are sent via **Postmark**.
- **Tenant Email (SDTA → Customer) — All tiers, point-based:**
  - **Mode 1 (ServizDesk-managed — default):** Sent through ServizDesk infrastructure via Postmark. Emails appear from ServizDesk's sending domain with the tenant's company name as the display sender. Point-based allocation applies. No configuration required from tenant.
  - **Mode 2 (Custom Domain — paid add-on, Pro/Enterprise):** Tenant authenticates their own business domain via DNS records (SPF, DKIM, DMARC). Emails send from the tenant's domain through Postmark's infrastructure. Includes inbound reply processing. See ServizDesk Email Specification V1 and Pricing & Billing Specification V2 Section 11.4.
  - **BYOS (Bring Your Own SMTP) — not supported.** All email delivery runs through Postmark regardless of tier.
- **Lite:** 400 email points/month. Manual sends only (quote sends, invoice sends, manual customer messages). No automated triggers.
- **Plus and above:** Manual and automated sends. Automated triggers include appointment reminders, on-my-way notifications, post-job follow-ups, and payment reminders.
- **Email point allocation and overage pricing:** See ServizDesk Pricing & Billing Specification V2, Section 10A.

### SMS
- **Available in:** All tiers. Point-based. 1 point = 1 outbound SMS message.
- **Lite:** 100 points/month. Manual sends only — no automated triggers.
- **Plus and above:** Manual and automated sends. Automated triggers include appointment reminders, on-my-way notifications, post-job follow-ups, and payment reminders.
- **Included allotments and add-on pricing:** See ServizDesk Pricing & Billing Specification V2, Section 10.
- **Provider:** Twilio.

## 14.6 Payment Architecture

- **Platform Billing (ServizDesk subscription charges):** Stripe Checkout. ServizDesk never stores raw card data.
- **Tenant Payment Processing (Plus and above):** Stripe Connect (Standard integration). Tenants link their own Stripe accounts via OAuth. SDTA generates Stripe Payment Links for invoices. No raw card data flows through SDTA at any tier.
- **PCI DSS Posture:** ServizDesk qualifies for PCI SAQ A. All card data handling delegated to Stripe.
- Full details in ServizDesk Pricing & Billing Specification V2, Section 9.

## 14.7 Data Import/Export

**Import Capabilities:**
- Customers (CSV)
- Assets (CSV)
- Products (CSV)
- Work Orders (CSV)
- Custom fields (CSV)

**Export Capabilities:**
- All major entities exportable to CSV (all tiers)
- QuickBooks-formatted CSV export (Plus and above)
- PDF document generation (scope per tier — see Section 14.4)

---

# 15. Document Relationships

## 15.1 Document Ownership Map

Each data domain is owned by exactly one document. All other documents reference, not duplicate.

| Data Domain | Owned By |
|---|---|
| Pricing, billing cycles, trials, Founding Partner program, storage pricing, SMS pricing | **Pricing & Billing Specification V2** |
| Tier feature definitions, feature gates, feature comparison matrix | **Product Tier Map V2** |
| Technical stack, infrastructure, tenancy architecture, security | **Technical Architecture V2** |
| Complete functional scope, entity definitions, data model, system workflows | **Top-Down Specifications V4** (this document) |
| Lite-specific module detail, seat counting rules, UI specifications | **Lite MVP V4 Specification** *(deferred — not in the current Working Documents set; to be used once Top-Down is fully clarified)* |
| Platform provisioning, SDP operations, tenant lifecycle | **Platform (SDP) Specification V2** |

## 15.2 This Document Depends On

- **ServizDesk Pricing & Billing Specification V2** — for all pricing, trial, and Founding Partner details
- **ServizDesk Product Tier Map V2** — for feature gate definitions per tier
- **ServizDesk Technical Architecture V2** — for stack, infrastructure, and tenancy decisions

## 15.3 Documents That Reference This Document

- **ServizDesk Product Tier Map V2** — references entity definitions and architectural principles
- **ServizDesk Lite MVP V4 Specification** — references entity definitions for Lite-scope modules
- **ServizDesk Plus Specification (future)** — will reference entity definitions for Plus-scope modules
- **ServizDesk Pro Specification (future)** — will reference entity definitions for Pro-scope modules

---


# 16. Tier Feature Mapping (Summary)

> **Note:** This is a high-level summary. Detailed tier specifications are maintained in separate documents (Lite MVP V4 Spec, Plus Spec, Pro Spec, Enterprise Spec). **All pricing is maintained exclusively in the ServizDesk Pricing & Billing Specification V2 — this table contains no pricing data.**

| Feature | Lite | Plus | Pro | Enterprise |
|---|:---:|:---:|:---:|:---:|
| **Core Entities** | | | | |
| Customers | ✓ | ✓ | ✓ | ✓ |
| Assets | ✓ | ✓ | ✓ | ✓ |
| Work Orders | ✓ | ✓ | ✓ | ✓ |
| Quotes | ✓ | ✓ | ✓ | ✓ |
| Invoices | ✓ | ✓ | ✓ | ✓ |
| Payments | ✓ | ✓ | ✓ | ✓ |
| Products | ✓ | ✓ | ✓ | ✓ |
| Tasks | ✓ | ✓ | ✓ | ✓ |
| WorkGroups | — | ✓ | ✓ | ✓ |
| Purchase Orders | — | ✓ | ✓ | ✓ |
| Vendors | — | ✓ | ✓ | ✓ |
| **CRM** | | | | |
| Leads | — | ✓ | ✓ | ✓ |
| Opportunities | — | — | ✓ | ✓ |
| Opportunity-Contact Assignment | — | — | ✓ | ✓ |
| **Asset Features** | | | | |
| Asset tracking | ✓ | ✓ | ✓ | ✓ |
| Warranty tracking | ✓ | ✓ | ✓ | ✓ |
| Nested Assets (parent/child) | — | — | ✓ | ✓ |
| QR Code scanning | — | — | ✓ | ✓ |
| **Work Order Features** | | | | |
| Checklists | ✓ | ✓ | ✓ | ✓ |
| Checklist Templates | ✓ | ✓ | ✓ | ✓ |
| Recurring Work Orders | — | ✓ | ✓ | ✓ |
| Custom WO Statuses | — | — | ✓ | ✓ |
| Custom Forms | — | — | ✓ | ✓ |
| Time Tracking | ✓ | ✓ | ✓ | ✓ |
| **Quoting** | | | | |
| E-Signature / Online Approval | — | ✓ | ✓ | ✓ |
| Deposit Collection | — | ✓ | ✓ | ✓ |
| Good/Better/Best Proposals | — | — | ✓ | ✓ |
| **PDF Generation** | | | | |
| PDF Generation (scope per tier — see Section 14.4) | Browser Print | Quotes / Invoices / WOs | Unrestricted | Unrestricted |
| **Invoicing** | | | | |
| Recurring Invoices | — | ✓ | ✓ | ✓ |
| Commission Tracking | — | — | ✓ | ✓ |
| **Inventory** | | | | |
| Product Catalog | ✓ | ✓ | ✓ | ✓ |
| Inventory Tracking | — | ✓ | ✓ | ✓ |
| Serialized Inventory | — | — | ✓ | ✓ |
| Multi-Location Inventory | — | — | ✓ | ✓ |
| Warehousing (Multiple Buildings) | — | — | — | ✓ |
| Price Tiers / Pricebooks | — | — | ✓ | ✓ |
| Bundles | ✓ | ✓ | ✓ | ✓ |
| **Service Agreements** | | | | |
| Maintenance Plans | — | ✓ | ✓ | ✓ |
| Auto-Generate Work Orders | — | ✓ | ✓ | ✓ |
| Recurring Billing | — | — | ✓ | ✓ |
| Plan Tiers (Silver/Gold/Plat) | — | — | ✓ | ✓ |
| **Scheduling** | | | | |
| Calendar Views | — | ✓ | ✓ | ✓ |
| Drag-and-Drop Scheduling | — | ✓ | ✓ | ✓ |
| Map View | — | — | ✓ | ✓ |
| Smart Assignment | — | — | ✓ | ✓ |
| Route Optimization | — | — | — | ✓ |
| **Communication** | | | | |
| SMS (point-based) | ✓ (manual) | ✓ | ✓ | ✓ |
| System Email (ServizDesk-managed) | ✓ (manual) | ✓ | ✓ | ✓ |
| System Email (Custom Domain — paid add-on) | — | — | + | + |
| **Customer Portal** | | | | |
| Online Booking (basic request) | — | ✓ | ✓ | ✓ |
| Customer Portal (full) | — | ✓ | ✓ | ✓ |
| **Automation** | | | | |
| Automation Rules | — | 2–5 | Unlimited | Unlimited |
| Zapier Integration | — | — | ✓ | ✓ |
| Webhooks | — | — | ✓ | ✓ |
| REST API | — | — | ✓ | ✓ |
| **Reporting** | | | | |
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Standard Reports | ✓ | ✓ | ✓ | ✓ |
| Advanced Reports | — | — | ✓ | ✓ |
| Custom Reports | — | — | ✓ | ✓ |
| **Integrations** | | | | |
| Stripe Payment Links | ✓ | ✓ | ✓ | ✓ |
| Standardized Accounting Export (CSV) | ✓ | ✓ | ✓ | ✓ |
| Consumer Financing | — | — | ✓ | ✓ |
| Google Calendar | — | ✓ | ✓ | ✓ |
| **Add-On Modules** | | | | |
| Fleet Maintenance (add-on) | — | + | + | + |
| **Equipment & Tools** | | | | |
| Equipment Tracking | — | — | ✓ | ✓ |
| Equipment Check-In / Check-Out | — | — | ✓ | ✓ |
| WorkFlow Required Tools (WFTools) | — | — | ✓ | ✓ |
| **Safety & Compliance** | | | | |
| SafetyForm Templates | — | — | ✓ | ✓ |
| Work Order Safety Form Answers | — | — | ✓ | ✓ |
| Required-Before-Work Enforcement | — | — | ✓ | ✓ |

> **Pricing:** See ServizDesk Pricing & Billing Specification V2 for all tier pricing, seat limits, storage included, and storage add-on options.

---

**End of ServizDesk Top-Down Specifications V4**
