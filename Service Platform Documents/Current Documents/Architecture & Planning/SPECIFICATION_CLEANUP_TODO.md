# ServizDesk — Specification Cleanup Todo List

**Generated:** March 27, 2026
**Last Updated:** March 28, 2026
**Status:** ✅ ALL 19 ITEMS RESOLVED
**Scope:** All living specifications under `Design Information/Design Documents/` (24 Markdown specs + 3 ERD PDFs). Lite MVP is excluded — on back burner until we are ready to focus on the Lite build.

---

## How to use this list

Each item includes the affected document(s), a description of the issue, and the fix applied. Items are grouped by type:

- **CONFLICT** — Two specs disagreed on the same decision. Resolved.
- **SPEC GAP** — Something was missing or undefined. Filled.
- **CLEANUP** — Wording was stale, ambiguous, or misleading. Fixed.

---

## CONFLICTS (all resolved)

### TODO-01: Customer status enum incomplete in Top-Down V4
- **Affected docs:** `ServizDesk_Top_Down_Specifications_V4.md` vs `ServizDesk_Data_Models_V6.md`, `ServizDesk_System_Status_Specification_V3.md`
- **Issue:** Top-Down V4 only lists Customer status as "Active, Inactive" (2 values). Data Models V6 (line 331) and System Status V3 both define it as "Active, Inactive, Hold, Closed" (4 values). Hold and Closed are missing from Top-Down, along with their transition rules and business behavior (e.g., Hold = no new work permitted).
- **Fix applied:** Update Top-Down V4 Customer section to include all 4 status values with transition rules matching System Status V3.
- **Status:** ✅ RESOLVED — High — affects Customer module build.

### TODO-02: Service Request number prefix mismatch
- **Affected docs:** `ServizDesk_Top_Down_Specifications_V4.md` (line 198) vs `ServizDesk_Data_Models_V6.md` (line 224), `ServizDesk_Tenant_Provisioning_Seed_Data_Specification_V2.md` (line 84)
- **Issue:** Top-Down V4 shows the example "TC26-0001" for Service Request numbering. Data Models V6 and Tenant Provisioning Seed Data both define `service_request_prefix = "SR"`, which would produce "SR26-0001".
- **Fix applied:** Update Top-Down V4 line 198 example to use "SR26-0001" to match Data Models V6 and Seed Data.
- **Status:** ✅ RESOLVED — Low — cosmetic, but could confuse developers.

### TODO-03: Universal Query field names don't match Data Models
- **Affected docs:** `ServizDesk_Universal_Query_Specification_V1.md` (Section 2.2) vs `ServizDesk_Data_Models_V6.md`
- **Issue:** UQI spec says Customer is searchable by `name`, `email`, `account_number`. Data Models V6 has `company_name` (not `name`), and `email` lives on the Person entity accessed through the Contact junction — not directly on Customer. Work Order search profile references `customer__name` which should be `customer__company_name`.
- **Fix applied:** Update UQI Section 2.2 Customer search profile to: `company_name`, `account_number`, `contacts__person__email` (or a simplified annotation). Update Work Order profile's `customer__name` to `customer__company_name`.
- **Status:** ✅ RESOLVED — Medium — affects search implementation.

---

## SPEC GAPS (all resolved)

### TODO-04: Database 'worker' alias not configured in Database Specification
- **Affected docs:** `ServizDesk_Database_Specification_V2.md` (Section 4.2), `ServizDesk_multi_tenancy_spec_v1.md`
- **Issue:** Multi-Tenancy spec references `.using('worker')` extensively for cross-tenant reads (staff admin, Celery tasks). Database Spec Section 4.2 only shows the `'default'` DATABASES entry. The `'worker'` alias configuration (using `SDTA_WORKER_DB_USER` / `SDTA_WORKER_DB_PASSWORD` env vars referenced in Section 13) is never shown.
- **Fix applied:** Add a second DATABASES dict entry for `'worker'` in Database Spec Section 4.2, using the worker credentials and pointing at the same database but with the `sdta_support` or `sdta_migration` role (BYPASSRLS). Clarify which role the worker alias uses.
- **Status:** ✅ RESOLVED — High — blocks any staff admin or Celery task implementation.

