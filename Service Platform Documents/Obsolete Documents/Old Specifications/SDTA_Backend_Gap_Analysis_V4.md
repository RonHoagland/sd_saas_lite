# ServizmaDesk — Cross-Document Gap Analysis V4

**Document Status:** Working Draft — V4
**Date:** March 2026
**Classification:** Internal — Confidential
**Source of Truth:** `SD_System_ERD__Base_System_V6.pdf`, `ServizmaDesk_Pricing_and_Billing_Specification_V2.md` (V2.11)
**Supersedes:** SDTA_Backend_Gap_Analysis_v3.md

---

## Analysis Scope

This gap analysis compares the full refreshed document library against two primary sources of truth:

1. **ERD V6** — the canonical entity/relationship diagram defining all SDTA data entities, their fields, and relationships
2. **Pricing & Billing Specification V2 (V2.11)** — the canonical source for all pricing, billing, storage, SMS, email, and add-on module definitions

Every document in the project library was examined for conflicts with these two sources, as well as for inter-document consistency issues introduced by recent updates to multiple specs simultaneously.

---

## Summary

| Category | Count |
|---|---|
| **Blocker — Must Fix Before Development** | 10 |
| **Should Fix — Before Beta/QA** | 9 |
| **Cosmetic / Low-Risk** | 3 |
| **Total Gaps** | 22 |

---

# BLOCKER GAPS — Must Fix Before Development

These gaps represent architectural conflicts, incorrect cardinality, or wrong entity definitions that would produce broken implementations if coded against.

---

