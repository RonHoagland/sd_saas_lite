# ServizmaDesk Pricing Specification — Document Update Guide

**Purpose:** This document shows exactly what sections need to be removed from existing ServizmaDesk specifications and replaced with references to the new **ServizmaDesk Pricing & Billing Specification V1**.

---

# Documents Requiring Updates

1. ServizmaDesk_Product_Tier_Map_V1.md
2. ServizmaDesk_Platform__SDP__Specification_V1.md
3. ServizmaDesk_SaaS_Operational_Plan_V2.md
4. ServizmaDesk_Lite___MVP_V3_Specification.md (Section 18.8 only)

---

# 1. ServizmaDesk_Product_Tier_Map_V1.md

## REMOVE: Section 3 (Pricing and Billing)

**Current content to remove:**
```markdown
# 3. Pricing and Billing

## 3.1 Pricing Table

|                    | Lite   | Plus   | Pro    | Enterprise |
|--------------------|--------|--------|--------|------------|
| Monthly Price/Seat | $28    | $59    | $118   | $TBD       |
| Annual Price/Seat  | $24    | $49    | $98    | $145       |
| Max Seats          | 10     | Unlimited | Unlimited | Unlimited |
| Storage Included   | 3 GB   | 10 GB  | 25 GB  | 25 GB      |
| Storage Upgrades   | Upgrade to 5 GB, 10 GB | Upgrade to 25 GB, 50 GB, 75 GB | Upgrade to 50 GB, 75 GB, Unlimited | Unlimited |
| Max Storage        | 10 GB  | 75 GB  | Unlimited | Unlimited |

## 3.2 Billing Rules

- All plans offer both monthly and annual billing options.
- Annual billing is charged as a lump sum at the annual rate. Monthly billing is charged per seat per month at the monthly rate.
- Customers may switch between monthly and annual billing. Changes take effect at the end of the current billing period.
- Seat-based billing: each active user consumes one seat. Terminated employees release their seat (see Lite V3 Specification, Section 18.8 for seat counting rules).
- Storage add-ons are billed as additional Stripe subscription line items.
- All prices are in USD.
```

## REPLACE WITH:

```markdown
# 3. Pricing and Billing

All pricing, billing cycles, storage add-ons, and Founding Partner program details are defined in the **ServizmaDesk Pricing & Billing Specification V1**.

**Quick Reference — Standard Tier Pricing (Annual Billing):**
- Lite: $29/seat/month (max 10 seats)
- Plus: $49/seat/month (unlimited seats)
- Pro: $98/seat/month (unlimited seats)
- Enterprise: TBD (future tier)

**Quick Reference — Founding Partner Program:**
- Founding Partner Lite: $200/seat/year (10 slots available)
- Founding Partner Plus: $400/seat/year (10 slots available)

For complete pricing details, billing rules, storage pricing, trial structure, and competitive positioning rationale, see:
→ **ServizmaDesk Pricing & Billing Specification V1**
```

---

## REMOVE: Section 4 (Free Trial Structure)

**Current content to remove:**
```markdown
# 4. Free Trial Structure

## 4.1 Trial Terms

- Duration: 14 days from account creation.
- No credit card required at signup.
- Full Lite functionality available during trial.
- Visible countdown timer displayed throughout the application during the trial period.

## 4.2 Trial Expiration Flow

**Days 1–14:** Full access. Countdown timer visible. Friendly reminders about trial end date with clear messaging that data will be preserved only if payment is provided.

**Day 15 (Trial End):** At exactly midnight on Day 15, the account enters read-only mode. The user has high visibility of this approaching deadline: a login warning shows the days remaining, and a countdown is displayed on both the User Dashboard and the Admin Section. Once in read-only mode, the user can log in and view all data but cannot create or edit records. A persistent banner prompts credit card entry, and the user is directed to the billing/account page to select a plan and enter payment.

**Day 45 (30 days after trial end):** Account is flagged for cleanup if no payment has been received. Standard 60-day data retention period begins from this point.

**Day 105 (60 days after cleanup flag):** Tenant data is permanently deleted per the data retention policy.

## 4.3 Trial Conversion

Upon entering a credit card on or after day 15, the first billing cycle begins immediately. The user selects their plan (Lite initially) and billing frequency (monthly or annual). There is no retroactive charge for the trial period.
```

## REPLACE WITH:

