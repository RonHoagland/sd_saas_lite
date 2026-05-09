# ServizmaDesk Gap Analysis V5

**Document Status:** Complete
**Date:** March 17, 2026
**Classification:** Internal — Confidential
**Truth Sources:** SD_System_ERD — Base System V7, ServizmaDesk Pricing & Billing Specification V2 (v2.11)
**Baseline:** Gap Analysis V4 (March 16, 2026)
**Scope:** Base System V7 alignment + Pricing & Billing V2 alignment across all current spec documents

---

## Scope Notes

- **ERD V7** is the primary structural truth source. Employee, Sessions/System Logs, and Fleet Maintenance entities have been separated into their own ERDs (Employee V1, System Logs V1, Fleet Maintenance V1). References to those entities in spec documents are flagged in Category 6 (Out of Scope) for a future pass — not treated as gaps in this analysis.
- **Pricing & Billing Specification V2 (v2.11)** is the pricing/billing truth source.
- **ERD V7 changes from V6:** The structural entity map is substantively identical to V6 for Base System purposes. The key change is the removal of Employee, Session/SystemLog, and Fleet entities to their own ERDs. The Sprint/Milestone/Portfolio/AssociatedTasks entities (future ServizmaProjects) remain in Base V7 and are correctly out of scope for current specs.

---

## Summary Dashboard

| Category | Gap Count | Blockers | Should Fix | Housekeeping |
|---|:---:|:---:|:---:|:---:|
| 1. ERD V7 Structural Mismatches | 6 | 5 | 1 | — |
| 2. P&B V2 Conflicts (Pricing Truth) | 2 | 2 | — | — |
| 3. Batch Corrections Still Pending | 4 | 2 | 2 | — |
| 4. Missing ERD V7 Entities | 2 | 1 | 1 | — |
| 5. Stale Version References | 6 | — | — | 6 |
| 6. Out of Scope (Future Pass) | 3 | — | — | 3 |
| **TOTAL** | **23** | **10** | **4** | **9** |

---

## Severity Definitions

- **Blocker:** Structural or data inconsistency that would cause implementation conflicts. Must resolve before development begins on the affected module.
- **Should Fix:** Accuracy issue that won't block implementation but will cause confusion during development or QA. Resolve before Beta.
- **Housekeeping:** Cosmetic or reference issue. Low risk. Resolve during next document maintenance pass.

---

# Category 1 — ERD V7 Structural Mismatches

These gaps represent cases where spec documents describe entity structures, relationships, or terminology that conflict with ERD V7.

---

### Gap 1.1 — Top-Down V3: Still Uses "Service Request" Instead of "TroubleCall"

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3
**ERD V7 Truth:** TroubleCall entity (Key ID, FKAsset, FKCustomer)
**Carryover from V4:** Yes — was flagged in V4, remains unresolved

**Problem:** Top-Down V3 Section 1.3 defines a "Service Request (Call Intake) Entity" with prefix SR26-0001 and a status set (New, Triaged, Converted to Work Order, Converted to Quote, Cancelled) that does not match TroubleCall.

**Specific locations:**
- Section 1.3 title and body (lines 187–210): Full "Service Request" entity definition
- Section 5.2 Customer Portal (lines 1100, 1117): References "Service Request (Section 1.3)"

**Already correct in:**
- Data Models V4 — defines `TroubleCall` (Section 1.4, line 509)
- System Status V2 — Section 9 defines TroubleCall lifecycle
- CSV Export V3 — uses "TroubleCall Number"
- Permission Management V2 — uses `crm_troublecall`
- Tenant Provisioning Seed Data V2 — uses prefix `TC`

**Fix:** Replace Section 1.3 entity with TroubleCall, update prefix to TC26, align status values with System Status V2 and Data Models V4. Update Customer Portal references to say "TroubleCall" instead of "Service Request."

---

### Gap 1.2 — Top-Down V3: Work Order ↔ Asset Cardinality Still Says M2M

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3
**ERD V7 Truth:** WorkOrder has a single FKAsset (one Asset per Work Order)
**Carryover from V4:** Yes — was flagged in V4, remains unresolved

**Problem:** Top-Down V3 describes Work Order ↔ Asset as many-to-many in multiple locations:

- Section 1.4, line 221: "Multiple Assets can be linked to one Work Order"
- Section 12.1, line 1636: "Work Order (many) ←→ (many) Assets [recommended, asset-centric link]"

**Already correct in:**
- Data Models V4, Architectural Mandate #9: "One Asset per Work Order — Work Orders link to exactly one Asset via a direct FK. Multi-asset coordination is handled via WorkGroups."
- ERD V7: WorkOrder has FKAsset (single FK), WorkGroupAssets provides the rolled-up multi-asset view

**Fix:** Update Section 1.4 to state one Asset per Work Order (nullable FK). Update Section 12.1 relationship summary to show `Work Order (many) ←→ (0..1) Asset`. Add a note that multi-asset coordination uses WorkGroups.

---

### Gap 1.3 — Top-Down V3: Missing Agreement → CustomerAgreement → PM Chain

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3
**ERD V7 Truth:** Agreements → CustomerAgreements (FKCustomer, FKAgreement, FKAsset) → PreventativeMaintenance (FKWorkFlow, FKAssets, FKCustomers, FKCustAgreements)
**Carryover from V4:** Yes — was flagged in V4, remains unresolved

**Problem:** Top-Down V3 Section 2.1 describes Maintenance Plans as directly linked to Customer and Asset(s). There is no mention of the Agreement entity, CustomerAgreement junction table, or the three-layer chain that ERD V7 and Data Models V4 both define.

**Already correct in:**
- Data Models V4, Section 2.2: Defines `Agreement`, `CustomerAgreement`, and `PreventativeMaintenance` with the correct FK chain
- ERD V7: Shows the full chain clearly

**Fix:** Rewrite Section 2.1 to describe the Agreement → CustomerAgreement → PM architecture. Agreement defines the template/terms, CustomerAgreement links a specific Customer + Agreement + Asset, and PM records generate Work Orders under a CustomerAgreement.

---

### Gap 1.4 — Top-Down V3: WorkFlow Not Described as Full SOP Engine

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3
**ERD V7 Truth:** WorkFlow → WFSteps → WFStepToDos + WFTools (FKEquipment) + WFInventory (FKInventory) + WFSafetyForms (FKSafetyForm)
**Carryover from V4:** Yes — was flagged in V4, remains unresolved

**Problem:** Top-Down V3 Section 8 describes "Custom Workflows" as custom status sequences (e.g., "Permit Applied → Material Ordered → Installation"). This is not what WorkFlow is in the ERD. WorkFlow in ERD V7 is a full Standard Operating Procedure engine with structured Steps, per-step ToDos, required Tools, required Inventory, and linked Safety Forms.

The WorkFlow entity does not appear as a defined entity anywhere in Top-Down V3. Section 8 conflates custom Work Order status sequences with the WorkFlow SOP engine — these are two different things.

**Already correct in:**
- Data Models V4, Section 3.1: Defines `WorkFlow`, `WFStep`, `WFStepToDo`, `WFTool`, `WFInventory` as the full SOP engine
- ERD V7: Shows the complete WorkFlow sub-graph

**Fix:** Add a WorkFlow Entity section to Top-Down V3 describing the SOP engine structure: WorkFlow → Steps → StepToDos, plus required Tools (via Equipment), required Inventory (via Product), and required SafetyForms. Clarify that Section 8 "Custom Status Workflows" (Pro/Enterprise) is a separate concept from the WorkFlow SOP engine.

---

### Gap 1.5 — Top-Down V3 & Data Models V4: Full Project Entity Still Present

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3, Data Models V4
**ERD V7 Truth:** WorkGroup(Project) is the base system grouping mechanism. Sprint, Milestone, Portfolio entities reference a future "Project" entity reserved for ServizmaProjects.
**Carryover from V4:** Yes — was flagged in V4 as a batch correction, remains unresolved in both documents

**Problem in Top-Down V3:**
- Section 1.5 (lines 305–334): Full "Project Entity" definition with fields, status, components
- Section 10.3 (lines 1463–1465): "Project Numbering" with PJ prefix
- Section 11.1 (lines 1587–1597): "Project Workflow" describing multi-phase work
- Section 12.1 relationship summary: Project relationships throughout (lines 1626, 1637, 1645–1646, 1651, 1658)
- Section 16 tier table (line 2089): "Projects | — | ✓ | ✓ | ✓"
- Multiple "Related Project" references on Work Order (222), Quote (345), Invoice (450), PO (730)