### TODO-05: Stripe webhook event types not enumerated
- **Affected docs:** `ServizDesk_Stripe_Webhook_Specification_V1.md`
- **Issue:** The spec defines architecture (signing, idempotency, multi-tenant resolution, retry logic) but never lists which Stripe event types SDTA actually handles (e.g., `charge.succeeded`, `charge.failed`, `invoice.payment_succeeded`, `customer.subscription.updated`, etc.). Implementers have to guess.
- **Fix applied:** Add a section to Stripe Webhook Spec listing all handled event types, what each one triggers in the application, and which status transitions result.
- **Status:** ✅ RESOLVED — High — blocks payment integration build.

### TODO-06: Email overage billing trigger undocumented in Pricing spec
- **Affected docs:** `ServizDesk_Pricing_and_Billing_Specification_V2.md`, `ServizDesk_Email_Specification_V1.md` (Section 7.2)
- **Issue:** Email Spec says overage accumulates in `email_points_overage` and is "flagged for end-of-period billing." But Pricing V2 doesn't document the mechanics: what task triggers the Stripe charge, when it runs, how overage is calculated into the invoice.
- **Fix applied:** Add a subsection to Pricing V2 Section 10A documenting: overage is billed on the tenant's billing anniversary, a background task reads the accumulated `email_points_overage`, calculates the charge, and submits a Stripe invoice line item.
- **Status:** ✅ RESOLVED — Medium — blocks email billing implementation.

### TODO-07: purge_deleted_tenant_data retention wording is ambiguous
- **Affected docs:** `ServizDesk_Background_Tasks_Specification_V2.md` (Section 3.1 table)
- **Issue:** The table says `purge_deleted_tenant_data` has "60 Days" retention. The full cancellation lifecycle is 30 days read-only + 60 days retention = 90 days total. After verification, the "60 Days" refers to the `deletion_scheduled_at` field on TenantState (set to `now() + 60 days` when status → Pending Deletion), so total is correct (90 days for billed, 105 for trial). But the table entry is misleading on its own.
- **Fix applied:** Change the retention column from "60 Days" to "60 days after `Pending Deletion` status (see `TenantState.deletion_scheduled_at`)" or similar clarifying language.
- **Status:** ✅ RESOLVED — Medium — not a real conflict, but confusing to anyone reading the table alone.

### TODO-08: PgBouncer transaction mode not emphasized in Technical Architecture
- **Affected docs:** `ServizDesk_Technical_Architecture_V2.md`, `ServizDesk_Database_Specification_V2.md` (Section 4.3)
- **Issue:** Database Spec clearly requires PgBouncer in transaction mode (Section 4.3). Technical Architecture only mentions this constraint indirectly when explaining why WebSockets/SSE are prohibited. An operator deploying from the Tech Architecture doc alone could miss this and default to session mode, causing tenant context leaks.
- **Fix applied:** Add a deployment note in Technical Architecture (infrastructure/deployment section) explicitly stating: "PgBouncer must be configured in transaction mode. Session mode will cause RLS tenant context to leak between requests."
- **Status:** ✅ RESOLVED — Medium — operational risk.

### TODO-09: Login flow missing explicit two-layer tenant context setup
- **Affected docs:** `ServizDesk_Technical_Architecture_V2.md` (Section 8.6), `ServizDesk_multi_tenancy_spec_v1.md`
- **Issue:** Multi-Tenancy spec requires both `set_current_tenant_id()` AND `SET LOCAL app.current_tenant_id` for all contexts. Technical Architecture's login flow (Section 8.6, step 4) mentions setting context but doesn't explicitly show the two-layer pattern as strongly as other sections. A developer implementing login could only do one layer.
- **Fix applied:** Update Tech Architecture Section 8.6 step 4 to explicitly reference both layers: "Call `set_current_tenant_id(tenant_id)` (Python context) and execute `SET LOCAL app.current_tenant_id` within `transaction.atomic()` (database RLS context). See Multi-Tenancy Specification V1 for the authoritative pattern."
- **Status:** ✅ RESOLVED — Medium — subtle but could cause RLS failures on authenticated requests.

---

## CLEANUP (all resolved)

