# ServizmaDesk Gap Analysis V3
**ERD-Driven Top-Down Review**

**Date:** March 2026
**Document Status:** Working Draft — V3
**Classification:** Internal — Confidential
**Basis of Truth:** SD_System_ERD__Base_System_v5.pdf
**Supersedes:** SDTA_Backend_Gap_Analysis_v2.md

---

## Purpose

This gap analysis compares the entire ServizmaDesk specification suite against the **ERD (Base System V5)** as the center of truth. The previous Gap Analysis V2 focused on inter-document consistency. This V3 identifies a systemic problem: many specifications were designed bottom-up from the Lite MVP scope rather than top-down from the full system ERD. As a result, entire entity domains present in the ERD are absent from or misrepresented in the specifications.

**Documents Reviewed:**
- SD_System_ERD__Base_System_v5.pdf (center of truth)
- ServizmaDesk_Top_Down_Specifications.md V1
- ServizmaDesk_Data_Models_V3.md
- ServizmaDesk_Lite_MVP_V4_Specification.md
- ServizmaDesk_Product_Tier_Map_V2.md
- ServizmaDesk_Technical_Architecture_V2.md
- ServizmaDesk_Pricing_and_Billing_Specification_V2.md
- ServizmaDesk_Platform__SDP__Specification_V2.md

---

## Severity Classification

| Severity | Definition |
|---|---|
| **BLOCKER** | Entity or subsystem exists in ERD but is completely absent from all specifications. Cannot build to ERD without resolution. |
| **CRITICAL** | Entity exists in specs but contradicts the ERD's structure, relationships, or naming in a way that would produce a wrong implementation. |
| **MAJOR** | Entity partially addressed but missing key fields, relationships, or junction tables shown in the ERD. |
| **MODERATE** | Terminology, naming, or structural inconsistency between documents that causes confusion but doesn't block implementation. |
| **MINOR** | Document formatting, duplication, or reference issues. |

---

# PART 1 — MISSING ENTITIES (ERD exists, Specs do not)

These are complete entities or subsystems present in the ERD that have no representation in any specification document.

---

## Gap 1.1 — TroubleCall Entity
**Severity:** BLOCKER
**ERD:** `TroubleCall` — Key ID, FK Asset, FK Customer
**WorkOrder in ERD:** Has `FKTroubleCall` — direct foreign key linking a Work Order to the originating Trouble Call.
**Specs:** The Top-Down Specification defines a `ServiceRequest` entity (Section 1.3). The Data Models V3 defines a `ServiceRequest` model (Section 2.5). Neither matches the ERD.

**Differences between ERD TroubleCall and Spec ServiceRequest:**
- ERD TroubleCall has a direct FK to Asset; ServiceRequest does not.
- ERD WorkOrder has a direct FKTroubleCall; the spec WorkOrder has no FK to ServiceRequest.
- The ERD treats TroubleCall as a direct precursor to WorkOrder with an explicit FK chain: TroubleCall → WorkOrder. The spec treats ServiceRequest as a status-driven conversion without a formal FK relationship.

**Action Required:** Decide whether to rename ServiceRequest to TroubleCall and add the ERD's FK structure (Asset link, WorkOrder backlink), or update the ERD to reflect the ServiceRequest design. Since the ERD is truth, the specs should be updated to match.

---

## Gap 1.2 — WorkGroup Subsystem
**Severity:** BLOCKER
**ERD Entities:**
- `WorkGroup` — Key ID, FK Customer, FK Address
- `WorkGroupTeam` — Key ID, FK WorkGroup, FK Employee, FK Emp-Role
- `WGTRoles` — Key ID
- `WG Division` — Key ID, FK WorkGroup, FK Address
- `WorkOrder` — has FK WorkGroup, FK WG Division

**Specs:** Entirely absent from all documents. No mention in Top-Down Specifications, Data Models V3, Product Tier Map V2, or Lite MVP V4.

**Impact:** The ERD shows Work Orders are assignable to WorkGroups and WG Divisions (service areas/territories), with team composition and role assignments. This is a complete subsystem governing how work is organized geographically or by customer group — a core operational capability for multi-team businesses.

**Action Required:** Define the WorkGroup subsystem in the Top-Down Specification, add data models, assign tier gates, and add WorkGroup/WG Division FKs to the WorkOrder model.

