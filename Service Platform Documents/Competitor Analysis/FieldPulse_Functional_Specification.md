# FieldPulse Functional Specification
**Detailed Product Structure & Data Model Documentation**

**Date:** March 2026  
**Classification:** Internal — Competitive Intelligence  
**Purpose:** Complete functional specification for head-to-head comparison with ServizmaDesk

---

# Document Purpose

This document provides a complete functional specification of FieldPulse's data model, features, workflows, and user interface structure. This is NOT a competitive analysis — it is a pure specification document that will be used to create a separate comparison document.

---

# 1. Data Model & Core Entities

## 1.1 Customer Entity

### Customer Record Structure

**Primary Fields:**
- **Status** — Dropdown (pipeline-based)
  - Values: Lead, Opportunity, Active, Inactive (customizable)
- **Account Type** — Dropdown
  - Values: Residential, Commercial
- **Assigned To** — Dropdown (team member assignment)
- **Lead Source** — Dropdown (customizable list)
- **Pipeline Status** — Dropdown (customizable workflow statuses)
- **Tax Exempt** — Toggle (on/off)

**Primary Contact Fields:**
- **First Name** — Text
- **Last Name** — Text
- **Company Name** — Text
- **Email** — Email (primary)
- **Alternate Email** — Email (optional)
- **Phone Number** — Phone (primary)
- **Alternate Phone** — Phone (optional)

**Address Fields:**
- **Service Address** — Full address (street, city, state, ZIP)
- **Billing Address** — Full address (optional separate address)
  - Toggle: "Use Separate Billing Address"

**Additional Contacts:**
- Can add multiple contacts linked to primary customer
- Each additional contact has: First Name, Last Name, Email, Phone
- Import capability via CSV template

**Additional Locations:**
- Can add multiple service locations linked to primary customer
- Each location has: Name (user-defined), Full Address
- Import capability via CSV template

**Tags:**
- Free-text tags for categorization and filtering
- Multiple tags per customer
- No predefined tag list

**Notes:**
- **Internal Notes** — Not visible to customer
- **Files/Attachments** — Upload documents, photos
- **Contracts** — Attach contract documents

**Custom Fields:**
- Unlimited custom fields can be created
- Field types:
  - Free text
  - Number
  - Date (with calendar picker)
  - Checkbox (toggle)
  - Dropdown (custom options)
- Visibility by role (Admin, Team Manager, Service Agent)
- Mass import capability for custom field data

**Related Records (Linked to Customer):**
- Job records
- Estimate records
- Invoice records
- Payment records
- Customer comments
- Photos/documents
- Communication history (emails, calls, messages)
- Service history timeline

---

## 1.2 Job Entity

### Job Record Structure

**Core Job Fields:**
- **Job Number** — Auto-generated sequential number
- **Customer** — Link to Customer record (required)
- **Related Project** — Link to Project (optional)
- **Job Status** — Dropdown
  - Default statuses: Draft, Scheduled, In Progress, Completed, Cancelled
  - **Custom Status Workflows** — Configurable per business
    - Example: "Permit Pending", "Material Ordered", "Awaiting Inspection"
  - Custom statuses can be created for specific service types
- **Assigned To** — Team member(s) assignment
  - Can assign multiple technicians to one job
- **Priority** — Dropdown (Low, Normal, High, Urgent)
- **Scheduled Date/Time** — Date and time picker
- **Estimated Duration** — Time estimate
- **Job Type** — Dropdown (customizable service categories)
- **Location** — Defaults to customer service address, can override

**Job Description:**
- **Title/Summary** — Short description
- **Detailed Description** — Long-form text field
- **Internal Notes** — Not visible to customer
- **Customer-Facing Notes** — Visible in customer portal

**Subtasks:**
- Can create multiple subtasks within a job
- Each subtask has:
  - Task name
  - Assigned to (team member)
  - Status
  - Due date
  - Notes
- Subtask progress tracking
- Can mark subtasks as "manager-only visible"

**Recurring Jobs:**
- Toggle: "Make this job recurring"
- Recurrence options:
  - Daily
  - Weekly
  - Monthly
  - Quarterly
  - Annual
  - Custom interval
- Auto-generate future jobs based on schedule

**Time Tracking:**
- **Clock In/Out** — GPS-stamped time tracking
- **Time Sheets** — View time by job, team member, or date range
- **Arrival/Departure Times** — Automatic GPS logging
- **Total Hours** — Calculated automatically
  - **Known Limitation:** Shows total hours per employee on job, not daily breakdown

**Custom Fields on Jobs:**
- Can create unlimited custom fields for job records
- Same field types as Customer custom fields
- Separate from Customer custom fields

**Attachments:**
- **Photos** — Upload from mobile or desktop
  - Before/After photo capability
- **Files** — PDF, documents, etc.
- **Forms** — Custom form attachments (PDF Form Filler)
- **Contracts** — Attach signed contracts

**Related Records:**
- **Estimates** — Linked estimate(s)
- **Invoices** — Linked invoice(s)
- **Work Orders** — Generated PDF work orders
- **Purchase Orders** — Related PO records
- **Assets** — Linked equipment/assets

---

## 1.3 Project Entity

### Project Structure

**Purpose:** Group multiple jobs under a single umbrella for complex/multi-phase work

