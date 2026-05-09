# ServizmaDesk CSV Export Specification (Top-Down Design)
**Document Version:** V3
**Status:** Working Draft
**Supersedes:** V2

## 1. Overview
This spec defines the authoritative column sets for data exports across the ServizmaDesk ecosystem. In accordance with the **Top-Down Design** philosophy, these exports are designed to handle the full breadth of the Enterprise ERD, ensuring data portability across all service tiers.

> **Entity Naming Note:** The internal entity name is `InventoryItem`. In the Lite tier UI, this is labeled as "Product." All other tiers use "Inventory Item."

## 2. Global Export Rules
- **Encoding**: UTF-8 with BOM for universal spreadsheet compatibility.
- **Date/Time**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) or the tenant's localized preference.
- **Currency**: Numeric decimals (e.g., `1250.50`) without currency symbols.
- **Headers**: Human-readable headers in the first row.
- **Security**: Restricted to users with the relevant `Export` permission for the specific resource.
- **Isolation**: Strictly scoped to the active `tenant_id`.
- **Tier Gating**: Export column sets include all fields for that entity. Entities gated above the tenant's current tier are not available for export.

## 3. Entity Column Sets

### 3.1 Identity & Access
#### Users (Employees)
1. Employee Number
2. First Name
3. Last Name
4. Work Email
5. Department
6. Position
7. Status (Active, On Leave, Inactive, Terminated)
8. Assigned Roles
9. Hire Date
10. Termination Date

#### Roles & Permissions
1. Role Name
2. Is Custom Role (True/False)
3. Resource Key
4. Can Create
5. Can View
6. Can Edit
7. Can Delete

### 3.2 CRM
#### Customers
1. Customer Number
2. Company Name
3. Account Type (Residential/Commercial)
4. Account Status (Active, Inactive, Hold, Closed)
5. Account Number
6. Tax Exempt (True/False)
7. Customer Since
8. Credit Limit
9. Credit Status
10. Assigned User
11. Lead Source
12. Primary Address
13. Primary Phone
14. Primary Contact Name

#### Contacts
1. Contact ID
2. First Name
3. Last Name
4. Linked Entity (Customer/Vendor/Carrier/Bank)
5. Linked Entity Name
6. Role / Title
7. Department
8. Is Primary (True/False)
9. Status (Active/Left)
10. Work Email
11. Work Phone
12. Mobile Phone

#### Leads (Plus+)
1. Lead Number
2. First Name
3. Last Name
4. Phone
5. Email
6. Source
7. Status (New, Contacted, Qualified, Converted, Lost)
8. Linked Customer

#### Opportunities (Plus+)
1. Opportunity Number
2. Customer Name
3. Name/Description
4. Status (Open, Won, Lost)
5. Estimated Value
6. Expected Close Date
7. Assigned To
8. Originating Lead Number

### 3.3 Assets & Inventory
#### Assets
1. Asset Number
2. Customer Name
3. Customer Number
4. Parent Asset Number (for nested assets)
5. Category
6. Type
7. Make
8. Model
9. Serial Number
10. Installation Date
11. Condition
12. Warranty Start Date
13. Warranty End Date
14. Warranty Status (Active/Expired/N/A)
15. Physical Site Address
16. Status (Active, Inactive, Decommissioned)

#### Inventory Items
1. Item Number
2. Item Name
3. Item Type (Service, Inventory, Non-Inventory)
4. SKU / Part Number
5. Category
6. Unit Cost
7. Unit Price
8. Taxable (True/False)
9. Is Bundle (True/False)
10. Preferred Vendor
11. Is Serialized (True/False)

### 3.4 Service Delivery
#### TroubleCalls
1. TroubleCall Number
2. Customer Name
3. Customer Number
4. Asset Number
5. Status (New, Triaged, Converted to Work Order, Converted to Quote, Cancelled)
6. Source (Phone, Portal, Widget, Email, Referral)
7. Issue Category
8. Urgency
9. Description
10. Requested Date/Time

#### Work Orders
1. Work Order Number
2. Customer Name
3. Customer Number
4. Asset Number
5. Asset Make/Model
6. Status
7. Priority
8. Type
9. Assigned User
10. WorkGroup Number
11. Scheduled Date
12. Completion Date
13. Service Description
14. Total Labor Hours
15. Total Part Cost
16. Total Amount
17. Originating TroubleCall Number
18. Originating PM Number

#### Quotes
1. Quote Number
2. Customer Name
3. Customer Number
4. Opportunity Number
5. Status
6. Quote Date
7. Expiry Date
8. Subtotal
9. Tax Total
10. Quote Total
11. Assigned To
12. Converted To (WO/Invoice Number)

#### WorkGroups (Plus+)
1. WorkGroup Number
2. Customer Name
3. Customer Number
4. Service Address
5. Status (Open, In Progress, Completed, Cancelled)
6. Number of Work Orders
7. Number of Assets