---

## Gap 1.3 — Agreements / CustomerAgreements
**Severity:** BLOCKER
**ERD Entities:**
- `Agreements` — Key ID (standalone)
- `CustomerAgreements` — Key ID, FK Customer, FK Agreement (M2M junction)

**Specs:** The Top-Down Specification defines MaintenancePlan (Section 2.1) but does not define a separate, generic Agreements entity. MaintenancePlan is asset-scoped and schedule-focused. The ERD's Agreements entity appears to be a broader concept — potentially covering service contracts, SLAs, warranty agreements, and terms beyond recurring maintenance.

**Action Required:** Define the Agreements entity and CustomerAgreements junction table in Top-Down Specifications and Data Models. Clarify the relationship between Agreements and MaintenancePlan (is MaintenancePlan a type of Agreement, or are they separate domains?).

---

## Gap 1.4 — Leads / Opportunity / Oppt-SASSIGNED-Contact
**Severity:** BLOCKER
**ERD Entities:**
- `Leads` — Key ID, FK Customer
- `Opportunity` — Key ID, FK Customer, FK Leads
- `Oppt-SASSIGNED-Contact` — Key ID, FK Opportunity, FK Contact, FK Company

**Specs:** The Top-Down Specification mentions "Customer Pipeline (Plus+)" as dropdown statuses on the Customer record (Lead, Opportunity, Active, Inactive). It does not define Leads or Opportunity as standalone entities. The Data Models V3 has no Leads or Opportunity models.

**Impact:** The ERD defines a full CRM pipeline: Lead → Opportunity → assigned Contacts per Opportunity. This is structurally different from a status dropdown on Customer. A dropdown cannot track multiple opportunities per customer, assign contacts per opportunity, or link opportunities to leads independently.

**Action Required:** Define Leads, Opportunity, and the Opportunity-Contact assignment junction table as first-class entities in Top-Down Specifications and Data Models. Assign tier gates (likely Plus+). Remove or redefine the "Customer Pipeline" dropdown concept to avoid collision with the standalone entities.

---

## Gap 1.5 — Equipment / Check In-Out / WFTools
**Severity:** BLOCKER
**ERD Entities:**
- `Equipment` — Key ID (company-owned tools and equipment, distinct from inventory)
- `Check In/Out` — Key ID, FK Tool, FK Employee (tool custody tracking)
- `WFTools` — Key ID, FK WorkFlow, FK Equipment (tools required per workflow)

**Specs:** Entirely absent. The Top-Down Specification does not mention company-owned tool/equipment tracking. The Product Catalog (Section 1.8) covers saleable inventory, not internal company tools.

**Impact:** This is a complete tool management subsystem: define equipment, track who has what (check in/out), and specify which tools a workflow requires. This is a significant operational feature for field service businesses.

**Action Required:** Define Equipment, Check In/Out, and WFTools entities in Top-Down Specifications and Data Models. Assign tier gates. Note: The ERD also has `Vehichle Inventory` (FK Fleet, FK Tools/Inventory) which connects fleet vehicles to the tools/inventory they carry — this should also be defined.

---

## Gap 1.6 — SafetyForms / WOSFAnswers
**Severity:** BLOCKER
**ERD Entities:**
- `SafetyForms` — Key ID
- `WOSFAnswers` — Key ID, FK WorkOrder, FK Employee, FK SafetyForms

**Specs:** The Top-Down Specification discusses "Custom Forms (Pro/Enterprise)" in Section 8.2 as a generic form builder concept. It does not define SafetyForms as a specific entity or model WOSFAnswers as a junction table linking completed safety form responses to Work Orders and Employees.

**Impact:** The ERD treats safety forms as first-class entities with per-Work-Order, per-Employee answer records. The spec's generic "Custom Forms" description doesn't capture this structure. The NotesorDocuments entity in the ERD also has FKSafetyForms, meaning safety form records can have notes/documents attached.

**Action Required:** Define SafetyForms and WOSFAnswers as distinct entities in Top-Down Specifications and Data Models, separate from the generic Custom Forms concept.

---

## Gap 1.7 — Employee Skills / Skills
**Severity:** BLOCKER
**ERD Entities:**
- `Skills` — Key ID
- `EmployeeSkills` — Key ID, FK Employee, FK Skills

