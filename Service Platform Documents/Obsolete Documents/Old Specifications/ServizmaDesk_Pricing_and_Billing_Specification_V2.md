# ServizmaDesk Pricing & Billing Specification V2

**Document Status:** Active  
**Version:** 2.11  
**Last Updated:** March 2026  
**Owner:** ServizmaDesk  
**Supersedes:** All pricing sections in Product Tier Map V1, Product Tier Map V2, Platform (SDP) Specification V1, Platform (SDP) Specification V2, Operational Plan V2, Operational Plan V3, and Top-Down Specifications V1/V3

---

# 1. Document Purpose & Scope

This document is the single source of truth for all ServizmaDesk pricing, billing, and Founding Partner program details. All other ServizmaDesk specifications reference this document for pricing information.

**In Scope:**
- Standard tier pricing (Lite, Plus, Pro, Enterprise)
- Monthly vs. annual billing models
- Founding Partner program structure (Lite and Plus tiers)
- Storage pricing and add-ons
- SMS point pricing and overage
- Email point pricing and overage
- Add-on module pricing (Storage, Fleet Maintenance, Custom Domain Email)
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

| Tier | Role | Annual Price/Seat | Customer Expectation |
|------|------|-------------------|---------------------|
| **Lite** | Gateway / Acquisition | $29/month | "Learning the system, trying it out" |
| **Plus** | Revenue Engine | $49/month | "Running my business day-to-day" |
| **Pro** | Growth Ceiling | $98/month | "Scaling operations, need advanced tools" |
| **Enterprise** | Future Vision | $179/month | "Multi-location, full ERP needs" |

**Critical Insight:** Lite is intentionally feature-limited to create natural upgrade pressure to Plus. The pricing gap from Lite → Plus (~69% increase on annual billing) must feel justified by the automation, scheduling, SMS, and communication tools unlocked in Plus.

---

# 3. Standard Pricing Structure

## 3.1 Tier Pricing Table

| Tier | Monthly Price/Seat | Annual Price/Seat | Max Seats |
|------|-------------------|------------------|-----------|
| **Lite** | $35/month | $29/month | 10 |
| **Plus** | $59/month | $49/month | Unlimited |
| **Pro** | $118/month | $98/month | Unlimited |
| **Enterprise** | $216/month | $179/month | Unlimited |

**Pricing Note:** Lite is priced at $29/month (annual) and $35/month (monthly). At $29/month annual, ServizmaDesk Lite is:
- 63% cheaper than HousecallPro Basic ($79)
- 26% cheaper than Jobber Core ($39)
- Positioned as "inexpensive" rather than "cheap" — deliberate signal of quality

**Enterprise Pricing Note:** Enterprise is priced at $179/month (annual) and $216/month (monthly). This positions ServizmaDesk Enterprise as dramatically more accessible than ServiceTitan ($200–$500/technician/month with $5K–$50K+ implementation fees) while delivering equivalent or superior capability — multi-location, full ERP accounting, route optimization, and bank feed integration — with no implementation fees and transparent published pricing.

**Annual Discount:** Annual billing provides approximately 17% discount vs. monthly billing across all tiers, including Enterprise ($216 → $179 = ~17.1%).

> **Storage included per tier is documented in Section 4. Storage add-on pricing is documented in Section 11.1.**

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

### Seat Licensing (Purchased Seats vs. Assigned Users)
Tenants are billed by the number of **Purchased Seats**, not dynamically by active users. This prevents "floating seat" abuse where admins juggle statuses to dodge fees.

- When a tenant wants to add a new employee beyond their current paid capacity, they must explicitly purchase an additional seat. This triggers a prorated charge for the remainder of the billing period.
- If an employee is set to Terminated, the seat they occupied becomes **vacant**, but the total number of paid seats remains unchanged. The tenant can invite a new employee into that vacant seat without triggering a new Stripe charge.
- To receive a credit/reduce cost, the tenant must explicitly reduce their seat count (remove a vacant seat) in the Billing section.

### Lite Seat Limit Enforcement
Lite tier is capped at 10 seats. When the account reaches 10 employees (Active + On Leave + Inactive), the system blocks creation of additional employees and displays:

> "Maximum employee limit reached for Lite plan. Upgrade to Plus for unlimited seats."

To free a seat, an employee must be set to Status: Terminated with a populated Termination Date.

---

# 4. Storage

## 4.1 Storage Provider

ServizmaDesk uses **DigitalOcean Spaces** as its file storage provider. DigitalOcean Spaces is an S3-compatible object storage service with a built-in CDN. It is the designated storage backend for all tenant-uploaded files including job photos, documents, attachments, and exported reports.

**DigitalOcean Spaces cost basis (platform operating cost — not charged directly to tenants):**
- Base subscription: $5.00/month (covers up to 250 GiB across all tenant buckets)
- Additional storage beyond 250 GiB: $0.02/GiB/month
- Outbound bandwidth: 1,024 GiB/month included; $0.01/GiB beyond that

These are ServizmaDesk's infrastructure costs. Tenants are not billed at DO Spaces rates — they are billed at the storage add-on rates defined in Section 11.1, which are priced to cover platform cost plus margin.

## 4.2 Included Storage by Tier

Each tier includes a monthly storage allocation as part of the base subscription. This covers all tenant-uploaded files stored in DigitalOcean Spaces.