### TODO-10: Email Spec Open Decision #4 already resolved
- **Affected docs:** `ServizDesk_Email_Specification_V1.md` (Section 8, Decision #4)
- **Issue:** Decision #4 asks "How long are sent emails stored for preview?" and suggests matching Postmark's 45-day window. Background Tasks V2 and Database Spec V2 already lock this to 12 months (which exceeds 45 days). The decision should be marked resolved.
- **Fix applied:** Update Decision #4 to: "✅ RESOLVED — 12-month retention. See Background Tasks Specification V2 (`purge_email_delivery_logs`) and Database Specification V2 Section 10.1."
- **Status:** ✅ RESOLVED — Low.

### TODO-11: Email Spec references non-existent GPS document
- **Affected docs:** `ServizDesk_Email_Specification_V1.md` (Section 10.4)
- **Issue:** Section 10.4 (Related Documents) references "ServizDesk GPS Tracking Strategy & Feasibility Brief V1" as a "parallel structure for a deferred feature." This document has been removed from the working set.
- **Fix applied:** Remove the GPS reference from Section 10.4, or note it was archived.
- **Status:** ✅ RESOLVED — Low.

### TODO-12: Email Spec pending updates reference old doc versions
- **Affected docs:** `ServizDesk_Email_Specification_V1.md` (Section 9)
- **Issue:** Section 9 (Pending Document Updates) references "Top-Down Specifications V1" for items 1-4. The current version is V4. All 8 items are marked complete, so this section is historical. The version references are stale.
- **Fix applied:** Update the version references (V1 → V4) or add a note: "All pending updates completed as of March 2026. Version references reflect the document version at time of original authoring."
- **Status:** ✅ RESOLVED — Low.

### TODO-13: Vendor entity missing dedicated section in Top-Down V4
- **Affected docs:** `ServizDesk_Top_Down_Specifications_V4.md`, `ServizDesk_Product_Tier_Map_V2.md`, `ServizDesk_Data_Models_V6.md`
- **Issue:** Product Tier Map V2 emphasizes "Vendors are a standalone entity" (distinct from Customers). Data Models V6 has a full Vendor table with Triad relationships. But Top-Down V4 doesn't have a dedicated Vendor section — vendors are mentioned under Plus tier additions but lack detailed entity specification.
- **Fix applied:** Add a Vendor Entity section to Top-Down V4 (under Plus features) with field list, status lifecycle, and relationship descriptions consistent with Data Models V6.
- **Status:** ✅ RESOLVED — Medium — affects Plus tier build.

### TODO-14: WorkGroupAsset automation rule not documented consistently
- **Affected docs:** `ServizDesk_Top_Down_Specifications_V4.md`, `ServizDesk_Data_Models_V6.md`
- **Issue:** Top-Down V4 states WorkGroupAsset records are "created automatically by the system when a Work Order with a non-null asset_id is added to a WorkGroup" and are "system-managed, not manually editable." Data Models V6 defines the junction table structure but does not explicitly state the automation rule.
- **Fix applied:** Add an implementation note to Data Models V6 WorkGroupAsset definition: "System-managed junction. Records are auto-created when a Work Order with a non-null `asset_id` is added to a WorkGroup. Not user-editable."
- **Status:** ✅ RESOLVED — Low — the rule exists in Top-Down, but should be echoed in Data Models for completeness.

### TODO-15: Invoice "Viewed" status transition mechanism unspecified
- **Affected docs:** `ServizDesk_Dashboard_Counter_Specification_V1.md`, `ServizDesk_Data_Models_V6.md`, `ServizDesk_System_Status_Specification_V3.md`
- **Issue:** Dashboard spec counts "Viewed" invoices as open. Data Models and System Status define the `Viewed` status value. But no spec documents the mechanism that triggers the transition from `Issued` → `Viewed` (e.g., when customer opens the Stripe payment link, is it a webhook callback? A tracking pixel? A redirect?).
- **Fix applied:** Add an implementation note to System Status V3 (Invoice lifecycle) or Data Models V6 describing: "Status transitions to `Viewed` when the customer accesses the payment link. The mechanism (Stripe Checkout session tracking or redirect callback) should be documented in the Stripe Webhook Specification."
- **Status:** ✅ RESOLVED — Medium — affects invoice workflow build.

### TODO-16: MFA failure threshold inconsistency
- **Affected docs:** `ServizDesk_Technical_Architecture_V2.md` (Section 8.6), `ServizDesk_Security_Features_Specification_V1.md` (Section 1.1)
- **Issue:** Technical Architecture mentions 3 failed MFA OTP attempts before invalidating the intermediate token (tracked in Redis). Security Features spec mentions account lockout after 5 consecutive failed login attempts. These are different thresholds for different stages (login vs. MFA), which is correct — but the docs don't clearly distinguish between them. A developer might confuse the two.
- **Fix applied:** Add clarifying language in both docs: "Account lockout (5 failed password attempts) is separate from MFA lockout (3 failed OTP attempts). Account lockout blocks the login form. MFA lockout invalidates the current authentication session and requires the user to start over."
- **Status:** ✅ RESOLVED — Low — logical but could trip up a developer.

### TODO-17: `sdta_support` credential rotation policy unclear
- **Affected docs:** `ServizDesk_multi_tenancy_spec_v1.md` (Section 12), `ServizDesk_Database_Specification_V2.md`
- **Issue:** Multi-Tenancy spec notes `sdta_support` is BYPASSRLS and "vault-locked / rotated after use." It's ambiguous whether "after use" means after every query session, after each support incident, or on a periodic schedule.
- **Fix applied:** Clarify in Database Spec (role definitions section): "`sdta_support` credentials are rotated after each support incident. Credentials are stored in a secrets vault (e.g., HashiCorp Vault) and checked out per-incident."
- **Status:** ✅ RESOLVED — Low — operational detail, but should be explicit before production.

### TODO-18: `sdta_readonly` role defined but not fully specified
- **Affected docs:** `ServizDesk_Database_Specification_V2.md`
- **Issue:** Database Spec defines `sdta_readonly` as a valid role (SELECT only, subject to RLS) but doesn't show environment variables, DATABASES configuration, or use cases for it. No other spec references it.
- **Fix applied:** Either add full configuration for the readonly role (env vars, DATABASES dict entry, intended use cases like reporting/analytics), or note it as "reserved for future use" to avoid confusion.
- **Status:** ✅ RESOLVED — Low — not needed for initial build.

### TODO-19: `failed_login_count` sync with django-axes
- **Affected docs:** `ServizDesk_Technical_Architecture_V2.md` (Section 8.6)
- **Issue:** Tech Architecture mentions that `User.failed_login_count` must be kept in sync with django-axes as a "display mirror." This synchronization requirement is easy to miss — it's a subtle implementation detail buried in a table. If missed, the employee management UI would show stale failure counts.
- **Fix applied:** Add an implementation note to Data Models V6 on the User entity: "`failed_login_count` is a display mirror of the django-axes failure count. Must be updated via a post-save signal or middleware when django-axes records a failure."
- **Status:** ✅ RESOLVED — Low — implementation detail.

---

## DEFERRED (not in scope for current Top-Down build)

### DEFERRED-01: Lite MVP "No SMS" vs Product Tier Map (100 SMS points for Lite)
- **Why deferred:** Lite MVP spec is on back burner. When we focus on the Lite build, the MVP spec needs a new section covering SMS and email manual sending flows, consistent with Product Tier Map V2.

### DEFERRED-02: Lite MVP Dashboard widget list (missing "Top 5 Active Tasks")
- **Why deferred:** Lite MVP spec is on back burner. When we revisit, add the Tasks widget to match Product Tier Map V2.

### DEFERRED-03: Lite MVP "Calendar reflects scheduled items" misleading language
- **Why deferred:** Lite MVP spec is on back burner. When we revisit, clarify that this is a date-sorted list, not a calendar UI.

---

## RESOLVED (from previous sweep — March 27, 2026)

These were identified and fixed in the prior session:

| ID | Issue | Resolution |
|----|-------|------------|
| C1 | SDP provisioning failure / refunds — two SDP V2 files disagreed | Duplicate removed. Root SDP V2 is sole authority. |
| C2 | Cancellation / retention timeline — two SDP V2 files disagreed | Duplicate removed. 30/60/90 phased model is canonical. |
| C3 | Asset nesting — parent_id self-FK vs SubAsset junction | Top-Down V4 updated to SubAsset junction. Matches Data Models V6. |
| C4 | "ServizmaDesk" naming in Lite MVP | All references replaced with "ServizDesk". |
| C5 | Django version 5.x vs 6.x | All specs now read Django 6.x. |

---

*Generated by cross-specification audit — update as items are resolved.*
