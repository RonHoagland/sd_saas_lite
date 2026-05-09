# ServizmaDesk Pricing & Billing Specification V1

**Document Status:** Draft  
**Version:** 1.1  
**Last Updated:** March 2026  
**Owner:** ServizmaDesk  
**Supersedes:** All pricing sections in Product Tier Map V1, Platform (SDP) Specification V1, Operational Plan V2, and Top-Down Specifications V1

---

# 1. Document Purpose & Scope

This document is the single source of truth for all ServizmaDesk pricing, billing, and Founding Partner program details. All other ServizmaDesk specifications reference this document for pricing information.

**In Scope:**
- Standard tier pricing (Lite, Plus, Pro, Enterprise)
- Monthly vs. annual billing models
- Founding Partner program structure (Lite and Plus tiers)
- Storage pricing and add-ons
- SMS point pricing (future)
- Trial structure and conversion flow
- Competitive positioning rationale

**Out of Scope:**
- Stripe technical implementation (covered in Platform Specification)
- Feature definitions by tier (covered in Product Tier Map)
- Billing UI/UX specifications (covered in individual tier specifications)

---

# 2. Pricing Philosophy & Market Positioning

## 2.1 Strategic Intent

ServizmaDesk pricing is designed to:

1. **Capture the underserved micro-business segment** (1-3 users) that Jobber and HousecallPro overprice
2. **Position Lite as an acquisition tier** — a low-friction entry point that demonstrates value
3. **Drive revenue through Plus** — where most customers are expected to land as they scale
4. **Provide a growth ceiling with Pro** — for serious businesses avoiding ServiceTitan's enterprise pricing
5. **Signal quality, not desperation** — pricing must be inexpensive without appearing cheap

## 2.2 Competitive Landscape

### Primary Competitors

| Competitor | Solo User Pricing | Small Team (3 users) | Target Market |
|------------|------------------|---------------------|---------------|
| **HousecallPro Basic** | $79/month | $189/month (flat, up to 5 users) | SMB home services |
| **Jobber Core** | $39/month | $129/month (2 users max) | SMB home services, broad verticals |
| **ServiceTitan** | Enterprise pricing | $300+/month | Mid-large enterprise HVAC/plumbing |

### ServizmaDesk Positioning

ServizmaDesk Lite at $29/month (annual) undercuts both primary competitors while delivering superior asset-centric architecture:

- **63% cheaper than HousecallPro Basic** ($79)
- **26% cheaper than Jobber Core** ($39)
- **Architectural advantage:** Asset as first-class entity (neither competitor has this)
- **QuickBooks CSV export in Lite** (HCP gates QB sync to $189/month Essentials tier)

## 2.3 The Pricing Ladder Strategy

ServizmaDesk uses a **gateway → revenue → growth** tier model:

| Tier | Role | Price Point | Customer Expectation |
|------|------|-------------|---------------------|
| **Lite** | Gateway / Acquisition | $29-35/month | "Learning the system, trying it out" |
| **Plus** | Revenue Engine | $49/month | "Running my business day-to-day" |
| **Pro** | Growth Ceiling | $98/month | "Scaling operations, need advanced tools" |
| **Enterprise** | Future Vision | TBD | "Multi-location, full ERP needs" |

**Critical Insight:** Lite is intentionally feature-limited to create natural upgrade pressure to Plus. The pricing gap from Lite → Plus (69-104% increase depending on final Lite price) must feel justified by the automation, scheduling, and communication tools unlocked in Plus.

---

# 3. Standard Pricing Structure

## 3.1 Tier Pricing Table

| Tier | Monthly Price/Seat | Annual Price/Seat | Max Seats | Storage Included | Max Storage |
|------|-------------------|------------------|-----------|------------------|-------------|
| **Lite** | $35/month | $29/month | 10 | 3 GB | 10 GB |
| **Plus** | $59/month | $49/month | Unlimited | 10 GB | 75 GB |
| **Pro** | $118/month | $98/month | Unlimited | 25 GB | Unlimited |
| **Enterprise** | TBD | $145/month (proposed) | Unlimited | 25 GB | Unlimited |

**Pricing Note:** Lite pricing raised from original $24/month (annual) to $29/month to signal quality while maintaining competitive advantage. At $29/month annual, ServizmaDesk Lite is:
- 63% cheaper than HousecallPro Basic ($79)
- 26% cheaper than Jobber Core ($39)
- Still positioned as "inexpensive" rather than "cheap"