**Problem in Data Models V4:**
- Project entity defined at line 485 with project_number (PJ26-0001)
- `project_id` FK on: WorkOrder (541), Quote (699), Invoice (764), Note (932), Requisition (1435)
- TenantPreference: `project_prefix` (178) and `project_start_number` (179)
- Part 5 Delete Rules (line 2139): Lists Project as a top-level entity

**Fix:** In both documents, replace "Project" with "WorkGroup" as the grouping mechanism. Remove the standalone Project entity definition. Replace project_id FKs with work_group_id (already present on WorkOrder and Task in Data Models V4). Remove Project Numbering from TenantPreference. Update the "Project Workflow" section to describe WorkGroup-based multi-WO coordination. Reserve "Project" naming for future ServizmaProjects product.

---

### Gap 1.6 — Product Tier Map V2: Vendor Architecture Fundamentally Wrong

**Severity:** BLOCKER
**Documents Affected:** Product Tier Map V2
**ERD V7 Truth:** Vendor is a completely standalone entity with its own Contacts (VContact), Phones (VPhones), and Addresses (VAddress) — zero connection to Customers.
**Carryover from V4:** Yes — was flagged in V4, remains unresolved

**Problem:** Product Tier Map V2 describes Vendors as a flag on the Customer table in two locations:

- Line 160: "Customer records gain a customer_type field (Customer, Vendor, Both). Single Customers table — vendor-specific UI elements appear only on vendor-flagged records."
- Line 395: "Customers are stored in a single table with a customer_type field (Customer, Vendor, Both)."
- Line 251 tier table: "Customers (Vendor Flag)"

**Already correct in:**
- Top-Down V3, Section 1.13: "Standalone Entity: Vendors are a completely separate entity from Customers. There is no connection between them."
- Data Models V4: Vendor defined as a standalone entity in Part 2
- ERD V7: Vendor is its own entity with VContact, VPhones, VAddress sub-tables

**Fix:** Rewrite the Plus tier Vendor description to match the standalone entity architecture. Remove customer_type language. Describe Vendor as an independent entity unlocked at Plus tier with its own Contact/Phone/Address records.

**Note:** This was already flagged as requiring a "major overhaul" of Product Tier Map V2 in the V4 gap analysis.

---

# Category 2 — Pricing & Billing V2 Conflicts

These gaps represent cases where spec documents contradict P&B V2 (truth source) on pricing, billing, or feature tier assignments.

---

### Gap 2.1 — Top-Down V3: Lite SMS and Email Contradicts P&B V2

**Severity:** BLOCKER
**Documents Affected:** Top-Down Specifications V3
**P&B V2 Truth:** Lite gets 100 SMS points/month (manual only) and 400 email points/month (manual only)

**Problem — SMS:**
- Section 14.5 (line 2015): "SMS — Available in: Plus and Pro tiers only." — This omits both Lite (100 points, manual only) and Enterprise.
- Section 16 tier table (line 2133): SMS shown as "—" for Lite.

**Problem — Email:**
- Section 14.5 (line 2011): "Lite: No system email sending. Users send from their own email client externally." — P&B V2 gives Lite 400 email points/month for manual sends (quote sends, invoice sends).
- Section 16 tier table (line 2134): System Email shown as "—" for Lite.

**Also:** Section 14.5 SMS text says "Plus and Pro tiers only" which omits Enterprise, though the tier table in Section 16 correctly shows Enterprise with ✓ for SMS.

**Fix:**
- Update Section 14.5 SMS text: "Available in all tiers. Lite: manual only (100 points/month). Plus, Pro, Enterprise: manual and automated."
- Update Section 14.5 Email text: "Available in all tiers. Lite: manual only (400 points/month — quote sends, invoice sends). Plus and above: manual and automated."
- Update Section 16 tier table: Change SMS and System Email from "—" to "✓ (manual)" for Lite.
- Reference P&B V2 Section 10 and 10A for allotment details.

---

### Gap 2.2 — Product Tier Map V2: Same Lite SMS/Email Conflict

