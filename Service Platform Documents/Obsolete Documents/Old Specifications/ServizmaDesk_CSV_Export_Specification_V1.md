# ServizmaDesk CSV Export Specification (Top-Down Design)
**Document Version:** V2
**Status:** Approved (Resolves Gap 2.10)

## 1. Overview
This spec defines the authoritative column sets for data exports across the ServizmaDesk ecosystem. In accordance with the **Top-Down Design** philosophy, these exports are designed to handle the full breadth of the Enterprise ERD, ensuring data portability across all service tiers.

## 2. Global Export Rules
- **Encoding**: UTF-8 with BOM for universal spreadsheet compatibility.
- **Date/Time**: ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`) or the tenant's localized preference.
- **Currency**: Numeric decimals (e.g., `1250.50`) without currency symbols.
- **Headers**: Human-readable headers in the first row.
- **Security**: Restricted to users with the relevant `Export` permission for the specific resource.
- **Isolation**: Strictly scoped to the active `tenant_id`.

## 3. Entity Column Sets

### 3.1 Identity & Access
#### Users (Employees)
1. Employee Number
2. First Name
3. Last Name
4. Work Email
5. Status (Active, On Leave, Inactive, Terminated)
6. Assigned Roles
7. Hire Date
8. Termination Date
9. Created On

#### Roles & Permissions
1. Role Name
2. Is Custom Role (True/False)
3. Resource Key
4. Can Create
5. Can View
6. Can Edit
7. Can Delete

### 3.2 CRM (The Triad)
#### Customers (Billing Entities)
1. Customer Number
2. Company Name
3. Account Type (Residential/Commercial)
4. Account Status (Active/Inactive)
5. Account Number
6. Tax Exempt (True/False)
7. Customer Since
8. Credit Limit
9. Credit Status
10. Assigned User
11. Lead Source
12. Primary Address
13. Primary Phone
14. Created On

#### Contacts (People links)
1. Contact ID
2. First Name
3. Last Name
4. Linked Customer/Vendor
5. Role / Title
6. Department
7. Is Primary (True/False)
8. Status (Active/Left)
9. Work Email
10. Work Phone
11. Mobile Phone
12. Created On

### 3.3 Assets & Product Catalog
#### Assets
1. Asset Number
2. Asset Name
3. Customer Name
4. Parent Asset (for nested assets)
5. Category
6. Type
7. Make
8. Model
9. Serial Number
10. Installation Date
11. Condition
12. Warranty End Date
13. Physical Site Address
14. Created On

#### Inventory (Products & Services)
1. Item Number
2. Item Name
3. Item Type (Part, Service, Consumable, Kit)
4. SKU / Part Number
5. Category
6. Status (Active/Inactive/Discontinued)
7. Unit Cost
8. Unit Price
9. Base Unit (EA, HR, etc.)
10. Is Serialized (True/False)
11. Created On

### 3.4 Service Delivery
#### Quotes
1. Quote Number
2. Customer Name
3. Subject
4. Status
5. Issued Date
6. Expiry Date
7. Subtotal
8. Tax Total
9. Quote Total
10. Assigned To
11. Converted To (WO/Invoice Number)
12. Created On

#### Work Orders
1. Work Order Number
2. Customer Name
3. Status
4. Priority
5. Type
6. Assigned User
7. Scheduled Date
8. Completion Date
9. Service Description
10. Total Labor Hours
11. Total Part Cost
12. Total Amount
13. Created On

### 3.5 Financials
#### Invoices
1. Invoice Number
2. Customer Name
3. Status
4. Issued Date
5. Due Date
6. Line Item Total
7. Tax Total
8. Invoice Total
9. Amount Paid
10. Balance Due
11. Stripe Payment URL
12. Created On

#### Payments
1. Payment Number
2. Invoice Number
3. Customer Name
4. Amount
5. Payment Date
6. Payment Method
7. Transaction ID
8. Payment Status
9. Created On

#### Ledger
1. Entry ID
2. Transaction Date
3. Entry Type (Debit/Credit)
4. Amount
5. Running Balance
6. Description
7. Linked Entity (Customer/Vendor)
8. Reference ID (Invoice/Payment/Bill)

### 3.6 Operations
#### Tasks
1. Task Number
2. Subject
3. Priority
4. Status
5. Assigned User
6. Linked Entity
7. Due Date
8. Completion Date

#### Checklist Templates
1. Template Name
2. Target Entity (Work Order Type)
3. Step Labels
4. Sort Orders