**Annual Discount:** Annual billing provides approximately 17% discount vs. monthly billing across all tiers.

## 3.2 Billing Cycles

All plans support both monthly and annual billing:

**Monthly Billing:**
- Charged per seat per month
- Billed on the anniversary of signup date each month
- Stripe manages recurring charges automatically
- Proration applied for mid-cycle seat changes

**Annual Billing:**
- Charged as lump sum for full year at annual rate
- Billed on anniversary of signup date each year
- Proration applied for mid-year seat changes
- Stripe handles proration calculation

**Switching Billing Cycles:**
- Customers may switch between monthly and annual from the Billing section in SDTA
- Changes take effect at the end of the current billing period
- No retroactive charges or credits for the current period

## 3.3 Seat-Based Billing Rules

### Seat Counting
Each active user consumes one seat. Seat count for billing purposes includes:

**Counted toward seat limit:**
- Employees with Status: Active
- Employees with Status: On Leave
- Employees with Status: Inactive

**Not counted toward seat limit:**
- Employees with Status: Terminated (and Termination Date populated)

### Seat Changes and Proration
| Event | SDP Action | Stripe Action |
|-------|-----------|---------------|
| New employee added | Notifies Stripe of new seat count | Prorates charge for remainder of billing period |
| Employee set to Terminated | Notifies Stripe of reduced seat count | Applies credit for remainder of billing period |

### Lite Seat Limit Enforcement
Lite tier is capped at 10 seats. When the account reaches 10 employees (Active + On Leave + Inactive), the system blocks creation of additional employees and displays:

> "Maximum employee limit reached for Lite plan. Upgrade to Plus for unlimited seats."

To free a seat, an employee must be set to Status: Terminated with a populated Termination Date.

---

# 4. Storage Pricing

## 4.1 Included Storage by Tier

| Tier | Storage Included | Max Storage Allowed | Add-On Options |
|------|-----------------|---------------------|----------------|
| **Lite** | 3 GB | 10 GB | +5 GB, +10 GB |
| **Plus** | 10 GB | 75 GB | +25 GB, +50 GB, +75 GB |
| **Pro** | 25 GB | Unlimited | +50 GB, +75 GB, Unlimited |
| **Enterprise** | 25 GB | Unlimited | Unlimited |

## 4.2 Storage Add-On Pricing

**Lite Tier:**
- +5 GB: $10/month
- +10 GB: $15/month

**Plus Tier:**
- +25 GB: $25/month
- +50 GB: $45/month
- +75 GB: $60/month

**Pro Tier:**
- +50 GB: $40/month
- +75 GB: $55/month
- Unlimited: $100/month

**Billing Notes:**
- Storage add-ons are billed as separate Stripe subscription line items
- Changes to storage add-ons take effect immediately
- Proration applies for mid-cycle storage changes
- If a customer downgrades from a higher tier to a lower tier, storage usage must be within the lower tier's max storage limit before downgrade is allowed

---

# 5. Founding Partner Program

## 5.1 Program Overview

The Founding Partner program offers exclusive legacy pricing to the first 20 companies (10 Lite, 10 Plus) who commit to ServizmaDesk during the initial launch phase. This program serves three strategic purposes:

1. **Early Validation:** Real businesses stress-testing the platform in production
2. **Controlled Feedback:** Direct access to early adopters for product refinement
3. **Revenue Injection:** Early cash flow during MVP stabilization phase

**Program Limits:**
- **10 Founding Partner — Lite slots**
- **10 Founding Partner — Plus slots**
- Once all 20 slots are filled, the program closes permanently
- No extensions, no exceptions

## 5.2 Founding Partner — Lite

**Target Customer:** Micro-businesses (1-3 users) who need basic service management structure.

**Pricing:**
- **$200 per seat per year** ($16.67/month equivalent)
- **$17 per seat per month** (monthly billing option, slight premium for convenience)

**Tier Access:** Full Lite tier features

**Commitment Terms:**
- 24-month lock from activation date
- Seats may be added during 24-month window at Founding Partner rate
- Automatic conversion to standard Lite pricing after 24 months expires
- No refunds
- No extensions to the 24-month window

