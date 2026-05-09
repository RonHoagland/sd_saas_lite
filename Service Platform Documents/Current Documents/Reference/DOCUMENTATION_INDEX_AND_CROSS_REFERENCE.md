# ServizDesk — Specification index & cross-reference

**What this is:** A **sorted inventory** of all living Markdown specifications, the **three ERD sources** they trace to, and a **cross-reference map** so teams can see which doc owns which decisions and where to look next.

**Scope:** `Design Information/Design Documents/` only — **excludes** `Old Docs/`, `Research - Future/`, and meta files like `DOCUMENTATION_CROSS_SPEC_CONFLICT_MATRIX.md`. *Competitor Analysis* is out of scope unless you add it.*

**Count:** There are **30** `.md` files in that tree. If your mental model is **”27 + 3 ERDs”**, the usual reconciliation is:

| Count | Meaning |
|-------|--------|
| **30** | Every living spec file on disk (below). Increased from 27 with the addition of three new implementation specs (Lifecycle Framework V1, Numbering Service V1, Note & Document Implementation V1). |
| **27** | **Canonical SDTA build set** if you do **not** treat these three as separate “sources of truth”: `Platform Spec Docs/ServizDesk_Platform__SDP__Specification_V2.md` (duplicate of root SDP V2), `Platform Spec Docs/ServizDesk Platform (SDP) Specification V1.md` (superseded generation), `ServizDesk_GPS_Tracking_Strategy_Feasibility_Brief_V1.md` (research; duplicate also under Research - Future). |
| **3 ERDs** | **Not** files in this repo — **PDFs named** in Data Models V6 (see § ERDs). Implementation truth for schema is **`ServizDesk_Data_Models_V6.md`**, not the PDFs, unless you re-import the PDFs into the repo. |

If your “24” is a different list (e.g. excludes `Platform Spec Docs/` entirely), say so and this table can be relabeled.

---

## 1. Three ERD sources (PDFs)

Declared in `ServizDesk_Data_Models_V6.md` (header):

1. `SD System ERD - Base System V12.pdf`
2. `SD System ERD - Employee V4.pdf`
3. `SD System ERD - System Logs V1.pdf`

**Cross-reference rule:** Any entity labeled “ERD: …” in Data Models V6 should match these diagrams **or** the doc’s explicit **Implementation Note** where the markdown intentionally diverges (e.g. `SubAsset` replacing `parent_asset_id` on `Asset`). Conflicts between **Top-Down V4** and **Data Models V6** on the same entity are tracked in `DOCUMENTATION_CROSS_SPEC_CONFLICT_MATRIX.md`.

---

## 2. Sorted inventory (all 30 files)