**Severity:** BLOCKER
**Documents Affected:** Product Tier Map V2
**P&B V2 Truth:** Same as Gap 2.1

**Problem:**
- Line 130: "No system email sending — users send from their own email client."
- Lines 313–314: SMS and System Email both "—" for Lite in the tier comparison table.
- Lines 142–143: SMS and system email listed as features Lite does NOT have (Plus additions).

**Fix:** Update Lite description and tier table to reflect P&B V2 allocations. Lite has SMS (100 points, manual only) and email (400 points, manual only). Adjust the "Plus additions" list to say Plus *adds automated* SMS/email triggers rather than SMS/email as concepts.

---

# Category 3 — Batch Corrections Still Pending

These were identified in the V4 analysis as batch corrections needed across documents. They remain unresolved.

---

### Gap 3.1 — Data Models V4 & Top-Down V3: Customer Status Missing Hold/Closed

**Severity:** SHOULD FIX
**Documents Affected:** Data Models V4, Top-Down Specifications V3

**Problem:**
- Data Models V4 line 278: Customer status = `Active, Inactive`
- Top-Down V3 line 38: Customer status = `Active, Inactive`
- Required: `Active, Inactive, Hold, Closed` with `hold_date`, `hold_reason`, and `closed_at` fields on Customer

**Fix:** Add Hold and Closed to the Customer status enum in both documents. Add the three associated date/reason fields to the Customer model in Data Models V4.

---

### Gap 3.2 — Data Models V4: Vehicle Prefix Still "V" Instead of "VS"

**Severity:** HOUSEKEEPING (but noting it was flagged as a batch correction)
**Documents Affected:** Data Models V4

**Problem:**
- Line 2047: `vehicle_number` shows "V26-0001" — should be "VS26-0001"
- TenantPreference line 182: `vehicle_prefix` default is "V" — should be "VS"

**Note:** Vehicle entity has moved to Fleet Maintenance ERD V1. This fix may be deferred to the Fleet ERD alignment pass. Re-categorizing as **SHOULD FIX** since Data Models V4 still defines the Vehicle model in Part 4.

---

### Gap 3.3 — Data Models V4: SMTP Fields Should Be Custom Domain Email Fields

**Severity:** BLOCKER
**Documents Affected:** Data Models V4

**Problem:** TenantPreference model (lines 184–191) still contains SMTP credential fields:
- `smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_use_tls`, `smtp_use_ssl`, `smtp_from_name`, `smtp_from_email`

BYOS (Bring Your Own SMTP) is explicitly not supported. This was confirmed in Email Specification V1, P&B V2, Top-Down V3, Technical Architecture V2, and SDP V2. These fields would implement a feature that has been architecturally ruled out.