### 3.5 Financials
#### Invoices
1. Invoice Number
2. Customer Name
3. Customer Number
4. Status
5. Invoice Date
6. Due Date
7. Line Item Total
8. Tax Total
9. Invoice Total
10. Amount Paid
11. Balance Due
12. Stripe Payment URL
13. Is Recurring (True/False)

#### Customer Payments
1. Payment Number
2. Invoice Number
3. Customer Name
4. Customer Number
5. Amount
6. Payment Date
7. Payment Method
8. Reference Number
9. Stripe Payment Intent ID

#### Vendor Payments (Plus+)
1. Payment ID
2. Vendor Name
3. PO Number
4. Vendor Bill Number
5. Amount
6. Payment Date
7. Payment Method
8. Reference Number

#### Ledger
1. Entry ID
2. Transaction Date
3. Entry Type (Debit/Credit)
4. Amount
5. Running Balance
6. Linked Customer
7. Linked Vendor
8. Reference (Invoice/Payment/PO/Bill Number)

### 3.6 Purchasing & Vendors (Plus+)
#### Vendors
1. Vendor Name
2. Account Number
3. Primary Contact Name
4. Primary Phone
5. Primary Address

#### Purchase Orders
1. PO Number
2. Vendor Name
3. Status (Draft, Sent, Partially Received, Received, Cancelled)
4. Order Date
5. Expected Delivery Date
6. Related Work Order Number
7. Total Amount

#### PO Line Items
1. PO Number
2. Item Name
3. Item Number
4. Quantity Ordered
5. Quantity Received
6. Unit Cost
7. Line Total

#### Vendor Bills
1. Vendor Bill Number
2. Vendor Name
3. Bill Date
4. Due Date
5. Amount
6. Status (Draft, Received, Partially Paid, Paid, Overdue, Void)
7. Related PO Number

#### RMAs
1. RMA Number
2. Vendor Name
3. Item Name
4. Item Number
5. PO Number
6. Quantity
7. Reason
8. Status (Initiated, Shipped, Received by Vendor, Credited, Closed, Denied)
9. Credit Amount

#### Requisitions
1. Requisition Number
2. Requesting Employee
3. Related Work Order Number
4. Status (New, Approved, Partially Fulfilled, Fulfilled, Cancelled)
5. Fulfillment Method

### 3.7 Service Agreements & PM (Plus+)
#### Agreements
1. Agreement Number
2. Agreement Name
3. Status (Pending, Active, Expired, Cancelled)
4. Start Date
5. End Date
6. Renewal Type (Manual, Auto-Renew)
7. Pricing Amount
8. Pricing Frequency
9. Discount Percentage

#### Customer Agreements
1. Customer Name
2. Customer Number
3. Agreement Name
4. Agreement Number
5. Asset Number
6. Asset Make/Model

#### Preventative Maintenance
1. PM Number
2. Customer Name
3. Customer Number
4. Asset Number
5. Asset Make/Model
6. Agreement Number
7. WorkFlow Name
8. Status (Active, Paused, Expired, Cancelled)
9. Frequency
10. Visits Per Period
11. Start Date
12. End Date
13. Default Assignee
14. Auto-Generate WOs (True/False)

### 3.8 Operations
#### Tasks
1. Task Number
2. Title
3. Priority
4. Status
5. Assigned User
6. Linked Customer
7. Linked Asset
8. Due Date
9. Completion Date

#### Checklist Templates
1. Template Name
2. Target Work Order Type
3. Step Labels
4. Sort Orders

### 3.9 Skills & Equipment (Pro+)
#### Employee Skills
1. Employee Name
2. Employee Number
3. Skill Name
4. Category (Certification, License, Training, Competency)
5. Date Earned
6. Expiration Date
7. Status (Active, Expired)

#### Equipment
1. Equipment Number
2. Name
3. Category
4. Serial Number
5. Status (Available, Checked Out, In Repair, Decommissioned)
6. Current Custodian (Employee Name)
7. Purchase Date
8. Purchase Cost

#### Equipment Check In/Out History
1. Equipment Number
2. Equipment Name
3. Employee Name
4. Checked Out At
5. Checked In At
6. Condition at Checkout
7. Condition at Return

### 3.10 Fleet Management (Add-On)
#### Vehicles
1. Vehicle Number
2. Year
3. Make
4. Model
5. VIN
6. License Plate
7. License State
8. Vehicle Type
9. Status (Active, Out of Service, Decommissioned)
10. Assigned Driver
11. Current Odometer
12. Registration Expiry
13. Insurance Expiry
14. Next Inspection Date

#### Vehicle Maintenance
1. Maintenance Number
2. Vehicle Number
3. Vehicle Make/Model
4. Maintenance Type
5. Status (Scheduled, Completed, Overdue, Cancelled)
6. Scheduled Date
7. Completed Date
8. Odometer at Service
9. Cost
10. Performed By (In-House/External)
11. Vendor Name

#### Mileage Log
1. Vehicle Number
2. Driver Name
3. Log Date
4. Odometer Start
5. Odometer End
6. Miles Driven
7. Trip Purpose
8. Related Work Order Number