### Gap 4.1 — Top-Down V3: Work Order ↔ Asset Cardinality Is Wrong

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Line 221, Line 1636
**Conflict With:** ERD V6, Data Models V4 (Architectural Mandate #9)

**Problem:** Top-Down V3 states "Multiple Assets can be linked to one Work Order" (Section 1.4, line 221) and the entity relationship summary shows "Work Order (many) ←→ (many) Assets" (line 1636). ERD V6 and Data Models V4 mandate **One Asset per Work Order** via a direct FK (`asset_id` on WorkOrder, Required). Multi-asset coordination is handled via WorkGroups, not M2M junctions on WorkOrder.

**Required Fix:**
- Section 1.4, line 221: Change "Multiple Assets can be linked to one Work Order" to "One Asset per Work Order (direct FK). Multi-asset coordination handled via WorkGroups (Plus+)."
- Section 12.1 relationship summary (line 1636): Change `Work Order (many) ←→ (many) Assets` to `Work Order (many) ←→ (1) Asset [required — one asset per WO]`

---

### Gap 4.2 — Top-Down V3: Uses "Service Request" Instead of "TroubleCall"

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Lines 187–211, 1100, 1117
**Conflict With:** ERD V6, Data Models V4

**Problem:** Section 1.3 defines the call intake entity as "Service Request" with auto-generated numbering `SR26-0001`. ERD V6 names this entity `TroubleCall`. Data Models V4 correctly uses `TroubleCall` with numbering `TC26-0001` and a direct FK on WorkOrder. Sections 5.2 (Customer Portal, lines 1100, 1117) also reference "Service Request."

**Required Fix:**
- Rename Section 1.3 from "Service Request (Call Intake) Entity" to "TroubleCall (Call Intake) Entity"
- Replace all field names: `Request Number → TroubleCall Number`, `SR26-0001 → TC26-0001`
- Update all "Service Request" references in Sections 5.2 to "TroubleCall"
- Add the direct FK from WorkOrder → TroubleCall (already present in Data Models V4 but not described in Top-Down V3)

---

### Gap 4.3 — Top-Down V3: Missing Agreement → CustomerAgreement → PM Chain

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Section 2.1 (lines 907–951)
**Conflict With:** ERD V6, Data Models V4 (Section 2.2)

**Problem:** Top-Down V3 describes Maintenance Plans linked directly to Customer and Asset(s) as a simple two-entity relationship. ERD V6 defines a three-tier architecture: **Agreement** (the plan template) → **CustomerAgreement** (three-way junction: Customer + Agreement + Asset) → **PreventativeMaintenance** (the actual recurring schedule) → auto-generated WorkOrders. Data Models V4 correctly implements this chain.

**Required Fix:**
- Add an Agreement entity definition (plan template with name, description, pricing, renewal terms)
- Add a CustomerAgreement entity definition (junction binding Customer + Agreement + Asset)
- Restructure Maintenance Plan section to show PM as a child of CustomerAgreement, not a standalone entity
- Update entity relationship summary (Section 12.1) to reflect the Agreement → CustomerAgreement → PM → WO chain

---

### Gap 4.4 — Top-Down V3: WorkFlow Not Described as SOP Engine

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Section 8.1 (lines 1258–1276)
**Conflict With:** ERD V6, Data Models V4 (Section 3.1)

**Problem:** Section 8 describes "Custom Workflows" as configurable Work Order status sequences (custom statuses like "Permit Applied" → "Material Ordered" → etc.). ERD V6 and Data Models V4 define WorkFlow as a **full SOP engine** with a proper entity hierarchy: WorkFlow → WFSteps → WFStepToDos (checklist items per step, with `is_required` flag) + WFTools (required Equipment per workflow) + WFInventory (required Product quantities per workflow). This is fundamentally richer than a status pipeline.

**Required Fix:**
- Rewrite Section 8.1 to describe WorkFlow as a full Standard Operating Procedure (SOP) entity with Steps, StepToDos, required Tools, and required Inventory
- Add WorkFlow to entity relationship summary (Section 12.1) showing the full entity tree
- Note that WorkFlow links to WorkOrder via FK and to PreventativeMaintenance via FK

---

### Gap 4.5 — Product Tier Map V2: Vendor Architecture Fundamentally Wrong

**Document:** `ServizmaDesk_Product_Tier_Map_V2.md`
**Locations:** Line 160 (Section 6.2 Plus), Line 251 (Feature Matrix), Lines 395 (Section 8.3)
**Conflict With:** ERD V6, Data Models V4 (Section 2.4), Top-Down V3 (Section 1.13)

**Problem:** Product Tier Map V2 describes vendors as a `customer_type` flag on Customer records: "Customer records gain a customer_type field (Customer, Vendor, Both). Single Customers table." Section 8.3 reiterates this: "Customers are stored in a single table with a customer_type field." ERD V6, Data Models V4, and Top-Down V3 all define **Vendor as a completely separate standalone entity** with its own table, its own Contacts (via shared Triad tables), its own Addresses, and its own Phones. There is explicitly "no connection" between Customer and Vendor.

**Required Fix:**
- Section 6.2 (Plus): Replace the `customer_type` flag description with "Vendor entity introduced as a standalone table. Vendor management UI becomes available. Purchase Orders link to Vendors."
- Feature Matrix (line 251): "Customers (Vendor Flag)" row should become "Vendors (Standalone Entity)"
- Section 8.3: Remove the `customer_type` field description entirely and replace with Vendor as a separate entity

**Impact:** This is a **major structural rewrite** for Product Tier Map V2, which is already flagged as needing a major overhaul.

---

### Gap 4.6 — Product Tier Map V2: "Projects, Epics, Use Cases" Are Legacy Terms

**Document:** `ServizmaDesk_Product_Tier_Map_V2.md`
**Locations:** Lines 217, 229–231
**Conflict With:** Batch corrections (Project reserved for future ServizmaProjects product)

**Problem:** Section 6.3 (Pro — Not Included) lists "Projects, Epics, Use Cases" as excluded features. Section 6.4 (Enterprise) defines "Projects" as a full project management module, "Epics" as project sub-components, and "Use Cases" as global intake objects. Per established batch corrections, **"Project" is reserved for the future ServizmaProjects product** and must not be used as an SDTA entity. WorkGroup is the SDTA grouping mechanism.

**Required Fix:**
- Remove "Projects, Epics, Use Cases" from Enterprise definition (Section 6.4)
- Remove "Projects, Epics, Use Cases" from Pro exclusion list (Section 6.3)
- If Enterprise needs a "complex multi-WO coordination" feature beyond WorkGroups, define it with new terminology that doesn't collide with ServizmaProjects

---

### Gap 4.7 — Data Models V4 & Top-Down V3: Project Entity Still Present

**Documents:** `ServizmaDesk_Data_Models_V4.md`, `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Data Models V4 lines 485–503, plus `project_id` FKs on WorkOrder (541), Quote (699), Invoice (764), Note (932), PurchaseOrder (1435). Top-Down V3 Section 1.5 (lines 305–334), plus `Related Project` references in Sections 1.4, 1.6, 1.7, 1.12, numbering config (lines 1463–1465), relationship summary (lines 1637, 1645–1646, 1651, 1658).
**Conflict With:** Batch corrections

**Problem:** Per batch corrections, the Project entity and all `project_id` FKs must be removed from SDTA documents. "Project" is reserved for future ServizmaProjects product. WorkGroup is the SDTA grouping mechanism.

**Required Fix (Data Models V4):**
- Remove the `Project` model definition entirely (lines 485–503)
- Remove `project_id` FK from WorkOrder, Quote, Invoice, Note, PurchaseOrder tables
- Remove `project_prefix` and `project_start_number` from TenantPreference (lines 178–179)

**Required Fix (Top-Down V3):**
- Remove Section 1.5 (Project Entity) entirely
- Remove "Related Project" from Work Order, Quote, Invoice, and Purchase Order entity definitions
- Remove Project numbering from Section 10.3
- Remove Project from entity relationship summary (Section 12.1)
- Remove Project Workflow from Section 11.1

---

### Gap 4.8 — Data Models V4: Vehicle Prefix "V" Should Be "VS"

**Document:** `ServizmaDesk_Data_Models_V4.md`
**Locations:** Line 182 (TenantPreference: `vehicle_prefix` Default: V), Line 2047 (`vehicle_number` V26-0001)
**Conflict With:** Batch corrections (Vehicle prefix "V" → "VS"; Vendor keeps "V")

**Problem:** Per batch corrections, Vehicle prefix should be "VS" (not "V") since "V" is reserved for Vendor. Top-Down V3 also uses V26-0001 at line 1765.

**Required Fix:**
- Data Models V4 line 182: Change `Default: V` to `Default: VS`
- Data Models V4 line 2047: Change `V26-0001` to `VS26-0001`
- Top-Down V3 line 1765: Change `V26-0001` to `VS26-0001`

---

### Gap 4.9 — Data Models V4 & Top-Down V3: Customer Status Missing Hold and Closed

**Documents:** `ServizmaDesk_Data_Models_V4.md` (line 278), `ServizmaDesk_Top_Down_Specifications_V3.md` (line 38)
**Conflict With:** Batch corrections

**Problem:** Customer status is defined as `Active, Inactive` in both documents. Per batch corrections, Customer status should be `Active, Inactive, Hold, Closed` with corresponding hold/closed date fields.

**Required Fix (Data Models V4):**
- Line 278: Change `Active, Inactive` to `Active, Inactive, Hold, Closed`
- Add `hold_date` (DateField, Nullable) and `closed_date` (DateField, Nullable) fields to Customer model

**Required Fix (Top-Down V3):**
- Line 38: Change `Active, Inactive` to `Active, Inactive, Hold, Closed`
- Add hold/closed semantics to Customer entity description

---

### Gap 4.10 — Data Models V4: SMTP Fields in TenantPreference (BYOS Not Supported)

**Document:** `ServizmaDesk_Data_Models_V4.md`
**Locations:** Lines 184–191
**Conflict With:** Email Specification V1, Pricing & Billing V2 (Section 10A), Top-Down V3 (Section 10.6)

**Problem:** TenantPreference contains BYOS SMTP fields (`smtp_host`, `smtp_port`, `smtp_username`, `smtp_password`, `smtp_use_tls`, `smtp_use_ssl`, `smtp_from_name`, `smtp_from_email`). BYOS is explicitly not supported per the Email Specification V1, Pricing & Billing V2, and Top-Down V3. All email delivery runs through Postmark. The Custom Domain Email add-on (Pro/Enterprise) uses DNS authentication, not SMTP credentials.

**Required Fix:**
- Remove all `smtp_*` fields from TenantPreference
- Add Custom Domain Email fields: `custom_email_domain` (CharField, Nullable), `domain_verification_status` (Enum: Pending/Verified/Failed, Nullable), `domain_verified_at` (DateTimeField, Nullable)

---

# SHOULD FIX — Before Beta/QA

These gaps are stale version references, cosmetic self-identification errors, or minor cross-reference inconsistencies that won't cause implementation bugs but should be corrected for document hygiene.

---

### Gap 4.11 — Top-Down V3: Self-Identifies as "V1" Throughout

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Line 2054 (Document Ownership Map: "Top-Down Specifications V1 (this document)"), Line 2161 (Footer: "End of ServizmaDesk Top-Down Specifications V1"), Line 7 (Status: "Working Draft — V1")

**Required Fix:** Update all self-references from V1 to V3.

---

### Gap 4.12 — Top-Down V3: References Technical Architecture V1 (V2 Exists)

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Locations:** Lines 2053, 2062

**Required Fix:** Update references from "Technical Architecture V1" to "Technical Architecture V2".

---

### Gap 4.13 — Data Models V4: Header References Top-Down Specifications V2 (V3 Exists)

**Document:** `ServizmaDesk_Data_Models_V4.md`
**Location:** Line 5 ("Derived from ... ServizmaDesk_Top_Down_Specifications_V2.md")

**Required Fix:** Update to "ServizmaDesk_Top_Down_Specifications_V3.md".

---

### Gap 4.14 — Internal API V1: References Data Models V2 (V4 Exists)

**Document:** `ServizmaDesk_Internal_API_Specification_V1.md`
**Location:** Line 777

**Required Fix:** Update to "Data Models V4". (Note: Internal API V1 is also flagged as needing a broader update to align with ERD V6 — this is a known item from the previous gap analysis.)

---

### Gap 4.15 — Lite MVP V4: References Data Models V3 (V4 Exists)

**Document:** `ServizmaDesk_Lite_MVP_V4_Specification.md`
**Location:** Line 93

**Required Fix:** Update to "Data Models V4". (Note: Lite MVP V4 is parked until Top-Down is fully flushed out.)

---

### Gap 4.16 — Email Spec V1: References "Top-Down Specifications V1" (V3 Exists)

**Document:** `ServizmaDesk_Email_Specification_V1.md`
**Locations:** Lines 367–370, 384

**Required Fix:** Update all references from "Top-Down Specifications V1" to "Top-Down Specifications V3".

---

### Gap 4.17 — Pricing & Billing V2: References "Top-Down Specifications V1" (V3 Exists)

**Document:** `ServizmaDesk_Pricing_and_Billing_Specification_V2.md`
**Locations:** Lines 7, 921, 927, 934

**Required Fix:** Update all references from "Top-Down Specifications V1" to "Top-Down Specifications V3".

---

### Gap 4.18 — SaaS Operational Plan V3: Header Still Says "ISBMG"

**Document:** `ServizmaDesk_SaaS_Operational_Plan_V3.md`
**Location:** Line 4 ("Company Name: Internet Solutions Business Management Group (ISBMG)")

**Required Fix:** Update to current branding. ISBMG is the behind-the-scenes legal entity; the document header should reference ServizmaDesk as the operational entity, consistent with all other documents.

---

### Gap 4.19 — SDP V1: Contains Stale Pricing ($24/$28) — Legacy Document Still in Library

**Document:** `ServizmaDesk_Platform__SDP__Specification_V1.md`
**Locations:** Lines 472, 487, 623

**Problem:** SDP V1 contains inline Lite pricing of $28/month ($24 annual) — stale figures from before pricing was finalized at $35/month ($29 annual). SDP V2 correctly delegates all pricing to Pricing & Billing V2 with no inline figures. SDP V1 is a superseded document but remains in the project library.

**Required Fix:** Either remove SDP V1 from the active library, or add a prominent "SUPERSEDED BY V2" watermark/header to prevent accidental reference.

---

# COSMETIC / LOW-RISK

These items are minor inconsistencies that don't affect implementation but should be cleaned up during the next document maintenance pass.

---

### Gap 4.20 — Top-Down V3: Product Tier Map V2 SMS Row Shows "—" for Lite

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Location:** Line 2133 (Tier Feature Mapping table — SMS row shows "—" for Lite)
**Conflict With:** Pricing & Billing V2 (Section 10.2 — Lite gets 100 SMS points/month, manual only)

**Required Fix:** Change Lite SMS from "—" to "✓ (manual)" or similar indicator, with a note that Lite SMS is manual-only (no automated triggers).

---

### Gap 4.21 — Top-Down V3: Stripe Payment Links Listed as Lite Feature in Tier Table

**Document:** `ServizmaDesk_Top_Down_Specifications_V3.md`
**Location:** Line 2150

**Observation:** The tier table shows "Stripe Payment Links ✓" for all tiers including Lite. This is consistent with Product Tier Map V2 and Pricing & Billing V2. No conflict — just noting for visibility that this is intentional (Lite gets Payment Links, Plus+ gets advanced embedded payment APIs).

**Status:** No fix needed.

---

### Gap 4.22 — Product Tier Map V2: Section 6.2 Plus SMS Description Is Vague

**Document:** `ServizmaDesk_Product_Tier_Map_V2.md`
**Location:** Line 168

**Problem:** SMS description says "Monthly allotment included with Plus. Additional point tiers available for purchase." The "additional point tiers" language predates the current overage-only model (no point packages at launch). Pricing & Billing V2 defines the current model as flat overage at $0.035/point with future packages deferred.

**Required Fix:** Update to: "Monthly allotment included with Plus. Overage charged per point beyond included allocation. See Pricing & Billing Specification V2, Section 10."

---

# Documents Confirmed Clean (No Gaps Found)

The following documents were reviewed and found to be consistent with ERD V6 and Pricing & Billing V2:

- `ServizmaDesk_multi_tenancy_spec_v1.md` — No ERD entity conflicts; architecture rules unchanged
- `ServizmaDesk_Invoice_Calculation_Specification_V1.md` — Calculation logic unchanged by ERD V6
- `ServizmaDesk_Stripe_Webhook_Specification_V1.md` — Webhook processing logic unchanged
- `ServizmaDesk_Universal_Query_Specification_V1.md` — Query patterns unchanged
- `ServizmaDesk_File_Upload_Specification_V1.md` — File storage logic unchanged
- `ServizmaDesk_Dashboard_Counter_Specification_V1.md` — Counter definitions unchanged
- `ServizmaDesk_Onboarding_Triggers_Specification_V2.md` — Already aligned to ERD V6
- `ServizmaDesk_System_Status_Specification_V2.md` — Already aligned to ERD V6 (uses TroubleCall, WorkGroup correctly)
- `ServizmaDesk_Background_Tasks_Specification_V2.md` — Already aligned to ERD V6
- `ServizmaDesk_Tenant_Provisioning_Seed_Data_Specification_V2.md` — Already aligned to ERD V6
- `ServizmaDesk_CSV_Export_Specification_V3.md` — Already aligned to ERD V6 (uses TroubleCall, WorkGroup correctly)
- `ServizmaDesk_Permission_Management_Specification_V2.md` — Already aligned to ERD V6
- `ServizmaDesk_Database_Specification_V2.md` — References Data Models V4 correctly
- `ServizmaDesk_GPS_Tracking_Strategy_Feasibility_Brief_V1.md` — Standalone feasibility doc; no entity conflicts
- Competitor analyses (Jobber, HousecallPro, Workiz, FieldPulse) — External analyses; unaffected by ERD changes

---

# Remaining Known Deferred Items (From Prior Analysis)

These items were identified in prior gap analyses and remain intentionally deferred:

1. **Skill/Certification requirements on Asset entity** — Skills required to work on an asset belong on the Asset entity (not WorkFlow). This requires a future `AssetSkill` junction table and assignment validation logic. Not yet added to ERD or specs. Deferred by design decision.

2. **Product Tier Map V2 — Major overhaul needed** — Product Tier Map V2 was already identified as needing the most work of any remaining document. This gap analysis confirms that assessment — Gaps 4.5, 4.6, and 4.22 add to the already-known overhaul scope.

3. **Internal API V1 — Full update needed** — Internal API V1 needs a comprehensive rewrite to align with ERD V6 entities and current Data Models V4. Gap 4.14 (stale version reference) is just the surface-level issue.

4. **Technical Architecture V2 — Stale Data Models V1 reference** — Line 19 and line 461 reference "ServizmaDesk SDTA Data Models V1"; should reference V4.

5. **Lite MVP V4 — Parked** — Lite MVP V4 is parked until Top-Down is fully flushed out. Once Top-Down V3 is corrected per this gap analysis, Lite MVP V4 should be reviewed and updated.

---

# Document Update Priority (Recommended Order)

Based on gap severity, dependency chains, and effort required:

| Priority | Document | Gaps | Effort |
|---|---|---|---|
| 1 | **Top-Down Specifications V3** | 4.1, 4.2, 4.3, 4.4, 4.7, 4.8, 4.9, 4.11, 4.12, 4.20 | High — structural rewrites to multiple sections |
| 2 | **Data Models V4** | 4.7, 4.8, 4.9, 4.10, 4.13 | Medium — entity removal, field changes, version refs |
| 3 | **Product Tier Map V2** | 4.5, 4.6, 4.22 | High — major overhaul (already known) |
| 4 | **Pricing & Billing V2** | 4.17 | Low — version reference updates only |
| 5 | **Email Spec V1** | 4.16 | Low — version reference updates only |
| 6 | **Lite MVP V4** | 4.15 | Low — parked; update when Top-Down is stable |
| 7 | **Internal API V1** | 4.14 | Low surface / High full rewrite (deferred) |
| 8 | **Technical Architecture V2** | Deferred item #4 | Low — version reference updates |
| 9 | **SaaS Operational Plan V3** | 4.18 | Low — branding update |
| 10 | **SDP V1** | 4.19 | Low — mark as superseded or remove |

---

*End of ServizmaDesk Cross-Document Gap Analysis V4*