**Post-Program Pricing:**
After 24 months, accounts auto-convert to:
- **Standard Lite: $29/month per seat** (annual) or $35/month (monthly)
- **Price increase: 72% from FP rate** ($16.67 → $29)

**Qualification Criteria:**
- 1-3 active users (or plan to remain at this scale)
- Primarily manual workflow needs
- Willing to provide monthly feedback calls during first 6 months

**Implemented via:** Stripe coupon code `FP_LITE_2025` (100% off difference between standard Lite annual rate and FP rate for 24 months)

## 5.3 Founding Partner — Plus

**Target Customer:** Established small businesses (3-8 users) who need automation, scheduling, and communication tools.

**Pricing:**
- **$400 per seat per year** ($33.33/month equivalent)
- **$34 per seat per month** (monthly billing option, slight premium for convenience)

**Tier Access:** Full Plus tier features (automation, scheduling, procurement, SMS, system email, PDF generation)

**Commitment Terms:**
- 24-month lock from activation date
- Seats may be added during 24-month window at Founding Partner rate
- Automatic conversion to standard Plus pricing after 24 months expires
- No refunds
- No extensions to the 24-month window

**Post-Program Pricing:**
After 24 months, accounts auto-convert to:
- **Standard Plus: $49/month per seat** (annual) or $59/month (monthly)
- **Price increase: 47% from FP rate** ($33.33 → $49)

**Qualification Criteria:**
- 3+ active users (or clear plan to scale to 3+ within 90 days)
- Currently using competitor tool OR managing business in spreadsheets/QuickBooks
- Willing to provide bi-weekly feedback calls during first 6 months
- Must activate at least 2 Plus-tier features (automation, scheduling, procurement, SMS) within first 90 days

**Implemented via:** Stripe coupon code `FP_PLUS_2025` (100% off difference between standard Plus annual rate and FP rate for 24 months)

## 5.4 Founding Partner Seat Addition Rules

**During 24-month FP window:**
- Additional seats added to FP account = charged at FP rate
- Example: FP Plus customer adds 2 seats in Month 8 → new seats charged at $400/year FP rate

**After 24-month FP window expires:**
- Additional seats added to converted account = charged at standard rate
- Example: Former FP Plus customer (now paying $49/month standard) adds 2 seats → new seats charged at $49/month standard rate

## 5.5 Founding Partner Upgrade Path

**FP Lite → Standard Plus Upgrade:**
- If FP Lite customer upgrades to Plus during 24-month window, they lose FP Lite pricing
- Upgrade immediately converts account to **standard Plus pricing** ($49/month annual or $59/month)
- This is the correct incentive structure — we want customers paying full price for Plus features

**FP Plus → Standard Pro Upgrade:**
- If FP Plus customer upgrades to Pro during 24-month window, they lose FP Plus pricing
- Upgrade immediately converts account to **standard Pro pricing** ($98/month annual or $118/month)

## 5.6 Founding Partner Revenue Projections

**Scenario: 5 Lite FP + 5 Plus FP (average 3 seats each)**

**During 24-month FP window:**
- 5 Lite FP companies × 3 seats × $200/year = $3,000/year
- 5 Plus FP companies × 3 seats × $400/year = $6,000/year
- **Total FP revenue: $9,000/year** for 24 months = **$18,000 total**

**After 24-month FP conversion:**
- 5 former Lite FP companies × 3 seats × $348/year (at $29/month annual) = $5,220/year
- 5 former Plus FP companies × 3 seats × $588/year (at $49/month annual) = $8,820/year
- **Total post-FP revenue: $14,040/year** (assumes zero natural upgrades during FP window)

**Expected Reality:** Some Lite FP customers will upgrade to standard Plus during the 24-month window, increasing annual revenue above baseline projections.

---

# 6. Free Trial Structure

## 6.1 Trial Terms

- **Duration:** 14 days from account creation
- **Credit card required:** No (true self-service trial)
- **Functionality available:** Full Lite tier functionality
- **Trial countdown:** Visible timer displayed throughout application
- **Data retention:** All data preserved if customer converts; 60-day grace period before deletion if customer does not convert

## 6.2 Trial Expiration Flow

**Days 1–14: Active Trial**
- Full access to all Lite features
- Countdown timer visible on Dashboard and Admin Section
- Friendly reminder messaging: "X days remaining. Your data will be preserved if you add payment before Day 15."

