# Document Organization Plan
*Generated: April 24, 2026 — Review before any files are moved*

---

## What I Found

You have two folders with significant overlap and version confusion:

- **Design Documents** — The older working folder. Uses the "ServizmaDesk_" naming convention. Also contains several newer April 2026 working files (architecture, audit reports, UI/UX work).
- **Design Information** — Has a cleaner sub-structure:
  - `Design Documents/` — Newer, reorganized specs using the updated "ServizDesk_" naming (no "ma"). These are the current canonical specs.
  - `Old Docs/` — Already designated as obsolete (ServizmaDesk_ lower versions).

**Key insight:** The naming convention shifted from `ServizmaDesk_` → `ServizDesk_` at some point during reorganization. The Design Information/Design Documents folder contains the current, highest-version specs under the new name.

---

## Proposed Folder Structure

```
Service Platform Documents/
├── Current Documents/
│   ├── Specifications/          ← Current ServizDesk_ specs (highest versions)
│   ├── ERDs/                    ← Highest-version ERDs only
│   ├── Architecture & Planning/ ← Roadmaps, implementation plans, scopes, to-dos
│   ├── Audit & Review/          ← Audit reports, code review findings
│   ├── UI-UX/                   ← Lite UI:X specs + UIX Prototypes
│   ├── Competitor Analysis/     ← All competitor docs (no duplicates found)
│   └── Reference/               ← API reference, index docs, fleet docs, ERP ideas
│
└── Obsolete Documents/
    ├── Old Specifications/      ← Superseded ServizmaDesk_ specs (lower versions)
    ├── Old ERDs/                ← Superseded ERD versions
    ├── Old Analysis/            ← Old gap analysis, deduplication summaries, reorg plans
    └── Archives/                ← Zip files (Archive.zip, ERDs.zip)
```

> **Note:** The existing Design Documents and Design Information folders would be dissolved into this new structure. Nothing is permanently deleted without your approval (except confirmed duplicates per your instruction).

---

## Files Going to Current Documents

### Specifications/
All from Design Information/Design Documents (the "ServizDesk_" canonical set):
- ServizDesk_Background_Tasks_Specification_V2.md
- ServizDesk_CSV_Export_Specification_V3.md
- ServizDesk_Dashboard_Counter_Specification_V1.md
- ServizDesk_Data_Models_V6.md
- ServizDesk_Database_Specification_V2.md
- ServizDesk_Email_Specification_V1.md
- ServizDesk_File_Upload_Specification_V1.md
- ServizDesk_Internal_API_Specification_V1.md
- ServizDesk_Invoice_Calculation_Specification_V1.md
- ServizDesk_Lifecycle_Framework_Specification_V1.md
- ServizDesk_Lite_MVP_V4_Specification.md
- ServizDesk_Note_Document_Implementation_Specification_V1.md
- ServizDesk_Numbering_Service_Specification_V1.md
- ServizDesk_Onboarding_Triggers_Specification_V2.md
- ServizDesk_Permission_Management_Specification_V2.md
- ServizDesk_Platform__SDP__Specification_V2.md
- ServizDesk_Pre_Code_Audit_and_Implementation_Plan.md
- ServizDesk_Pricing_and_Billing_Specification_V2.md
- ServizDesk_Product_Tier_Map_V2.md
- ServizDesk_SaaS_Operational_Plan_V3.md
- ServizDesk_Security_Features_Specification_V1.md
- ServizDesk_Stripe_Webhook_Specification_V1.md
- ServizDesk_System_Status_Specification_V3.md
- ServizDesk_Technical_Architecture_V2.md
- ServizDesk_Tenant_Provisioning_Seed_Data_Specification_V2.md
- ServizDesk_Top_Down_Specifications_V4.md
- ServizDesk_Universal_Query_Specification_V1.md
- ServizDesk_multi_tenancy_spec_v1.md

### ERDs/
- SD System ERD - Base System V12.pdf ← newest base system ERD
- SD System ERD - Employee V4.pdf ← newest employee ERD
- SD System ERD - System Logs V1.pdf ← only version (keep one copy)
- SD System ERD - Fleet Maintenance V2.pdf ← newest fleet ERD

### Architecture & Planning/
- ARCHITECTURE.md
- DEVELOPMENT_ROADMAP_TO_FRONTEND.md
- FRONTEND_READINESS_PLAN.md
- BACKEND_STABILIZATION_SCOPE.md
- PRODUCTION_PARITY_CHECKLIST.md
- LITE_BUILD_TODO.md
- implementation_plan.md
- SPECIFICATION_CLEANUP_TODO.md
- SDTA_Gap_Analysis_V5.md ← highest version gap analysis
- Service Platform Tiering Plan V2

### Audit & Review/
- BACKEND_READINESS_AUDIT_2026-04-05.md
- SD_Service_01_Audit_Report.md
- codebase_audit_report.md
- CODE_REVIEW_FINDINGS.md

### UI-UX/
- Lite UI:X/ (entire folder — 4 files)
- UIX Prototypes/lite-shell-prototype.html

### Competitor Analysis/
- FieldPulse_Competitor_Analysis_2026.docx
- FieldPulse_Competitor_Analysis_2026.md
- FieldPulse_Functional_Specification.md
- HousecallPro_Competitor_Analysis_2026.docx
- Jobber_Competitor_Analysis_2026.docx
- ServiceTitan_Competitive_Intelligence_Dossier_v1.md
- Workiz_Competitor_Analysis_2026.docx
- servicetitan_deep_dive_report.md