**Project Fields:**
- **Project Name** — Text
- **Customer** — Link to Customer record
- **Project Status** — Dropdown
  - Default: Planning, In Progress, On Hold, Completed, Cancelled
- **Start Date** — Date picker
- **Target Completion Date** — Date picker
- **Project Manager** — Assigned team member
- **Budget** — Currency field
- **Actual Cost** — Calculated from linked jobs
- **Completion Percentage** — Manual or auto-calculated

**Project Components:**
- **Grouped Jobs** — Multiple jobs linked to project
- **Timeline Tracking** — Gantt chart view of project schedule
- **Task Management** — Prioritize and delegate tasks
- **Cost Tracking** — Real-time labor, materials, overhead
- **Profitability Monitoring** — Track margin throughout project
- **Custom Financial Reports** — Per-project reporting

**Project-Level Features:**
- **Multi-day support** — Jobs spanning multiple visits/phases
- **Team collaboration** — Communication between field and office
- **Real-time updates** — Task progress visible to all stakeholders

---

## 1.4 Estimate Entity

### Estimate Record Structure

**Header Fields:**
- **Estimate Number** — Auto-generated sequential
- **Customer** — Link to Customer record (required)
- **Related Job** — Link to Job (optional)
- **Related Project** — Link to Project (optional)
- **Estimate Date** — Date picker (defaults to today)
- **Expiration Date** — Date picker (configurable default in settings)
- **Assigned To** — Team member who created/owns estimate

**Estimate Status:**
- **Draft** — Being created
- **Sent** — Sent to customer (auto-updated)
- **Viewed** — Customer opened estimate (tracked)
- **Accepted** — Customer accepted
- **Rejected** — Customer rejected
- **Expired** — Past expiration date
- Manual statuses for tracking post-decision process

**Line Items:**
- **Add from Item List** — Pull from pre-defined inventory
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
- **Unit Cost** — Currency (internal cost)
- **Unit Price** — Currency (customer price)
- **Markup** — Percentage or fixed amount
- **Quantity** — Number
- **Taxable** — Toggle (yes/no)
- **Visible to Customer** — Toggle (can hide line items)
- **Track Inventory** — Toggle (decrement stock on use)

**Line Item Organization:**
- **Groupings** — Group items with title and subtotal
  - Can hide individual item names/prices from customer
  - Show only group total
- **Bundles** — Pre-configured sets of items
  - Saved bundles can be inserted with one click
- **Add-Ons** — Optional items customer can select
  - Create "add-on options" customers can choose

**Estimate Options (Good/Better/Best Pricing):**
- **Dynamic Proposals** — Multiple pricing tiers
- **Add Estimate Option** — Create multiple estimate variants
- Customer sees options side-by-side and selects preferred
- Requires Dynamic Proposals add-on

**Subtotal Calculations:**
- **Line Item Subtotal** — Sum of all line items
- **Discounts** — Percentage or fixed amount
- **Surcharges** — Additional fees
- **Tax** — Applied to taxable items only
  - Default tax rate from settings
  - Can override per-estimate
- **Credit Card Fee** — Percentage or fixed amount
  - Display separately or roll into total
- **Grand Total** — Final amount

**Notes & Attachments:**
- **Estimate Notes** — Visible to customer on PDF
- **Internal Notes** — Not visible to customer
- **Files** — Attach supporting documents
- **Contracts** — Attach contract for signature

**Templates:**
- **Save as Template** — Toggle when creating estimate
- Templates include:
  - All line items
  - Groupings and bundles
  - QuickBooks class (if using QB integration)
  - Tags
  - Custom fields
  - Notes
  - Contract attachments
- **Import Template** — Select saved template when creating new estimate

**Estimate PDF Customization:**
- Company information (logo, address, contact)
- Verbiage customization (call it "Quote", "Proposal", etc.)
- Show/hide fields:
  - Item SKU
  - Item description
  - Unit cost (typically hidden)
  - Unit price
  - Quantity
  - Line item subtotals
  - Tax breakdown
  - Payment terms
- Header/footer customization

**Conversion:**
- **Convert to Invoice** — One-click conversion
  - Transfers all line items, customer info, job link
  - Can optionally keep estimate record (configurable in settings)
  - Default: Estimate record is deleted on conversion

---

## 1.5 Invoice Entity

### Invoice Record Structure

**Header Fields:**
- **Invoice Number** — Auto-generated sequential
- **Customer** — Link to Customer record (required)
- **Related Job** — Link to Job (optional)
- **Related Project** — Link to Project (optional)
- **Invoice Date** — Date picker (defaults to today)
- **Due Date** — Date picker
  - Auto-populate methods (configurable):
    - Based on Creation Date + N days
    - Based on Sent Date + N days
    - Based on Job Completion + N days
    - Manual entry
- **Assigned To** — Team member

**Invoice Status:**
- **Draft** — Being created
- **Sent** — Sent to customer
- **Viewed** — Customer opened invoice (tracked)
- **Partially Paid** — Partial payment received
- **Paid** — Full payment received (auto-updated)
- **Overdue** — Past due date, unpaid
- **Cancelled** — Invoice voided

**Line Items:**
- **Identical structure to Estimates**
- Can pull from Item List or create new
- Bundles and groupings supported
- Visibility controls per line item

