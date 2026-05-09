# ServizDesk — Cross-Specification Conflict Matrix (Living Docs)

**Purpose:** Surface **incompatible rules** across the current specification set so implementation does not encode “Part A” in a way that contradicts “Part D” (or C) when different teams or phases build in parallel.

**Scope:** All Markdown under [`Design Information/Design Documents/`](.) **excluding** archived trees (`Old Docs/`, `Old Code/`, and other `Old*` folders). **Research - Future** is flagged as non-normative where it touches product behavior.

**Method:** Topic clustering + pairwise comparison of authoritative vs referencing docs. “Conflict” = same decision point, mutually exclusive outcomes, or one doc’s mandate contradicted by another’s.

---

## Executive summary — conflict resolution log

All five original conflicts have been **resolved** as of March 27, 2026.

| ID | Topic | Resolution | Date |
|----|--------|------------|------|
| C1 | **SDP provisioning failure / refunds** | **Resolved.** Duplicate SDP V2 file in `Platform Spec Docs/` removed. Root `ServizDesk_Platform__SDP__Specification_V2.md` is sole authority: payment retained, `PROVISIONING_FAILED`, no auto refund. | 2026-03-27 |
| C2 | **Cancellation / retention timeline** | **Resolved.** Same file removal. Root SDP V2 + Pricing V2 rule applies: 30-day read-only + 60-day retention, 7-day deletion warning, 90-day total. | 2026-03-27 |
| C3 | **Asset parent/child modeling** | **Resolved.** Top-Down V4 updated to align with Data Models V6. Assets are grouped via the `SubAsset` junction table (many-to-many). The former `parent_asset_id` self-FK is retired. | 2026-03-27 |
| C4 | **Product naming & cross-references** | **Resolved.** All "ServizmaDesk" references in Lite MVP V4 replaced with "ServizDesk". | 2026-03-27 |
| C5 | **Framework version (Django)** | **Resolved.** All specs now read **Django 6.x** (Top-Down V4, Technical Architecture V2, Multi-Tenancy V1, Lite MVP V4). | 2026-03-27 |

**No open conflicts remain.** Legacy SDP V1 and duplicate SDP V2 in `Platform Spec Docs/` have been removed. GPS feasibility brief duplicates have been cleaned up.

---

## 1. Duplicate or near-duplicate files (resolved)

All duplicate files identified in the original audit have been removed:

- **SDP V2 duplicate** (`Platform Spec Docs/ServizDesk_Platform__SDP__Specification_V2.md`) — removed. Root copy is sole authority.
- **SDP V1** (`Platform Spec Docs/ServizDesk Platform (SDP) Specification V1.md`) — removed. Superseded by V2.
- **GPS feasibility brief duplicate** — cleaned up.
- **ServizmaDesk SDTA Agent Handoff** — removed. Referenced stale spec versions (Data Models V4 instead of V6).

`Platform Spec Docs/` now contains only `ServizDesk_Lite_MVP_V4_Specification.md`.

---

## 2. Domain-by-domain conflict matrix

### 2.1 Platform (SDP) — provisioning, billing lifecycle, email

| Decision point | Authoritative per doc map | Conflict detail |
|----------------|---------------------------|-----------------|
| Phase 2 failure after payment capture | Root SDP §4.5: **retain capture**, `PROVISIONING_FAILED`, **no auto refund** | **C1 resolved** — duplicate removed; root SDP is sole authority |
| Post-cancellation phases | Root SDP + Pricing §8: **30d read-only + 60d retention**, **7d** deletion warning | **C2 resolved** — duplicate removed; 90-day phased model is canonical |
| Staff audit field name | `system_audit_uuid` (root SDP) | **Resolved** — conflicting copy removed |

**Downstream coupling:** Email spec and Operational plan now align with the single SDP V2 cancellation timeline.

---

### 2.2 Data model — assets, work orders, hierarchy

| Decision point | Source A | Source B | Conflict |
|----------------|----------|----------|----------|
| Nested assets | Top-Down §14.2 #4: **`SubAsset` junction** | Data Models V6: **`SubAsset` junction** | **C3 resolved** — Top-Down updated to match Data Models V6; many-to-many grouping via junction table |
| One WO / one Asset | Top-Down §14.2 #3; Data Models narrative | **Aligned** (both say one asset per WO via FK) | OK |

**Build risk:** None — both docs now agree on `SubAsset` junction table approach.

---

### 2.3 Multi-tenancy & database

