# ServizmaDesk Top-Down Specifications
**Complete Product Structure & Data Model Documentation**

**Date:** March 2026
**Document Status:** Working Draft — V2
**Classification:** Internal — Confidential
**Purpose:** Full functional specification defining ServizmaDesk's complete product scope across all tiers
**Supersedes:** ServizmaDesk Top-Down Specifications V1
**Basis of Truth:** SD_System_ERD__Base_System_V6.pdf

---

# Document Purpose

This document provides a complete functional specification of ServizmaDesk's data model, features, workflows, and system structure. It defines the full product ceiling — the maximum functional scope across all tiers (Lite, Plus, Pro, Enterprise). Individual tier specifications determine which features are available at each plan level.

**Architectural Foundation:** ServizmaDesk is **asset-centric**. Unlike job-centric competitors where the Work Order is the primary organizing entity, ServizmaDesk treats the **Asset** (customer-owned equipment) as a first-class data entity. Work Orders, maintenance plans, warranty tracking, and service history are organized *around* Assets, not the other way around. This is the platform's core structural differentiator.

**Naming Conventions (canonical — applies to all ServizmaDesk documents):**
- **Customer** — The business or individual receiving service
- **Asset** — Customer-owned equipment tracked for service
- **Work Order** — A unit of service work on a single Asset (equivalent to "Job" in competitor platforms)
- **Quote** — A price proposal sent to a customer (equivalent to "Estimate" in competitor platforms)
- **Product** — An item in the product/service catalog (equivalent to "Inventory" in the ERD)
- **Preventative Maintenance (PM)** — A scheduled maintenance definition for a specific Asset under a service Agreement (equivalent to "Maintenance Plan" in competitor platforms)

**Document Scope:** This document covers the ServizmaDesk Tenant App (SDTA) only — the customer-facing application. It does not cover the ServizmaDesk Platform (SDP), which is the internal operations and billing platform. SDP is documented separately in the ServizmaDesk Platform (SDP) Specification V2.

**Single Source of Truth Policy:** Each data domain is owned by exactly one document. This document does not duplicate pricing, billing, trial structure, or technical stack decisions. Those are referenced from their owning documents. See Section 19 for the full document ownership map.

---

# 1. Data Model & Core Entities

## 1.1 Customer Entity

### Customer Record Structure

**Primary Fields:**
- **Customer Number** — Auto-generated (ServizmaDesk record numbering: C26-0001)
- **Status** — Dropdown
  - Values: Active, Inactive
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
- Each Contact links a **Person** record to this Customer (see Section 1.17 — Person Entity)
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
- Service Agreements (via CustomerAgreements)
- Leads and Opportunities
- Notes and documents
- Communication history
- Service history timeline
- Banking relationships (via Banks entity)
- Accounting records

---

## 1.2 Asset Entity

### Asset Record Structure

> **Architectural Note:** The Asset is ServizmaDesk's primary organizing entity. Unlike competitor platforms where equipment tracking is optional and secondary to job records, ServizmaDesk treats every Asset as a first-class data entity with its own complete lifecycle — installation, service history, warranty tracking, maintenance schedules, and eventual decommissioning. **Each Work Order operates on exactly one Asset.**

**Core Asset Fields:**
- **Asset Number** — Auto-generated (ServizmaDesk record numbering: A26-0001)
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

**Nested Assets (Parent/Child — Pro/Enterprise):**
- **Parent Asset** — Link to parent Asset record (nullable)
- Supports hierarchical equipment structures
  - Example: Rooftop HVAC Unit (parent) → Compressor (child), Blower Motor (child), Control Board (child)
- Each child Asset has independent warranty tracking, service history, and lifecycle
- Parent/child relationships visible in Asset detail view as a tree structure

**Asset Relationships:**
- **Customer** — Required relationship
- **Location** — Service location at customer site
- **Service History** — All Work Orders linked to this Asset (chronological timeline)
- **Preventative Maintenance** — PM schedules linked to this Asset
- **Service Agreements** — Agreements covering this Asset (via CustomerAgreements)
- **WorkGroups** — WorkGroups this Asset belongs to (via WorkGroupAssets)
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

## 1.3 TroubleCall (Call Intake) Entity

### TroubleCall Record Structure

**Purpose:** The entry point for all new customer service requests before they are converted into scheduled Work Orders or Quotes. This handles triage, incoming web bookings, and call center intake.

**TroubleCall Fields:**
- **TroubleCall Number** — Auto-generated (ServizmaDesk record numbering: TC26-0001)
- **Customer** — Link to Customer record (required, or "Unknown/New Lead" details)
- **Asset** — Link to Asset record (optional — identified during intake when known)
- **Location** — Link to Customer Location
- **Status** — Dropdown
  - Default values: New, Triaged, Converted to Work Order, Converted to Quote, Cancelled
- **Source** — Dropdown
  - Values: Phone, Customer Portal, Web Widget, Email, Referral
- **Issue Category** — Dropdown (e.g., HVAC Repair, Plumbing Leak, Electrical Outage)
- **Urgency** — Dropdown (Low, Normal, High, Emergency)
- **Customer Issue Description** — Text (exact customer wording)
- **Triage Notes** — Internal text (dispatcher/CSR notes on next steps)
- **Requested Date/Time** — Customer's preferred service window (from portal/widget)

**TroubleCall Relationships:**
- **Customer** — Required relationship
- **Asset** — Optional (linked when the asset is identified during intake)
- **Work Orders** — When triaged successfully, a TroubleCall converts into a Work Order or Quote. The Work Order retains a direct FK back to the originating TroubleCall.
- **Customer Portal** — TroubleCalls are directly created by the customer via the Portal

---

## 1.4 Work Order Entity

### Work Order Record Structure

> **Architectural Note:** A Work Order operates on exactly **one Asset**. When multiple assets need service in a single visit, each asset gets its own Work Order. Work Orders are grouped into a **WorkGroup** (Section 3.3) for dispatch and scheduling coordination. This preserves clean, per-asset service history while supporting multi-asset job coordination.