| Tier | Storage Included | Max Storage Allowed |
|------|-----------------|---------------------|
| **Lite** | 3 GB | 10 GB |
| **Plus** | 10 GB | 75 GB |
| **Pro** | 25 GB | 500 GB |
| **Enterprise** | 50 GB | 1,500 GB |

**Storage allocation notes:**
- Storage is measured as total file storage per tenant across all DigitalOcean Spaces buckets assigned to that tenant
- Included storage resets are not applicable — storage is cumulative, not a monthly consumption allowance
- If a tenant's usage approaches their included allocation, an in-app alert is triggered at 80% and 100% of the included limit
- If a tenant exceeds their included storage, they must either purchase a storage add-on or delete files before uploading new ones
- If a tenant downgrades to a lower tier, their storage usage must be within the lower tier's maximum storage limit before the downgrade is permitted

## 4.3 Storage Add-Ons

Storage add-on pricing is documented in **Section 11.1 (Storage Add-Ons)**.

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

## 9.3 Stripe Connect Fees and Tenant Payment Processing

**Applies to:** All tiers — Lite, Plus, and Pro

> **Decision Status: LOCKED** — These decisions are final and apply to all tier specifications.

### The "Double Dip" Structure

When a tenant processes a customer payment through Stripe Connect, **Stripe charges fees at two levels:**

**Level 1: Standard Payment Processing Fees (Paid by Tenant)**
- **2.9% + $0.30** per successful card charge
- This is Stripe's standard payment processing rate
- Tenant's customer pays → Stripe deducts 2.9% + $0.30 → remainder goes to tenant's Stripe balance

**Level 2: Stripe Connect Platform Fees (Paid by ServizmaDesk)**
- **$2.00 per month** per "active account" (any tenant who receives a payout that month)
- **$0.25 + 0.25%** per payout sent from Stripe to tenant's bank account
- These are the fees Stripe charges **ServizmaDesk** for providing the Connect infrastructure

**Example: $10,000 tenant transaction**
- Customer pays $10,000
- Stripe deducts $290 + $0.30 = $290.30 (from tenant)
- Tenant receives $9,709.70 in Stripe balance
- Tenant requests payout to bank
- Stripe charges ServizmaDesk: $2 (monthly active fee) + $0.25 + $24.27 (0.25% of $9,709.70) = **$26.52**
- **Total to Stripe: $316.82** (2.9% from tenant + platform fees from ServizmaDesk)

### Industry Standard: Application Fees

Most FSM SaaS platforms (Jobber, HousecallPro, FieldPulse) charge tenants an **"application fee"** of 1-2% on top of the standard Stripe processing fees to cover Connect costs and generate profit. ServizmaDesk applies the same model across all tiers, consistent with industry practice, at a rate significantly below competitors.

**Example of Competitor Approach:**
- Tenant processes $10,000 payment
- Stripe deducts: $290.30 (2.9% + $0.30)
- **Platform charges application fee:** 1.5% = $150
- Tenant receives: $9,709.70 - $150 = $9,559.70
- Platform keeps: $150 application fee
- Platform pays Stripe Connect fees: ~$27
- **Platform profit: $123** (82% margin on payment processing)

### ✅ Locked Decision: ServizmaDesk Application Fee — 0.5%

**Application fee: 0.5%** on all tenant payment transactions, applied to all tiers (Lite, Plus, and Pro).

**Rationale:**
1. **Consistent with industry practice** — all major competitors charge application fees across all tiers
2. **Covers Stripe Connect costs** (~0.3%) with a small margin (~0.2%)
3. **Dramatically cheaper than competitors** (0.5% vs. 1.5–2%)
4. **Honest, defensible marketing claim** — "Industry's lowest payment processing fees"
5. **Universal application** — applying at all tiers keeps the model simple and consistent

**Example: $10,000 tenant transaction with ServizmaDesk**
- Customer pays $10,000
- Stripe deducts: $290.30 (2.9% + $0.30) — paid by tenant
- ServizmaDesk application fee: $50.00 (0.5%) — paid by tenant
- Tenant receives: $9,659.70
- ServizmaDesk pays Stripe Connect fees: ~$26.52
- **ServizmaDesk net: ~$23.48**

**Marketing Comparison:**

| Provider | Processing Fee | Platform Markup | Total Cost on $10K |
|----------|---------------|----------------|-------------------|
| **Competitor Typical** | 2.9% + $0.30 | 1.5% | $440.30 |
| **ServizmaDesk** | 2.9% + $0.30 | 0.5% | $340.30 |
| **Savings with ServizmaDesk** | — | — | **$100** |

**Implementation:**
- Application fee: 0.5% charged via Stripe Connect application fee mechanism
- Disclosed in tenant onboarding and tenant agreement
- Itemized on payout statements: "Stripe Processing: $290.30 | ServizmaDesk Platform Fee: $50.00"

### ✅ Locked Decision: Annual High-Volume Loyalty Reward (Volume Rebate)

**Eligibility:** Annual billing accounts only (monthly billing accounts do not qualify).

**Threshold:** Process >$100,000 in cumulative volume within a single annual billing cycle.

**Reward:** A subscription credit representing **0.1%** of their total processed volume for that year (effectively a 20% rebate on the 0.5% application fee they paid). ServizmaDesk retains the remaining 0.4%. 