| Decision point | [`ServizDesk_multi_tenancy_spec_v1.md`](ServizDesk_multi_tenancy_spec_v1.md) | [`ServizDesk_Database_Specification_V2.md`](ServizDesk_Database_Specification_V2.md) | Notes |
|----------------|------------------|----------------------|--------|
| RLS + `SET LOCAL` in middleware | Sample wraps `get_response` in `transaction.atomic()` | RLS policies + role matrix | **Internal consistency:** sample code in multi-tenancy spec must match implementation patterns; **not** a cross-doc contradiction with DB spec, but **implementation must pick one transaction model** |
| DB name / users | `servizdesk_sdta`, `sdta_app`, `sdta_migration` | Same | Aligned |
| Retention window in DB spec §10 | References **30 + 60 + 7 days** | Must match **Pricing §8** | Align with **Pricing** as billing owner; if SDP alternate copy wins, **Database** and **Pricing** must be updated together |

---

### 2.4 Permissions & tiers

| Decision point | [`ServizDesk_Permission_Management_Specification_V2.md`](ServizDesk_Permission_Management_Specification_V2.md) | [`ServizDesk_Product_Tier_Map_V2.md`](ServizDesk_Product_Tier_Map_V2.md) vs Top-Down §16 |
| Resource registry keys | Central registry (`resource_key` list) | Tier map defines feature gates | **Must stay in sync:** e.g. fleet add-on, procurement modules — if a resource exists in Permission spec but tier map says “not in tier,” enforcement must be explicit. |
| “Additive union” of roles | OR across roles for permissions | Tier decorator may deny | **Not a contradiction** if layered: tier first, then role — document order of checks in one place |

---

### 2.5 Technical architecture — real-time, DB, stack

| Topic | Technical Architecture V2 | Cross-check |
|-------|---------------------------|-------------|
| **SSE/WebSockets** | **Prohibited**; Pusher + HTMX polling | **Aligned** with Top-Down §14.5 summary |
| **SQLite** | **Prohibited** everywhere | **Aligned** with Top-Down §14.2 #7 |
| **Django version** | **6.x** | Top-Down §14.1 | **C5 resolved** — all specs and code now aligned on Django 6.x |

---

### 2.6 Integrations (Stripe, internal API)

| Topic | Docs | Conflict |
|-------|------|----------|
| Stripe webhook behavior | [`ServizDesk_Stripe_Webhook_Specification_V1.md`](ServizDesk_Stripe_Webhook_Specification_V1.md) | **C1 resolved** — single SDP refund model (retain payment, manual handling); webhook handlers have one authoritative rule set |
| Internal API | [`ServizDesk_Internal_API_Specification_V1.md`](ServizDesk_Internal_API_Specification_V1.md) | Contract is defined; **endpoint list** must be implemented in lockstep with SDP/SDTA split — placeholder routing in code is separate from this doc audit |

---

## 3. Naming and reference drift (indirect build conflicts)

| Location | Status |
|----------|--------|
| Lite MVP V4 (`Platform Spec Docs/`) | **C4 resolved** — all "ServizmaDesk" references replaced with "ServizDesk" (March 27, 2026) |
| Top-Down §15 ownership map | **ServizDesk** file names — aligned |

---

## 4. Non-normative / research

| Document | Treatment |
|----------|-----------|
| `Research - Future/*` | **Do not** treat as binding for MVP; may **preview** features that conflict with “locked” Technical Architecture (e.g. future GPS) |

---

## 5. Reconciliation status

All five original reconciliation items have been completed (March 27, 2026):

1. ~~Merge or retire one SDP V2 copy~~ — **Done.** Duplicate and V1 removed from `Platform Spec Docs/`.
2. ~~Pick one cancellation + retention + refund story~~ — **Done.** Root SDP V2 (90-day phased model) is canonical.
3. ~~Resolve Asset hierarchy~~ — **Done.** Top-Down V4 updated to `SubAsset` junction; aligns with Data Models V6.
4. ~~Normalize Lite MVP naming~~ — **Done.** All "ServizmaDesk" → "ServizDesk" in Lite MVP V4.
5. ~~Record Django major version~~ — **Done.** All specs now read Django 6.x.

---

## 6. Document inventory (living, non-archived)

**Hub (11):** Top-Down V4, Technical Architecture V2, Data Models V6, Pricing & Billing V2, Product Tier Map V2, Database V2, Multi-Tenancy V1, Internal API V1, SDP V2, Security Features V1, Permission Management V2.

**Supporting (12):** CSV Export V3, Background Tasks V2, Email V1, Stripe Webhook V1, Invoice Calculation V1, File Upload V1, Universal Query V1, Dashboard Counter V1, Onboarding Triggers V2, Tenant Provisioning Seed V2, System Status V3, SaaS Operational Plan V3.

**Scoped (1):** Lite MVP V4 (`Platform Spec Docs/`).

**ERDs (3):** SD System ERD — Base System V12.pdf, Employee V4.pdf, System Logs V1.pdf.

---

*This matrix is based on static document comparison; it does not replace integration tests or legal review of billing/refund policy.*