**Core Work Order Fields:**
- **Work Order Number** — Auto-generated (ServizmaDesk record numbering: W26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Asset** — Link to Asset record (required — one asset per Work Order)
- **Related Project** — Link to Project (optional)
- **TroubleCall** — Link to originating TroubleCall (optional — backlink if converted from a TroubleCall)
- **WorkFlow** — Link to WorkFlow record (optional — defines the operational steps for this Work Order)
- **Preventative Maintenance** — Link to PM record (optional — backlink if auto-generated from a PM schedule)
- **WorkGroup** — Link to WorkGroup (optional — for grouped/batched dispatch)
- **WG Division** — Link to WG Division (optional)
- **Vehicle** — Link to Vehicle record (optional — Fleet add-on only)
- **Work Order Status** — Dropdown
  - Default statuses: Draft, Scheduled, In Progress, On Hold, Completed, Closed, Cancelled
  - **Custom Status Workflows (Pro/Enterprise)** — Configurable per business
    - Example: "Permit Pending", "Material Ordered", "Awaiting Inspection"
    - Custom statuses can be created for specific service types
- **Assigned To** — Single primary employee assignment (FK to Employee/User record)
- **Priority** — Dropdown (Low, Normal, High, Urgent)
- **Scheduled Date/Time** — Date and time picker
- **Estimated Duration** — Time estimate
- **Work Order Type** — Dropdown (customizable service categories)
  - Examples: Service Call, Repair, Installation, Maintenance, Inspection, Diagnostic
- **Location** — Defaults to customer service address, can override
- **Hold Date** — Date/time (required when status is On Hold)
- **Hold Reason** — Text (required when status is On Hold)
- **Closed At** — Date/time (required when status is Closed)

**Work Order Team (Multi-Employee Assignment):**
- **Primary Assignee** — `assigned_to` field on Work Order (lead technician)
- **Additional Team Members** — Via WorkOrderTeam junction table (FK WorkOrder, FK Employee)
- Multiple employees can be assigned to one Work Order
- Each team member is tracked independently for time tracking and accountability

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
- **TaskTimes** — Time tracking per task per employee
- **TaskToDos** — Checklist items within a task

**Line Items:**
- Products and services used/performed on this Work Order
- Pulled from Product Catalog or created as free-text
- Bundles can be inserted
- Structure identical to Quote/Invoice line items

**Recurring Work Orders:**
- Toggle: "Make this Work Order recurring"
- Recurrence options: Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom interval
- Auto-generate future Work Orders based on schedule
- Link to Preventative Maintenance if applicable

**Time Tracking:**
- **Clock In/Out** — Time tracking per employee per Work Order
- **Time Entries** — View time by Work Order, employee, or date range
- **Arrival/Departure Times** — Logged per visit
- **Total Hours** — Calculated automatically
- **Labor Cost** — Calculated from hours × employee rate

**Safety Forms:**
- **WOSFAnswers** — Completed safety form responses per Work Order, per Employee
- Links to SafetyForms entity (Section 8.3)
- Each answer record captures which employee completed which safety form for which Work Order

**Custom Fields on Work Orders (Pro/Enterprise):**
- Custom fields can be created for Work Order records
- Same field types as Customer custom fields
- Separate from other entity custom fields

**Attachments:**
- **Photos** — Upload from mobile or desktop (before/after photo capability)
- **Files** — PDF, documents, forms
- **Forms** — Custom form attachments (Pro/Enterprise)
- **Signatures** — Customer sign-off capture

**Related Records:**
- **Quotes** — Linked quote(s)
- **Invoices** — Linked invoice(s)
- **Asset** — The single asset being serviced
- **Purchase Orders** — Related PO records (Plus+)
- **Project** — Parent project if applicable
- **TroubleCall** — Originating trouble call
- **PM** — Originating preventative maintenance schedule
- **WorkGroup** — Dispatch group this WO belongs to
- **Requisitions** — Part requisitions raised from this WO

---

## 1.5 Project Entity

### Project Structure

**Purpose:** Group multiple Work Orders under a single umbrella for complex, multi-phase work (e.g., HVAC system replacement, electrical panel upgrade, bathroom remodel)

**Project Fields:**
- **Project Number** — Auto-generated
- **Project Name** — Text
- **Customer** — Link to Customer record (required)
- **Project Status** — Dropdown
  - Default: Planning, In Progress, On Hold, Completed, Cancelled
- **Start Date** — Date picker
- **Target Completion Date** — Date picker
- **Project Manager** — Assigned employee
- **Budget** — Currency field
- **Actual Cost** — Calculated from linked Work Orders (labor + materials)
- **Completion Percentage** — Manual or auto-calculated from Work Order statuses

**Project Components:**
- **Grouped Work Orders** — Multiple Work Orders linked to project
- **Timeline Tracking** — Visual view of project schedule
- **Cost Tracking** — Real-time labor, materials, overhead
- **Profitability Monitoring** — Track margin throughout project

**Project-Level Features:**
- **Multi-day support** — Work Orders spanning multiple visits/phases
- **Team coordination** — Assign different employees per phase
- **Progress billing** — Invoice by phase or percentage of completion (Pro/Enterprise)

---

## 1.6 Quote Entity

### Quote Record Structure

**Header Fields:**
- **Quote Number** — Auto-generated (ServizmaDesk record numbering: Q26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Related Opportunity** — Link to Opportunity record (optional — see Section 2.3)
- **Related Work Order** — Link to Work Order (optional)
- **Related Project** — Link to Project (optional)
- **Related Asset(s)** — Link to Asset(s) being quoted for service (via QuoteAsset junction)
- **Quote Date** — Date picker (defaults to today)
- **Expiration Date** — Date picker (configurable default in settings)
- **Assigned To** — Employee who created/owns quote

**Quote Status:**
- **Draft** — Being created
- **Sent** — Sent to customer
- **Viewed** — Customer opened quote (tracked)
- **Approved** — Customer accepted
- **Rejected** — Customer rejected
- **Expired** — Past expiration date
- **Converted** — Converted to Invoice or Work Order

**Line Items:**
- **Add from Product Catalog** — Pull from pre-defined inventory
- **Create New Line Item** — Create on-the-fly
- **Insert Bundle** — Pre-configured bundles of items

**Line Item Fields (per item):**
- **Item Name** — Text
- **Type** — Dropdown: Service, Product - Inventory, Product - Non-Inventory
- **SKU** — Text (optional)
- **Description** — Long-form text
- **Unit Cost** — Currency (internal cost — not visible to customer)
- **Unit Price** — Currency (customer price)
- **Markup** — Percentage or fixed amount
- **Quantity** — Number
- **Taxable** — Toggle (yes/no)
- **Visible to Customer** — Toggle (can hide internal line items)

**Line Item Organization:**
- **Groupings** — Group items with title and subtotal (can hide individual names/prices, show only group total)
- **Bundles** — Pre-configured sets of items (see Product Catalog section) inserted with one click
- **Add-On Options** — Optional items customer can select (Pro/Enterprise)

**Good/Better/Best Proposals (Pro/Enterprise):**
- **Multi-Option Quoting** — Create multiple pricing tiers within a single quote
- Customer sees options side-by-side and selects preferred tier
- Each option has its own line items, subtotal, and description
- Increases average ticket by anchoring to middle option

**Subtotal Calculations:**
- **Line Item Subtotal** — Sum of all line items
- **Discounts** — Percentage or fixed amount
- **Surcharges** — Additional fees
- **Tax** — Applied to taxable items only (default tax rate from settings, can override per-quote)
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

**Conversion:**
- **Convert to Invoice** — One-click conversion (transfers all line items, deposits applied)
- **Convert to Work Order** — Generate Work Order from approved quote

---

## 1.7 Invoice Entity

### Invoice Record Structure

**Header Fields:**
- **Invoice Number** — Auto-generated (ServizmaDesk record numbering: I26-0001, annual reset)
- **Customer** — Link to Customer record (required)
- **Related Work Order** — Link to Work Order (optional)
- **Related Project** — Link to Project (optional)
- **Related Asset(s)** — Link to Asset(s) serviced (via InvoiceAsset junction)
- **Invoice Date** — Date picker (defaults to today)
- **Due Date** — Date picker (auto-populate methods configurable: Creation Date + N days, Sent Date + N days, WO Completion + N days, Manual entry)
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
- Toggle: Make Recurring
- Recurrence options: Weekly, Monthly, Quarterly, Annual, Custom interval
- Auto-generate and optionally auto-send

**Payment Features:**
- **Record Manual Payment** — Cash, check, bank transfer, other
- **Stripe Payment Link** — Generate payment link for customer
- **Partial Payments** — Record multiple payments against invoice
- **Deposits Applied** — Deposits collected on Quotes reduce balance due

**Subtotal Calculations:**
- Line Item Subtotal, Discounts, Surcharges, Tax, Total Due
- Deposits Applied (from quote approval)
- Amount Paid (sum of payments received)
- Balance Due (calculated remaining)

**Commission Tracking (Pro/Enterprise):**
- Enable Commission Calculations toggle in settings
- Methods: Percentage of gross sales, Percentage of gross margin
- Default rate configurable, can override per invoice

**Notes, Attachments, Templates, PDF Generation:**
- Same capabilities as Quotes (notes, internal notes, files, templates, PDF customization)

**Generation from Quotes:**
- Convert Quote to Invoice — transfers all line items and details, deposits applied automatically

---

## 1.8 Product Catalog (Items & Services)

### Product Repository Structure

> **Naming Note:** The ERD uses "Inventory" as the entity name throughout. In user-facing specifications and UI, this entity is called "Product" for clarity. Product in specs = Inventory in ERD.

**Purpose:** Central catalog of all products and services the business offers. Products are referenced on Quotes, Invoices, and Work Orders as line items.

**Product Fields:**
- **Product Number** — Auto-generated (ServizmaDesk reverse alphabet encoding: XT-0001)
- **Product Name** — Text (required)
- **Type** — Dropdown (required): Service, Product - Inventory, Product - Non-Inventory
- **Category** — Dropdown (customizable)
- **SKU** — Text (optional)
- **Unit Cost** — Currency (what you pay)
- **Unit Price** — Currency (what you charge)
- **Markup** — Calculated (Price - Cost / Cost × 100)
- **Description** — Long-form text
- **Taxable** — Toggle (yes/no)

**Inventory Tracking (Plus+ — Products with type "Product - Inventory"):**
- Quantity on Hand, Quantity Minimum, Quantity Allocated, Quantity On Order, Quantity Reserved, Quantity Available
- **Preferred Vendor** — Link to Vendor
- **Location/Hub** — Where item is stored (multi-location in Pro/Enterprise, per-truck in Enterprise)

**Serialized Inventory (Pro/Enterprise):**
- Toggle: Serialized Item. Each unit tracked by unique serial number with full custody chain.

**Bundles:**
- Pre-configured sets of items grouped as reusable packages (via BundleItem/KitItems table)
- Bundles inserted with one click on Quotes and Invoices

**Price Tiers / Pricebooks (Pro/Enterprise):**
- Customer-specific pricing via multiple price tiers
- Pricebook entries override standard Product prices
- Price tier assigned to Customer record, auto-applies on Quotes/Invoices

**Price History (InvPriceHistory):**
- Historical record of price changes per product
- Audit trail of when prices were updated and by whom

**Mass Import:**
- Import products via CSV template

---

## 1.9 Warehouse / Location Entity (Plus+)

### Warehouse Record Structure

**Purpose:** Defines the physical or mobile locations where inventory (Products) is stored.

**Warehouse/Location Fields:**
- **Warehouse Number** — Auto-generated (ServizmaDesk record numbering: WH26-0001)
- **Warehouse Name** — Text (required)
- **Type** — Dropdown: Physical Hub, Mobile (Van/Truck)
- **Status** — Active, Inactive
- **Assigned Employee** — Link to Employee (especially for Mobile/Van types)
- **Address** — Full address (for Physical Hubs), via Address table
- **Phone** — Via Phone table (for Warehouse contact)
- **Notes** — Internal notes

**Sub-Location Record Structure:**
- **Location Number** — User-generated (e.g., "A1.B3.C2")
- **Parent Warehouse** — Link to Warehouse record (required)
- **Type** — Dropdown: Area, Bin, Shelf, Section, Cabinet, Room
- **Description** — Text
- **Status** — Active, Inactive

**Loc_Assigned_Inv:**
- Junction table tracking which Products are assigned to which sub-locations (FK Location, FK Inventory/Product)

**Warehouse Relationships:**
- Sub-Locations (one warehouse → many sub-locations)
- Inventory quantities tracked per sub-location, rolling up to warehouse, then to product
- Purchase Orders can be received directly into a specific Warehouse
- Work Orders — inventory used on a Work Order is decremented from the assigned Warehouse

---

## 1.10 Payment Entity (Customer Payments)

### Customer Payment Record Structure

**Payment Types:**
- Credit/Debit Card (via Stripe Payment Links), Cash, Check, Bank Transfer, Other

**Payment Fields:**
- **Payment Number** — Auto-generated (ServizmaDesk record numbering: P26-0001, annual reset)
- **Invoice** — Link to Invoice record (required)
- **Customer** — Link to Customer record (denormalized for reporting)
- **Employee** — Link to Employee who recorded the payment
- **Payment Date** — Date received
- **Amount** — Currency
- **Payment Method** — Dropdown
- **Reference Number** — For check/transfer tracking
- **Stripe Payment Intent ID** — For Stripe-processed payments
- **Vehicle Maintenance** — Link to VehicleMaintenance (optional — for fleet expense payments)
- **Stripe Response** — Link to StripeResponse record
- **Notes** — Internal notes about payment

**Stripe Integration:**
- Payment Links generated per Invoice for customer self-service payment
- Webhook processing for automatic payment recording
- Idempotent processing (no duplicate records from duplicate webhook events)
- No markup — ServizmaDesk passes through Stripe fees with no additional markup

**Consumer Financing (Pro/Enterprise):**
- Third-party integration (Wisetack or equivalent)
- Offer financing to customers at point of sale

**Payment Tracking:**
- Payment history per customer
- Payment status on invoices
- Aging reports (Plus+)
- Payment reminders (Plus+ automation)

---

## 1.11 Vendor Payment Entity (Outgoing Payments)

### Vendor Payment Record Structure

> **Architectural Note:** Customer payments (Section 1.10) and Vendor payments are separate entities in the ERD. Customer payments are incoming (money received from customers). Vendor payments are outgoing (money paid to vendors for purchases and bills).

**Vendor Payment Fields:**
- **Payment Number** — Auto-generated
- **Purchasing** — Link to PurchaseOrder record (optional)
- **Vendor** — Link to Vendor record (required)
- **VendorBill** — Link to VendorBill record (optional)
- **Payment Date** — Date paid
- **Amount** — Currency
- **Payment Method** — Dropdown
- **Reference Number** — Check number, transfer reference
- **Notes** — Internal notes

---

## 1.12 Vendor Entity (Plus+)

### Vendor Record Structure

> **Standalone Entity:** Vendors are a completely separate entity from Customers. There is no connection between them. In Lite, there is no reference to Vendors in any way.

**Vendor Fields:**
- **Vendor Name** — Text (required)
- **Account Number** — Vendor account reference
- **Notes** — Vendor-specific notes

**Contacts (via Contact Table):**
- Vendor has one or more Contact records (VContact in ERD)
- Each Contact links a Person record to this Vendor
- Socials, Phone numbers managed via shared Triad tables

**Addresses (via Address Table — VAddress in ERD):**
- Vendor addresses managed via shared Address Table

**Vendor Relationships:**
- Contacts — People associated with this vendor
- Products — Products sourced from this vendor (preferred vendor per product)
- Purchase Orders — PO history with vendor
- VendorBills — Bills received from vendor
- Vendor Payments — Payments made to vendor
- Cost Tracking — Track prices over time
- RMAs — Return authorizations with vendor

---

## 1.13 VendorBills Entity (Plus+)

### VendorBill Record Structure

> **Architectural Note:** A VendorBill represents the vendor's invoice to your business (accounts payable). This is separate from a PurchaseOrder, which represents your request to the vendor. VendorBills have an independent lifecycle and vendor payments link directly to VendorBills.

**VendorBill Fields:**
- **Bill Number** — Auto-generated or manual entry
- **Vendor** — Link to Vendor record (required)
- **Bill Date** — Date received
- **Due Date** — Date payment is due
- **Amount** — Currency
- **Status** — Draft, Received, Partially Paid, Paid, Overdue, Void
- **Related Purchase Order** — Link to PO (optional)
- **Notes** — Internal notes

**VendorBill Relationships:**
- Vendor (required)
- Vendor Payments — Payments applied to this bill
- Ledger entries — Financial recording
- Notes/Documents — Supporting documentation

---

## 1.14 Purchase Order Entity (Plus+)

### Purchase Order Structure

**PO Fields:**
- **PO Number** — Auto-generated
- **Vendor** — Link to Vendor record (required)
- **Related Work Order** — Link to Work Order (optional)
- **Related Project** — Link to Project (optional)
- **Order Date** — Date picker
- **Expected Delivery Date** — Date picker
- **Status** — Draft, Sent, Partially Received, Received, Cancelled

**PO Line Items (P-LineItems):**
- **Product** — From Product Catalog or create new
- **Quantity Ordered** — Number
- **Quantity Received** — Number (updated on receipt via Receiving)
- **Unit Cost** — Cost per unit
- **Total** — Calculated
- **POR Line Item** — Link to Part Requisition line if originated from requisition

**Receiving:**
- Dedicated Receiving entity (FK PLineItem, FK Inventory/Product, FK Employee)
- Mark line items as received (full or partial) with employee accountability
- Receiving updates inventory quantities automatically
- Variance tracking (ordered vs. received)

**Lot Info:**
- Lot/batch tracking per received item (FK PLineItem, FK Inventory/Product)
- Lot number, expiration date, batch traceability

---

## 1.15 Part Requisition Entity (Plus+)

### Requisition Structure

**Purpose:** Technicians in the field request parts when their van inventory is insufficient.

**Requisition Fields:**
- **Requisition Number** — Auto-generated
- **Requesting Employee** — FK Employee (required)
- **Related Work Order** — FK Work Order (optional)
- **Related Fleet Vehicle** — FK Vehicle (optional)
- **Status** — New, Approved, Partially Fulfilled, Fulfilled, Cancelled
- **Fulfillment Method** — Warehouse Transfer, direct Purchase Order

**Requisition Line Items (RLineItem):**
- **Product** — Link to Product Catalog (or free-text for non-catalog items)
- **Quantity Requested** — Number
- **Quantity Fulfilled** — Number (updates as parts arrive)
- **Related PO Line** — FK PLineItem (if fulfilled via PO)
- **Notes** — E.g., "Need specific brand for consistency"

**Requisition Workflow:**
- Technician submits Requisition from mobile app
- Purchasing agent or Warehouse Manager reviews
- Requisition can be converted to a Purchase Order (sent to Vendor) or an Inventory Transfer (from Main Hub to Technician Van)

---

## 1.16 RMA Entity (Return Merchandise Authorization) (Plus+)

### RMA Record Structure

**Purpose:** Manages the return of defective or incorrect parts to vendors.

**RMA Fields:**
- **RMA Number** — Auto-generated
- **PO Line Item** — FK PLineItem (the original purchase line being returned)
- **Product** — FK Inventory/Product (the item being returned)
- **Vendor** — FK Vendor (who it's being returned to)
- **Status** — Initiated, Shipped, Received by Vendor, Credited, Closed, Denied
- **Reason** — Dropdown (Defective, Wrong Item, Damaged, Overstock, Other)
- **Quantity** — Number being returned
- **Credit Amount** — Currency (expected or received credit)
- **Notes** — Internal notes

**RMA Relationships:**
- Links back to original PO Line Item for traceability
- Notes/Documents for shipping labels, correspondence

---

## 1.17 Person Entity

### Person Record Structure

> **Architectural Note:** The Person entity represents a permanent human identity, independent of any company or customer relationship. A Person can be linked to multiple Customers (or Vendors) through Contact records. When a person changes companies, their Person record persists — only the Contact relationship changes.

**Person Fields:**
- **First Name** — Text (required)
- **Last Name** — Text (required)

**Person Relationships:**
- Contacts — All Contact records linking this Person to Customers and/or Vendors
- Socials — Personal social media profiles and personal emails (via Socials Table)
- A single Person can have multiple active Contacts
- Person record is never deleted when a Contact is removed — history is preserved

---

## 1.18 Socials Entity

### Socials Record Structure

**Socials Fields:**
- **Type** — Dropdown: Email, Facebook, LinkedIn, Instagram, Twitter/X, YouTube, Website, Other
- **URL** — Text (email address or full URL to profile/page)

**Socials Relationships:**
- **Contact** — For company-assigned emails and professional profiles
- **Person** — For personal emails and social media
- **User/Employee** — For employee social/email
- **Customer** — Direct customer-level social links
- **Vendor** — Direct vendor-level social links
- At least one parent FK required. Supports unlimited entries per parent.

---

## 1.19 Standalone Task Entity

### Task Record Structure

**Purpose:** Standalone internal tasks not tied to a specific Work Order.

**Task Fields:**
- **Task Number** — Auto-generated (ServizmaDesk record numbering: T26-0001)
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

# 2. CRM Pipeline

## 2.1 Leads Entity (Plus+)

### Lead Record Structure

**Purpose:** Captures potential customers who have not yet been qualified or converted to a full Customer record. Leads are the top of the sales funnel.

**Lead Fields:**
- **Lead Number** — Auto-generated
- **Customer** — Link to Customer record (optional — nullable for unqualified leads)
- **Contact Info** — Name, Phone, Email (captured before Customer creation)
- **Source** — Dropdown (Referral, Website, Advertisement, Trade Show, Cold Call, Other)
- **Status** — New, Contacted, Qualified, Converted, Lost
- **Notes** — Internal notes

**Lead Relationships:**
- Customer (optional — linked when lead is associated with an existing customer)
- Opportunities — Leads generate Opportunities when qualified
- Notes/Documents — Supporting documentation

---

## 2.2 Opportunity Entity (Plus+)

### Opportunity Record Structure

**Purpose:** Represents a qualified sales opportunity that may result in a Quote and eventual work. Tracks the sales pipeline from qualification through close.

**Opportunity Fields:**
- **Opportunity Number** — Auto-generated
- **Customer** — Link to Customer record (required)
- **Lead** — Link to originating Lead (optional)
- **Name/Description** — Text describing the opportunity
- **Status** — Open, Won, Lost
- **Estimated Value** — Currency
- **Expected Close Date** — Date picker
- **Assigned To** — Employee (salesperson)
- **Notes** — Internal notes

**Opportunity Relationships:**
- Customer (required)
- Lead (optional — originating lead)
- Quotes — Quotes generated from this opportunity
- Assigned Contacts — People at the customer involved in this opportunity (via Oppt-SASSIGNED-Contact)
- Notes/Documents

---

## 2.3 Opportunity Assigned Contacts (Oppt-SASSIGNED-Contact)

### Junction Table

**Purpose:** Links specific contacts (people at the customer's company) to an Opportunity. Different opportunities at the same customer may involve different decision-makers.

**Fields:**
- **Opportunity** — FK Opportunity (required)
- **Contact** — FK Contact (required)
- **Company** — FK Customer (required — denormalized for clarity)
- **Role in Opportunity** — Text (e.g., "Decision Maker", "Technical Evaluator", "Budget Approver")

---

# 3. Scheduling, Dispatch & WorkGroups

## 3.1 Schedule/Calendar Views

### Calendar Interface

**View Options:**
- Daily View, Weekly View, Employee View
- **Map View** — Geographic view of scheduled Work Orders (Pro/Enterprise)

**Drag-and-Drop Scheduling:**
- Move Work Orders to different date/time/employee
- Resize to adjust duration
- Color-coding by status, priority, type, or custom tags

**Employee Availability:**
- Working Hours per employee
- Time Off blocking
- Skills/Certifications matching (Pro/Enterprise — see Section 9.2)

## 3.2 Work Order Assignment

### Assignment Methods

**Manual Assignment:**
- Drag-and-drop via calendar
- From Work Order record — select assigned employee(s)
- WorkOrderTeam for multiple employees

**Smart Assignment (Pro/Enterprise):**
- Skill-based matching (see Section 9.2)
- Availability-based — only show available employees
- Workload balancing — distribute evenly across team

## 3.3 WorkGroup Entity (Plus+)

### WorkGroup Record Structure

> **Architectural Note:** A WorkGroup organizes multiple Work Orders for coordinated dispatch. Since each Work Order operates on a single Asset, WorkGroups provide the multi-asset grouping capability. WorkGroupAssets provides a rolled-up view of all assets across the group's Work Orders.

**WorkGroup Fields:**
- **WorkGroup Number** — Auto-generated
- **Customer** — FK Customer (required)
- **Address** — FK Address (service location for the group)
- **Status** — Open, In Progress, Completed, Cancelled
- **Notes** — Internal notes

**WorkGroupTeam (Junction Table):**
- **WorkGroup** — FK WorkGroup
- **Employee** — FK Employee
- **Employee Role** — FK WGTRoles (role within this work group)

**WGTRoles:**
- Defines roles within a WorkGroup (e.g., Lead Technician, Helper, Apprentice)

**WG Division:**
- Sub-division within a WorkGroup for geographic or organizational segmentation
- **WorkGroup** — FK WorkGroup
- **Address** — FK Address (division-specific location)

**WorkGroupAssets (Junction Table):**
- **Asset** — FK Asset
- **WorkGroup** — FK WorkGroup
- Provides rolled-up view of all Assets being serviced across the WorkGroup's Work Orders

## 3.4 Route Planning (Pro/Enterprise)

### Location Features

**Travel Coordination:**
- Travel time calculation between Work Orders
- Manual route planning
- Route optimization — traffic-aware suggestions (Enterprise)

**Customer Notifications:**
- "On the Way" alerts
- Arrival window estimates

---

# 4. WorkFlow Engine

## 4.1 WorkFlow Entity (Pro/Enterprise)

### WorkFlow Record Structure

> **Architectural Note:** The WorkFlow entity defines a complete operational procedure — the sequence of steps, the checklist items within each step, the tools required, and the parts/inventory required. WorkFlows drive both Preventative Maintenance schedules and Work Order execution. This is structurally different from simple status workflows; a WorkFlow is a full Standard Operating Procedure (SOP).

**WorkFlow Fields:**
- **WorkFlow Number** — Auto-generated
- **Name** — Text (e.g., "Residential HVAC Install SOP", "Quarterly Filter Service Procedure")
- **Description** — Long-form text
- **Status** — Active, Inactive, Draft
- **Work Order Type** — Optional auto-apply trigger (when WO type matches)

**WorkFlow Relationships:**
- Steps — Ordered list of WFSteps
- Tools Required — Equipment needed for this workflow (via WFTools)
- Inventory Required — Parts/products needed for this workflow (via WF Inventory)
- Preventative Maintenance — PMs that use this workflow
- Work Orders — WOs executing this workflow

---

## 4.2 WFSteps Entity

### Workflow Step Structure

**WFStep Fields:**
- **WorkFlow** — FK WorkFlow (required)
- **Step Name** — Text (e.g., "Disconnect Power", "Remove Access Panel", "Clean Coils")
- **Sort Order** — Integer (sequence within workflow)
- **Description** — Long-form text (detailed instructions)
- **Estimated Duration** — Time estimate for this step

**WFStepToDos:**
- Checklist items within a workflow step
- **WFStep** — FK WFSteps (required)
- **ToDo Label** — Text
- **Sort Order** — Integer
- **Is Required** — Boolean (must complete before step can be marked done)

---

## 4.3 WFTools (WorkFlow Required Equipment)

### Junction Table

**Purpose:** Defines which Equipment items (company-owned tools) are required to complete a workflow.

**Fields:**
- **WorkFlow** — FK WorkFlow
- **Equipment** — FK Equipment (see Section 9.3)

---

## 4.4 WF Inventory (WorkFlow Required Parts)

### Junction Table

**Purpose:** Defines which Products/Inventory items are needed to complete a workflow.

**Fields:**
- **WorkFlow** — FK WorkFlow
- **Product** — FK Inventory/Product

---

# 5. Service Agreements & Preventative Maintenance

## 5.1 Agreements Entity (Plus+)

### Agreement Record Structure

> **Architectural Note:** Agreements define the terms and scope of service contracts between the business and its customers. This is a broader concept than a simple maintenance schedule — an Agreement can cover multiple assets, define service levels, pricing tiers, response times, and discount structures. Preventative Maintenance (PM) records are the specific scheduled maintenance deliverables under an Agreement.

**Agreement Fields:**
- **Agreement Number** — Auto-generated
- **Name** — Text (e.g., "Gold Service Plan", "Annual Maintenance Contract")
- **Description** — Long-form text (terms, inclusions, exclusions)
- **Status** — Active, Expired, Cancelled, Pending
- **Start Date** — Date picker
- **End Date** — Date picker (or Ongoing)
- **Renewal Type** — Manual, Auto-Renew
- **Pricing** — Monthly, Quarterly, Annual fee
- **Discount Percentage** — Percentage discount on additional work for agreement holders

**Plan Tiers (Pro/Enterprise):**
- Silver, Gold, Platinum (or custom tier names)
- Different services/inclusions per tier

---

## 5.2 CustomerAgreements (Junction Table)

### Three-Way Junction

**Purpose:** Binds one Customer + one Agreement + one Asset per row. A customer with 3 HVAC units on a Gold Plan = 3 CustomerAgreement rows.

**Fields:**
- **Customer** — FK Customer (required)
- **Agreement** — FK Agreement (required)
- **Asset** — FK Asset (required)

**Example:**
- Row 1: Acme Corp + Gold Plan + RTU-001
- Row 2: Acme Corp + Gold Plan + RTU-002
- Row 3: Acme Corp + Gold Plan + Furnace-001

---

## 5.3 Preventative Maintenance Entity (Plus+)

### PM Record Structure

> **Architectural Note:** A PM record defines the maintenance schedule and operational workflow for a specific Asset under a specific CustomerAgreement. Each PM generates Work Orders per its schedule. The PM is driven by a WorkFlow (steps, ToDos, required tools, required parts) — not a simple checklist template.

**PM Fields:**
- **PM Number** — Auto-generated
- **Asset** — FK Asset (required — one PM per asset per agreement)
- **Customer Agreement** — FK CustomerAgreements (required — links back to the agreement covering this asset)
- **WorkFlow** — FK WorkFlow (required — defines the SOP for this maintenance)
- **Customer** — FK Customer (denormalized for reporting/filtering)
- **Status** — Active, Paused, Expired, Cancelled
- **Frequency** — Daily, Weekly, Monthly, Quarterly, Semi-Annual, Annual, Custom
- **Visits per Period** — Number of visits included
- **Start Date** — Date picker
- **End Date** — Date picker (or Ongoing)
- **Default Assignee** — FK Employee (default technician)
- **Auto-Generate Work Orders** — Boolean
- **Advance Generation Days** — How far ahead to create upcoming WOs

**PM Relationships:**
- Asset (required — the equipment being maintained)
- CustomerAgreement (required — the agreement this PM fulfills)
- WorkFlow (required — the operational procedure)
- Work Orders (generated — auto-created per schedule, each WO has FKPrev_Maint back to this PM)

**PM → Work Order Generation:**
- System creates Work Orders per schedule
- Each generated WO inherits: Customer, Asset, WorkFlow, Assigned Employee
- Each generated WO has `prev_maint_id` linking back to the PM that created it
- Reminders sent to customer and technician per configurable advance days

---

# 6. Inventory Management (Detail)

## 6.1 Inventory Counts Entity (Plus+)

**Purpose:** Records physical inventory count events for reconciliation against system quantities.

**Fields:**
- **Product** — FK Inventory/Product (required)
- **Count Date** — DateTimeField
- **Counted By** — FK Employee
- **Physical Count** — Number (actual counted quantity)
- **System Count** — Number (quantity per system at time of count)
- **Variance** — Calculated (Physical - System)
- **Adjustment Applied** — Boolean
- **Notes** — Internal notes

---

## 6.2 Inventory Transfers Entity (Plus+)

**Purpose:** Tracks movement of inventory between locations (e.g., from Main Hub to Van 01, between warehouses).

**Fields:**
- **Source Location** — FK Location/SubLocation
- **Destination Location** — FK Location/SubLocation
- **Product** — FK Inventory/Product
- **Quantity** — Number
- **Transfer Date** — DateTimeField
- **Initiated By** — FK Employee
- **Status** — Pending, In Transit, Completed, Cancelled
- **Notes** — Internal notes

---

## 6.3 Receiving Entity (Plus+)

**Purpose:** Detailed receiving records when PO items arrive, with employee accountability.

**Fields:**
- **PO Line Item** — FK PLineItem (required)
- **Product** — FK Inventory/Product (required)
- **Employee** — FK Employee (who received the goods)
- **Quantity Received** — Number
- **Received Date** — DateTimeField
- **Condition** — Dropdown (Good, Damaged, Partial)
- **Notes** — Internal notes

---

## 6.4 Lot Info Entity (Pro/Enterprise)

**Purpose:** Lot/batch tracking for received inventory items.

**Fields:**
- **PO Line Item** — FK PLineItem
- **Product** — FK Inventory/Product
- **Lot Number** — Text
- **Expiration Date** — DateField (nullable)
- **Quantity** — Number
- **Notes** — Internal notes

---

# 7. Financial Entities

## 7.1 Native Accounting Entity (All Tiers)

### Financial Tier Scalability

> **Architectural Decision:** ServizmaDesk utilizes a "Native Accounting First" approach that scales with the customer's tier, supported by robust CSV exports for external tax prep.

**Accounting Entity:**
- **Customer** — FK Customer (nullable)
- **Carrier** — FK Carrier (nullable — for insurance/surety accounting)
- **Bank** — FK Bank (nullable — for banking relationship tracking)
- **Account Type** — Dropdown (Receivable, Payable, Revenue, Expense, etc.)
- **Balance** — Currency

**Tier 1: Lite (Basic Income Ledger)**
- No true double-entry General Ledger. Tracks generated Invoices and applied Payments. Simple list view showing Balance Due per customer and total revenue collected.

**Tier 2: Plus (Advanced AR/AP & Expense Tracking)**
- Advanced AR with aging reports. Introduces AP via Purchase Orders and VendorBills. Basic expense tracking for job costing margin.

**Tier 3: Pro (Native Core Accounting)**
- Chart of Accounts (COA). True Double-Entry General Ledger (GL).

**Tier 4: Enterprise (Full ERP Accounting)**
- All Pro features plus Journal Entries, Multi-Location Accounting, Bank Feed Integration (Plaid/Finicity), Fixed Asset Management, Complex Tax Liabilities.

---

## 7.2 Ledger Entity

**Purpose:** The authoritative financial net balance trace for all accounts.

**Ledger Fields:**
- **Payment** — FK Payment (link to customer or vendor payment transaction)
- **Customer** — FK Customer (nullable)
- **Vendor** — FK Vendor (nullable)
- **Purchasing** — FK PurchaseOrder (nullable)
- **Invoice** — FK Invoice (nullable)
- **Entry Type** — Debit, Credit
- **Amount** — Currency
- **Running Balance** — Calculated at write-time

---

## 7.3 Banks Entity (Plus+)

### Bank Record Structure

**Purpose:** Represents banking relationships linked to customers (for ACH payments, financing, direct deposit of receivables).

**Bank Fields:**
- **Bank Name** — Text (required)
- **Customer** — FK Customer (required)
- **Account Type** — Dropdown (Checking, Savings, Line of Credit, Other)
- **Routing Number** — Text (encrypted)
- **Account Number** — Text (encrypted — last 4 digits displayed)
- **Status** — Active, Inactive
- **Notes** — Internal notes

**Bank Relationships:**
- Contacts, Phones, Addresses via shared Triad tables (just like Customer and Vendor)
- Accounting — linked to Accounting entity

---

## 7.4 Carrier Entity (Plus+)

### Carrier Record Structure

**Purpose:** Represents insurance carriers, surety bond providers, or other financial carriers linked to the business's accounting.

**Carrier Fields:**
- **Carrier Name** — Text (required)
- **Carrier Type** — Dropdown (Insurance, Surety, Freight, Other)
- **Policy/Account Number** — Text
- **Status** — Active, Inactive
- **Notes** — Internal notes

**Carrier Relationships:**
- Contacts, Phones, Addresses via shared Triad tables
- Accounting — linked to Accounting entity

---

# 8. Safety & Compliance

## 8.1 SafetyForms Entity (Pro/Enterprise)

### Safety Form Record Structure

**Purpose:** Defines reusable safety form templates (e.g., OSHA job site safety checklist, confined space entry permit, electrical lockout/tagout procedure).

**SafetyForm Fields:**
- **Form Name** — Text (required)
- **Description** — Long-form text
- **Status** — Active, Inactive, Draft
- **Form Fields** — JSON or structured field definitions (text, checkbox, dropdown, signature, photo)
- **Required Before Work** — Boolean (if true, technician must complete before starting WO)

---

## 8.2 WOSFAnswers Entity (Pro/Enterprise)

### Work Order Safety Form Answers

**Purpose:** Records the completed safety form responses for a specific Work Order by a specific Employee.

**Fields:**
- **Work Order** — FK WorkOrder (required)
- **Employee** — FK Employee (required — who completed the form)
- **Safety Form** — FK SafetyForms (required — which form was completed)
- **Answers** — JSON (the actual responses to each form field)
- **Completed At** — DateTimeField
- **Notes** — Internal notes

---

## 8.3 Custom Forms (Pro/Enterprise)

### Form Builder Features

**Form Types:**
- Service checklists, Equipment installation forms, Customer sign-off forms, Inspection reports, Compliance/regulatory forms

**Form Field Types:**
- Text, Date (calendar picker), Checkboxes, Dropdown lists, Signature fields, Photo upload

**Form Workflow:**
- Fill out on mobile in the field
- Attach to Work Order record as permanent documentation
- Send to customer for e-signature
- PDF generation of completed forms

---

# 9. Employee Management & Skills

## 9.1 Employee / User Roles & Permissions

### Role Types

**Administrator:** Full access to all features and settings, billing management (via SDP), employee management.

**User:** Operational access to day-to-day features. Create and edit Customers, Assets, Work Orders, Quotes, Invoices. Limited Admin Area access.

**Read-Only:** View-only access. Cannot create, edit, or delete records.

**Custom Roles (Pro/Enterprise):** Define custom permission profiles with granular entity-level and field-level controls.

### Permissions

**Entity-Level:** Per-entity create, read, update, delete controls. Configurable per role.

**Field-Level Visibility (Pro/Enterprise):** Show/hide financial data (cost, margin, markup), internal notes, custom fields by role.

## 9.2 Skills & Employee Skills (Pro/Enterprise)

### Skills Entity

**Purpose:** Defines certifications, licenses, and competencies that employees can hold.

**Skills Fields:**
- **Skill Name** — Text (e.g., "EPA 608 Certification", "Journeyman Electrician", "CDL Class B")
- **Category** — Dropdown (Certification, License, Training, Competency)
- **Status** — Active, Inactive

### EmployeeSkills (Junction Table)

**Fields:**
- **Employee** — FK Employee
- **Skill** — FK Skills
- **Date Earned** — DateField
- **Expiration Date** — DateField (nullable — for renewable certifications)
- **Status** — Active, Expired

**Usage:**
- Smart Assignment uses EmployeeSkills to match Work Orders to qualified employees
- Compliance reporting — track expired certifications across the team

---

## 9.3 Equipment Entity (Company-Owned Tools)

### Equipment Record Structure

> **Architectural Note:** Equipment tracks company-owned tools and equipment (e.g., refrigerant recovery machine, pipe threader, multimeter). This is distinct from Products/Inventory (items sold to customers) and Assets (customer-owned equipment). Equipment items are internal company property.

**Equipment Fields:**
- **Equipment Number** — Auto-generated
- **Name** — Text (required)
- **Category** — Dropdown (Power Tool, Hand Tool, Diagnostic, Safety, Other)
- **Serial Number** — Text
- **Status** — Available, Checked Out, In Repair, Decommissioned
- **Purchase Date** — DateField
- **Purchase Cost** — Currency
- **Notes** — Internal notes

### Check In/Out Entity

**Purpose:** Tracks custody of Equipment items — who has which tool and when.

**Fields:**
- **Equipment/Tool** — FK Equipment (required)
- **Employee** — FK Employee (required)
- **Checked Out At** — DateTimeField
- **Checked In At** — DateTimeField (nullable — null = still checked out)
- **Condition at Checkout** — Dropdown (Good, Fair, Needs Repair)
- **Condition at Return** — Dropdown (Good, Fair, Damaged)
- **Notes** — Text

---

## 9.4 Positions Entity

### Position Record Structure

> **Architectural Note:** Positions define organizational job titles (e.g., "Senior Technician", "Service Manager", "Dispatcher"). This is separate from Roles, which define system permissions. An employee has a Position (org chart) and one or more Roles (access control).

**Position Fields:**
- **Position Title** — Text (required)
- **Department** — FK Department (required)
- **Description** — Text
- **Status** — Active, Inactive

---

## 9.5 Departments Entity

### Department Record Structure

**Department Fields:**
- **Department Name** — Text (required)
- **Status** — Active, Inactive

**Department Relationships:**
- Employees — FK Department on Employee
- Positions — Positions belong to Departments
- Locations — Locations assigned to Departments (via Locations entity)

---

## 9.6 CreditCards Entity (Pro/Enterprise)

### Credit Card Record Structure

**Purpose:** Tracks company credit cards assigned to employees for expense tracking and fleet fuel purchases.

**CreditCard Fields:**
- **Employee** — FK Employee (required — card holder)
- **Card Type** — Dropdown (Visa, Mastercard, Amex, Other)
- **Last Four Digits** — Text (for identification only — never store full card number)
- **Issuing Bank** — Text
- **Expiration Date** — DateField
- **Credit Limit** — Currency
- **Status** — Active, Suspended, Cancelled
- **Notes** — Internal notes

---

## 9.7 User Sessions & Audit Trail

### Access & Activity Logging

**Session Logging (On Login Attempt):**
- Session ID, User Details, Login/Logout/Expiration Timestamps, IP Address, Browser, OS, Device Type, Permission Snapshot

**Audit Event Logging (During Session):**
- Event Timestamp, Action Performed (Created, Updated, Deleted, Approved, Voided, etc.), Target Record, Record ID, Event Details
- Every Audit Event linked to originating Session ID

---

# 10. Customer Communication & Portal

## 10.1 Communication (Plus+)

### Communication Features

**Email Communication:** Send Quotes, Invoices, Payment Links to customers. Email history tracked per customer. Configurable email templates.

**SMS (Plus+):** Point-based model. 1 point = 1 outbound SMS.

**Automated Communications (Plus+ Automations):** Appointment reminders, WO completion follow-up, Payment reminders, Maintenance reminders, Review requests (Pro/Enterprise).

**Automation Engine (Plus+):** Basic "IF [event] THEN [action]" rules. Plus: 2–5 rules. Pro/Enterprise: Unlimited.

## 10.2 Customer Portal (Plus+)

### Portal Features

**Customer Self-Service:**
- Request Service — creates a TroubleCall (Section 1.3)
- View Service History — past Work Orders and Invoices
- Quote Review & Approval — review, comment, approve/reject with E-signature
- Pay Invoices — online payment via Stripe (partial and full)
- View Asset Information — registered Assets and warranty status
- Communication — message directly with business/dispatcher

**Portal Branding:** Business logo, colors, custom portal URL.

**Online Booking Widget (Lite Minimal Version):** Simple service request form. Creates inbound TroubleCall. No date/time selection — business contacts customer to schedule.

---

# 11. Reporting & Analytics

## 11.1 Dashboard

Key metrics at a glance: Work Orders (open, scheduled, completed, overdue), Quotes (sent, approved, rejected, conversion rate), Invoices (outstanding, overdue, paid this period), Revenue (month, YTD), Assets (total tracked, upcoming maintenance due), Employee activity. Filterable by date range, employee, WO type, customer, status.

## 11.2 Reports

**Work Order Reports:** WO Summary, Completion Rate, Duration (actual vs. estimated), Asset Service Frequency.

**Financial Reports:** Revenue, Expenses (Plus+), Profitability (Pro/Enterprise), Tax Summary, Aging Report (Plus+).

**Employee Reports:** Performance, Time Tracking, Commission (Pro/Enterprise).

**Customer Reports:** Customer List, Service History, Payment History.

**Asset Reports:** Asset Inventory, Warranty Expiration, Maintenance Compliance, Asset Lifecycle Cost.

**Inventory Reports (Plus+):** Inventory Levels, Low Stock Alerts, Inventory Usage, Inventory Value, Fleet/Truck Min. Quantity Report.

## 11.3 Exports

CSV Export — all major entities (all tiers). PDF Export — Quotes, Invoices, WOs (Plus+). Accounting Export — standardized CSV for CPAs (Section 12.1).

---

# 12. Integrations

## 12.1 Accounting Exports (All Tiers)

> **Architectural Boundary:** ServizmaDesk does not support live, two-way API syncs with QuickBooks or Xero. Uses Standardized Accounting Export format.

Pre-formatted for QuickBooks. Exports: Customers/Vendors, Invoices, Payments Received, Purchase Orders/Bills (Plus+). Automated delivery (scheduled email to CPA).

## 12.2 Payment Processing (Stripe)

Stripe Connect (Standard) — each tenant connects their own Stripe account. Payment Links per Invoice. No markup. Webhook processing. PCI SAQ A compliance.

## 12.3 Consumer Financing (Pro/Enterprise)

Wisetack or equivalent. Offer payment plans at point of sale.

## 12.4 Payroll Integration (All Tiers)

ServizmaDesk tracks Employee Time and Commissions. Wage calculation offloaded to third-party payroll providers (Gusto, ADP, QuickBooks Payroll, Standard CSV export).

## 12.5 Other Integrations

Google Calendar (Plus+). SMTP email configuration. Zapier (Pro/Enterprise). Webhooks (Pro/Enterprise). REST API (Pro/Enterprise). Plaid/Finicity — bank feed for Enterprise GL.

---

# 13. Mobile Application

## 13.1 Mobile Access Strategy

**Responsive Web Application:** Full feature parity between desktop and mobile. No native iOS/Android app at launch. PWA capable for home screen installation.

## 13.2 Mobile Features

Schedule Access, Work Order Execution (notes, photos, checklists, signatures), Quoting & Invoicing from mobile, Payment collection. Full mobile web parity on all features.

## 13.3 Offline Mode (Roadmap)

Read-only access to scheduled WOs, customer, and Asset data while offline. Note-taking and photo capture queued for sync. Conflict resolution on reconnection.

---

# 14. Fleet Management (Add-On Module)

## 14.1 Overview

Fleet Management is a paid add-on module for Pro and Enterprise tiers. Flat per-tenant per-month rate.

## 14.2 Vehicle Entity

**Vehicle Fields:** Vehicle Number (V26-0001), Status (Active, Out of Service, Decommissioned), Year, Make, Model, Trim, VIN, License Plate, License State, Color, Vehicle Type, Assigned Driver (FK Employee), Odometer (Current), Purchase Date, Purchase Price, Notes.

**Compliance Fields:** Registration Expiry, Insurance Policy/Provider/Expiry, Inspection dates. Compliance alerts at 30-day, 7-day, and overdue thresholds.

**Vehicle Inventory (VehicleInventory Junction):**
- **Vehicle** — FK Fleet/Vehicle
- **Tool/Product** — FK Equipment or Inventory/Product
- Tracks tools and inventory items carried on each vehicle

## 14.3 Vehicle Maintenance Entity

Maintenance Number (M26-0001), Vehicle (FK), Maintenance Type, Status (Scheduled, Completed, Overdue, Cancelled), Scheduled/Completed Dates, Odometer at Service, Next Service Due (Date and Odometer), Performed By (In-House/External), Vendor Name (FK Vendor), Cost, Description. Maintenance alerts for upcoming service.

## 14.4 Mileage Log Entity

Vehicle (FK), Employee/Driver (FK), Date, Odometer Start/End, Miles Driven (calculated), Trip Purpose, Related Work Order (FK, optional), Notes. Odometer integrity validation.

## 14.5 Fleet Relationships

```
Vehicle (1) ←→ (many) Maintenance Records
Vehicle (1) ←→ (many) Mileage Log Entries
Vehicle (1) ←→ (many) Vehicle Inventory items
Vehicle (many) ←→ (1) Employee [assigned driver]
Vehicle (1) ←→ (many) Documents
Work Order (many) ←→ (0..1) Vehicle [vehicle dispatched for job]
```

---

# 15. Technical Architecture Notes

> **Full technical architecture details are maintained in the ServizmaDesk Technical Architecture V2.** This section provides a summary reference only.

## 15.1 Platform Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12+ |
| Framework | Django 5.x |
| Database | PostgreSQL 16+ |
| Frontend Interactions | HTMX v2.x |
| Styling | Tailwind CSS |
| Web Server | Nginx |
| Application Server | Gunicorn |
| Cloud Provider | DigitalOcean |
| Object Storage | DigitalOcean Spaces |
| Async Worker | Celery |
| Message Broker | Redis (managed, separate from web server) |

## 15.2 Architectural Mandates

1. **UUIDs Only** — All primary and foreign keys use UUIDv4. Auto-incrementing integers prohibited.
2. **Abstracted Pricing** — Products link to Price Tiers / Pricebooks.
3. **One Asset per Work Order** — Multi-asset coordination via WorkGroups.
4. **Parent/Child Architecture** — Asset table includes nullable parent_id for nested equipment.
5. **Tenant Isolation** — Three-layer defense: database constraint → Django middleware → PostgreSQL RLS.
6. **No Vanilla CSS** — Tailwind CSS only.
7. **No SQLite** — PostgreSQL required in all environments.

## 15.3 Asynchronous Processing

Celery + Redis for: 60-day data deletion worker, heavy CSV exports, Stripe webhook processing, PDF generation (Plus/Pro), email delivery.

## 15.4 PDF Generation

- **Lite:** Browser print via CSS Print Media Queries only.
- **Plus:** Server-side PDF via WeasyPrint (Quotes, Invoices, WOs).
- **Pro & Enterprise:** Unrestricted PDF generation.

## 15.5 Communication Architecture

**Email:**
- Platform Email (SDP → Tenant): Postmark
- Tenant Email (SDTA → Customer, Plus+): ServizmaDesk-managed or Bring Your Own SMTP
- Lite: No system email sending

**SMS:** Plus and Pro tiers. Point-based. Provider TBD (Twilio or equivalent).

## 15.6 Payment Architecture

- Platform Billing: Stripe Checkout (never store raw card data)
- Tenant Payment Processing (Plus+): Stripe Connect (Standard)
- PCI DSS: SAQ A — all card data delegated to Stripe

## 15.7 Data Import/Export

Import: Customers, Assets, Products, Work Orders, Custom fields (all CSV). Export: All major entities to CSV (all tiers), QuickBooks-formatted CSV (Plus+), PDF (scope per tier).

---

# 16. Notes & Documents (Exclusive Arc Pattern)

## 16.1 Note Entity

Master internal commentary record. DB-level CHECK constraint enforces exactly one parent FK per row.

**Note Fields:**
- **Note Type** — Enum: Internal Note, Call, Email, Site Visit, Customer Comment, Reminder
- **Body** — Text

**Parent FK Coverage (one required per row):**
- Customer, Contact, Lead, Opportunity, Quote, Invoice, Work Order, Asset, TroubleCall, Preventative Maintenance, WorkFlow, Payment (Customer), Payment (Vendor), Employee/User, Vendor, Purchase Order, Project, Task, Vehicle, Warehouse, Ledger, Requisition, RMA, Equipment, SafetyForms, VendorBills

## 16.2 Document Entity

Master file attachment record. Same exclusive arc pattern as Notes.

**Document Fields:**
- **File Name** — Text
- **File Key** — S3/Spaces key
- **File Size** — Bytes
- **MIME Type** — Text

**Parent FK Coverage:** Same as Notes entity.

---

# 17. Entity Relationship Summary

```
ASSET-CENTRIC ARCHITECTURE
============================

Person (1) ←→ (many) Contacts [permanent identity]
Person (1) ←→ (many) Socials [personal emails, social media]

Contact (many) ←→ (1) Person [required]
Contact (many) ←→ (1) Customer or Vendor [required]
Contact (1) ←→ (many) Phones, Socials

Customer (1) ←→ (many) Contacts
Customer (1) ←→ (many) Phones, Addresses, Socials
Customer (1) ←→ (many) Assets [primary relationship]
Customer (1) ←→ (many) Work Orders
Customer (1) ←→ (many) Quotes, Invoices, Payments
Customer (1) ←→ (many) CustomerAgreements [service agreements]
Customer (1) ←→ (many) Leads, Opportunities
Customer (1) ←→ (many) Banks, Accounting records
Customer (1) ←→ (many) WorkGroups

Asset (many) ←→ (1) Customer [required]
Asset (many) ←→ (1) Address/Location [optional]
Asset (1) ←→ (many) Work Orders [service history — one WO per asset]
Asset (1) ←→ (many) CustomerAgreements [agreement coverage]
Asset (1) ←→ (many) Preventative Maintenance records
Asset (1) ←→ (many) WorkGroupAssets [group membership]
Asset (0..1) ←→ (many) Child Assets [parent/child — Pro/Enterprise]

TroubleCall (many) ←→ (1) Customer [required]
TroubleCall (many) ←→ (0..1) Asset [optional]
TroubleCall (1) ←→ (many) Work Orders [conversion]

Work Order (many) ←→ (1) Customer [required]
Work Order (many) ←→ (1) Asset [required — one asset per WO]
Work Order (many) ←→ (0..1) TroubleCall [originating call]
Work Order (many) ←→ (0..1) WorkFlow [operational procedure]
Work Order (many) ←→ (0..1) Preventative Maintenance [originating PM]
Work Order (many) ←→ (0..1) WorkGroup [dispatch group]
Work Order (many) ←→ (0..1) WG Division [sub-group]
Work Order (many) ←→ (0..1) Vehicle [fleet add-on]
Work Order (many) ←→ (0..1) Project [umbrella]
Work Order (1) ←→ (many) WorkOrderTeam [additional employees]
Work Order (1) ←→ (many) WOLine Items
Work Order (1) ←→ (many) Tasks (subtasks), TaskTimes, TaskToDos
Work Order (1) ←→ (many) Checklist Items
Work Order (1) ←→ (many) Time Entries
Work Order (1) ←→ (many) WOSFAnswers [safety form responses]
Work Order (1) ←→ (many) Quotes, Invoices

WorkGroup (1) ←→ (many) Work Orders
WorkGroup (1) ←→ (many) WorkGroupTeam [team assignments]
WorkGroup (1) ←→ (many) WorkGroupAssets [rolled-up asset list]
WorkGroup (1) ←→ (many) WG Divisions

Agreement (1) ←→ (many) CustomerAgreements
CustomerAgreement (many) ←→ (1) Customer
CustomerAgreement (many) ←→ (1) Agreement
CustomerAgreement (many) ←→ (1) Asset
CustomerAgreement (1) ←→ (many) Preventative Maintenance records

Preventative Maintenance (many) ←→ (1) Asset [required]
Preventative Maintenance (many) ←→ (1) CustomerAgreement [required]
Preventative Maintenance (many) ←→ (1) WorkFlow [required]
Preventative Maintenance (1) ←→ (many) Work Orders [generated]

WorkFlow (1) ←→ (many) WFSteps
WFStep (1) ←→ (many) WFStepToDos
WorkFlow (1) ←→ (many) WFTools [required equipment]
WorkFlow (1) ←→ (many) WF Inventory [required parts]

Lead (many) ←→ (0..1) Customer
Lead (1) ←→ (many) Opportunities
Opportunity (many) ←→ (1) Customer
Opportunity (1) ←→ (many) Oppt-SASSIGNED-Contact
Opportunity (1) ←→ (many) Quotes

Vendor (1) ←→ (many) Contacts, Phones, Addresses [shared triad]
Vendor (1) ←→ (many) Purchase Orders
Vendor (1) ←→ (many) VendorBills
Vendor (1) ←→ (many) Vendor Payments
Vendor (1) ←→ (many) RMAs

Purchase Order (1) ←→ (many) PO Lines
PO Line (1) ←→ (many) Receiving records
PO Line (1) ←→ (many) Lot Info records
PO Line (1) ←→ (many) RMA records

Product (1) ←→ (many) Quote Lines, Invoice Lines, WO Lines, PO Lines
Product (1) ←→ (many) Pricebook Entries
Product (1) ←→ (many) Price History records
Product (1) ←→ (many) Inventory Stock records
Product (1) ←→ (many) Inventory Count records
Product (1) ←→ (many) Inventory Transfer records

Warehouse (1) ←→ (many) Sub-Locations
Warehouse (many) ←→ (1) Employee [van assignments]
Sub-Location (1) ←→ (many) Inventory Stock records

Equipment (1) ←→ (many) Check In/Out records [custody tracking]
Equipment (1) ←→ (many) WFTools [workflow requirements]

Vehicle (1) ←→ (many) Maintenance Records
Vehicle (1) ←→ (many) Mileage Log Entries
Vehicle (1) ←→ (many) Vehicle Inventory items
Vehicle (many) ←→ (0..1) Employee [assigned driver]

Bank (many) ←→ (1) Customer
Bank (1) ←→ (many) Contacts, Phones, Addresses [shared triad]
Carrier (1) ←→ (many) Contacts, Phones, Addresses [shared triad]
Carrier ←→ Accounting

Employee (1) ←→ (many) EmployeeRoles [permission assignments]
Employee (many) ←→ (1) Department
Employee (1) ←→ (many) EmployeeSkills [certifications]
Employee (1) ←→ (many) CreditCards [company cards]
Employee (1) ←→ (many) Phones, Addresses, Socials [shared triad]
Employee (many) ←→ (1) Person [identity via person_id]
```

---

# 18. Tenant Preferences & Settings

## 18.1 Company Information

Company Name, Address, Phone, Email, Website, Logo. Branding used on printed forms, portal, email templates.

## 18.2 Regional & Locale Settings

Default Currency/Symbol, Decimal Precision, Timezone, Date Format, Phone Country Code/Format.

## 18.3 Record Numbering

Configurable prefix and start number for all entity types. Annual reset option. Forward-only constraint against SequenceTracker.

**Numbering Entities:** Customer (C), Asset (A), Work Order (W), Quote (Q), Invoice (I), Payment (P), Project (PJ), Purchase Order (PO), Task (T), Employee (E), Product (XT — reverse alphabet), Vehicle (V), TroubleCall (TC), PM, Agreement, Requisition, RMA, Equipment.

## 18.4 Financial Defaults

Default Tax Rate, Tax Label, Default Payment Terms, Default Quote Expiration Days, Fiscal Year Start Month.

## 18.5 Enterprise Multi-Location (Enterprise)

Multiple business locations with location-specific overrides for tax rate, timezone, numbering prefix.

## 18.6 Email SMTP Configuration

SMTP Host, Port, Username, Password, TLS/SSL toggles, From Name, From Email Address.

---

# 19. Document Relationships

## 19.1 Document Ownership Map

| Data Domain | Owned By |
|---|---|
| Pricing, billing cycles, trials, Founding Partner program, storage pricing, SMS pricing | **Pricing & Billing Specification V2** |
| Tier feature definitions, feature gates, feature comparison matrix | **Product Tier Map V2** |
| Technical stack, infrastructure, tenancy architecture, security | **Technical Architecture V2** |
| Complete functional scope, entity definitions, data model, system workflows | **Top-Down Specifications V2** (this document) |
| Lite-specific module detail, seat counting rules, UI specifications | **Lite MVP Specification** (to be rewritten from this document) |
| Platform provisioning, SDP operations, tenant lifecycle | **Platform (SDP) Specification V2** |

## 19.2 This Document Depends On

- ServizmaDesk Pricing & Billing Specification V2
- ServizmaDesk Product Tier Map V2
- ServizmaDesk Technical Architecture V2
- SD_System_ERD__Base_System_V6.pdf (center of truth)

## 19.3 Documents That Reference This Document

- ServizmaDesk Product Tier Map V2
- ServizmaDesk Lite MVP Specification (to be rewritten)
- ServizmaDesk Plus Specification (future)
- ServizmaDesk Pro Specification (future)
- ServizmaDesk Data Models (to be rewritten from this document)

---

# 20. Tier Feature Mapping (Summary)

> **Note:** This is a high-level summary. Detailed tier specifications are maintained in separate documents. **All pricing is maintained exclusively in the ServizmaDesk Pricing & Billing Specification V2.**

| Feature | Lite | Plus | Pro | Enterprise |
|---|:---:|:---:|:---:|:---:|
| **Core Entities** | | | | |
| Customers | ✓ | ✓ | ✓ | ✓ |
| Assets | ✓ | ✓ | ✓ | ✓ |
| Work Orders (single asset per WO) | ✓ | ✓ | ✓ | ✓ |
| Quotes | ✓ | ✓ | ✓ | ✓ |
| Invoices | ✓ | ✓ | ✓ | ✓ |
| Payments (Customer) | ✓ | ✓ | ✓ | ✓ |
| Products (Catalog) | ✓ | ✓ | ✓ | ✓ |
| Tasks | ✓ | ✓ | ✓ | ✓ |
| TroubleCalls | ✓ | ✓ | ✓ | ✓ |
| Projects | — | ✓ | ✓ | ✓ |
| Purchase Orders | — | ✓ | ✓ | ✓ |
| Vendors | — | ✓ | ✓ | ✓ |
| VendorBills | — | ✓ | ✓ | ✓ |
| Vendor Payments | — | ✓ | ✓ | ✓ |
| Requisitions | — | ✓ | ✓ | ✓ |
| RMA | — | ✓ | ✓ | ✓ |
| **CRM Pipeline** | | | | |
| Leads | — | ✓ | ✓ | ✓ |
| Opportunities | — | ✓ | ✓ | ✓ |
| Opportunity Assigned Contacts | — | ✓ | ✓ | ✓ |
| **Asset Features** | | | | |
| Asset tracking | ✓ | ✓ | ✓ | ✓ |
| Warranty tracking | ✓ | ✓ | ✓ | ✓ |
| Nested Assets (parent/child) | — | — | ✓ | ✓ |
| QR Code scanning | — | — | ✓ | ✓ |
| **Service Agreements & PM** | | | | |
| Agreements | — | ✓ | ✓ | ✓ |
| CustomerAgreements | — | ✓ | ✓ | ✓ |
| Preventative Maintenance | — | ✓ | ✓ | ✓ |
| Auto-Generate Work Orders from PM | — | ✓ | ✓ | ✓ |
| Plan Tiers (Silver/Gold/Plat) | — | — | ✓ | ✓ |
| Recurring Billing on Agreements | — | — | ✓ | ✓ |
| **WorkGroups & Dispatch** | | | | |
| WorkGroups | — | ✓ | ✓ | ✓ |
| WorkGroupTeam | — | ✓ | ✓ | ✓ |
| WG Divisions | — | — | ✓ | ✓ |
| WorkOrderTeam (multi-employee) | ✓ | ✓ | ✓ | ✓ |
| **WorkFlow Engine** | | | | |
| WorkFlow (full SOP) | — | — | ✓ | ✓ |
| WFSteps / WFStepToDos | — | — | ✓ | ✓ |
| WFTools / WF Inventory | — | — | ✓ | ✓ |
| Custom Status Workflows | — | — | ✓ | ✓ |
| **Work Order Features** | | | | |
| Checklists | ✓ | ✓ | ✓ | ✓ |
| Checklist Templates | ✓ | ✓ | ✓ | ✓ |
| Recurring Work Orders | — | ✓ | ✓ | ✓ |
| Time Tracking | ✓ | ✓ | ✓ | ✓ |
| **Quoting** | | | | |
| E-Signature / Online Approval | — | ✓ | ✓ | ✓ |
| Deposit Collection | — | ✓ | ✓ | ✓ |
| Good/Better/Best Proposals | — | — | ✓ | ✓ |
| **Invoicing** | | | | |
| Recurring Invoices | — | ✓ | ✓ | ✓ |
| Commission Tracking | — | — | ✓ | ✓ |
| **Inventory** | | | | |
| Product Catalog | ✓ | ✓ | ✓ | ✓ |
| Inventory Tracking | — | ✓ | ✓ | ✓ |
| Inventory Counts | — | ✓ | ✓ | ✓ |
| Inventory Transfers | — | ✓ | ✓ | ✓ |
| Receiving (detailed) | — | ✓ | ✓ | ✓ |
| Serialized Inventory | — | — | ✓ | ✓ |
| Multi-Location Inventory | — | — | ✓ | ✓ |
| Warehouse (location type) | — | ✓ | ✓ | ✓ |
| Price Tiers / Pricebooks | — | — | ✓ | ✓ |
| Price History | — | ✓ | ✓ | ✓ |
| Lot Tracking | — | — | ✓ | ✓ |
| Bundles | ✓ | ✓ | ✓ | ✓ |
| **Financial** | | | | |
| Basic Income Ledger | ✓ | ✓ | ✓ | ✓ |
| Advanced AR/AP | — | ✓ | ✓ | ✓ |
| Banks | — | ✓ | ✓ | ✓ |
| Carriers | — | ✓ | ✓ | ✓ |
| Accounting Entity | — | ✓ | ✓ | ✓ |
| Chart of Accounts / GL | — | — | ✓ | ✓ |
| Full ERP Accounting | — | — | — | ✓ |
| **Safety & Compliance** | | | | |
| SafetyForms | — | — | ✓ | ✓ |
| WOSFAnswers | — | — | ✓ | ✓ |
| Custom Forms | — | — | ✓ | ✓ |
| **Employee Management** | | | | |
| Skills / EmployeeSkills | — | — | ✓ | ✓ |
| Equipment / Check In-Out | — | — | ✓ | ✓ |
| Positions | — | ✓ | ✓ | ✓ |
| Departments | ✓ | ✓ | ✓ | ✓ |
| CreditCards | — | — | ✓ | ✓ |
| Custom Roles | — | — | ✓ | ✓ |
| **Scheduling** | | | | |
| Calendar Views | — | ✓ | ✓ | ✓ |
| Drag-and-Drop Scheduling | — | ✓ | ✓ | ✓ |
| Map View | — | — | ✓ | ✓ |
| Smart Assignment | — | — | ✓ | ✓ |
| Route Optimization | — | — | — | ✓ |
| **Communication** | | | | |
| SMS (point-based) | — | ✓ | ✓ | ✓ |
| System Email (managed) | — | ✓ | ✓ | ✓ |
| System Email (BYOSMTP) | — | ✓ | ✓ | ✓ |
| **Customer Portal** | | | | |
| Online Booking (basic request) | ✓ | ✓ | ✓ | ✓ |
| Customer Portal (full) | — | ✓ | ✓ | ✓ |
| **Automation** | | | | |
| Automation Rules | — | 2–5 | Unlimited | Unlimited |
| Zapier Integration | — | — | ✓ | ✓ |
| Webhooks | — | — | ✓ | ✓ |
| REST API | — | — | ✓ | ✓ |
| **Reporting** | | | | |
| Dashboard | ✓ | ✓ | ✓ | ✓ |
| Standard Reports | ✓ | ✓ | ✓ | ✓ |
| Advanced Reports | — | ✓ | ✓ | ✓ |
| Custom Reports | — | — | ✓ | ✓ |
| **Integrations** | | | | |
| Stripe Payment Links | ✓ | ✓ | ✓ | ✓ |
| Standardized Accounting Export | ✓ | ✓ | ✓ | ✓ |
| Consumer Financing | — | — | ✓ | ✓ |
| Google Calendar | — | ✓ | ✓ | ✓ |
| **Add-On Modules** | | | | |
| Fleet Management (add-on) | — | — | + | + |

> **Pricing:** See ServizmaDesk Pricing & Billing Specification V2 for all tier pricing.

---

**End of ServizmaDesk Top-Down Specifications V2**