**Cap:** The reward is capped at **50% of the total cost of their annual subscription.** It cannot exceed this amount, nor can it result in a cash payout.

**Example Scenario:**
- User is on the Plus tier ($588/year).
- During the year, they process $450,000 through Stripe Connect.
- 0.1% reward calculation: $450.
- Maximum allowable cap (50% of $588): $294.
- **Credit Applied:** $294 applied toward their upcoming annual renewal invoice.

**Implementation Requirements:**
- Celery background worker tracks cumulative payment volume per tenant per annual billing cycle.
- At billing anniversary date, worker evaluates whether threshold was met.
- If volume > $100K: Stripe subscription credit is calculated (Total Volume * 0.001) and capped at (Annual Subscription Price * 0.5).
- Credit is applied before next charge — the tenant's renewal is automatically discounted.
- Tenant is notified via in-app notification and email detailing the volume processed, the rebate earned, and the actual renewal cost.

### Documentation in Tenant Agreements

Tenant agreements must disclose:
1. Stripe's standard processing fees (2.9% + $0.30)
2. ServizmaDesk's application fee (0.5%)
3. Total effective rate per transaction (approximately 3.4% + $0.30)
4. Payout schedule and fee structure
5. Stripe Connect required for all payment processing — no alternative processors
6. Annual High-Volume Loyalty Reward eligibility, threshold, and reward terms

---

# 10. SMS Pricing

## 10.1 SMS Point System Overview

- **1 point = 1 outbound SMS message segment**
- Each tier receives a monthly point allotment included in the base subscription
- Points are allocated **per tenant per month** — the pool is not multiplied by seat count
- Tenants who exhaust their included allocation are charged a flat per-point overage rate for the remainder of the billing period
- This ensures tenants never lose SMS functionality mid-month regardless of usage volume

## 10.2 Included Point Allotments by Tier

| Tier | Included Points/Month | SMS Mode | Notes |
|---|---|---|---|
| **Lite** | 100 | Manual only | No automated triggers; tenant-initiated messages only |
| **Plus** | 350 | Manual and automated | Includes automation-triggered messages (reminders, follow-ups, etc.) |
| **Pro** | 750 | Manual and automated | Includes automation-triggered messages (reminders, follow-ups, etc.) |
| **Enterprise** | TBD | Manual and automated | To be defined in Enterprise specification — minimum parity with Pro (750 points) expected |

**Lite SMS Scope Note:** Lite tier SMS is restricted to manually initiated outbound messages only. Automated triggers (appointment reminders, on-my-way notifications, post-job follow-ups, payment reminders, etc.) are a Plus and Pro feature. This restriction is enforced at the platform level.

## 10.3 Overage Pricing

Once a tenant's monthly point allotment is exhausted, additional outbound messages are charged at a flat overage rate:

- **Overage rate: $0.035 per point (per message segment)**
- Overage applies to all tiers equally (Lite, Plus, Pro)
- Overage charges are metered in real time and billed at the end of the monthly billing period as a separate Stripe charge
- There is no cap on overage — tenants may send as many messages as needed beyond their included allocation
- Tenants are notified via in-app alert and email when they reach 80% and 100% of their included allocation

## 10.4 Point Reset Policy

- Included points reset on the tenant's **monthly billing anniversary date**
- Unused points **do not roll over** to the next billing period
- Overage charges from the prior period are invoiced at reset

## 10.5 Point Pool Rules

- The monthly point pool is a **single per-tenant allocation**, not per-seat
- A Plus tenant with 5 seats receives 350 points/month total — not 1,750
- All seats within the tenant account draw from the same shared pool
- Admins can monitor pool consumption in the tenant billing dashboard

## 10.6 Billing Implementation Notes

- Twilio A2P 10DLC is the underlying SMS provider
- ServizmaDesk registers as the ISV brand; each tenant is registered as a campaign under the ServizmaDesk A2P umbrella
- A2P campaign registration fees (~$1.50–$10/month per active SMS tenant) are a platform operating cost absorbed by ServizmaDesk — not passed through to tenants
- Per-message Twilio cost (base rate + carrier passthrough fees) is approximately $0.012/message — the overage rate of $0.035 provides approximately 65% gross margin on overage consumption
- Messages that terminate in a "Failed" status do not consume a point

## 10.7 International SMS

- International SMS pricing is to be defined
- International messages may consume multiple points per message depending on destination country and carrier
- International overage rate structure to be confirmed when international SMS scope is defined

## 10.8 Future: SMS Point Packages

Once usage patterns are established post-launch, ServizmaDesk intends to offer optional SMS point packages as flat-fee monthly add-ons. Point packages allow tenants who consistently exceed their included allocation to replace variable overage billing with predictable flat-fee billing.

**Design intent:**
- Packages will be offered in fixed point tiers (e.g., +500 points, +1,000 points, +2,500 points)
- Package pricing will be set below the equivalent overage cost to reward commitment
- Packages replace overage for the points they cover — any usage beyond the package ceiling reverts to per-point overage rate
- SMS point packages will be priced significantly higher than email point packages (when offered) to reflect the ~12x higher underlying Twilio cost per message vs. Postmark email cost