| # | Path | Role |
|---|------|------|
| 1 | `ServizDesk_Background_Tasks_Specification_V2.md` | Celery tasks, periodic jobs, purge ordering |
| 2 | `ServizDesk_CSV_Export_Specification_V3.md` | Export behavior, entity coverage |
| 3 | `ServizDesk_Dashboard_Counter_Specification_V1.md` | Dashboard metrics |
| 4 | `ServizDesk_Data_Models_V6.md` | **ORM / field-level authority** (SDTA) |
| 5 | `ServizDesk_Database_Specification_V2.md` | PostgreSQL roles, RLS, retention hooks |
| 6 | `ServizDesk_Email_Specification_V1.md` | Postmark, inbound/outbound, points |
| 7 | `ServizDesk_File_Upload_Specification_V1.md` | Uploads, scanning, storage paths |
| 8 | `ServizDesk_GPS_Tracking_Strategy_Feasibility_Brief_V1.md` | Research — GPS feasibility |
| 9 | `ServizDesk_Internal_API_Specification_V1.md` | **SDP ↔ SDTA** REST contract |
| 10 | `ServizDesk_Invoice_Calculation_Specification_V1.md` | Invoice math, rounding |
| 11 | `ServizDesk_Lifecycle_Framework_Specification_V1.md` | **Data-driven state machine** — deny-by-default transition enforcement, immutable audit trail |
| 12 | `ServizDesk_Note_Document_Implementation_Specification_V1.md` | **Note & Document models** — exclusive arc enforcement, file audit trail (FileUploadLog, FileDownloadLog) |
| 13 | `ServizDesk_Numbering_Service_Specification_V1.md` | **Number generation** — atomic sequences, configurable formatting, replaces SequenceTracker |
| 14 | `ServizDesk_Onboarding_Triggers_Specification_V2.md` | Onboarding checklist / triggers |
| 15 | `ServizDesk_Permission_Management_Specification_V2.md` | Resource keys, roles, CRUD matrix |
| 16 | `ServizDesk_Platform__SDP__Specification_V2.md` | **SDP (root copy)** — provisioning, billing lifecycle |
| 17 | `ServizDesk_Pricing_and_Billing_Specification_V2.md` | **Pricing / tiers / retention** (high coupling) |
| 18 | `ServizDesk_Product_Tier_Map_V2.md` | Tier feature matrix |
| 19 | `ServizDesk_SaaS_Operational_Plan_V3.md` | Ops runbook |
| 20 | `ServizDesk_Security_Features_Specification_V1.md` | Tenant-facing security |
| 21 | `ServizDesk_Stripe_Webhook_Specification_V1.md` | Stripe events |
| 22 | `ServizDesk_System_Status_Specification_V3.md` | **Status enumerations** (referenced heavily by Data Models and Lifecycle Framework) |
| 23 | `ServizDesk_Technical_Architecture_V2.md` | **Stack, boundaries, integrations** |
| 24 | `ServizDesk_Tenant_Provisioning_Seed_Data_Specification_V2.md` | Seed data at provision (NumberingRules, LifecycleStateDefs, roles) |
| 25 | `ServizDesk_Top_Down_Specifications_V4.md` | **Product ceiling, ownership map** |
| 26 | `ServizDesk_Universal_Query_Specification_V1.md` | Search/query UX |
| 27 | `ServizDesk_multi_tenancy_spec_v1.md` | Tenant middleware, managers, `SET LOCAL` |
| 28 | `Platform Spec Docs/ServizDesk_Lite_MVP_V4_Specification.md` | Lite MVP slice |
| 29 | `Platform Spec Docs/ServizDesk Platform (SDP) Specification V1.md` | **Legacy SDP** — prefer V2 for current rules |
| 30 | `Platform Spec Docs/ServizDesk_Platform__SDP__Specification_V2.md` | **Duplicate path** — must stay in sync with #16 or retire |

---

## 3. Cross-reference — who points to whom (hub view)

**Read first (hubs):**

- **Top-Down V4** — Section 15 ownership map; defers pricing/stack to other docs.
- **Technical Architecture V2** — cites SDP V2, Pricing V2, Multi-Tenancy V1, Data Models V6.
- **Data Models V6** — cites System Status V3, File Upload V1, Pricing V2, Email V1, Technical Architecture V2, Onboarding V2.
- **Database Specification V2** — cites Multi-Tenancy V1, Pricing §8, Background Tasks V2, SDP V2 (governance).
- **Internal API V1** — cites Pricing V2, Tenant Provisioning Seed V2.

**High coupling clusters** (build these together):

| Cluster | Docs |
|---------|------|
| **Billing + lifecycle** | SDP V2 (pick **one** file: #16 vs #30), Pricing V2, Stripe Webhook V1, Email V1, Database V2 §10, Background Tasks V2 |
| **Tenancy + DB** | Multi-Tenancy V1, Database V2, Technical Architecture V2 |
| **Features + model** | Data Models V6, System Status V3, Permission V2, Product Tier Map V2 |
| **Lifecycle + state machine** | Lifecycle Framework V1, System Status V3, Background Tasks V2, Data Models V6 |
| **Numbering** | Numbering Service V1, Seed Data V2 §5, Data Models V6 §1.9, Top-Down V4 §10.3 |
| **Attachments + files** | Note & Document Implementation V1, File Upload V1, Data Models V6 §1.8, Background Tasks V2 |
| **Lite scope** | Lite MVP V4, Product Tier Map V2, Pricing V2 |

**Pairwise conflicts** (same topic, divergent answers): see **`DOCUMENTATION_CROSS_SPEC_CONFLICT_MATRIX.md`** — do not duplicate that analysis here.

---

## 4. Questions to confirm (optional)

1. Should **Competitor Analysis/** Markdown files be included in the next pass (would raise the count above 27)?
2. Should **GPS** and **duplicate SDP** files be archived/moved so the **on-disk count** matches your **24** without mental subtraction?

---

*Generated for build planning — update when specs are merged or retired.*