**Line Item Fields:**
- Same as Estimate line items
- Plus: **QuickBooks Class** (if using QB integration)

**Recurring Invoices:**
- **Toggle: Make Recurring**
- Recurrence options:
  - Weekly
  - Monthly
  - Quarterly
  - Annual
  - Custom interval
- Auto-generate and optionally auto-send

**Payment Features:**
- **Record Manual Payment** — Cash, check, other
- **FieldPulse Payments** — Integrated credit card processing
  - 2.9% processing fee (reported by users)
- **Payment Requests** — Send payment link via email/SMS
- **Partial Payments** — Record multiple payments against invoice
- **Down Payments** — Collect deposit before work starts

**Subtotal Calculations:**
- **Line Item Subtotal**
- **Discounts** — Percentage or fixed amount (added in FieldPulse updates)
- **Surcharges** — Additional fees (added in FieldPulse updates)
- **Tax** — Configurable tax rate
  - Can use different tax labels: Tax, HST, GST, VAT
- **Credit Card Fee** — If customer paying via card
- **Total Due**
- **Amount Paid**
- **Balance Due**

**Commission Tracking:**
- **Enable Commission Calculations** — Toggle in settings
- Methods:
  - Percentage of gross sales
  - Percentage of gross margin
- Default rate configurable
- Can override per invoice

**Automatic Markup:**
- **Enable/Disable in settings**
- Apply markup based on:
  - Unit cost × markup percentage = unit price
- Auto-calculates pricing

**Notes & Attachments:**
- **Invoice Notes** — Visible to customer
- **Internal Notes** — Hidden from customer
- **Files** — Supporting documents
- **Contracts** — For signature

**Templates:**
- **Save as Invoice Template** — Toggle when creating
- **Import Template** — Load pre-configured invoice structure

**Invoice PDF Customization:**
- Same customization options as Estimates
- Additional fields:
  - Payment terms
  - Due date
  - Amount paid / balance due

**Generation from Estimates:**
- **Convert Estimate to Invoice** — Most common method
- Transfers all line items and details
- Option to preserve estimate record

**Generate Work Order from Invoice:**
- **Actions → Generate Work Order PDF**
- Creates PDF with scope of work, no pricing
- Can attach to existing job or create new job
- Options:
  - Download PDF
  - Send to be filled (e-signature)
  - Open in PDF Form Filler

---

## 1.6 Item List (Product/Service Catalog)

### Item Repository Structure

**Purpose:** Central catalog of all products and services offered

**Item Fields:**
- **Item Name** — Text (required)
- **Type** — Dropdown (required)
  - **Service** — Labor, service work
  - **Product - Inventory** — Track stock levels
  - **Product - Non-Inventory** — Don't track stock
- **SKU** — Text (optional)
- **Unit Cost** — Currency (what you pay)
- **Unit Price** — Currency (what you charge)
- **Markup** — Calculated (Price - Cost / Cost × 100)
- **Description** — Long-form text
- **Taxable** — Toggle (yes/no)
- **Track Inventory** — Toggle (yes/no)
  - Only available for "Product - Inventory" type
  - If enabled, stock decrements when used on invoice

**Inventory Tracking (if enabled):**
- **Quantity on Hand** — Number
- **Reorder Point** — Trigger for low stock alert
- **Reorder Quantity** — How much to order
- **Preferred Vendor** — Link to vendor (if using vendor management)
- **Location/Hub** — Where item is stored
  - Multiple locations supported (multi-location feature)
  - Track inventory per location
  - Track inventory per truck

**Serialized Inventory:**
- **Toggle: Serialized Item**
- Each unit has unique serial number
- Track:
  - Serial number
  - Where stored (hub/truck)
  - When installed
  - Which technician used it
  - Which customer received it
  - Warranty coverage
  - Maintenance schedule
- Auto-decrement when invoiced by serial number

**Price Tiers:**
- **Customer-Specific Pricing**
- Create multiple price tiers:
  - Residential Standard
  - Commercial Standard
  - Preferred Customer
  - Contractor Discount
  - etc.
- Two pricing methods:
  - **Item Price Range** — Markup/discount based on item price/cost
  - **Flat Markup/Discount** — Fixed percentage for tier
- Price tier assigned to customer
- Auto-applies tier pricing on estimates/invoices
- Can override per line item

**Custom Fields on Line Items:**
- Can add custom fields to track additional data
- Field types: Text, Number, Date, Dropdown, Checkbox
- Visibility controls (customer-facing or internal only)

**Mass Import:**
- Import items via CSV template
- Template includes all standard fields
- Can import serialized inventory (requires hubs already created)

**Pricebook Integration:**
- **Pricebook** — Add-on feature or included in higher tiers
- Pre-built pricebooks for common services
- "Flat-rate pricing" capability
- Select equipment/service, auto-populates pricing

---

## 1.7 Payment Entity

### Payment Record Structure

**Payment Types:**
- **Credit Card** — Via FieldPulse Payments integration
- **Cash**
- **Check**
- **Bank Transfer**
- **Other** — Custom payment method

**Payment Fields:**
- **Payment Date** — Date received
- **Amount** — Currency
- **Payment Method** — Dropdown (see types above)
- **Reference Number** — For check/transfer tracking
- **Applied To** — Link to Invoice(s)
  - Can split payment across multiple invoices