```markdown
# 4. Free Trial Structure

ServizmaDesk offers a 14-day free trial with no credit card required. Full trial terms, expiration flow, and conversion process are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 6**.

**Trial Flow Summary:**
- Days 1-14: Full Lite access with countdown timer
- Day 15: Account enters read-only mode (data preserved)
- Day 45: Account flagged for cleanup (60-day grace period begins)
- Day 105: Permanent data deletion

For complete trial structure details, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 6**
```

---

## REMOVE: Section 5 (Founding Partner Program)

**Current content to remove:**
```markdown
# 5. Founding Partner Program

- Limited to the first 10 companies.
- Valid for 24 months from activation date.
- Price: Customer has the option to pay $200 per seat per year, or $17 per seat per month (the monthly option is a fraction higher for convenience).
- No refunds.
- Seats may be added during the 24-month window at the Founding Partner rate.
- Automatic conversion to standard pricing after the 24-month window expires.
- No extensions to the Founding Partner window.
- Implemented via Stripe coupon/discount codes — no custom billing logic required in SDP.

Purpose: Early validation, controlled feedback, and early revenue injection during the initial launch phase.
```

## REPLACE WITH:

```markdown
# 5. Founding Partner Program

ServizmaDesk offers two Founding Partner tiers with exclusive legacy pricing for early adopters:

- **Founding Partner Lite:** $200/seat/year (10 slots available)
- **Founding Partner Plus:** $400/seat/year (10 slots available)

Both programs offer 24-month pricing locks with automatic conversion to standard pricing after expiration.

For complete Founding Partner program details, qualification criteria, conversion rules, and revenue projections, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 5**
```

---

# 2. ServizmaDesk_Platform__SDP__Specification_V1.md

## REMOVE: Section 5.2 (Plan Limits Table)

**Current content to remove:**
```markdown
## 5.2 Plan Limits Table

The following limits apply to ServizmaDesk Lite. Plus, Pro, and Enterprise limits are to be defined in their respective specifications.

| Limit                  | ServizmaDesk Lite     |
|------------------------|------------------|
| Max Seats              | 10               |
| Attachment Storage     | 3GB              |
| Storage Add-Ons        | +5GB, +10GB      |
| Price Per Seat         | $28/month (or $24/month billed annually) |
| Billing Cycles         | Monthly, Annual  |
| API Access             | No               |
| SMS                    | No               |
| Automation             | No               |
| Multi-Location         | No               |
```

## REPLACE WITH:

```markdown
## 5.2 Plan Limits Table

Plan limits (seats, storage, features) are defined in **ServizmaDesk Product Tier Map V1**.

Pricing for all tiers is defined in **ServizmaDesk Pricing & Billing Specification V1**.

**Quick Reference — Lite Limits:**
- Max Seats: 10
- Storage Included: 3 GB (max 10 GB with add-ons)
- Price: $29/seat/month (annual) or $35/seat/month (monthly)

For complete plan limits, see:
→ **ServizmaDesk Product Tier Map V1, Section 6**

For complete pricing details, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 3**
```

---

## REMOVE: Section 5.3 (Billing Cycles)

**Current content to remove:**
```markdown
## 5.3 Billing Cycles

Customers choose between monthly and annual billing at signup. Both options are available for all plans.

**Monthly billing:**
- Billed per seat per month
- ServizmaDesk Lite: $28 per seat per month (or $24 billed annually)
- Billed on the same date each month (anniversary of signup date)

**Annual billing:**
- Billed annually as a lump sum
- Annual pricing to be defined (typically a discount vs monthly rate)
- Billed on the anniversary of the signup date each year

Customers may switch between monthly and annual billing from the Billing section in SDTA. Switching billing cycles takes effect at the end of the current billing period.
```

## REPLACE WITH:

```markdown
## 5.3 Billing Cycles

Customers choose between monthly and annual billing at signup. Billing cycle rules, pricing, and switching behavior are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 3.2**.

**Implementation Note:** SDTA reads billing cycle from SDP tenant record. Stripe manages recurring billing automatically. When customer switches billing cycle in SDTA, SDTA notifies SDP, SDP updates Stripe subscription, and change takes effect at end of current billing period.
```

---

## REMOVE: Section 6.3 (Billing Model)