**Day 15: Trial Ends → Read-Only Mode**
- At midnight on Day 15, account automatically enters read-only mode
- User can log in and view all data but cannot create or edit records
- Persistent banner displays: "Your trial has ended. Add payment to resume full access."
- User is directed to Billing section to select plan (Lite, Plus, Pro) and enter payment
- Data remains intact and accessible in read-only state

**Day 45: Cleanup Flag (30 days post-trial)**
- If no payment has been received by Day 45, account is flagged for cleanup
- 60-day data retention grace period begins
- Email sent to account owner: "Your trial account will be permanently deleted in 60 days unless you add payment."

**Day 105: Permanent Deletion (60 days post-cleanup flag)**
- Tenant data is permanently deleted per data retention policy
- No recovery possible after this point

## 6.3 Trial Conversion

**Payment Entry:**
- Upon entering payment on or after Day 15 (read-only mode), account is immediately restored to full access
- Customer selects plan (Lite, Plus, or Pro) and billing frequency (monthly or annual)
- First billing cycle begins immediately
- **No retroactive charge for the trial period** — billing starts from conversion date forward

**Conversion Incentives:**
- Email sequence during Days 10-14 highlighting key features used during trial
- Optional: "Convert to Plus within 30 days of trial start and receive first 2 months at 50% off" (future consideration)

---

# 7. Plan Upgrades and Downgrades

## 7.1 Upgrades (Lite → Plus → Pro)

**Behavior:**
- Takes effect immediately upon confirmation
- Customer is charged prorated amount for remainder of current billing period at new plan rate
- Unused credit from lower plan is applied against higher plan charge
- Stripe handles all proration calculations automatically
- SDTA account is updated immediately to reflect new plan limits (storage, seats, features)
- SDP updates tenant record with new plan and Stripe subscription details
- Plan change confirmation email sent to billing email address

**Example: Lite → Plus Upgrade (Mid-Month)**
- Customer on Lite monthly plan ($35/month, 3 seats) = $105/month total
- Upgrades to Plus on Day 15 of billing cycle
- Remaining 15 days at Plus rate ($59/month, 3 seats) = $177/month total
- Prorated charge: (15 days ÷ 30 days) × $177 = $88.50
- Credit from unused Lite period: (15 days ÷ 30 days) × $105 = $52.50
- **Net charge at upgrade: $88.50 - $52.50 = $36.00**

## 7.2 Downgrades (Pro → Plus → Lite)

**Behavior:**
- Takes effect immediately upon confirmation
- Customer receives credit for unused time on higher plan, applied against lower plan charge
- Stripe handles all proration calculations automatically
- SDTA account is updated immediately to reflect lower plan limits
- SDP updates tenant record with new plan and Stripe subscription details

**Downgrade Restrictions:**
Before downgrade is allowed, SDP verifies:

| Check | Rule |
|-------|------|
| **Seat count** | Active + On Leave + Inactive employees must be ≤ lower plan seat limit |
| **Storage usage** | Current storage used must be ≤ lower plan max storage limit |

**Downgrade Blocked Message:**
If any check fails, customer sees:

> "Your account cannot be downgraded to ServizmaDesk Lite at this time. The following must be resolved first:
> - You have 12 active seats. ServizmaDesk Lite allows a maximum of 10 seats. Please set 2 employees to Terminated status.
> - You are using 15 GB of storage. ServizmaDesk Lite allows a maximum of 10 GB. Please reduce storage usage before downgrading."

**Data Preservation on Downgrade:**
- Higher-tier data is **not deleted** on downgrade
- UI restricts access to higher-tier features (Leads, Opportunities, Advanced Procurement, etc.)
- Data remains in database
- If customer upgrades again, data reappears
- This is a key benefit of shared-schema, UI-gated architecture

**Example: Plus → Lite Downgrade**
- Customer downgrades from Plus to Lite
- Leads module becomes inaccessible in UI (feature not available in Lite)
- All Lead records remain in database unchanged
- If customer upgrades back to Plus, Leads module reappears with all historical data intact

---

# 8. Cancellations and Data Retention

## 8.1 Cancellation Process

**Customer-Initiated:**
- Customer may cancel from Billing section in SDTA or by contacting ServizmaDesk support
- Cancellation takes effect at the end of the current billing period
- No partial refunds for unused time in current period
- Customer retains full access until end of paid period