**Specs:** The Top-Down Specification mentions "Skills/Certifications" in Section 3.1 for smart assignment (Pro/Enterprise) but does not define Skills or EmployeeSkills as data entities. The Data Models V3 has no Skills or EmployeeSkills tables.

**Action Required:** Define Skills and EmployeeSkills in Top-Down Specifications and Data Models. Assign tier gates.

---

## Gap 1.8 — VendorBills
**Severity:** BLOCKER
**ERD Entity:** `VendorBills` — Key ID, FK Vendor
**Related ERD references:** Payments entity has FKVendorBills. NotesorDocuments has FKVendorBills.

**Specs:** The Top-Down Specification mentions "log Vendor Bills against [Purchase Orders]" (Section 1.17, Tier 2: Plus) but does not define VendorBills as a standalone entity. Data Models V3 has no VendorBills model.

**Impact:** VendorBills is a separate entity from PurchaseOrder in the ERD. A VendorBill represents the vendor's invoice to you (accounts payable), while a PurchaseOrder represents your request to the vendor. These have an independent lifecycle and the ERD links payments directly to VendorBills.

**Action Required:** Define VendorBills as a standalone entity in Top-Down Specifications and Data Models.

---

## Gap 1.9 — Banks
**Severity:** BLOCKER
**ERD Entity:** `Banks` — Key ID, FK Customer
**Related ERD references:** Contacts has FKBank. Phones has FKBank. Addresses has FKBank. Accounting has FKBank.

**Specs:** No mention of a Banks entity in any specification document.

**Impact:** The ERD shows Banks as an entity linked to Customers, with their own contacts, phones, and addresses via the shared triad tables. This likely represents the customer's banking relationships (for ACH payments, financing, etc.).

**Action Required:** Define the Banks entity in Top-Down Specifications and Data Models. Clarify its purpose and tier gate.

---

## Gap 1.10 — Accounting Entity
**Severity:** BLOCKER
**ERD Entity:** `Accounting` — Key ID, FK Customer, FK Carrier, FK Bank

**Specs:** The Top-Down Specification defines a Native Accounting system (Section 1.17) as a tiered capability description but does not define an Accounting data entity. The Data Models V3 defines a `Ledger` model but not an Accounting entity.

**Action Required:** Define the Accounting entity. Clarify relationship to the existing Ledger model and the Carrier entity (see Gap 1.11).

---

## Gap 1.11 — Carrier Entity
**Severity:** BLOCKER
**ERD References:** Accounting has FKCarrier. Contacts has FKCarrier. Phones has FKCarrier. Addresses has FKCarrier.

**Specs:** No mention of Carrier in any specification document.

**Impact:** The ERD shows Carrier as an entity with contacts, phones, and addresses (via shared triad tables), connected to Accounting. This likely represents insurance carriers, surety bond providers, or shipping carriers.

**Action Required:** Define the Carrier entity in Top-Down Specifications and Data Models. Clarify its purpose, relationships, and tier gate.

---

## Gap 1.12 — RMA (Return Merchandise Authorization)
**Severity:** BLOCKER
**ERD Entity:** `RMA` — Key ID, FK PLineItem, FK Inventory, FK Vendor
**Related ERD references:** NotesorDocuments has FKRMAs.

**Specs:** No mention of RMA in any specification document.

**Impact:** RMA manages the return of defective or incorrect parts to vendors. It links to the original purchase line item, the inventory item, and the vendor. This is a standard supply chain function for businesses maintaining parts inventory.

**Action Required:** Define RMA in Top-Down Specifications and Data Models. Assign tier gate (likely Plus+ alongside Purchasing).

---

## Gap 1.13 — Inventory Subsystem Detail
**Severity:** BLOCKER
**ERD Entities not in Specs:**
- `InventoryCounts` — Key ID, FK Inventory (physical inventory count records)
- `InventoryTransfers` — Key ID, FK Location, FK Inventory (movement between locations)
- `Receiving` — Key ID, FK PLineItem, FK Inventory, FK Employee (PO receipt processing)
- `LotInfo` — Key ID, FK PLineItem, FK Inventory (lot/batch tracking)
- `InvPriceHistory` — Key ID, Key Inventory (historical pricing)