**Trigger for launch:** Packages will be designed and priced after sufficient post-launch data confirms typical tenant usage patterns. No packages will be offered at initial launch — overage-only model applies until patterns are validated.

**Spec reference:** When SMS point packages are designed, pricing will be added to this section and the Open Pricing Decisions section updated accordingly.

---

# 10A. Email Pricing

## 10A.1 Email Point System Overview

Email uses a separate point system from SMS. The two systems are independent — email points and SMS points are distinct pools with separate allocations, overages, and billing line items. Tenants see a separate bar graph for each.

- **1 point = 1 outbound email**
- Each tier receives a monthly email point allotment included in the base subscription
- Points are allocated **per tenant per month** — the pool is not multiplied by seat count
- Tenants who exhaust their included allocation are charged a flat per-point overage rate for the remainder of the billing period
- Failed email deliveries (bounced, rejected) do not consume a point — confirmed by Postmark delivery webhook
- Tenants are notified via in-app alert when they reach 80% and 100% of their monthly allocation

**Email is not SMS.** Email costs approximately $0.001/email at platform scale via Postmark — roughly 12x cheaper than SMS ($0.012/message via Twilio). Overage rates and point package pricing (when introduced) will reflect this cost difference. The two systems share the same UX model but are priced independently.

## 10A.2 Email Provider and Cost Basis

**Provider:** Postmark (transactional email delivery)

ServizmaDesk maintains a single Postmark account. All tenant emails across all tiers flow through this account. Postmark has no concept of individual tenants — ServizmaDesk meters per-tenant usage internally via application-level counters, resetting at each tenant's billing anniversary.

**Platform cost basis:**
- Postmark base plan: $15/month for 10,000 emails
- At mid-scale volume across all tenants: approximately **$1.00 per 1,000 emails ($0.001/email)**
- Overage rate of $0.005/point provides approximately **80% gross margin** on overage consumption
- A2P compliance costs for email are minimal compared to SMS — no carrier registration fees

**Sending modes:**
- **Platform-managed (default):** ServizmaDesk sends from its own domain (`notifications@mail.servizmadesk.com`). Tenant's company name appears as the display sender name. Available on all tiers. No additional cost.
- **Custom domain (paid add-on):** Tenant authenticates their own domain via DNS records (SPF, DKIM, DMARC). Emails send from the tenant's domain through Postmark's infrastructure. Available on Plus and above. See Section 11.4.
- **BYOS (Bring Your Own SMTP):** Not supported. ServizmaDesk does not allow tenants to route platform email through their own SMTP credentials. This decision was made to maintain delivery visibility, metering accuracy, and consistent tenant experience. Competitors (Jobber, HousecallPro, FieldPulse, Workiz) do not offer BYOS either.

## 10A.3 Competitive Baseline — What Email Must Do

ServizmaDesk's platform-managed email must match the following competitor baseline at all relevant tiers:

- Send quotes to customers by email from within the platform
- Send invoices to customers by email from within the platform
- Send automated notifications (booking confirmations, appointment reminders, on-my-way, job completion, payment receipts) — Plus and above
- Configurable reply-to address per email type (e.g., quotes reply to estimator, invoices reply to billing contact)
- Outbound communications log with delivery status and open tracking per tenant
- Branded with tenant company name as display sender

No competitor captures inbound email replies back into their platform. ServizmaDesk's inbound reply processing (Phase 1 add-on) is above-market functionality.

## 10A.4 Included Email Point Allotments by Tier

| Tier | Included Points/Month | Email Mode | Notes |
|---|---|---|---|
| **Lite** | 400 | Manual only | Quote and invoice sending; no automated triggers |
| **Plus** | 1,600 | Manual and automated | Full automated notification suite included |
| **Pro** | 4,000 | Manual and automated | Full automated notification suite included |
| **Enterprise** | 12,000 | Manual and automated | Full automated notification suite included |

**Allocation rationale:** Base allocations are intentionally set at approximately 80% of expected typical usage for an active tenant at each tier. This keeps included allocations lean, drives predictable overage revenue, and creates natural conversion targets for point packages when introduced.

**Lite email scope:** Lite is restricted to manually initiated outbound emails (quote sends, invoice sends, manual customer messages). Automated triggers (appointment reminders, on-my-way notifications, post-job follow-ups, payment reminders) are a Plus and above feature, consistent with SMS mode restrictions on Lite.

## 10A.5 Overage Pricing

- **Overage rate: $0.005 per point (per email)**
- Overage applies to all tiers equally
- Overage charges are metered in real time and billed at the end of the monthly billing period as a separate Stripe charge
- There is no cap on overage — tenants may send as many emails as needed beyond their included allocation

**Margin note:** At $0.001 platform cost per email, the $0.005 overage rate provides approximately 80% gross margin on overage consumption. This is intentionally lower than the SMS overage margin (65%) in absolute dollar terms, reflecting the lower underlying cost — tenants are not penalised for email volume the way they would be for SMS.

## 10A.6 Point Reset Policy

- Included points reset on the tenant's **monthly billing anniversary date**
- Unused points **do not roll over** to the next billing period
- Overage charges from the prior period are invoiced at reset
- Email and SMS points reset independently on the same billing anniversary date

## 10A.7 Point Pool Rules