**Staff-Initiated:**
- ServizmaDesk staff may cancel account for Terms of Service violations or non-payment
- Customer is notified via email before cancellation takes effect
- Standard data retention policy applies

## 8.2 Data Retention Policy

**Active Accounts:**
- All data retained indefinitely while account is active and in good standing

**Post-Cancellation:**
- **Read-only access for 30 days** after final billing period ends
- Customer can log in, view data, and export records
- No create/edit/delete operations allowed
- Account status: "Cancelled - Data Accessible"

**60-Day Grace Period:**
- After 30-day read-only period expires, account enters 60-day grace period
- Customer can no longer log in
- Data remains in database
- Customer may reactivate account by contacting support and entering payment
- Account status: "Cancelled - Grace Period"

**Permanent Deletion:**
- **90 days after cancellation** (30-day read-only + 60-day grace), tenant data is permanently deleted
- No recovery possible after deletion
- Customer is notified via email 7 days before permanent deletion

**Timeline Summary:**
- Day 0: Cancellation effective date (end of paid period)
- Days 1-30: Read-only access
- Days 31-90: Grace period (no access, data retained)
- Day 91: Permanent deletion

---

# 9. Payment Security and PCI Compliance

## 9.1 No Raw Card Data Storage

**Critical Security Requirement:** ServizmaDesk never stores raw payment card data at any layer.

**Platform Billing (ServizmaDesk subscription charges):**
- All card collection uses **Stripe Checkout**
- Customer redirected to Stripe-hosted payment page
- Stripe returns tokenized payment method ID to SDP
- SDP stores only: Stripe Customer ID, Subscription ID, payment method ID (token)
- **No card numbers, CVV, or expiration dates stored in ServizmaDesk systems**

**Tenant Payment Processing (Plus and above):**
- Tenants use **Stripe Connect** to bill their own customers
- Payment collection happens via Stripe-hosted forms or Stripe Payment Links
- Tenant systems (SDTA) never see raw card data
- All PCI compliance burden handled by Stripe

## 9.2 PCI DSS Posture

ServizmaDesk qualifies for **PCI SAQ A** (Self-Assessment Questionnaire A) because:
- No card data flows through ServizmaDesk systems
- No card data is stored on ServizmaDesk servers
- All payment collection delegated to Stripe (PCI Level 1 Service Provider)

This is a non-negotiable architecture decision and applies to all tiers and all payment flows.

---

# 10. SMS Pricing (Future)

**Note:** SMS is a Plus and Pro tier feature. Pricing structure to be defined in Plus specification. Placeholder details below.

## 10.1 SMS Point System

- **1 point = 1 outbound SMS message**
- Monthly point allotment included with Plus and Pro
- Additional point tiers available for purchase as add-ons

**Proposed Point Allotments (Pending Validation):**
- Plus: 100 points/month included
- Pro: 250 points/month included

**Proposed Add-On Point Tiers (Pending Validation):**
- +100 points: $10/month
- +500 points: $40/month
- +1,000 points: $75/month

**Point Rollover:** Unused points do not roll over to next billing period.

**International SMS:** International SMS pricing to be defined. May consume multiple points per message depending on destination country.

---

# 11. Open Pricing Decisions

The following pricing elements are identified but not yet finalized:

## 11.1 To Be Defined in Plus Specification
- SMS point allotments and add-on pricing (final validation required)
- System email daily limits for ServizmaDesk-managed email mode
- Maintenance Agreements pricing (if unbundled from Plus tier)

## 11.2 To Be Defined in Pro Specification
- REST API rate limits and potential premium API tier pricing
- Advanced reporting add-on pricing (if unbundled from Pro tier)

## 11.3 Add-On Module Pricing

Add-on modules are available to eligible tiers at a flat per-tenant per-month rate, billed as a separate Stripe subscription line item. Add-ons are not per-seat.

| Add-On Module | Available To | Pricing Model | Price |
|---|---|---|---|
| **Fleet Management** | Pro, Enterprise | Flat per-tenant/month | TBD — target range $49–69/month |

**Fleet Management pricing notes:**
- Flat rate per tenant regardless of vehicle count
- Available only when tenant is on Pro or Enterprise base plan
- Add-on is cancelled independently of base plan — cancelling Fleet Management does not cancel the base subscription
- Data retention on add-on cancellation: Vehicle, Maintenance, and Mileage Log records enter the standard 60-day grace period before deletion
- If tenant downgrades from Pro to Plus or Lite, Fleet Management add-on is automatically cancelled (add-on requires Pro or Enterprise base)