**Specs:** The Data Models V3 defines `InventoryStock` (Section 2.3) for quantity tracking and `PurchaseOrderLine` with `quantity_received` for partial receiving. None of the five entities above are defined.

**Impact:** The ERD envisions a full warehouse management system: physical counts for reconciliation, inter-location transfers, detailed receiving with employee tracking, lot/batch traceability, and price history auditing. The specs only cover a basic stock quantity tracker.

**Action Required:** Define all five entities in Top-Down Specifications and Data Models. Assign tier gates.

---

## Gap 1.14 — Positions Entity
**Severity:** MAJOR
**ERD Entity:** `Positions` — Key ID, FK Department

**Specs:** No mention. The specs define Roles (permission-based) and Departments but not Positions (job title/organizational hierarchy tracking, e.g., "Senior Technician", "Service Manager").

**Action Required:** Define Positions in Top-Down Specifications and Data Models. Clarify relationship to Roles (Roles = permissions; Positions = organizational title).

---

## Gap 1.15 — CreditCards (Employee)
**Severity:** MAJOR
**ERD Entity:** `CreditCards` — Key ID, FK Employee

**Specs:** No mention in any document.

**Impact:** Tracks company credit cards assigned to employees — relevant for expense tracking and fleet fuel purchases.

**Action Required:** Define CreditCards in Top-Down Specifications and Data Models. Likely tied to Fleet add-on or Pro/Enterprise expense tracking.

---

## Gap 1.16 — Vehicle Inventory
**Severity:** MAJOR
**ERD Entity:** `Vehichle Inventory` — Key ID, FK Fleet, FK Tools/Inventory

**Specs:** The Top-Down Specification notes that "A Vehicle functions as a Mobile Warehouse" (Section 1.18) for inventory. The Data Models V3 does not define a VehicleInventory junction table linking vehicles to the tools/inventory they carry.

**Action Required:** Define VehicleInventory junction table, or confirm that the Warehouse model (with type=Mobile) and SubLocation structure adequately covers this ERD entity.

---

# PART 2 — STRUCTURAL CONTRADICTIONS (Specs vs. ERD)

These are cases where specs define something differently from how the ERD structures it.

---

## Gap 2.1 — WorkOrder: Single FK vs. M2M for Assets
**Severity:** CRITICAL
**ERD:** WorkOrder has `FKAsset` — a single direct foreign key to one Asset.
**Specs:** Top-Down Specification Section 1.4 states "Multiple Assets can be linked to one Work Order." Data Models V3 defines a `WorkOrderAsset` M2M junction table.

**Conflict:** The ERD shows a single FK (one asset per work order), while the specs define a many-to-many relationship. These are fundamentally different data structures.

**Action Required:** Decide which is correct. If a Work Order can serve multiple assets (common in field service — e.g., tune-up on two HVAC units in one visit), the M2M junction is correct and the ERD should be updated. If one asset per Work Order is intended (each unit gets its own WO), the M2M table should be removed from Data Models. This is a foundational architectural decision.

---

## Gap 2.2 — WorkOrder: Missing ERD Foreign Keys
**Severity:** CRITICAL
**ERD WorkOrder FKs:**
- FKPrev_Maint (→ Preventative Maintenance)
- FKWorkFlow (→ WorkFlow)
- FKAsset (→ Asset — see Gap 2.1)
- FKTroubleCall (→ TroubleCall — see Gap 1.1)
- FK Customer ✓ (present in specs)
- FK Employee ✓ (present as `assigned_to`)
- FK Vehicles ✓ (present as `vehicle_id`)
- FK WorkGroup (→ WorkGroup — see Gap 1.2)
- FK WG Division (→ WG Division — see Gap 1.2)

**Specs Data Models V3 WorkOrder FKs:**
- customer_id ✓
- project_id (not in ERD)
- quote_id (not in ERD — backlink)
- vehicle_id ✓
- converted_to_invoice_id (not in ERD — backlink)
- assigned_to ✓

**Missing from Data Models vs ERD:**
- `prev_maint_id` → PreventativeMaintenance
- `workflow_id` → WorkFlow
- `trouble_call_id` → TroubleCall
- `work_group_id` → WorkGroup
- `wg_division_id` → WG Division

**Action Required:** Add all missing FKs to the WorkOrder data model after the parent entities are defined.

---

