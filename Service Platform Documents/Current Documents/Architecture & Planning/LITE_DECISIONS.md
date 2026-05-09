# ServizDesk Lite — Product Decisions

**Status:** Approved by Ron, 2026-04-24
**Scope:** Resolves spec §29 "Still to specify" for Lite tier, plus tooling decisions that affect the frontend build.

---

## Decisions

| # | Decision | Resolution | Notes |
|---|---|---|---|
| A | Asset Type list | Tenant-controlled `ValueList` | Seed with common service-trade types (HVAC Unit, Furnace, Water Heater, Boiler, Electrical Panel, Plumbing Fixture, Appliance, Generator, Other); tenants can add/remove via ValueList admin. |
| B | Company Settings field list | Same as drafted minus numbering prefixes | **Lite tenants do NOT control numbering prefixes** — they receive the system defaults. This is a tier restriction over the Numbering Service V1 spec, which allows tenant control at higher tiers. |
| C | Quote/Invoice void reasons | Free-text, optional | No structured reason code list in Lite. |
| D | Global search scope | Customers + Jobs + Invoices, prefix match | Name / phone / customer# / job# / invoice#. No fuzzy search. |
| E | Accessibility target | WCAG 2.1 AA, informal | Spot-check keyboard nav, focus rings, color contrast, alt text, ARIA as we build. No formal third-party audit for MVP. Formal VPAT deferred until a customer requires one. |
| F | Payment processor | Manual logging only | Lite records payment details (cash/check/credit card/ACH/bank transfer/other) without processing. Card processing (Stripe) begins in Plus. **Remove the "Copy Payment Link" button from the prototype** when building Invoice detail. |
| G | Invoice "Client View" toggle | Skip | PDF is the customer view; no in-app toggle needed. |
| H | Sidebar structure | Show all nav items; hide items not available in Lite's tier | Not a Lite-specific nav list — a tier-aware visibility mechanism. |
| I | CSS framework | **Bootstrap 5** | Replaces the Tailwind CDN currently in `base.html`. Components we need (offcanvas drawer, modals, forms, tables, tabs, toasts, status badges) all ship with Bootstrap; no build step required. |
| J | Frontend JS | HTMX + Django templates, small vanilla JS as needed | No SPA, no Node toolchain, no Playwright. |
| K | Email (outbound) | **None in Lite.** Users send documents via their own email client. | Per Lite MVP V4 Spec: "System email sending, Transactional email provider integration — not included in Lite." The in-app "Send" action on a Quote or Invoice marks the record as Sent (triggers snapshot/lock per §18/§20) but does NOT originate an email. Users obtain the document via browser print (see §L) and attach to an email composed in their own client (Outlook, Gmail, Apple Mail, etc.). Postmark + `django-anymail` are introduced in **Plus** for system-originated emails. |
| L | PDF generation | **Browser print (CSS Print Media Queries) in Lite.** | Per Tech Architecture V2 §3.2 and Lite MVP V4. Lite has no server-side PDF. Developers must write `@media print` CSS so the browser can print clean 8.5x11 pages without UI chrome. WeasyPrint (server-side PDF) is deferred to **Plus** and used there for automated attachments. |
| M | Frontend asset delivery | **All vendored into `static/vendor/` — no runtime CDN references.** | The system is web-aware but must run correctly when deployed behind a firewall (no outbound internet access to jsdelivr/unpkg/etc.). All third-party CSS and JS (Bootstrap 5.3.3, Lucide 0.469.0, and any future library) are committed into `static/vendor/<library>-<version>/` and served by Django's staticfiles. Versions are pinned in the directory name. Upgrades are an explicit commit, not a drift from `@latest`. |
| N | Workspace-based login | **Login form takes Workspace + Username + Password.** Username uniqueness is per-tenant. | One login screen serves both deploy modes (multi-tenant SaaS and per-customer single-tenant) and both account types (tenant Users and StaffUsers). The Workspace field is the tenant subdomain (e.g. `acme`). On submit: (1) resolve tenant by `subdomain` (must be Active); (2) try tenant User scoped to `(tenant_id, username)`; (3) fall back to StaffUser by email when the username contains `@`. Session stores `active_tenant_id` so middleware can establish tenant context for StaffUsers (who have no `tenant_id` of their own). Username uniqueness migrated from global to `(tenant_id, username)` — same for email — so two tenants can each have an `admin` user. Spec impact (deferred to spec-cleanup pass): Multi-Tenancy V1 §5/§9, Permission Management V2, Security Features V1. |

---

## Follow-up: specs that need alignment with these decisions

These multi-tier specs currently contradict a decision above and need a tier carve-out or edit. Do not silently edit — get Ron's call on each:

- ~~**`Specifications/ServizDesk_Technical_Architecture_V2.md`** — names Tailwind as the canonical CSS framework.~~ ✅ Updated 2026-04-24.
- ~~**`Specifications/ServizDesk_Numbering_Service_Specification_V1.md`** §3.1~~ ✅ Updated 2026-04-24.
- ~~**`UI-UX/Lite UI:X/Lite Tier UI & Functionality Specification (v1).md`** §29~~ ✅ Updated 2026-04-24.
- ~~**`UI-UX/Lite UI:X/Lite Tier UI & Functionality Specification (v1).md` §26**~~ ✅ Updated 2026-04-24 — rewrote Quote/Invoice Send to state-transition-only; no system email; browser print + user's own client for delivery.
- ~~**`Specifications/ServizDesk_Email_Specification_V1.md` §4.1 (Lite table)**~~ ✅ Updated 2026-04-24 — replaced misleading "Manual Only" table with explicit "No System-Originated Customer Emails" policy + list of platform-level emails (welcome, admin reset) that do fire.
- **`UI-UX/UIX Prototypes/lite-shell-prototype.html`** — contains the stale Stripe "Copy Payment Link" button. Remove when building Invoice detail per decision F.