- **Notes** — Internal notes about payment

**FieldPulse Payments Integration:**
- **Integrated credit card processing**
- **Reported fee:** 2.9% + per-transaction fee
- **CardConnect** — Payment processor
  - **Canadian Limitation:** $1,500 transaction limit
- **Payment Link** — Send link to customer for online payment
- **On-site Payment** — Collect payment via mobile app
- **Automatic Status Update** — Invoice marked paid when payment received

**Customer Financing:**
- **Third-party integrations:**
  - Wisetack
  - FieldPulse Capital
  - Acorn Finance (not available in Canada)
- Offer financing to customers at point of sale
- Approval and terms managed by financing partner

**Payment Tracking:**
- **Payment history per customer**
- **Payment status on invoices**
- **Aging reports** — Track overdue invoices
- **Payment reminders** — Automated reminders for unpaid invoices

---

## 1.8 Asset/Equipment Entity

### Asset Management Feature

**Purpose:** Track customer-owned equipment for maintenance and service

**Asset Fields:**
- **Asset Name/Type** — Equipment description (e.g., "Rooftop HVAC Unit")
- **Make** — Manufacturer
- **Model** — Model number
- **Serial Number** — Unique identifier
- **Installation Date** — Date picker
- **Warranty Start** — Date picker
- **Warranty End** — Date picker
- **Location** — Physical location at customer site
  - Can link to specific customer address if multi-location
- **Status** — Active, Inactive, Decommissioned
- **Notes** — Equipment-specific notes

**Asset Relationships:**
- **Linked to Customer** — Required relationship
- **Service History** — All jobs/work orders related to this asset
- **Maintenance Agreements** — Recurring maintenance linked to asset
- **Documents** — Manuals, warranties, spec sheets
- **Photos** — Equipment photos

**Maintenance Agreements:**
- **Attach maintenance packages to assets**
- Create tiered plans:
  - Silver, Gold, Platinum levels
  - Custom tier names
  - Different services per tier
- **Schedule reminders** — Auto-remind for next service
- **Convert to Work Orders** — One-click WO generation from agreement

**Asset Tracking Limitations:**
- **Not asset-centric** — Assets are tracked *within* jobs, not jobs organized *around* assets
- Assets are an optional feature, not the core data model
- Equipment tracking is secondary to job tracking

---

## 1.9 Purchase Order Entity

### Purchase Order Structure

**PO Fields:**
- **PO Number** — Auto-generated
- **Vendor** — Supplier/vendor reference
- **Related Job** — Link to job (optional)
- **Order Date** — Date picker
- **Expected Delivery Date** — Date picker
- **Status** — Draft, Sent, Received, Cancelled

**PO Line Items:**
- **Item** — From item list or create new
- **Quantity** — Number ordered
- **Unit Cost** — Cost per unit
- **Total** — Calculated

**Custom Fields on PO Line Items:**
- Unlimited custom fields
- Field types: Text, Number, Date, Dropdown, Checkbox
- Common examples:
  - **Item Status** — "Not Arrived", "Dispatched", "Arrived", "Returned"
  - **Related Job** — Link specific line item to job (in addition to PO-level job link)
  - **Return Toggle** — Mark items for return
- **Visibility controls:**
  - By role (Service Agent, Team Manager, Admin)
  - Customer/Supplier visibility toggle

**PO Creation:**
- **Create from web app**
- **Create from mobile app** — "Create PO on the go"
- **From job site** — Technician can create PO for missing parts

**Enable/Disable Settings:**
- **PO Creation Based on Item Vendors** — Toggle in settings
- Auto-suggest PO creation when adding items with assigned vendors

---

## 1.10 Vendor/Supplier Entity

**Vendor Fields:**
- **Vendor Name** — Text
- **Contact Name** — Text
- **Email** — Email
- **Phone** — Phone
- **Address** — Full address
- **Notes** — Vendor-specific notes

**Vendor Relationships:**
- **Items** — Products sourced from this vendor
  - Preferred vendor per item in item list
- **Purchase Orders** — PO history with vendor
- **Invoices** — Supplier invoices received (for cost tracking)

**Supplier Invoice Tracking:**
- Track actual job costs by recording supplier invoices
- Compare estimated cost vs. actual cost
- Job profitability analysis

---

# 2. Scheduling & Dispatch

## 2.1 Schedule/Calendar Views

### Calendar Interface

**View Options:**
- **Daily View** — Single day, all team members
- **Weekly View** — Week at a glance
- **Technician View** — Per-technician schedule
- **Gantt Chart View** — Project timelines
- **Map View** — Geographic view of scheduled jobs

**Drag-and-Drop Scheduling:**
- **Move jobs** — Drag to different date/time/technician
- **Resize** — Adjust job duration
- **Color-coding** — By job status, priority, or custom tags

**Dispatch Availability:**
- **Working Hours** — Set per technician
- **Time Off** — Block out unavailable times
- **Skills/Certifications** — Match jobs to qualified techs

**Real-Time Updates:**
- **Instant sync** — Changes visible to office and field immediately
- **Push notifications** — Alert techs to schedule changes
- **GPS tracking** — See tech location in real-time

## 2.2 Job Assignment

### Assignment Methods

**Manual Assignment:**
- **Drag-and-drop** — Assign job to technician via calendar
- **From job record** — Select assigned technician(s)
- **Multiple technicians** — Assign multiple techs to one job