## Gap 2.3 — WorkOrderTeam (Multi-Employee Assignment)
**Severity:** CRITICAL
**ERD Entity:** `WorkOrderTeam` — Key ID, FK WorkOrder, FK Employee (M2M junction for multiple technicians per Work Order)
**Specs:** Data Models V3 defines only a single `assigned_to` FK on WorkOrder. The Top-Down Specification Section 3.2 states "Assign multiple employees to one Work Order" but the data model doesn't support this.

**Action Required:** Add WorkOrderTeam M2M junction table to Data Models V3. Keep `assigned_to` as the primary/lead technician and use WorkOrderTeam for additional team members, matching the ERD pattern.

---

## Gap 2.4 — Shared Triad Tables: Missing ERD Connections
**Severity:** CRITICAL
**ERD:** Contacts, Phones, and Addresses all have FK links to: Customer, Vendor, **Carrier**, **Bank**. Addresses also link to Warehouse and Asset.
**Specs:** Data Models V3 Triad tables link to: Customer, Contact, Vendor, User, and Asset (Address only). Missing: Carrier, Bank.

**Action Required:** After Carrier and Bank entities are defined, add their FK columns to the shared triad tables (Address, Phone, Contact).

---

## Gap 2.5 — Inventory vs. Product Naming
**Severity:** MODERATE
**ERD:** Uses `Inventory` as the entity name throughout. All FKs reference "FK Inventory."
**Specs:** Uses `Product` as the entity name. Data Models V3 defines the table as `Product`.

**Impact:** Not a structural issue (they represent the same concept), but a naming divergence that could cause confusion during development when referencing the ERD. The ERD's Pricebook also uses "Key Inventory" while specs use "product_id."

**Action Required:** Acknowledge this as an intentional rename (Product is more user-friendly than Inventory for a catalog) and add a mapping note to the Data Models document stating: "Product in specs = Inventory in ERD."

---

## Gap 2.6 — Preventative Maintenance vs. MaintenancePlan
**Severity:** CRITICAL
**ERD Entity:** `Preventative Maintenance` — Key ID, FK WorkFlow, FK Asset, FK Customer
**Specs:** `MaintenancePlan` — FK Customer, FK ChecklistTemplate, FK User (assignee). Links to Assets via M2M junction `MaintenancePlanAsset`.

**Key differences:**
- ERD links PM directly to WorkFlow; specs link MaintenancePlan to ChecklistTemplate.
- ERD has a direct FKAsset (one asset per PM record); specs use a M2M junction (multiple assets per plan).
- ERD references WorkFlow entity (see Gap 2.7); specs reference ChecklistTemplate.
- ERD WorkOrder has FKPrev_Maint directly; specs have no direct backlink from WorkOrder to MaintenancePlan.

**Action Required:** Reconcile the two designs. The ERD's WorkFlow-driven approach (PM links to a WorkFlow which has Steps and step ToDos) is more structured than the spec's ChecklistTemplate approach. These may need to coexist or one needs to replace the other.

---

## Gap 2.7 — WorkFlow Subsystem: ERD vs. Specs
**Severity:** CRITICAL
**ERD Entities:**
- `WorkFlow` — Key ID
- `WFSteps` — Key ID, FK WorkFlow
- `WFStepToDos` — Key ID, FK WFSteps
- `WFTools` — Key ID, FK WorkFlow, FK Equipment (tools needed per workflow)
- `WF Inventory` — Key ID, FK WorkFlow, FK Inventory (parts needed per workflow)
- Referenced by: Preventative Maintenance (FKWorkFlow), WorkOrder (FKWorkFlow)

**Specs:**
- Top-Down Specification Section 8.1 defines "Custom Status Workflows" — configurable Work Order status sequences.
- Data Models V3 Part 4 defines `WorkflowTemplate` (trigger_event field) and `WorkflowStep` (step_name, sort_order) — only 2 fields each, no ToDos.

**Key differences:**
- ERD WorkFlow is a full operational definition: steps → step-level ToDos → required tools → required inventory. It drives Preventative Maintenance and is directly referenced from WorkOrder.
- Specs treat workflow as either a status progression (Top-Down) or a minimal automation trigger (Data Models). Neither captures the ERD's depth.
- ERD has WFStepToDos (checklist items per workflow step); specs have no equivalent.
- ERD has WF Inventory (parts required per workflow); specs have no equivalent.
- ERD has WFTools (equipment required per workflow); specs have no equivalent.