- The monthly email point pool is a **single per-tenant allocation**, not per-seat
- A Plus tenant with 5 seats receives 1,600 email points/month total — not 8,000
- All seats within the tenant account draw from the same shared pool
- Admins can monitor email and SMS pool consumption separately in the tenant billing dashboard

## 10A.8 Future: Email Point Packages

Once usage patterns are established post-launch, ServizmaDesk intends to offer optional email point packages as flat-fee monthly add-ons — mirroring the SMS point package roadmap.

**Design intent:**
- Packages will be offered in fixed point tiers
- Package pricing will be set below the equivalent overage cost to reward commitment
- Email point packages will be priced significantly lower than SMS point packages, reflecting the ~12x lower underlying Postmark cost vs. Twilio SMS cost
- Both email and SMS packages may be offered as a bundled "Communication Package" combining points from both pools at a combined rate

**Trigger for launch:** Same as SMS — packages will be designed after sufficient post-launch data confirms typical usage patterns. Overage-only model applies at initial launch.

## 10A.9 Custom Domain Email Add-On

Custom domain email sending and inbound reply processing are available as a paid add-on. See **Section 11.4** for pricing and scope.

---

Add-on modules are confirmed, finalized pricing decisions. They are billed as separate Stripe subscription line items, independent of the base plan subscription. Add-ons are not per-seat unless otherwise noted.

## 11.1 Storage Add-Ons

Storage add-ons expand a tenant's included storage allocation beyond what is provided in their base tier (see Section 4.2). Add-ons are priced on a value basis, not a cost basis — DigitalOcean Spaces storage is inexpensive infrastructure; the add-on price reflects the convenience, platform management, and CDN delivery included.

### Storage Provider Cost Basis

**Provider:** DigitalOcean Spaces (S3-compatible object storage with built-in CDN)
- Platform base subscription: $5.00/month (covers 250 GiB across all tenant buckets — a fixed platform operating cost, not per-tenant)
- Additional storage: **$0.02/GiB/month** beyond the 250 GiB base
- Outbound bandwidth: 1,024 GiB/month included; $0.01/GiB beyond that

All storage add-on pricing is set well above the $0.02/GiB DO cost, resulting in high gross margins across all tiers. Margins below reflect the incremental DO storage cost only — bandwidth and platform overhead are absorbed into the base platform operating budget.

### Lite Tier Storage Add-Ons

Base included: 3 GB. Maximum storage allowed: 10 GB.

| Add-On | Storage Added | Total Storage | DO Cost/Month | Monthly Charge | Gross Margin |
|---|---|---|---|---|---|
| Tier 1 | +3 GB | 6 GB | ~$0.06 | $10 | ~99.4% |
| Tier 2 | +4 GB | 10 GB (max) | ~$0.08 | $15 | ~99.5% |

*Lite tenants requiring more than 10 GB must upgrade to Plus.*

### Plus Tier Storage Add-Ons

Base included: 10 GB. Maximum storage allowed: 75 GB.

| Add-On | Storage Added | Total Storage | DO Cost/Month | Monthly Charge | Gross Margin |
|---|---|---|---|---|---|
| Tier 1 | +15 GB | 25 GB | ~$0.30 | $25 | ~98.8% |
| Tier 2 | +25 GB | 50 GB | ~$0.50 | $45 | ~98.9% |
| Tier 3 | +25 GB | 75 GB (max) | ~$0.50 | $60 | ~99.2% |

*Plus tenants requiring more than 75 GB must upgrade to Pro.*

### Pro Tier Storage Add-Ons

Base included: 25 GB. Maximum storage allowed: 500 GB.

| Add-On | Storage Added | Total Storage | DO Cost/Month | Monthly Charge | Gross Margin |
|---|---|---|---|---|---|
| Tier 1 | +25 GB | 50 GB | ~$0.50 | $40 | ~98.75% |
| Tier 2 | +25 GB | 75 GB | ~$0.50 | $55 | ~99.1% |
| Tier 3 | +25 GB | 100 GB | ~$0.50 | $100 | ~99.5% |
| Tier 4 | +400 GB | 500 GB (max) | ~$8.00 | $200 | ~96% |

**Pro storage design note:** The gap between Tier 3 (100 GB) and Tier 4 (500 GB) is intentional. A Pro tenant requiring more than 100 GB but less than 500 GB is exhibiting storage behavior that has likely outgrown the Pro tier. The gap serves as a natural nudge toward either upgrading to Enterprise or auditing and removing unnecessary files. There is no intermediate step between 100 GB and 500 GB by design.

*Pro tenants requiring more than 500 GB must upgrade to Enterprise.*

### Enterprise Tier Storage Add-Ons

Base included: 50 GB. Maximum storage allowed: 1,500 GB.

| Add-On | Storage Added | Total Storage | DO Cost/Month | Monthly Charge | Gross Margin |
|---|---|---|---|---|---|
| Tier 1 | +50 GB | 100 GB | ~$1.00 | $75 | ~98.7% |
| Tier 2 | +250 GB | 350 GB | ~$5.00 | $175 | ~97.1% |
| Tier 3 | +500 GB | 750 GB | ~$10.00 | $300 | ~96.7% |
| Tier 4 | +750 GB | 1,500 GB (max) | ~$15.00 | $450 | ~96.7% |

*Enterprise tenants requiring more than 1,500 GB should contact ServizmaDesk for custom storage pricing.*