### Reference/
- ServizDesk_API_Reference.docx
- DOCUMENTATION_INDEX_AND_CROSS_REFERENCE.md
- DOCUMENTATION_CROSS_SPEC_CONFLICT_MATRIX.md
- fleet_maintenance_saa_s_master_blueprint.md
- fleet_maintenance_schema.md
- ERP Desktop Ideas.txt

---

## Files Going to Obsolete Documents

### Old Specifications/
All superseded "ServizmaDesk_" specs from Design Documents (replaced by ServizDesk_ equivalents):
- ServizmaDesk Platform (SDP) Specification V1.md
- ServizmaDesk_Background_Tasks_Specification_V2.md
- ServizmaDesk_CSV_Export_Specification_V3.md
- ServizmaDesk_Dashboard_Counter_Specification_V1.md
- ServizmaDesk_Data_Models_V4.md
- ServizmaDesk_Database_Specification_V1.md
- ServizmaDesk_Database_Specification_V2.md
- ServizmaDesk_Email_Specification_V1.md
- ServizmaDesk_File_Upload_Specification_V1.md
- ServizmaDesk_Internal_API_Specification_V1.md
- ServizmaDesk_Invoice_Calculation_Specification_V1.md
- ServizmaDesk_Lite_MVP_V4_Specification.md
- ServizmaDesk_Onboarding_Triggers_Specification_V2.md
- ServizmaDesk_Permission_Management_Specification_V2.md
- ServizmaDesk_Platform__SDP__Specification_V2.md
- ServizmaDesk_Pricing_and_Billing_Specification_V2.md
- ServizmaDesk_Product_Tier_Map_V2.md
- ServizmaDesk_SaaS_Operational_Plan_V3.md
- ServizmaDesk_Stripe_Webhook_Specification_V1.md
- ServizmaDesk_System_Status_Specification_V2.md ← superseded by V3
- ServizmaDesk_System_Status_Specification_V3.md ← also superseded by the ServizDesk_ V3
- ServizmaDesk_Technical_Architecture_V2.md
- ServizmaDesk_Tenant_Provisioning_Seed_Data_Specification_V2.md
- ServizmaDesk_Top_Down_Specifications_V4.md
- ServizmaDesk_Universal_Query_Specification_V1.md
- ServizmaDesk_multi_tenancy_spec_v1.md
- ServizmaDesk_Gap_Analysis_V3.md ← superseded by V5
- SDTA_Backend_Gap_Analysis_V4.md ← superseded by V5

From Design Information/Old Docs (already designated old):
- All lower-version specs already in Old Docs
- ServizmaDesk_Enterprise_Top_Down_Design_V2.md
- ServizmaDesk_Pricing_Spec_Update_Guide.md

### Old ERDs/
- SD System ERD - Base System V7.pdf
- SD System ERD - Base System V8.pdf
- SD System ERD - Base System V9.pdf
- SD System ERD - Base System v2.pdf (from Old Docs)
- SD System ERD - Base System V3.pdf (from Old Docs)
- SD System ERD - Base System v4.pdf (from Old Docs)
- SD System ERD - Base System v5.pdf (from Old Docs)
- SD System ERD - Base System V6.pdf (from Old Docs)
- SD System ERD - Employee V1.pdf
- SD System ERD - Employee V2.pdf
- SD System ERD - Fleet Maintenance V1.pdf ← superseded by V2

### Old Analysis/
- SDPA_backend_readiness_report_v1.md
- SDTA_Backend_Gap_Analysis_v2.md (from Old Docs)
- SDTA_backend_implementation_todo_v1.md (from Old Docs)
- ServizmaDesk_Deduplication_Summary.md
- ServizmaDesk_Document_Reorganization_Plan.md

### Archives/
- Archive.zip
- ERDs.zip

---

## True Duplicates — Proposed for Deletion

These are exact or near-exact copies:
1. `ServizmaDesk_Deduplication_Summary copy.md` — duplicate of ServizmaDesk_Deduplication_Summary.md
2. `ServizmaDesk_Document_Reorganization_Plan copy.md` — duplicate of ServizmaDesk_Document_Reorganization_Plan.md
3. `SD System ERD - System Logs V1.pdf` exists in two locations — will keep one copy in Current/ERDs

---

## THREE Ambiguous Files — Your Call Required

These files in Design Documents have no updated "ServizDesk_" equivalent and no newer version. I need your direction:

| File | What it is | My suggestion |
|------|-----------|---------------|
| ServizmaDesk_SDTA_Agent_Handoff.md | Agent handoff doc specific to SDTA | Current → Reference |
| ServizmaDesk_SDTA_Data_Models_V1.md | SDTA-specific data models | Current → Specifications |
| ServizmaDesk_GPS_Tracking_Strategy_Feasibility_Brief_V1.md | GPS feasibility study | Current → Reference |

---

## Summary Count

| Destination | File Count |
|-------------|-----------|
| Current Documents | ~55 files |
| Obsolete Documents | ~55 files |
| Deleted (true duplicates) | 3 files |

---

*Please review this plan and confirm before I make any changes.*