**Action Required:** Completely redefine the WorkFlow subsystem in specs to match the ERD's full structure: WorkFlow → WFSteps → WFStepToDos, plus WFTools and WF Inventory junction tables.

---

## Gap 2.8 — Ledger Entity Structure
**Severity:** MAJOR
**ERD Ledger:** Key ID, FK Payment, FK Customer, FK Vendor, FK Purchasing, FK Invoice
**Specs Data Models V3 Ledger:** Has FK Payment, FK Customer, FK Vendor, FK Purchasing (labelled `purchasing_id`), FK Invoice. Also has `entry_type` (Debit/Credit) and `running_balance`.

**Assessment:** The FK structure aligns. However, the ERD does not show entry_type or running_balance fields. The Ledger header in Data Models shows both `LedgerEntry` and `Ledger` — there's a formatting artifact where both names appear on consecutive lines, suggesting a rename that wasn't cleaned up.

**Action Required:** Clean up the Ledger/LedgerEntry naming in Data Models V3. Verify field completeness against the ERD.

---

## Gap 2.9 — Payments (Two Separate Entities in ERD)
**Severity:** CRITICAL
**ERD:** Defines TWO separate Payments entities:
1. **Payments (Vendor side):** Key ID, FK Purchasing, FK Vendor, FK VendorBills — outgoing payments to vendors
2. **Payments (Customer side):** Key ID, FK Invoice, FK Customer, FK Employee, FK VehicleMaint, FK Stripe Response — incoming payments from customers

**Specs:** Data Models V3 defines a single `Payment` model (Section 1.4) covering only customer-side payments (FK Invoice, FK Customer, stripe_payment_intent_id).

**Action Required:** Define a separate `VendorPayment` model for outgoing payments to vendors, with FKs to PurchaseOrder, Vendor, and VendorBills.

---

# PART 3 — INTRA-DOCUMENT ISSUES

Issues within individual documents that compound the ERD alignment problems.

---

## Gap 3.1 — Data Models V3: Duplicated Part 2
**Severity:** MINOR
**Issue:** The Data Models V3 document contains two copies of Part 2 (Plus/Pro/Enterprise Tier Models). MaintenancePlan, MaintenancePlanAsset, Vendor, PurchaseOrder, PurchaseOrderLine, Warehouse, SubLocation, InventoryStock, and Fleet models all appear twice — first starting around line 900, then again starting around line 1353 (after a second "# PART 2" heading).

**Action Required:** Remove the duplicate section.

---

## Gap 3.2 — Data Models V3: SystemErrorLog Duplicate Field
**Severity:** MINOR
**Issue:** The `SystemErrorLog` model has `updated_on` listed twice (lines 1241-1242).

**Action Required:** Remove the duplicate field.

---

## Gap 3.3 — Lite MVP V4: "Companies" vs. "Customers" Terminology
**Severity:** MODERATE
**Issue:** The Lite MVP V4 uses "Companies" in Section 6.2 (deletion rules — "Companies: Any linked Assets, Quotes, Work Orders, Invoices") and Section 12.2 (module capabilities — "## 12.2 Companies"). All other spec documents use "Customer" as the canonical entity name. The Top-Down Specification explicitly defines the naming convention: "Customer — The business or individual receiving service."

**Action Required:** Replace all instances of "Companies" with "Customers" in Lite MVP V4.

---

## Gap 3.4 — Lite MVP V4: Product Type Enum Mismatch
**Severity:** CRITICAL
**Issue:** Lite MVP V4 Section 12.4 defines Product types as: `Part, Service, Consumable, Kit`. The Top-Down Specification and Data Models V3 define Product types as: `Service, Product - Inventory, Product - Non-Inventory` with a separate `is_bundle` flag for kit/bundle handling.

These are completely different enum sets. A developer building from the Lite MVP would implement the wrong type system.

**Action Required:** Update Lite MVP V4 Section 12.4 to use the canonical Product type enum from the Top-Down Specification: `Service, Product - Inventory, Product - Non-Inventory`. Replace "Kit" with reference to the Bundle mechanism (`is_bundle` flag + BundleItem table).

---