## 11.4 To Be Defined in Enterprise Specification
- Enterprise monthly pricing (currently placeholder $145/month annual)
- Enterprise tier seat structure (flat rate vs. per-seat)
- Offline mobile app pricing (if offered as paid add-on)

## 11.5 To Be Defined in Financial Planning
- Annual billing discount percentage validation (currently ~17% across all tiers)
- Fleet Management final price point (validate against standalone fleet software market)
- Multi-year prepay discount structure (if offered)
- Non-profit/educational discount structure (if offered)
- Referral credit program (if implemented)

---

# 12. Document Relationships

## 12.1 This Document Supersedes

All pricing and billing sections in the following documents are superseded by this specification:

- **ServizmaDesk Product Tier Map V1** — Section 3 (Pricing and Billing), Section 4 (Free Trial Structure), Section 5 (Founding Partner Program)
- **ServizmaDesk Platform (SDP) Specification V1** — Section 5.2 (Plan Limits Table), Section 5.3 (Billing Cycles), Section 6.3 (Billing Model), Section 6.4 (Seat Billing), Section 6.5 (Storage Add-On Billing)
- **ServizmaDesk SaaS Operational Plan V2** — Section 2 (Product Tier Structure), Section 3 (Founding Partner Program)
- **ServizmaDesk Top-Down Specifications V1** — Section 14 Pricing rows in the Tier Feature Mapping table

## 12.2 This Document Depends On

- **ServizmaDesk Product Tier Map V1** — for feature definitions by tier
- **ServizmaDesk Platform (SDP) Specification V1** — for Stripe technical implementation, provisioning flows, and billing automation

## 12.3 Documents That Reference This Specification

- **ServizmaDesk Product Tier Map V1** — references this document for all pricing details
- **ServizmaDesk Platform (SDP) Specification V1** — references this document for billing rules and pricing structure
- **ServizmaDesk Lite MVP V3 Specification** — references this document for Lite pricing and trial structure
- **ServizmaDesk Top-Down Specifications V1** — references this document for all pricing; contains no pricing data of its own
- **ServizmaDesk Plus Specification (future)** — references this document for Plus pricing and SMS point pricing
- **ServizmaDesk Pro Specification (future)** — references this document for Pro pricing

---

# 13. Competitive Positioning Summary

## 13.1 Why ServizmaDesk Pricing Works

**Lite at $29/month (annual):**
- 63% cheaper than HousecallPro Basic ($79)
- 26% cheaper than Jobber Core ($39)
- Still signals quality (not "cheap" like $24/month would)
- Includes Asset architecture (unique differentiator)
- Includes QuickBooks-formatted CSV export (HCP gates QB to $189/month tier)

**Plus at $49/month (annual):**
- Competitive with HCP Essentials ($189 flat for up to 5 users = $38/user) at 4-5 user scale
- Significantly cheaper than Jobber Grow ($349 for up to 6 users = $58/user)
- Unlocks automation, scheduling, SMS, procurement — real operational efficiency gains
- Natural upgrade path from Lite when businesses hit growth inflection point

**Pro at $98/month (annual):**
- Way cheaper than ServiceTitan (enterprise pricing, $300+/month)
- Competitive with Jobber Plus ($599 for up to 15 users = $40/user) at smaller scale
- Provides growth ceiling for businesses avoiding "big platform" pricing
- Multi-location, API access, advanced reporting — serious business tools

## 13.2 The Pricing Ladder Psychology

**Lite ($29):** "I can try this without breaking the bank."  
**Plus ($49):** "The automation and scheduling will save me more than $49/month in time."  
**Pro ($98):** "I'm scaling my business and need real tools, but I'm not paying ServiceTitan prices."

Each tier jump must feel **justified by the value unlocked**, not just a price increase.

---

# 14. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 Draft | March 2026 | ServizmaDesk | Initial draft incorporating competitive analysis, Founding Partner tier structure, and strategic pricing decisions |
| 1.1 | March 2026 | ServizmaDesk | Added Top-Down Spec to supersedes list; renamed Service Item → Asset in positioning language; removed ISBMG references; added Top-Down Spec to referencing documents list |

---

**END OF DOCUMENT**
