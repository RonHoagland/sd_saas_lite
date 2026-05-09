# ServizmaDesk Email Specification V1

**Document Status:** Draft  
**Version:** 1.0  
**Date:** March 2026  
**Owner:** ServizmaDesk  

---

# 1. Purpose and Scope

This document is the authoritative specification for all email sending, receiving, and routing functionality in ServizmaDesk. It covers:

- Platform-managed email architecture and provider details
- Competitive baseline requirements
- Email point system implementation
- Custom Domain Email add-on (Phase 1)
- Email routing system (Phase 2 — future)
- Open engineering decisions

**Pricing** is maintained exclusively in the **ServizmaDesk Pricing & Billing Specification V2, Section 10A and Section 11.4**. This document contains no pricing data.

---

# 2. Competitive Baseline

## 2.1 What Competitors Do

All four primary competitors (Jobber, HousecallPro, FieldPulse, Workiz) follow the same email model:

- All outbound emails send from the **platform's own domain**, not the tenant's domain
- The tenant's **company name** appears as the display sender name in the customer's inbox
- Customer replies go to a **configured reply-to address** (a team member's external inbox) — they do not return to the platform
- No competitor captures inbound email back into their system
- No competitor offers SMTP credential input or custom domain sending

**Jobber specifically:** Sends from `notification@msg.getjobber.com`. Tenants can configure which team member receives replies per email type (quotes → estimator, invoices → billing contact, jobs → assigned tech). Reply-to is configured globally in settings with per-item overrides. Outbound sends are logged in a Client Communications Report with delivery status and open tracking.

## 2.2 ServizmaDesk Baseline Requirements

To match competitors at all relevant tiers, ServizmaDesk must provide:

- Send quotes to customers by email from within the platform
- Send invoices to customers by email from within the platform
- Send automated notifications (booking confirmations, appointment reminders, on-my-way, job completion, payment receipts) — Plus and above
- Configurable reply-to address per email type
- Outbound communications log with delivery status and open tracking per customer record
- Tenant company name as display sender name
- Branded email templates with tenant logo and contact details

## 2.3 ServizmaDesk Differentiation

ServizmaDesk exceeds the competitor baseline with:

- **Custom domain sending (Phase 1 add-on):** Emails appear from the tenant's own domain — no competitor offers this
- **Inbound reply capture (Phase 1 add-on):** Customer replies attach to records in-platform — no competitor does this
- **Email routing (Phase 2 add-on):** Multiple inbound addresses mapped to system actions — no competitor has this at any price

---

# 3. Email Provider Architecture

## 3.1 Provider: Postmark

ServizmaDesk uses **Postmark** as its transactional email delivery platform. Postmark was selected for:

- Industry-leading deliverability (98.5%+ inbox placement)
- Native inbound email processing via webhooks
- Per-domain authentication (SPF, DKIM, DMARC) — required for custom domain add-on
- Transparent pricing and no hidden fees
- Already in the ServizmaDesk confirmed tech stack

## 3.2 Single Account / Multi-Tenant Model

ServizmaDesk operates **one Postmark account**. All tenant emails across all tiers flow through this single account. Postmark has no awareness of individual tenants — ServizmaDesk manages all tenant-level metering internally.

**How per-tenant metering works:**
- Every outbound email dispatched through Postmark is logged against the originating tenant's `email_points_used` counter in the ServizmaDesk database
- Postmark fires a delivery webhook for each sent message confirming delivery status (delivered, bounced, failed)
- Failed deliveries (bounced, rejected, spam-blocked) do not increment the tenant's counter — the webhook handler checks status before logging
- At each tenant's billing anniversary, the counter is read, overage is calculated and charged via Stripe, then the counter resets to zero
- The tenant sees a real-time bar graph in their billing dashboard showing points used vs. included allocation for the current period

## 3.3 Message Streams

Postmark uses Message Streams to separate email types. ServizmaDesk should configure at minimum:

- **Transactional stream:** Quotes, invoices, job notifications, payment receipts, booking confirmations, reminders
- **Broadcast stream (future):** Marketing emails, campaign sends — not in current scope but stream should be created for future use

Keeping streams separate maintains sender reputation — transactional emails are not penalised by marketing send patterns.

## 3.4 Sending Modes

### Mode 1: Platform-Managed (Default — All Tiers)

All emails send from ServizmaDesk's verified sending domain. Postmark handles delivery, bounce management, and reputation maintenance.

- **From address:** `notifications@mail.servizmadesk.com` (or similar verified subdomain)
- **Display name:** Tenant's company name (e.g., `Acme HVAC Services`)
- **Reply-To:** Configured per email type in tenant settings — goes to a team member's external inbox
- **No additional setup required** from the tenant

### Mode 2: Custom Domain (Paid Add-On — Plus and Above)

Tenant authenticates their domain with Postmark via DNS records. Emails send from the tenant's domain through Postmark's infrastructure. See Section 5 for full specification.

### Mode 3: BYOS (Not Supported)

BYOS (Bring Your Own SMTP) is not supported. Reasons:

1. **No delivery visibility:** ServizmaDesk cannot track delivery status, bounces, or open rates through the tenant's own mail server
2. **No metering accuracy:** Email point counting requires ServizmaDesk to control the sending path
3. **Support liability:** Gmail, Hotmail, and similar consumer accounts have strict daily sending limits (Gmail: 500/day free, 2,000/day Workspace). When limits are hit, emails silently fail. Tenants blame ServizmaDesk. This creates unresolvable support burden
4. **Competitor standard:** No FSM competitor supports BYOS. It is not an expected feature
5. **Replaced by better alternative:** Custom domain authentication gives tenants the result they want (emails from their domain) without the liability of routing through their own mail server

---

# 4. Platform Email Functionality (All Tiers)

## 4.1 Outbound Email Types by Tier

### Lite — Manual Only

| Email Type | Trigger | Notes |
|---|---|---|
| Quote sent | Manual — user clicks Send | PDF attachment optional |
| Invoice sent | Manual — user clicks Send | PDF attachment optional |
| Manual customer message | Manual — user composes | General communication |

No automated triggers on Lite. Consistent with SMS manual-only restriction.

### Plus, Pro, Enterprise — Manual and Automated

All Lite email types, plus:

| Email Type | Trigger | Notes |
|---|---|---|
| Booking confirmation | Auto — Work Order created/booked | |
| Appointment reminder | Auto — configurable timing before visit | 24hr, 2hr, etc. |
| On my way notification | Manual/Auto — tech dispatched | |
| Job completion notification | Auto — Work Order marked complete | |
| Payment receipt | Auto — payment recorded | |
| Invoice follow-up | Auto — configurable days after send | |
| Quote follow-up | Auto — configurable days after send | |
| Review request | Auto — configurable days after job completion | |
| Maintenance reminder | Auto — based on Customer Agreement schedule | |

## 4.2 Reply-To Configuration

Tenants configure reply-to addresses per email category in Settings → Email & Notifications:

- **Quote emails** → designated estimator/sales contact
- **Invoice emails** → designated billing contact
- **Job/Work Order emails** → assigned technician or dispatcher
- **General emails** → company default email

If a specific reply recipient is not configured, replies fall back to the company default email address.

If a reply recipient is deactivated as a user, their reply-to assignment is automatically removed and falls back to company default.

## 4.3 Outbound Communications Log

Every outbound email is recorded in the tenant's Communications Log and on the relevant customer/record timeline:

- Timestamp
- Email type
- Recipient email address
- Delivery status (Delivered, Bounced, Pending)
- Open status and timestamp (if opened)
- Preview of email body

This matches and exceeds Jobber's Client Communications Report.

## 4.4 Email Templates

Tenants can customise email templates per email type:

- Subject line
- Body text with merge tags (customer name, job address, tech name, quote total, invoice total, due date, etc.)
- Company logo (from tenant settings)
- Company contact details (auto-populated from tenant settings)

Default templates are provided for all email types at activation. Tenants customise as needed.

---

# 5. Custom Domain Email Add-On (Phase 1)

## 5.1 Overview

The Custom Domain Email add-on has two components that are sold together as a single add-on:

1. **Custom domain outbound** — emails appear to come from the tenant's own domain
2. **Inbound reply processing** — customer replies are captured back into ServizmaDesk and attached to records

Both components require domain verification. They are not available separately.

## 5.2 Custom Domain Outbound Setup Flow

1. Tenant navigates to Settings → Email → Custom Domain
2. Tenant enters their domain (e.g., `acmehvac.com`)
3. ServizmaDesk generates and displays three DNS records:
   - **SPF record** — authorises Postmark to send on behalf of the domain
   - **DKIM record** — cryptographic signature for email authenticity
   - **DMARC record** — policy for handling unauthenticated mail
4. Tenant adds these records to their DNS provider (instructions shown for common providers: GoDaddy, Cloudflare, Namecheap, Google Domains, etc.)
5. Tenant clicks "Verify Domain" — ServizmaDesk triggers Postmark domain verification
6. Postmark checks DNS records (can take up to 48 hours to propagate)
7. Once verified, all outbound platform emails for the tenant send from their domain via Postmark

**From address format:** `[email-type]@[tenant-domain]` — e.g., `quotes@acmehvac.com`, `invoices@acmehvac.com`

ServizmaDesk manages the Postmark domain registration on the backend. The tenant only fills in a form and adds DNS records — no Postmark account required.

## 5.3 Inbound Reply Processing Setup

Once the domain is verified, ServizmaDesk automatically configures inbound reply processing:

1. ServizmaDesk generates a unique inbound address per tenant: `reply+[unique_tenant_token]@inbound.servizmadesk.com`
2. This address is embedded as the `Reply-To` header on every outbound email for that tenant
3. When a customer replies, Postmark receives the email at the inbound address and fires a webhook to ServizmaDesk
4. ServizmaDesk's inbound webhook handler:
   - Extracts the tenant token from the To address
   - Identifies the originating record (Quote, Invoice, Work Order, Customer) from the token embedded in the original email's Message-ID
   - Attaches the reply as a new entry in the communication thread on that record
   - Notifies the configured reply recipient (same as their reply-to setting) via in-app notification

**Result:** The tenant sees a full conversation thread on the Quote or Invoice record — outbound send, customer reply, any subsequent replies — without leaving ServizmaDesk.

## 5.4 Phase 1 Inbound Addresses

Two pre-configured inbound address types in Phase 1:

| Address | Maps To | Action |
|---|---|---|
| `quotes@[tenant-domain]` | Reply-to for all Quote emails | Attaches reply to originating Quote record |
| `invoices@[tenant-domain]` | Reply-to for all Invoice emails | Attaches reply to originating Invoice record |

All other email types (notifications, reminders, etc.) use a generic reply token that attaches to the Customer record.

## 5.5 Phase 1 Scope Limitations

- One domain per tenant
- Inbound processing handles replies to outbound emails only — new inbound emails from unrecognised senders are not processed in Phase 1
- Unrecognised sender handling (new leads, new inquiries) is Phase 2 scope
- MMS/attachments in replies: attachments in customer replies are stored but not parsed
- No auto-responder functionality in Phase 1

## 5.6 Tenants Without a Domain

Tenants on Lite or those who have not purchased the Custom Domain add-on use platform-managed mode by default (emails from `@mail.servizmadesk.com`). This matches the functionality provided by all competitors and is fully acceptable for entry-level tenants.

Tenants who do not own a domain but want professional email sending should be directed to purchase a domain from a registrar (GoDaddy, Namecheap, Google Domains, etc.) before enabling the custom domain add-on.

---

# 6. Email Routing System (Phase 2 — Future)

## 6.1 Overview

Phase 2 extends inbound email processing from simple reply capture to a configurable routing system. Tenants can define multiple inbound email addresses, each mapped to a specific action within ServizmaDesk.

This is a meaningfully more complex feature than Phase 1 and is scoped as a separate, higher-priced add-on tier.

## 6.2 Phase 2 Scope (Initial)

Starting addresses and mappings for Phase 2:

| Address | Action |
|---|---|
| `inquire@[tenant-domain]` | Create new Lead in ServizmaCRM, notify assigned sales contact, appear in Lead queue |
| `quotes@[tenant-domain]` | Enhanced — new quote request from recognised customer creates Quote record; unrecognised sender creates Lead |
| `invoices@[tenant-domain]` | Enhanced — replies attach to invoice; payment disputes create flagged note |
| `service@[tenant-domain]` | Create new TroubleCall / service request from recognised customer |

**Unrecognised sender handling (Phase 2):**
- Email arrives from address not in the customer database
- ServizmaDesk creates a new Lead record with the sender's email, name (from email display name), and message body
- Assigned team member is notified
- Admin can convert the Lead to a Customer from the Lead record

## 6.3 Phase 2 Competitive Context

No FSM competitor has email routing at any price point. The closest analogy is Workiz's VoIP call routing system (~$100/month add-on). Phase 2 email routing should be priced in a similar range — it provides equivalent workflow automation value through a different channel.

Phase 2 pricing to be defined when scope is finalised. Maintained in this document and the Pricing & Billing Specification when ready.

## 6.4 Phase 2 Open Engineering Decisions

1. **Catch-all vs. specific addresses:** Does ServizmaDesk configure a catch-all (`*@[tenant-domain]`) and route based on To address, or register specific addresses only? Catch-all is simpler but requires handling spam/noise. Specific addresses require the tenant to update DNS for each new address.

2. **Spam handling:** Inbound emails from unrecognised senders that appear to be spam — what's the threshold and what happens? Options: discard silently, quarantine in a review queue, create Lead anyway.

3. **Multiple domains:** Phase 2 may allow tenants to register multiple domains (e.g., a business with multiple brands or locations). Pricing implications TBD.

4. **Auto-responder:** Should ServizmaDesk send an automatic acknowledgement when an inbound email creates a record? (e.g., "Thanks, we received your inquiry and will be in touch.") This would consume an outbound email point.

---

# 7. Email Points — Engineering Implementation

## 7.1 Counter Architecture

Per-tenant email counters in the ServizmaDesk database:

- `email_points_included` — set at tier provisioning and updated on plan changes
- `email_points_used` — incremented on each confirmed outbound send
- `email_points_overage` — accumulates overage points for Stripe billing
- `email_period_start` — billing anniversary date for reset

## 7.2 Send Flow

1. Application initiates email send (user action or automation trigger)
2. ServizmaDesk checks `email_points_used` vs `email_points_included`
3. If within allocation: send via Postmark, increment `email_points_used` on delivery confirmation webhook
4. If over allocation: send via Postmark, increment `email_points_overage`, flag for end-of-period billing
5. Postmark delivery webhook confirms delivery status — only confirmed sends increment counters
6. Failed delivery (bounce, rejection): counter not incremented, log failure on record

## 7.3 Tenant Dashboard Display

Tenants see two separate bar graphs in their billing dashboard:

- **Email Points:** [used] / [included] with overage cost displayed if applicable
- **SMS Points:** [used] / [included] with overage cost displayed if applicable

Both bars show:
- Current period usage in real time
- Percentage of allocation consumed
- Estimated overage charge (if applicable) based on current usage rate
- Days remaining in current billing period

No raw pricing is shown in the bar graphs themselves — only points and estimated charges. This keeps the UX simple and avoids confusion between the two systems.

## 7.4 Alerts

- **80% allocation consumed:** In-app notification to account admin
- **100% allocation consumed:** In-app notification + email to account admin (ironic but necessary)
- **Custom domain verification confirmed:** In-app notification + email
- **Custom domain DNS records missing or expired:** In-app warning

---

# 8. Open Decisions

| # | Decision | Notes |
|---|---|---|
| 1 | Plus tier access to custom domain outbound only (without inbound) | Currently Phase 1 add-on is Pro+ only at $20/month. Evaluate whether Plus tenants should get outbound custom domain authentication at a lower price point (e.g., $10/month) without inbound reply processing. This is the authoritative open decision for this question — previously listed in Pricing & Billing Spec Section 12.1 and removed from there. Resolve before Plus specification is written. |
| 2 | Enterprise email allotment vs Pro | Enterprise at 12,000 points/month. Validate against expected Enterprise usage profile (multi-location, higher volume) before confirming |
| 3 | Daily send limits in platform-managed mode | Postmark shared IP pools have throughput limits. Confirm if per-tenant daily limits are needed to prevent one tenant from consuming burst capacity |
| 4 | Email retention in Communications Log | How long are sent emails stored for preview? Postmark stores 45 days of full content history. ServizmaDesk should match or exceed this |
| 5 | Attachment handling in inbound replies | Customer attaches a photo to a reply — stored where? Counted against storage allocation? |
| 6 | Phase 2 pricing | To be defined when Phase 2 scope is finalised |
| 7 | Bundled Communication Package | Combined SMS + email point package — evaluate after both individual package models are established post-launch |
| 8 | International email | No specific considerations beyond standard Postmark international delivery — confirm no additional per-country pricing applies |

---

# 9. Pending Document Updates

The following documents contain references that conflict with decisions made in this specification. They must be updated before the affected tier specifications are built. All changes stem from the BYOS decision (BYOS dropped, replaced by Custom Domain authentication) and the Postmark provider confirmation.

| # | Document | Location | Issue | Required Change | Status |
|---|---|---|---|---|---|
| 1 | **Top-Down Specifications V1** | Section 10.6 (Email SMTP Configuration) | Entire section defines BYOS SMTP credential fields (Host, Port, Username, Password, TLS, SSL) | Replace with Custom Domain Authentication section — tenant provides domain, ServizmaDesk generates DNS records (SPF, DKIM, DMARC), domain verified via Postmark | ✅ Complete — V1 updated March 2026 |
| 2 | **Top-Down Specifications V1** | Line ~1249 (Email Provider setting) | Describes "Configurable SMTP or Point-based system" | Update to "Point-based system (platform-managed) or Custom Domain authentication (paid add-on)" | ✅ Complete — V1 updated March 2026 |
| 3 | **Top-Down Specifications V1** | Section covering email modes (~line 2001) | Mode 2 defined as "Bring Your Own SMTP" | Replace Mode 2 with Custom Domain authentication — DNS-verified, Postmark-delivered from tenant domain | ✅ Complete — V1 updated March 2026 |
| 4 | **Top-Down Specifications V1** | Tier feature matrix (~line 2126) | Row: `System Email (Bring Your Own SMTP)` | Replace with `System Email (Custom Domain — paid add-on, Pro+)` | ✅ Complete — V1 updated March 2026 |
| 5 | **Product Tier Map V2** | Email mode description (~line 169) | Describes Mode 2 as "Bring Your Own SMTP with no limit, sent through tenant's own email provider" | Update to Custom Domain authentication description | ✅ Complete — V2 updated March 2026 |
| 6 | **Product Tier Map V2** | Tier feature matrix (~line 315) | Row: `System Email (Bring Your Own SMTP)` | Replace with `System Email (Custom Domain — paid add-on, Pro+)` | ✅ Complete — V2 updated March 2026 |
| 7 | **Technical Architecture V2** | Line ~193 | States "Two modes are planned: ServizmaDesk-managed and Bring Your Own SMTP (BYOSMTP)" | Update to confirmed architecture: Mode 1 = platform-managed (default, all tiers via Postmark); Mode 2 = Custom Domain (paid add-on, Plus+, DNS-authenticated); BYOS dropped | ✅ Complete — V2 updated March 2026 (also fixed stale SMS allotments 100/250→350/750, confirmed Twilio as provider dropping Plivo candidate, removed stale system email deferral from Defers To) |
| 8 | **SDP Specification V2** | Line ~1172 | States "The provider has not been selected yet" | Remove stale language — Postmark is confirmed (contradicted by line 1315 in the same document) | ✅ Complete — V2 updated March 2026 (also fixed stale BYOS reference in Section 9.4 decision note and removed stale dependency rule from Section 9.5) |

**Priority order for updates:** Top-Down Specifications V1 first (most references, most impact), then Product Tier Map V2, then Technical Architecture V2, then SDP Specification V2.

---

# 10. Document Relationships

## 10.1 This Document Depends On
- **Pricing & Billing Specification V2** — Section 10A (email pricing), Section 11.4 (custom domain add-on pricing)
- **Top-Down Specifications V3** — Communication features per tier (Section 14.5)

## 10.2 Documents That Reference This Specification
- **Pricing & Billing Specification V2** — Section 11.4 references this document for Phase 2 scope

## 10.3 Documents Requiring Updates Due to This Specification
See **Section 9 (Pending Document Updates)** for the full list of affected documents and required changes.

## 10.4 Related Documents
- **ServizmaDesk GPS Tracking Strategy & Feasibility Brief V1** — parallel structure for a deferred feature
- **Postmark documentation** — inbound processing, domain authentication, message streams

---

# 11. Version History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | March 2026 | ServizmaDesk | Initial specification. Covers competitive baseline, Postmark architecture, platform email functionality, Phase 1 custom domain add-on (outbound + inbound reply), Phase 2 email routing (future), points engineering implementation, and open decisions. BYOS decision documented and rationale provided. Added Section 9 Pending Document Updates — 4 documents identified requiring updates due to BYOS removal and Postmark confirmation: Top-Down Specifications V1, Product Tier Map V2, Technical Architecture V2, SDP Specification V2. |
| 1.1 | March 2026 | ServizmaDesk | Expanded Open Decision item 1 (Plus tier custom domain) to be the authoritative home for this question, noting it was removed from Pricing & Billing Specification V2 Section 12.1 and should be resolved before the Plus specification is written. |
| 1.2 | March 2026 | ServizmaDesk | Updated Section 9 Pending Document Updates — marked items 1–4 (Top-Down Specifications V1) as complete. All four Top-Down Spec changes applied: Section 10.6 replaced with Custom Domain Authentication, Email Provider setting updated, email modes updated, tier feature matrix BYOS row replaced with Custom Domain add-on row. Items 5–8 remain pending. |
| 1.3 | March 2026 | ServizmaDesk | Marked items 5–6 (Product Tier Map V2) as complete. Four changes applied: Plus email description updated to point-based system with Custom Domain add-on reference, Pro email description updated to remove stale two-modes/daily-limits language, tier feature matrix BYOS row replaced with Custom Domain add-on row, stale "System email daily limits" open item removed from feature specification list. Items 7–8 remain pending. |
| 1.4 | March 2026 | ServizmaDesk | Marked item 8 (SDP Specification V2) as complete. Three changes applied: Section 9.1 stale "provider not selected" paragraph removed, Section 9.4 decision note updated to remove BYOS/User-supplied SMTP reference and reflect confirmed architecture (Postmark for all email, point-based system, Custom Domain add-on), Section 9.5 rule 6 (stale "email provider must be selected" dependency) removed. Item 7 (Technical Architecture V2) remains pending. |
| 1.5 | March 2026 | ServizmaDesk | Marked item 7 (Technical Architecture V2) as complete. Four changes applied: email row updated to confirmed architecture (point-based, Postmark, Custom Domain add-on, BYOS not supported); SMS allotments corrected (100/250→350/750, Lite 100 manual-only noted); Twilio confirmed as SMS provider (Plivo candidate removed); stale "system email architecture" item removed from Defers To row. All 8 pending document updates now complete. |

---

**END OF DOCUMENT**