## Gap 3.5 — Lite MVP V4: Employee Fields Contradict Triad Architecture
**Severity:** CRITICAL
**Issue:** Lite MVP V4 Section 18.3 defines Employee core fields with inline contact information:
- First Name, Last Name (directly on Employee)
- Address, City, State, Zip (directly on Employee)
- Phone 1, Phone 2 (directly on Employee)
- Work Email, Personal Email (directly on Employee)

This contradicts the Data Models V3 architecture where:
- User → Person (FK person_id) for First/Last Name
- Phone numbers managed via shared Phone table
- Addresses managed via shared Address table
- Emails managed via shared Social table
- No contact fields stored directly on the User model

A developer following the Lite MVP would build inline fields on Employee. A developer following Data Models V3 would use the Triad architecture. These produce incompatible database schemas.

**Action Required:** Update Lite MVP V4 Section 18.3 to reference the Triad architecture (User → Person, shared Phone/Address/Social tables) instead of defining inline fields.

---

## Gap 3.6 — Lite MVP V4: Deletion Policy Conflicts with Data Models V3
**Severity:** MAJOR
**Issue:** Lite MVP V4 Section 6.8 states: "Notes are the only record type that cascade delete with their parent." and "Documents are considered a blocking relationship." However, Data Models V3 Section 5.1 states: "If a top-level entity has any child records, it cannot be deleted. The user must delete all children before the parent." and lists preferred soft-delete alternatives (Status = Inactive/Decommissioned/Cancelled).

These describe different deletion philosophies. The Lite MVP treats Notes as cascade-delete and Documents as blocking. Data Models V3 doesn't differentiate between Notes and Documents for deletion behavior and suggests soft-delete as preferred.

**Action Required:** Reconcile deletion behavior across documents. Define a single authoritative deletion policy that both documents reference.

---

## Gap 3.7 — Lite MVP V4: Contact Limit (2 per Customer)
**Severity:** MAJOR
**Issue:** Lite MVP V4 Section 12.2 specifies "Contacts (2)" as a limit for Lite tier. The Top-Down Specification Section 1.1 states "Can add unlimited Contacts per Customer." The ERD shows no contact limit.

This is potentially an intentional Lite tier gate (limit contacts to keep it simple). However, it's not reflected in the Product Tier Map V2 or the Top-Down spec's tier feature matrix. If it's intentional, it needs to be formally documented as a tier-gated limit.

**Action Required:** If the 2-contact limit is intentional for Lite, add it to the Product Tier Map V2 feature matrix and the Top-Down Specification tier summary. If it's an error, remove it from Lite MVP V4.

---

## Gap 3.8 — Lite MVP V4: Phone Number Structure
**Severity:** MAJOR
**Issue:** Lite MVP V4 Section 12.2 specifies phone numbers as "Fax, Phone1, Phone2" — implying exactly three fixed phone fields. The ERD, Top-Down spec, and Data Models V3 all use a shared Phone table with unlimited entries per entity and typed records (Mobile, Office, Home, Fax, Other).

**Action Required:** Update Lite MVP V4 to reference the shared Phone table structure rather than fixed fields. If Lite intentionally limits the number of phone records, document this as a tier gate.

---

## Gap 3.9 — NotesorDocuments Entity: Missing FK Coverage
**Severity:** MAJOR
**ERD NotesorDocuments FKs:** FK Customer, FK Contact, FK Lead, FK Opportunity, FK Quotes, FK Invoices, FK WorkOrders, FK Assets, FK TroubleCalls, FK PM, FK WorkFlows, FK Payments, FK Assets (duplicate?), FK Employees, FK Purchases, FK Inventory, FK Warehouse, FK Vendors, FK Vechicles, FK Ledger, FK Requisitions, FK RMAs, FK Equipment, FK SafetyForms, FK VendorBills.

**Specs Data Models V3 Note/Document FKs:** customer_id, contact_id, quote_id, invoice_id, work_order_id, asset_id, payment_id, user_id, vendor_id, purchase_order_id, project_id, task_id, vehicle_id, service_request_id.