### Storage Add-On Billing Rules

- Billed as a separate Stripe subscription line item per tenant
- Add-ons are not per-seat — one storage add-on applies to the entire tenant account
- Changes take effect immediately; proration applies for mid-cycle changes
- Only one storage add-on may be active at a time per tenant — selecting a higher tier replaces the current one
- If a tenant downgrades their base plan, any active storage add-on that would cause total storage to exceed the new tier's maximum is automatically cancelled; the tenant must reduce their storage usage before the downgrade is permitted
- In-app alerts are triggered at 80% and 100% of the tenant's current total storage allocation

## 11.2 Fleet Maintenance Add-On

| Detail | Value |
|---|---|
| **Price** | $15/vehicle/month |
| **Available To** | Plus, Pro, Enterprise |
| **Billing Model** | Per vehicle, per month |

**Fleet Maintenance includes:** Vehicle records, maintenance scheduling, service interval tracking, mileage logs, and maintenance history per vehicle.

**Fleet Maintenance notes:**
- Available to Plus tier and above
- Billed per vehicle — tenants are charged for each active vehicle record in their account
- Add-on is cancelled independently of base plan — cancelling Fleet Maintenance does not cancel the base subscription
- Data retention on cancellation: Vehicle, Maintenance, and Mileage Log records enter the standard 60-day grace period before deletion
- If tenant downgrades to Lite, Fleet Maintenance add-on is automatically cancelled
- Proration applies for mid-cycle vehicle additions or removals
- Minimum vehicle count: TBD — to be confirmed before feature build

## 11.3 GPS Tracking — Future Consideration

GPS Tracking is not part of the current ServizmaDesk add-on roadmap. There are no current plans to build or offer a GPS Tracking module.

If GPS Tracking is pursued in a future phase, the intended approach is a full platform partnership (Option A) — reselling or white-labeling an established GPS telematics provider (e.g., Samsara, Motive, or Azuga) via an ISV arrangement, with ServizmaDesk surfacing location data natively within the platform. This is a hardware-dependent feature that requires significant commercial and integration investment and is not appropriate for the current product stage.

A GPS Tracking feasibility and strategy brief has been prepared as a separate document: **ServizmaDesk GPS Tracking Strategy & Feasibility Brief**. All market research, cost analysis, pricing considerations, and open decisions related to GPS Tracking are maintained there.

## 11.4 Custom Domain Email Add-On

The Custom Domain Email add-on enables tenants to send platform emails from their own business domain and receive customer email replies back into ServizmaDesk. This is a Phase 1 premium feature — no competitor offers equivalent functionality at any price point.

| Detail | Pro | Enterprise |
|---|---|---|
| **Price** | $20/month per tenant | $40/month per tenant |
| **Available To** | Pro, Enterprise | Enterprise |
| **Billing Model** | Flat per-tenant/month | Flat per-tenant/month |

**Phase 1 includes:**

- **Custom domain outbound:** Tenant provides their domain (e.g., `acmehvac.com`). ServizmaDesk generates the required SPF, DKIM, and DMARC DNS records and displays them with setup instructions. Once the tenant adds the records and domain verification is confirmed via Postmark, all platform-managed emails for that tenant send from their domain (e.g., `From: quotes@acmehvac.com`) through Postmark's infrastructure
- **Inbound reply processing:** ServizmaDesk embeds a unique reply address token in the `Reply-To` header of every outbound email. When a customer replies, Postmark receives the reply and fires a webhook to ServizmaDesk. The inbound handler identifies the tenant and the originating record (Quote, Invoice, Work Order, Customer) from the token and attaches the reply as a communication thread entry visible to all authorised team members

**Phase 1 scope limitations:**
- One domain per tenant
- Inbound replies attach to existing records only — new inbound emails from unrecognised senders are not supported in Phase 1
- Two pre-configured inbound addresses: `quotes@[tenant-domain]` and `invoices@[tenant-domain]`

**Phase 2 (future, separate pricing):** Full email routing system — multiple configurable inbound addresses mapped to system actions (create Lead, create Work Order request, attach to customer record). Priced comparably to Workiz's communication suite add-on (~$100/month). See **ServizmaDesk Email Specification V1** for full Phase 2 scope.

**Custom Domain Email add-on billing rules:**
- Billed as a separate flat Stripe subscription line item per tenant
- Cancelled independently of base plan
- If tenant downgrades below Pro, add-on is automatically cancelled
- Domain DNS records remain the tenant's responsibility — ServizmaDesk provides setup instructions but does not manage the tenant's DNS

---

# 12. Open Pricing Decisions

The following pricing elements are identified but not yet finalized:

## 12.1 To Be Defined in Enterprise Specification
- Enterprise monthly billing confirmed at $216/month; annual confirmed at $179/month
- Enterprise tier seat structure (flat rate vs. per-seat — currently per-seat, to be validated)
- Enterprise SMS point allotment (minimum parity with Pro at 750 points expected)
- Offline mobile app pricing (if offered as paid add-on)
- Enterprise storage add-on structure (currently included in contract — details TBD)
- Dedicated onboarding and support model definition