**Fix:** Replace SMTP fields with Custom Domain Email fields:
- `custom_email_domain` (CharField, nullable)
- `domain_verification_status` (Enum: Pending, Verified, Failed)
- `postmark_domain_id` (CharField, nullable — Postmark's internal reference)
- Remove all `smtp_*` fields

---

### Gap 3.4 — Data Models V4: Project Entity and project_id FKs

**Severity:** BLOCKER
**See:** Gap 1.5 above — this is the Data Models V4 portion of the same issue.

---

# Category 4 — Missing ERD V7 Entities in Specs

---

### Gap 4.1 — Data Models V4: WFSafetyForms Junction Table Missing

**Severity:** BLOCKER
**Documents Affected:** Data Models V4
**ERD V7 Truth:** WFSafetyForms (Key ID, FKWorkFlow, FKSafetyForm) — links SafetyForms to WorkFlows

**Problem:** Data Models V4 Section 3.1 defines `WorkFlow`, `WFStep`, `WFStepToDo`, `WFTool`, and `WFInventory` — but does not define a `WFSafetyForm` junction table. ERD V7 clearly shows WFSafetyForms as a junction linking WorkFlow to SafetyForm.

Data Models V4 does define `SafetyForm` (line 1871) and `WOSFAnswers` (line 1888), but there's no way to associate required SafetyForms with a WorkFlow template — only with completed Work Orders.

**Fix:** Add `WFSafetyForm` model to Data Models V4 Section 3.1:
- `id` (UUIDv4 PK)
- `tenant_id` (UUID FK → Tenant)
- `workflow_id` (UUID FK → WorkFlow)
- `safety_form_id` (UUID FK → SafetyForm)

---

### Gap 4.2 — Top-Down V3: Quote Status Says "Approved" — Should Be "Accepted"

**Severity:** SHOULD FIX
**Documents Affected:** Top-Down Specifications V3

**Problem:** Top-Down V3 Section 1.6 (line 355) uses "Approved" as the Quote status for customer acceptance. Every other document uses "Accepted":
- Data Models V4 (line 702): `Accepted`
- System Status V2 (line 31): `Accepted`
- Product Tier Map V2 (line 110): `Accepted`

**Fix:** Change "Approved" to "Accepted" in Top-Down V3 Section 1.6 Quote Status list.

---

# Category 5 — Stale Version References

These are document cross-references pointing to superseded versions. Low risk but create confusion during development.

---

### Gap 5.1 — Top-Down V3: Self-Identifies as "V1"

**Severity:** HOUSEKEEPING
**Locations:**
- Header line 6: "Document Status: Working Draft — V1" (should be V3)
- Line 2054: "Top-Down Specifications V1 (this document)"
- Line 2161: "End of ServizmaDesk Top-Down Specifications V1"

---

### Gap 5.2 — Top-Down V3: References Technical Architecture V1

**Severity:** HOUSEKEEPING
**Locations:**
- Line 1942: "Technical Architecture V1"
- Line 2053: "Technical Architecture V1"
- Line 2062: "Technical Architecture V1"
**Should reference:** Technical Architecture V2

---

### Gap 5.3 — Data Models V4: Source Reference Says ERD V6 and Top-Down V2

**Severity:** HOUSEKEEPING
**Location:** Line 5: "Source: Derived from `SD_System_ERD__Base_System_V6.pdf` and `ServizmaDesk_Top_Down_Specifications_V2.md`"
**Should reference:** ERD V7 and Top-Down V3

---

### Gap 5.4 — Technical Architecture V2: References Data Models V1

**Severity:** HOUSEKEEPING
**Locations:**
- Line 19: "ServizmaDesk SDTA Data Models V1"
- Line 461: "Depends On / Validates Against — ServizmaDesk SDTA Data Models V1"
**Should reference:** Data Models V4

---

### Gap 5.5 — Pricing & Billing V2: References Top-Down Specifications V1

**Severity:** HOUSEKEEPING
**Locations:**
- Line 921: Supersedes section references "Top-Down Specifications V1"
- Line 927: Depends On section references "Top-Down Specifications V1"
- Line 934: Referencing docs list references "Top-Down Specifications V1"
**Should reference:** Top-Down Specifications V3

---

### Gap 5.6 — Email Specification V1: Live Reference to Top-Down V1

**Severity:** HOUSEKEEPING
**Location:** Line 384: "Top-Down Specifications V1 — Communication features per tier"
**Should reference:** Top-Down Specifications V3
**Note:** Lines 367–370 also reference "Top-Down Specifications V1" but these are in a completed-updates tracking table (historical record) and do not need correction.

---

# Category 6 — Out of Scope (Entities Moved to Separate ERDs)

Per Ron's instruction, these are flagged for a future alignment pass — not treated as gaps in this analysis.

---

### Gap 6.1 — Data Models V4: SessionLog and AuditEvent Still Defined

**Future Pass Item**
Data Models V4 Section 1.1 (line 212) and Section 1.9 (line 234) still define `SessionLog` and `AuditEvent` models. These entities have been moved to the System Logs ERD V1. When a future alignment pass is done against System Logs ERD V1, verify these definitions are consistent or determine whether they should be removed from Data Models V4 and placed in a separate System Logs data model document.

---

### Gap 6.2 — Data Models V4: Fleet Entities Still Defined

**Future Pass Item**
Data Models V4 Part 4 (lines 2039–2130) still defines `Vehicle`, `VehicleMaintenance`, `MileageLog`, and `VehicleInventory`. These entities have been moved to the Fleet Maintenance ERD V1. Same future alignment consideration as 6.1.

---

### Gap 6.3 — Data Models V4: Employee/User Entity Definition Scope

**Future Pass Item**
Data Models V4 Section 1.1 defines the `User` model (Employee). The Employee entity has been moved to its own ERD (Employee V1). The `User` model in Data Models V4 covers the SDTA login/access aspects, which is appropriate for the Base System, but field parity with Employee ERD V1 should be verified in a future pass.

---

# Recommended Fix Priority

## Phase 1 — Blockers (Before Development)

| Priority | Gap | Document | Effort |
|:---:|---|---|---|
| 1 | 1.5 + 3.4 | Top-Down V3 + Data Models V4 | HIGH — Remove Project entity, replace with WorkGroup throughout |
| 2 | 1.1 | Top-Down V3 | MEDIUM — Replace Service Request with TroubleCall |
| 3 | 1.2 | Top-Down V3 | LOW — Fix WO↔Asset cardinality text |
| 4 | 1.3 | Top-Down V3 | MEDIUM — Rewrite Maintenance Plan section with Agreement chain |
| 5 | 1.4 | Top-Down V3 | MEDIUM — Add WorkFlow SOP engine description |
| 6 | 1.6 | Product Tier Map V2 | HIGH — Rewrite Vendor architecture (part of planned major overhaul) |
| 7 | 2.1 | Top-Down V3 | LOW — Fix SMS/Email tier text and table |
| 8 | 2.2 | Product Tier Map V2 | LOW — Fix SMS/Email Lite entries |
| 9 | 3.3 | Data Models V4 | LOW — Replace SMTP fields with Custom Domain fields |
| 10 | 4.1 | Data Models V4 | LOW — Add WFSafetyForm junction table |

## Phase 2 — Should Fix (Before Beta/QA)

| Priority | Gap | Document | Effort |
|:---:|---|---|---|
| 11 | 3.1 | Data Models V4 + Top-Down V3 | LOW — Add Hold/Closed to Customer status |
| 12 | 3.2 | Data Models V4 | LOW — Vehicle prefix V→VS |
| 13 | 4.2 | Top-Down V3 | LOW — Quote status Approved→Accepted |
| 14 | 5.1–5.6 | Multiple | LOW — Version reference updates |

## Phase 3 — Future Pass (Separate ERD Alignment)

| Item | Description |
|---|---|
| 6.1 | Verify SessionLog/AuditEvent against System Logs ERD V1 |
| 6.2 | Verify Vehicle/Fleet models against Fleet Maintenance ERD V1 |
| 6.3 | Verify User/Employee model against Employee ERD V1 |

---

# Observations

## What's Working Well

1. **Data Models V4** is the strongest document in the suite — it correctly implements most ERD V6/V7 architecture including TroubleCall, the Agreement→CustomerAgreement→PM chain, WorkGroups, the full WorkFlow SOP engine (minus WFSafetyForms), and one-asset-per-WO.

2. **Recently updated docs are clean.** CSV Export V3, Permission Management V2, System Status V2, Tenant Provisioning Seed Data V2, Background Tasks V2, Onboarding Triggers V2, and Database Specification V2 all use correct ERD V6/V7 terminology and architecture. The targeted update pass worked.

3. **P&B V2 is internally consistent and well-maintained.** No structural issues found. The only P&B-related gaps are in other documents failing to reflect P&B V2 decisions.

4. **SDP V2 is clean.** Correctly defers all pricing to P&B V2, uses no stale entity names.

## What Needs Attention

1. **Top-Down V3 has the most gaps (9 of 23).** Five of the six Category 1 blockers and both Category 2 blockers touch this document. It is the single highest-priority document to fix.

2. **Five of the V4 blocker items (1.1–1.5) remain unresolved.** These were first identified in the V4 gap analysis and have carried forward unchanged. Top-Down V3 has not been updated since V4 was delivered.

3. **Product Tier Map V2 major overhaul** is still needed. The Vendor architecture issue (Gap 1.6) plus the SMS/Email Lite issue (Gap 2.2) reinforce that this document needs a comprehensive rewrite against ERD V7 and P&B V2.

---

# SDP V1 — Legacy Document Note

SDP Specification V1 still contains stale pricing ($28/$24 per seat) at lines 472, 487, and 623. This document is fully superseded by SDP V2, which correctly defers all pricing to P&B V2. No action required unless SDP V1 is still being consulted by anyone — in which case it should be archived or clearly marked as superseded.

---

**End of Gap Analysis V5**