**Missing FKs on Note/Document (entities from ERD not yet in specs):**
- FK Lead (→ Leads entity — Gap 1.4)
- FK Opportunity (→ Opportunity entity — Gap 1.4)
- FK TroubleCall (→ Gap 1.1)
- FK PM (→ PreventativeMaintenance — Gap 2.6)
- FK WorkFlow (→ Gap 2.7)
- FK Inventory/Product (→ already named `product_id` — confirm present... actually not present in Note/Document)
- FK Warehouse
- FK Ledger
- FK Requisitions (→ PartRequisition)
- FK RMA (→ Gap 1.12)
- FK Equipment (→ Gap 1.5)
- FK SafetyForms (→ Gap 1.6)
- FK VendorBills (→ Gap 1.8)

**Action Required:** After all missing entities are defined, update the Note and Document models to include FKs for every entity that can have notes/documents attached, matching the ERD's comprehensive list.

---

# PART 4 — SUMMARY & PRIORITIZED ACTION PLAN

## Statistics

| Severity | Count |
|---|---|
| BLOCKER | 13 |
| CRITICAL | 8 |
| MAJOR | 6 |
| MODERATE | 2 |
| MINOR | 2 |
| **Total** | **31** |

## Root Cause

The specification suite was built outward from the Lite MVP rather than downward from the ERD. The Top-Down Specification (which should represent the full system ceiling) was itself influenced by the Lite MVP scope. As a result:
- Entire ERD subsystems (WorkGroup, Leads/Opportunities, Equipment/Tools, Safety Forms, Agreements) were never specified.
- The WorkFlow subsystem was reduced from a full operational definition (steps → ToDos → required tools → required parts) to a minimal automation trigger.
- Financial entities (VendorBills, Banks, Carrier, dual Payment types, Accounting) were collapsed or omitted.
- Supply chain entities (RMA, Receiving, LotInfo, InventoryCounts, InventoryTransfers, InvPriceHistory) were omitted.
- Data Models V3 was built to match the Top-Down spec rather than the ERD, inheriting all its omissions.

## Recommended Resolution Order

**Phase 1 — Foundational (resolve before any further spec work):**
1. Resolve Gap 2.1 — WorkOrder single FK vs. M2M for Assets (architectural decision)
2. Resolve Gap 2.7 — WorkFlow subsystem definition (drives PM, WO, and Equipment gaps)
3. Resolve Gap 2.6 — PreventativeMaintenance vs. MaintenancePlan reconciliation

**Phase 2 — Missing Entity Definitions (add to Top-Down Specifications):**
4. Gap 1.1 — TroubleCall
5. Gap 1.2 — WorkGroup subsystem
6. Gap 1.3 — Agreements / CustomerAgreements
7. Gap 1.4 — Leads / Opportunity / Oppt-SASSIGNED-Contact
8. Gap 1.5 — Equipment / Check In-Out / WFTools
9. Gap 1.6 — SafetyForms / WOSFAnswers
10. Gap 1.7 — Skills / EmployeeSkills
11. Gap 1.8 — VendorBills
12. Gap 1.9 — Banks
13. Gap 1.10 — Accounting entity
14. Gap 1.11 — Carrier
15. Gap 1.12 — RMA
16. Gap 1.13 — Inventory subsystem detail (5 entities)
17. Gap 1.14 — Positions
18. Gap 1.15 — CreditCards
19. Gap 1.16 — VehicleInventory

**Phase 3 — Structural Corrections (update Data Models V3):**
20. Gap 2.2 — Add missing WorkOrder FKs
21. Gap 2.3 — Add WorkOrderTeam M2M
22. Gap 2.4 — Add Carrier/Bank FKs to triad tables
23. Gap 2.9 — Define VendorPayment model
24. Gap 3.9 — Update Note/Document FK coverage

**Phase 4 — Document Cleanup:**
25. Gap 3.1 — Remove Data Models V3 duplicated Part 2
26. Gap 3.2 — Fix SystemErrorLog duplicate field
27. Gap 3.3 — Fix Companies → Customers terminology
28. Gap 3.4 — Fix Product Type enum
29. Gap 3.5 — Fix Employee inline fields → Triad architecture
30. Gap 3.6 — Reconcile deletion policies
31. Gap 3.7 — Formalize Contact limit tier gate
32. Gap 3.8 — Fix Phone number structure
33. Gap 2.5 — Add Inventory/Product naming note
34. Gap 2.8 — Clean up Ledger/LedgerEntry naming

---

**End of ServizmaDesk Gap Analysis V3**