## 12.2 To Be Defined in Financial Planning
- Annual billing discount percentage validation (currently ~17% across all tiers)
- Fleet Maintenance minimum vehicle count (to be confirmed before feature build)
- SMS point packages — tier structure and pricing (post-launch, after usage patterns confirmed)
- Email point packages — tier structure and pricing (post-launch, after usage patterns confirmed)
- Bundled Communication Package (combined SMS + email points) — evaluate after individual packages are established
- Multi-year prepay discount structure (if offered)
- Non-profit/educational discount structure (if offered)
- Referral credit program (if implemented)
- Enterprise SMS point allotment (minimum parity with Pro at 750 points — confirm in Enterprise specification)

---

# 13. Document Relationships

## 13.1 This Document Supersedes

All pricing and billing sections in the following documents are superseded by this specification:

- **ServizmaDesk Product Tier Map V1 and V2** — Section 3 (Pricing and Billing), Section 4 (Free Trial Structure), Section 5 (Founding Partner Program)
- **ServizmaDesk Platform (SDP) Specification V1 and V2** — Section 5.2 (Plan Limits Table), Section 5.3 (Billing Cycles), Section 6.3 (Billing Model), Section 6.4 (Seat Billing), Section 6.5 (Storage Add-On Billing)
- **ServizmaDesk SaaS Operational Plan V2** — Section 2 (Product Tier Structure), Section 3 (Founding Partner Program)
- **ServizmaDesk SaaS Operational Plan V3** — any pricing sections
- **ServizmaDesk Top-Down Specifications V3** — Section 16 Pricing rows in the Tier Feature Mapping table

## 13.2 This Document Depends On

- **ServizmaDesk Product Tier Map V2** — for feature definitions by tier
- **ServizmaDesk Platform (SDP) Specification V2** — for Stripe technical implementation, provisioning flows, and billing automation
- **ServizmaDesk Top-Down Specifications V3** — for entity definitions and module scope

## 13.3 Documents That Reference This Specification

- **ServizmaDesk Product Tier Map V2** — references this document for all pricing details
- **ServizmaDesk Platform (SDP) Specification V2** — references this document for billing rules and pricing structure
- **ServizmaDesk Lite MVP V4 Specification** — references this document for Lite pricing and trial structure
- **ServizmaDesk Top-Down Specifications V3** — references this document for all pricing; contains no pricing data of its own
- **ServizmaDesk Email Specification V1** — Section 11.4 of this document defines Custom Domain Email add-on pricing referenced in the Email Spec
- **ServizmaDesk GPS Tracking Strategy & Feasibility Brief V1** — references this document for GPS future consideration note
- **ServizmaDesk Plus Specification (future)** — references this document for Plus pricing and SMS/email point pricing
- **ServizmaDesk Pro Specification (future)** — references this document for Pro pricing
- **ServizmaDesk Enterprise Specification (future)** — references this document for Enterprise pricing

---

# 14. Competitive Positioning Summary

## 14.1 Why ServizmaDesk Pricing Works

**Lite at $29/month (annual):**
- 63% cheaper than HousecallPro Basic ($79)
- 26% cheaper than Jobber Core ($39)
- Signals quality without feeling cheap
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

**Enterprise at $179/month (annual):**
- Dramatically cheaper than ServiceTitan ($200–$500/technician/month)
- No implementation fees vs. ServiceTitan's $5K–$50K+ upfront cost
- No multi-year lock-in — ServizmaDesk publishes pricing and lets tenants cancel
- Delivers multi-location, full ERP accounting, route optimization, bank feed integration — features ServiceTitan charges enterprise rates for
- Transparent, self-serve pricing — no sales call required to find out what it costs

## 14.2 The Pricing Ladder Psychology

**Lite ($29):** "I can try this without breaking the bank."
**Plus ($49):** "The automation and scheduling will save me more than $49/month in time."
**Pro ($98):** "I'm scaling my business and need real tools, but I'm not paying ServiceTitan prices."
**Enterprise ($179):** "I need multi-location and full ERP — and I'm still paying a fraction of what ServiceTitan costs."

Each tier jump must feel **justified by the value unlocked**, not just a price increase.

---