**Current content to remove:**
```markdown
## 6.3 Billing Model

### Per-Seat Monthly Billing
ServizmaDesk Lite is billed per active seat per month or per year.

- **Price:** $28 per seat per month (or $24 billed annually)
- **Seat count used for billing:** Seat count at the time of billing (Active + On Leave + Inactive employees — Terminated employees do not count)
- **Billing date:** Anniversary of the signup date each month (monthly) or each year (annual)

### Monthly Billing
- Customer is charged for their current seat count on each monthly anniversary
- Stripe Billing manages the recurring charge automatically
- If seats have changed since the last billing date, Stripe applies proration automatically

### Annual Billing
- Customer is charged for their current seat count for a full year on each annual anniversary
- Annual pricing is defined per plan (to be confirmed — typically a discount vs monthly rate)
- If seats change during an annual billing period, Stripe applies proration for the remainder of the annual period

### Switching Billing Cycles
- Customers may switch between monthly and annual billing from the Billing section in SDTA
- Switching takes effect at the end of the current billing period
- Stripe handles the transition and any proration automatically
```

## REPLACE WITH:

```markdown
## 6.3 Billing Model

ServizmaDesk uses per-seat billing for all tiers. Billing model, pricing, seat counting rules, and proration behavior are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 3**.

**SDP Implementation Notes:**
- SDP maintains Stripe Customer ID and Subscription ID per tenant
- When seat count changes in SDTA (employee added/terminated), SDTA notifies SDP, SDP updates Stripe subscription quantity
- Stripe applies proration automatically for mid-cycle seat changes
- SDP never stores raw payment card data (see Section 6.8 for PCI posture)

For complete billing model details, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 3**
```

---

## REMOVE: Section 6.4 (Seat Billing & Charge Calculation)

**Current content to remove:**
```markdown
## 6.4 Seat Billing & Charge Calculation

Seat billing is managed entirely through Stripe Billing subscriptions. SDP updates the Stripe subscription quantity whenever the seat count changes and Stripe handles all proration automatically.

### When Seat Count Changes
| Event                        | SDP Action                              | Stripe Action                          |
|------------------------------|----------------------------------------|----------------------------------------|
| New employee added           | Notifies Stripe of new seat count      | Prorates charge for remainder of period|
| Employee set to Terminated   | Notifies Stripe of reduced seat count  | Applies credit for remainder of period |

### Seat Count at Billing Time
The seat count used for each billing cycle is the count of employees with status Active, On Leave, or Inactive at the time the invoice is generated. Terminated employees are excluded.

### Cost Display in SDTA
The Billing section in SDTA displays:
- Current seat count and cost per seat
- Total monthly or annual subscription cost
- Estimated next charge amount and date
```

## REPLACE WITH:

```markdown
## 6.4 Seat Billing & Charge Calculation

Seat billing rules and seat counting logic are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 3.3**.

**SDP Implementation:**
- SDP receives seat count updates from SDTA when employees are added/terminated
- SDP updates Stripe subscription quantity immediately
- Stripe applies proration automatically
- SDP does not calculate charges — Stripe handles all billing math

**Seat Counting (Implementation Reference):**
- Counted: Active, On Leave, Inactive employees
- Not counted: Terminated employees (with Termination Date populated)

For complete seat billing rules, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 3.3**
```

---

## REMOVE: Section 6.5 (Storage Add-On Billing)

**Current content to remove:**
```markdown
## 6.5 Storage Add-On Billing

Customers may purchase additional storage from the Billing section in SDTA.
```

## REPLACE WITH:

```markdown
## 6.5 Storage Add-On Billing

Storage add-on pricing and limits are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 4**.

**SDP Implementation:**
- Storage add-ons are billed as separate Stripe subscription line items
- When customer purchases storage add-on in SDTA, SDTA notifies SDP, SDP creates new subscription line item in Stripe
- Proration applies for mid-cycle storage changes

For complete storage pricing, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 4**
```

---

# 3. ServizmaDesk_SaaS_Operational_Plan_V2.md

## REMOVE: Section 2 (Product Tier Structure)