**Rule-Based Assignment:**
- **Automated scheduling** — Based on:
  - Technician skills
  - Availability
  - Proximity to job site (GPS-based)
  - Current workload

**Limitations:**
- **No intelligent routing** — No AI-powered optimization
- **Manual dispatching** — Dispatcher must assign each job
- **No automated route optimization** — Techs don't get optimized routes

## 2.3 Route Planning

### GPS & Location Features

**GPS Tracking:**
- **Real-time location** — Track techs in field
- **Arrival/Departure** — Auto-log arrival at job site
- **Travel time calculation** — Basic travel time estimates
- **Manual route planning** — Dispatcher plans routes manually

**Mobile Notifications:**
- **"On the Way" Alerts** — Auto-notify customer when tech dispatched
- **Arrival window** — Give customer arrival time window
- **Customer arrival window** — Custom field on job for expected arrival

**Route Optimization:**
- **No automated optimization** — Users report this as missing feature
- **Manual route planning** — Dispatcher arranges jobs by geography

---

# 3. Mobile Application

## 3.1 Mobile App Capabilities

### Core Mobile Features

**Schedule Access:**
- **View schedule** — Daily, weekly view
- **See job details** — Customer, location, notes, attachments
- **Update job status** — In transit, arrived, in progress, complete
- **Clock in/out** — GPS-stamped time tracking

**Job Execution:**
- **Access customer info** — Full customer record, service history
- **Add notes** — Job-specific notes
- **Capture photos/videos** — Before/after documentation
- **Signature capture** — Customer sign-off
- **Upload to job record** — Photos, forms, signatures

**Estimates & Invoices:**
- **Create estimates** — Full estimate creation from mobile
  - Pull from item list
  - Insert bundles
  - Add groupings
  - Create add-ons
  - Multiple estimate options
- **Convert to invoice** — Tap to convert accepted estimate
- **Create invoices** — Full invoice creation
- **Collect payments** — Credit card processing via mobile
  - Stripe/CardConnect integration
  - Cash/check recording

**Inventory Management:**
- **Barcode scanning** — Scan items to update inventory
- **Check stock levels** — View inventory on hand
- **Transfer stock** — Move items between trucks/locations
- **Create purchase orders** — Order parts from field

**Offline Mode:**
- **Claimed capability:** Work offline, sync when online
- **User-reported issues:**
  - "Unreliable offline mode"
  - "Data loss in areas with poor coverage"
  - Multiple reports of offline failures
  - Recommendation: Don't rely on offline mode for critical data

### Mobile App Issues (User-Reported)

**UI/UX Problems:**
- "Not user-friendly"
- "Cramped interface"
- "Too many taps" to complete actions
- Photo upload bugs
- Tax options limited on mobile
- Schedule view doesn't display well on mobile

**Functionality Issues:**
- Offline mode unreliable
- Sync failures
- Data loss reports

---

# 4. Customer Communication & Portal

## 4.1 Communication Hub

### Unified Communication

**Communication Channels:**
- **Email** — Send/receive from within app
- **SMS** — Text messaging (separate from FieldPulse Engage VoIP)
- **Phone Calls** — Track call history (if using Engage)
- **All in one view** — Unified inbox for all customer communication

**Communication Features:**
- **Real-time notifications** — Alert when customer responds
- **Customer-specific notes** — Add context for team members
- **Communication history** — Full timeline of interactions

**Automated Communications:**
- **Post-job follow-ups** — Thank you, feedback requests
- **Review requests** — Auto-request reviews after job completion
- **Appointment reminders** — Auto-remind customers of scheduled jobs
- **Payment reminders** — Auto-send reminders for unpaid invoices
- **Maintenance reminders** — Remind customers of recurring services
- **Trigger-based workflows** — Customize when messages send

**FieldPulse Engage (VoIP Add-On):**
- **Business phone system**
- **Personal or shared numbers** — Keep personal numbers private
- **Call forwarding** — Forward calls to team
  - **Reported Issue:** "Can't forward to multiple people" — workflow bottleneck
- **Voicemail** — Store customer voicemails in app
- **Text messages** — Store SMS in app
- **Reported as "unstable and limited"** by users

## 4.2 Customer Portal

### Portal Features

**Customer Self-Service:**
- **Online booking** — Customers book appointments
- **Service requests** — Submit service requests 24/7
- **View service history** — See past jobs and invoices
- **Approve estimates** — E-signature for estimate acceptance
- **Pay invoices** — Online payment via Stripe/CardConnect
- **Request services** — Schedule maintenance, new work
- **Communication** — Message directly with business

**Smart Dispatch:**
- Part of customer booking portal
- Auto-assign jobs based on availability and location

**Portal Customization:**
- Portal URL: yourcompany.fieldpulse.com (or custom domain)
- Branding: Logo, colors (degree of customization unclear from sources)

---

# 5. Reporting & Analytics

## 5.1 Dashboard & Widgets

### Dashboard Features

**Customizable Dashboard:**
- **Drag-and-drop widgets** — Build custom views
- **Real-time data** — Live updates
- **Multiple dashboard views** — Create different dashboards for different roles