# 15. Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 Draft | March 2026 | ServizmaDesk | Initial draft incorporating competitive analysis, Founding Partner tier structure, and strategic pricing decisions |
| 2.0 | March 2026 | ServizmaDesk | Renamed to V2. Added Fleet Management add-on pricing section. Renamed Asset → Asset in positioning language. Removed ISBMG references. Updated all document cross-references to current versions. Added Top-Down Spec to supersedes and referencing documents lists. |
| 2.1 | March 2026 | ServizmaDesk | Finalized SMS pricing structure. Added Lite SMS (100 points/month, manual only). Updated Plus to 350 points/month, Pro to 750 points/month. Replaced add-on package model with flat $0.035/point overage rate. Established per-tenant (not per-seat) pool rule. Added billing implementation notes including Twilio cost basis and A2P 10DLC details. Removed SMS from Open Pricing Decisions. |
| 2.2 | March 2026 | ServizmaDesk | Replaced single Fleet Management add-on with two independent modules: Fleet Maintenance ($15/vehicle/month, Plus+) and GPS Tracking ($30/vehicle/month, Pro+). Added Fleet Bundle ($35/vehicle/month, Pro+, 22% discount). Changed billing model from flat per-tenant to per-vehicle. Updated Open Pricing Decisions to reflect fleet pricing as resolved; added minimum vehicle count as TBD item. |
| 2.3 | March 2026 | ServizmaDesk | Removed GPS Tracking add-on and Fleet Bundle. GPS Tracking deferred to future consideration — no current plans. Fleet Maintenance ($15/vehicle/month, Plus+) confirmed as the sole fleet add-on. Added GPS future consideration note with reference to GPS Tracking Strategy & Feasibility Brief. |
| 2.4 | March 2026 | ServizmaDesk | Fixed Section 2.3: cleaned Lite price from range to confirmed $29/month annual; set Enterprise to $155/month; corrected Lite→Plus upgrade gap math. Fixed Section 3.1: removed stale $24 reference from Pricing Note; updated Enterprise from $145 to $155; removed storage columns (now in Section 4); added pointer to Sections 4 and 11. Rewrote Section 4 as storage-only section covering DigitalOcean Spaces as provider, DO cost basis, included storage per tier, and allocation rules. Added Storage Add-On pricing to Section 11. |
| 2.5 | March 2026 | ServizmaDesk | Structural correction: moved confirmed add-ons (Storage, Fleet Maintenance, GPS future note) out of Open Pricing Decisions into new dedicated Section 11 (Add-On Module Pricing). Open Pricing Decisions renumbered to Section 12. Fixed stale $145 Enterprise reference in former Section 11.4 (now Section 12.3). Renumbered Document Relationships to Section 13, Competitive Positioning to Section 14, Version History to Section 15. |
| 2.6 | March 2026 | ServizmaDesk | Rewrote Section 11.1 Storage Add-Ons with corrected tier structure, per-tier cost analysis tables, DO cost basis ($0.02/GiB), and gross margin documentation. Corrected Lite add-on increments (+3 GB/$10, +4 GB/$15). Corrected Plus add-on increments (+15 GB/$25, +25 GB/$45, +25 GB/$60). Updated Pro to 500 GB maximum with four tiers; documented intentional gap between 100 GB and 500 GB as strategic upgrade nudge. Added Enterprise storage add-ons (50 GB base, four tiers to 1,500 GB max; over 1,500 GB requires contact). Updated Section 4.2 to reflect corrected Enterprise base (50 GB) and maximums (Pro 500 GB, Enterprise 1,500 GB). |
| 2.7 | March 2026 | ServizmaDesk | Finalized Enterprise pricing: $216/month (monthly billing), $179/month (annual billing) — maintains consistent ~17% annual discount across all tiers. Updated Section 2.3, 3.1 Pricing Note, Section 12.3, and Competitive Positioning (Section 14) to reflect confirmed Enterprise pricing. Added Enterprise to pricing ladder psychology. Added Enterprise competitive context note vs. ServiceTitan ($200–$500/technician/month + $5K–$50K implementation). Removed "TBD" from Enterprise monthly price in tier table. |
| 2.8 | March 2026 | ServizmaDesk | Added Section 10A Email Pricing — point system, Postmark cost basis ($0.001/email), included allocations (Lite 400, Plus 1,600, Pro 4,000, Enterprise 12,000), overage rate ($0.005/point, ~80% gross margin), BYOS decision (not supported), competitive baseline, future email point packages note. Updated Section 10.1 SMS overview to remove stale no-packages language. Added Section 10.8 future SMS point packages note including SMS/email cost differential warning for future package pricing. Added Section 11.4 Custom Domain Email Add-On ($20/month Pro, $40/month Enterprise) covering Phase 1 scope (custom domain outbound + inbound reply processing) and Phase 2 future routing system reference. Updated Section 12.1 and 12.4 with email-related open items including point packages and bundled communication package consideration. |
| 2.9 | March 2026 | ServizmaDesk | Cleaned Section 12.1: removed obsolete "system email daily limits" item (resolved by point system design), removed "Maintenance Agreements pricing if unbundled" item (not applicable — Maintenance Plans are a core Plus feature, not an add-on candidate), moved "Custom Domain Email for Plus" to Email Specification V1 Section 8 open decisions as its authoritative home. |
| 2.10 | March 2026 | ServizmaDesk | Removed Section 12.1 (Plus Specification items) entirely — remaining item (Maintenance Agreement billing model) is a feature scope question already answered in Top-Down Specifications V1 (recurring billing is Pro/Enterprise only). Renumbered Sections 12.2–12.4 to 12.1–12.3. |
| 2.11 | March 2026 | ServizmaDesk | Removed Section 12.1 (Pro Specification items) entirely. REST API rate limits: no DO cost for API calls, rate limiting is an engineering concern not a pricing decision. Advanced reporting add-on: reporting not yet scoped, nothing to price. Renumbered 12.2–12.3 to 12.1–12.2. Open Pricing Decisions now contains only Enterprise Specification items and Financial Planning items. |
| 2.11a | March 2026 | ServizmaDesk | Document cleanup pass: updated header status from Draft to Active, version from 2.0 to 2.11. Fixed Section 1 scope list — removed stale "SMS point pricing (future)" label, added email pricing and add-on modules to scope. Fixed three stale Section 11.3 cross-references (storage add-ons are in Section 11.1, not 11.3). Updated Section 13.3 — corrected Lite MVP V3 reference to V4, added Email Specification V1, GPS Brief V1, and Enterprise Specification (future) to referencing documents list. |

---

**END OF DOCUMENT**