**Current content to remove:**
```markdown
# 2. Product Tier Structure

## Lite – $24 per seat
- Max 10 seats
- 3 GB included (max 10 GB)
- Upgrade to 5 GB, 10 GB
- Manual workflow
- No automation
- No SMS
- No system email sending
- Catalog-only inventory
- CSV export only

## Plus – $49 per seat
- Unlimited seats
- Automation
- SMS (points system)
- System email sending (limited)
- 10 GB included (max 75 GB)
- Upgrade to 25 GB, 50 GB, 75 GB

## Pro – $98 per seat
- Built on Plus
- 25 GB included (unlimited upgrades)
- Advanced automation
- Dispatch board
- Inventory movement
- Vendor + PO system
- Advanced reporting
- Multi-location
- API access

## Enterprise – Pricing TBD (Future Tier) 
- This is a future tier and will be developed at a later date.
- Scope TBD - See the *Enterprise Top-Down Design Specification* for the full capabilities and roadmap.
```

## REPLACE WITH:

```markdown
# 2. Product Tier Structure

ServizmaDesk offers four tiers. Feature definitions are in **ServizmaDesk Product Tier Map V1**. Pricing is in **ServizmaDesk Pricing & Billing Specification V1**.

**Tier Summary (Annual Pricing):**
- **Lite:** $29/seat/month — Solo operators and micro-businesses (max 10 seats)
- **Plus:** $49/seat/month — Growth tier with automation, scheduling, SMS (unlimited seats)
- **Pro:** $98/seat/month — Advanced tools for scaling businesses (unlimited seats)
- **Enterprise:** TBD — Future tier for multi-location ERP needs

**Founding Partner Programs:**
- **FP Lite:** $200/seat/year (10 slots)
- **FP Plus:** $400/seat/year (10 slots)

For complete tier feature definitions, see:
→ **ServizmaDesk Product Tier Map V1, Section 6**

For complete pricing and billing details, see:
→ **ServizmaDesk Pricing & Billing Specification V1**
```

---

## REMOVE: Section 3 (Founding Partner Program)

**Current content to remove:**
```markdown
# 3. Founding Partner Program

- Limited to first 10 companies
- Valid 24 months from activation
- $200 per seat annually
- $17 per seat monthly
- No refunds
- Seats can be added during 24-month window
- Automatic conversion to standard pricing after 24 months
- No extensions

Purpose:
- Early validation
- Controlled feedback
- Early revenue injection
```

## REPLACE WITH:

```markdown
# 3. Founding Partner Program

ServizmaDesk offers two Founding Partner tiers:
- **FP Lite:** $200/seat/year (10 slots)
- **FP Plus:** $400/seat/year (10 slots)

For complete Founding Partner program details, qualification criteria, and revenue projections, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 5**
```

---

# 4. ServizmaDesk_Lite___MVP_V3_Specification.md

## MODIFY: Section 18.8 (Employee Seat Limit Enforcement)

**Current content (keep most of it, modify pricing references):**

The section contains detailed seat counting logic which should remain. Only the pricing display references need to be updated.

**Find and replace the following text:**

OLD:
```markdown
The cost of adding a new employee seat is displayed near the Add button.
```

NEW:
```markdown
The cost of adding a new employee seat is displayed near the Add button (current Lite pricing: $29/seat/month annual or $35/seat/month monthly — see ServizmaDesk Pricing & Billing Specification V1 for current rates).
```

---

OLD:
```markdown
When adding a new Employee, the Administrator receives a cost increase warning before confirming.
```

NEW:
```markdown
When adding a new Employee, the Administrator receives a cost increase warning before confirming. The warning displays the current per-seat cost (see ServizmaDesk Pricing & Billing Specification V1, Section 3 for pricing details).
```

---

# Summary of Changes

| Document | Sections to Remove/Modify | Replacement Reference |
|----------|--------------------------|----------------------|
| **Product Tier Map V1** | Section 3 (Pricing and Billing)<br>Section 4 (Free Trial)<br>Section 5 (Founding Partner) | Reference to Pricing & Billing Spec V1 |
| **Platform (SDP) Spec V1** | Section 5.2 (Plan Limits)<br>Section 5.3 (Billing Cycles)<br>Section 6.3 (Billing Model)<br>Section 6.4 (Seat Billing)<br>Section 6.5 (Storage Add-On) | Reference to Pricing & Billing Spec V1 |
| **Operational Plan V2** | Section 2 (Product Tier Structure)<br>Section 3 (Founding Partner) | Reference to Pricing & Billing Spec V1 |
| **Lite MVP V3 Spec** | Section 18.8 pricing references | Add references to Pricing & Billing Spec V1 |

---

**END OF UPDATE GUIDE**