**Key Metrics Tracked:**
- **Jobs** — Open jobs, jobs today, completed jobs
- **Quotes/Estimates** — Sent, accepted, conversion rate
- **Invoices** — Open invoices, overdue, paid
- **Revenue** — This month, year-to-date
- **Team performance** — Jobs per tech, completion rates
- **Customer activity** — New customers, active customers

**Filtering:**
- By date range
- By team member
- By job type
- By customer
- By status

## 5.2 Reports

### Available Reports

**Job Reports:**
- **Job Profit Margin** — Detailed cost/profit by job
  - Line-item costs
  - Added expenses
  - Final invoice total
  - Margin calculation
- **Job Duration vs. Schedule** — Actual vs. estimated time
- **Job Status Summary** — Jobs by status
- **Subtask-Level Reports** — Track delays, reassign work

**Financial Reports:**
- **Revenue Reports** — By period, by service type, by customer
- **Expense Reports** — Track costs, compare to budget
- **Profitability Reports** — Margin analysis
- **Sales Tax Calculations** — Simplified tax reporting
  - **Praised feature:** "Significantly reduced manual work"
  - Auto-calculate tax owed

**Team Performance:**
- **Technician Performance** — Jobs completed, hours worked, revenue generated
- **Team Comparison** — Compare performance across team members
- **Time tracking reports** — Clock in/out, job duration
  - **Known limitation:** Only shows total hours on job, not daily breakdown

**Customer Reports:**
- **Customer List** — Exportable customer database
- **Service History** — Per-customer service timeline
- **Payment History** — Customer payment patterns

**Inventory Reports:**
- **Inventory Levels** — Quantity on hand by item
- **Low Stock Alerts** — Items below reorder point
- **Inventory Usage** — Parts used by job, by technician
- **Inventory Value** — Total value of inventory

**Report Limitations:**
- **Standard needs only** — "Works well for standard needs"
- **Falls short for deep analytics** — "Not suitable for detailed performance metrics"
- **Limited customization** — Canned reports, limited custom report builder

## 5.3 Exports

**Export Capabilities:**
- **CSV Export** — Most lists can be exported to CSV
  - Customers
  - Jobs
  - Estimates
  - Invoices
  - Payments
  - Items
  - Inventory
- **PDF Export** — Estimates, invoices, work orders
- **QuickBooks Sync** — Push to accounting system
  - **Major reported issue:** "Terrible", "buggy", "duplicate entries"

---

# 6. Integrations

## 6.1 Accounting Integrations

### QuickBooks

**QuickBooks Online:**
- **Sync entities:**
  - Customers
  - Line items (products/services)
  - Estimates
  - Invoices
  - Payments
- **Two-way sync** — Changes in either system reflect in the other
- **QuickBooks Class** — Map transactions to QB classes
- **User rating:** 4.2/5 for QB Online integration

**QuickBooks Desktop:**
- **Same sync capabilities as Online**
- **User-reported issues:**
  - "Terrible" integration
  - "Buggy"
  - "Not seamless"
  - "Scattered data"
  - "Duplicate entries"
  - Users resort to double-entry workarounds
  - **Called FieldPulse's "Achilles heel"** in multiple reviews

**Xero:**
- Similar sync capabilities to QuickBooks
- Customers, line items, invoices, payments
- User reports less clear on quality

**MYOB:**
- Australia only
- Similar sync capabilities

### Reported Integration Problems

**QuickBooks Issues (Extensive User Complaints):**
- Data doesn't sync correctly
- Duplicate customer entries
- Scattered transaction data
- Missing transactions
- Manual reconciliation required
- **User quote:** "You're an FSM, not an ERP, so you HAVE to play nice with accounting software. QBO sucks rocks."
- **Multiple users report:** Just double-entering everything manually

## 6.2 Payment Processing

**CardConnect:**
- Built-in payment processor
- 2.9% fee (reported)
- **Canadian limitation:** $1,500 transaction limit
  - Blocks large invoices in Canada

**Stripe:**
- Mentioned in comparisons
- Unclear if native integration or via CardConnect

**Square:**
- Mentioned in comparisons
- Native integration unclear

**Clover Connect:**
- Payment processing option

**Payrix:**
- Payment processing option

## 6.3 Other Integrations

**Communication:**
- **Mailchimp** — Email marketing
- **NiceJob** — Review management
- **CHIIRP** — Customer communication automation
- **HighLevel** — CRM/marketing automation

**Photo/Documentation:**
- **CompanyCam** — Photo documentation
  - **Highly praised integration** by users

**Fleet Tracking:**
- **Azuga Fleet Tracking** — $30/vehicle/month add-on
  - Real-time GPS
  - Route tracking
  - Vehicle diagnostics

**Financing:**
- **Wisetack** — Customer financing
- **FieldPulse Capital** — In-house financing option
- **Acorn Finance** — Not available in Canada

**Answering Services:**
- **Ruby Receptionist** — Live answering service
- **AnswerForce** — 24/7 answering

**Automation:**
- **Zapier** — Connect to 1,000+ apps
  - Automate workflows between FieldPulse and other tools

**Calendar:**
- **Google Calendar** — Sync schedules

**Specialized:**
- **Marketing360** — Marketing services
- **Million Dollar Plumber** — Industry coaching
- **Trinity** — Business coaching
- **Free2Grow** — Business development
- **CFM** — Flat-rate pricing system
- **The Granite Group** — Supplier (wholesale plumbing/HVAC)
- **XAPPAI** — AI tools

**Supplier:**
- **Reece** — Australia only, supplier integration for inventory

## 6.4 API Access

**FieldPulse API:**
- **Available on Enterprise tier ONLY**
- REST API
- Requires API key from FieldPulse support

**API Capabilities:**
- **CRMs:** Create/update customers in external CRM
- **Scheduling:** Create/assign jobs from external system
- **Invoicing:** Sync invoices with other systems
- **Estimates:** Update estimate status
- **Material Lists:** Create material lists from external data
- **Custom Fields:** Send form data from other tools
- **Contracts:** Write/send contracts from third-party into FieldPulse
- **Task Tracking:** Create/update subtasks from external task management

**Webhooks:**
- **Limited to job status changes only** currently
- Users notified of breaking changes to API

---

# 7. Custom Workflows & Forms

## 7.1 Custom Status Workflows

### ClearPath Feature

**Purpose:** Configure job workflows specific to business/service type

**Workflow Configuration:**
- **Create custom job statuses** beyond default Draft/Scheduled/In Progress/Complete
- **Example workflows:**
  - **Plumbing:** "Site Assessment" → "Shutoff and Drain" → "Remove Old Piping" → "Install New Line" → "Pressure Test" → "Restore" → "Customer Sign-Off"
  - **Electrical:** "Permit Pending" → "Material Ordered" → "Installation" → "Inspection" → "Final Check" → "Customer Approval"
  - **HVAC:** "Diagnostic" → "Quote Approval" → "Equipment Ordered" → "Installation" → "System Test" → "Complete"

**Workflow Enforcement:**
- **Required steps** — Block job closure until mandatory steps complete
- **Guided progression** — Techs follow workflow in sequence
- **Manager oversight** — Ensure quality standards met
- **Consistency** — Every job follows same process

**Workflow Benefits:**
- **Quality assurance** — Prevent missed steps
- **Documentation** — Track what was done, when, by whom
- **Training** — New techs follow established process
- **Customer confidence** — Professional, repeatable process

**GPS Location Stamps:**
- Auto-generated when tech advances through custom workflow statuses
- **Can be disabled** — Toggle off location stamps if not needed

## 7.2 Custom Forms

### Form Builder Features

**Form Types Supported:**
- **HVAC Service Checklist** — Routine maintenance, repairs
- **Equipment Installation Checklist** — New installations
- **Safety Checklists** — Job site safety protocols
- **Customer Sign-Off Forms** — Approval/acceptance
- **Incident Reports** — Workplace incidents
- **Pre & Post Work Order Forms** — Before/after documentation
- **Rebate Forms** — Customer rebate applications
- **Compliance Forms** — Regulatory requirements
- **State/County Required PDF Forms** — Import and edit regulatory forms

**Form Field Types:**
- **Text fields** — Free text entry
- **Date fields** — Calendar picker
- **Checkboxes** — Yes/no toggles
- **Dropdown lists** — Select from options
- **Signature fields** — E-signature capture
- **Photo upload** — Attach images to form

**Required Fields:**
- **Toggle: "Required Field"** — Must be completed before submission
- Ensures critical information never missed

**Form Workflow:**
- **Fill out in field** — Complete on mobile app
- **Offline support** — Save while offline, sync when online
- **Attach to job record** — Forms stored with job
- **Send for signature** — Email form to customer for e-signature
- **PDF Form Filler** — Edit and fill PDF forms

**Import PDF Forms:**
- **Import state/county required forms**
- Add fillable fields to existing PDF
- Eliminate manual paperwork
- Ensure regulatory compliance

---

# 8. User Management & Permissions

## 8.1 User Roles

### Role Types

**Administrator:**
- Full access to all features
- Company settings
- Billing
- User management
- All customer/job data

**Team Manager:**
- Manage assigned team members
- View team performance
- Access team schedules
- Create jobs, estimates, invoices
- **Limitation reported:** "Can't create forms" — lacks granular permissions

**Service Agent (Limited User):**
- Field technician role
- View assigned schedule
- Update job status
- Create estimates/invoices from mobile
- Limited office access

**Custom Roles:**
- Unclear if fully custom roles are supported
- Custom field visibility by role is supported

## 8.2 Permissions

### Permission Controls

**Access Controls:**
- **User account management** — Activate/deactivate users
- **Profiles** — User information, contact details
- **Role assignment** — Assign user to role
- **Permissions** — What user can do
- **Multi-device access** — Web, mobile, tablet

**Visibility Controls:**
- **Custom field visibility** — Show/hide fields by role
- **Customer data access** — Control who sees what customer info
- **Financial data** — Restrict pricing/cost visibility
- **Manager-only tasks** — Mark tasks visible only to managers

**Location Tracking:**
- **GPS time stamps** — Capture location on clock in/out
- **Limited users** — Even limited users get location stamps
- **Privacy toggle** — Can disable location stamps on custom workflow progression

**Reported Issues:**
- "Permission settings too restrictive"
- "Lacking granularity"
- "Team Managers can't create forms"
- Need more flexible role-based permissions

---

# 9. Workflow Summary

## 9.1 Core Workflows

### Service Call Workflow

**Typical Flow:**
1. **Customer calls/books online** → Create customer record (if new)
2. **Create job** → Link to customer, assign technician, schedule
3. **Dispatch** → Tech sees job on mobile schedule
4. **Travel to job** → GPS tracks arrival
5. **Complete work** → Update job status, add notes, photos
6. **Create estimate** (if needed) → On-site estimation via mobile
7. **Customer approves** → E-signature on estimate
8. **Convert to invoice** → One-click conversion
9. **Collect payment** → Credit card via mobile or send payment link
10. **Job complete** → Mark job complete, auto-sync to office

### Project Workflow

**Multi-Phase Project:**
1. **Create project** → Group related jobs under project
2. **Create multiple jobs** → Each phase = separate job
3. **Assign team members** → Different techs per phase
4. **Track progress** → Monitor completion percentage
5. **Track costs** → Real-time cost vs. budget
6. **Invoice per phase** → Or invoice at project completion
7. **Close project** → Mark complete when all jobs done

### Recurring Service Workflow

**Maintenance Agreement:**
1. **Create maintenance agreement** → Linked to customer
2. **Link to asset** — Equipment being serviced
3. **Set schedule** → Frequency (monthly, quarterly, etc.)
4. **Auto-create jobs** → System generates jobs per schedule
5. **Reminder notifications** → Alert customer of upcoming service
6. **Convert to work order** → One-click WO generation
7. **Complete job** → Regular job workflow
8. **Invoice** → Bill per agreement terms

---

# 10. Data Model Relationships

## 10.1 Entity Relationship Summary

```
Customer (1) ←→ (many) Jobs
Customer (1) ←→ (many) Estimates
Customer (1) ←→ (many) Invoices
Customer (1) ←→ (many) Payments
Customer (1) ←→ (many) Assets
Customer (1) ←→ (many) Additional Contacts
Customer (1) ←→ (many) Additional Locations
Customer (1) ←→ (many) Maintenance Agreements

Job (many) ←→ (1) Customer [required]
Job (many) ←→ (1) Project [optional]
Job (1) ←→ (many) Estimates [optional]
Job (1) ←→ (many) Invoices [optional]
Job (1) ←→ (many) Assets [optional]
Job (1) ←→ (many) Subtasks
Job (1) ←→ (many) Time Entries

Project (1) ←→ (many) Jobs
Project (many) ←→ (1) Customer

Estimate (many) ←→ (1) Customer [required]
Estimate (many) ←→ (1) Job [optional]
Estimate (many) ←→ (1) Project [optional]
Estimate (1) ←→ (many) Estimate Lines
Estimate (1) ←→ (1) Invoice [on conversion]

Invoice (many) ←→ (1) Customer [required]
Invoice (many) ←→ (1) Job [optional]
Invoice (many) ←→ (1) Project [optional]
Invoice (1) ←→ (many) Invoice Lines
Invoice (1) ←→ (many) Payments

Payment (many) ←→ (1) Customer
Payment (many) ←→ (1) Invoice

Asset (many) ←→ (1) Customer [required]
Asset (1) ←→ (many) Maintenance Agreements
Asset (1) ←→ (many) Jobs [service history]

Purchase Order (1) ←→ (many) PO Lines
Purchase Order (many) ←→ (1) Vendor
Purchase Order (many) ←→ (1) Job [optional]

Item List (1) ←→ (many) Estimate Lines
Item List (1) ←→ (many) Invoice Lines
Item List (1) ←→ (many) PO Lines
```

## 10.2 Key Architectural Notes

**Job-Centric Model:**
- **Primary organizing principle:** Job/Work Order
- Customer → Job → Estimate/Invoice/Payment
- Assets are linked TO jobs, not jobs linked to assets
- This is fundamentally different from asset-centric design

**Optional Relationships:**
- Jobs don't require estimates or invoices (can exist independently)
- Estimates don't require jobs (can create standalone)
- Invoices don't require jobs (can invoice without work order)
- Assets are completely optional (many users don't use asset tracking)

**Multi-Tenancy:**
- Single database, multi-tenant SaaS
- All data scoped by company/account ID
- No data sharing between customers

---

# 11. Technical Architecture Notes

## 11.1 Platform

**Deployment:**
- Cloud-native SaaS
- No on-premise option
- Multi-tenant architecture

**Access:**
- Web browser (all modern browsers)
- iOS app (iPhone, iPad)
- Android app (phone, tablet)
- Real-time sync across all devices

**Database:**
- Proprietary (not disclosed publicly)
- Likely PostgreSQL or similar RDBMS

**Hosting:**
- Not disclosed publicly
- Likely AWS, Azure, or GCP

## 11.2 Data Import/Export

**Import Capabilities:**
- Customers (CSV)
- Line items (CSV)
- Serialized inventory (CSV)
- Jobs (CSV)
- Custom fields (CSV)
- Assets (CSV)
- Pricebooks (if enabled)
- Additional contacts (CSV)
- Additional locations (CSV)

**Export Capabilities:**
- All major entities exportable to CSV/Excel
- Estimates/Invoices to PDF
- QuickBooks sync (push data)

**Data Migration Service:**
- Offered by FieldPulse
- Migrate from other FSM platforms
- Typically 4-6 weeks
- No downtime during migration
- Engineering team handles migration

---

**END OF FUNCTIONAL SPECIFICATION**
