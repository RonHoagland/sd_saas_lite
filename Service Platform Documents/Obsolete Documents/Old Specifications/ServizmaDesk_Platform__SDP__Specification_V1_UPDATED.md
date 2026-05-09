# ServizmaDesk
# ServizmaDesk Platform (SDP) – V1 Specification

> **Note:** SDP stands for ServizmaDesk Platform. It is the central administrative and operational back-office system for the ServizmaDesk ecosystem. (Working Draft)

> **Document Version:** V1
> **Status:** Working Draft — Outline Only
> **Last Updated:** February 2026
> **Compatibility:** Designed to synchronize with ServizmaDesk Lite MVP V3 Specification and Product Tier Map V1.

---

# 1. Platform Identity

---

## 1.1 Purpose

The ServizmaDesk Platform (SDP) is the central control system for all ServizmaDesk products. It is the authoritative back office that governs every customer account, billing relationship, and security credential across the entire ServizmaDesk product family.

SDP is not a customer-facing product in the traditional sense. It is an internal operations platform used by ServizmaDesk staff, with a limited self-service surface exposed to customers for signup, billing, and account management.

No ServizmaDesk tenant account can exist without SDP creating it first. No charge is made to a customer without SDP initiating it. No Administrator credential is stored anywhere except SDP.

---

## 1.2 Core Roles

SDP serves five distinct roles within the ServizmaDesk business:

**Gatekeeper**
No tenant account exists in any ServizmaDesk application without SDP provisioning it first. SDP generates the Tenant UUID, initializes the account in the target application, and controls whether that account remains active or suspended.

**Single Source of Truth**
SDP holds the authoritative record for every customer account across all ServizmaDesk products — company details, plan status, seat counts, storage limits, and account history. The ServizmaDesk applications read from SDP but do not own this data.

**Billing System**
All customer charges flow through SDP via ServizmaDesk's Stripe account. Subscription billing, seat changes, storage add-ons, proration, and payment failure handling are all managed here.

**Security Authority**
Administrator security credentials — Security PIN and security question answers — are stored exclusively in SDP and are never replicated to any ServizmaDesk application. Account recovery for locked Administrators is initiated and completed through SDP.

**Staff Operations Hub**
ServizmaDesk support and operations staff perform all account management tasks through SDP — account lookup, plan changes, seat adjustments, account unlocks, suspensions, and cancellations.

---

## 1.3 ServizmaDesk Tenant Apps Served

SDP is the platform for all current and future ServizmaDesk products:

| Application       | Status         |
|-------------------|----------------|
| ServizmaDesk Lite      | In development |
| ServizmaDesk Plus      | Planned        |
| ServizmaDesk Pro       | Planned        |
| ServizmaDesk Enterprise| Future — scope not yet defined |

All ServizmaDesk applications share the same SDP instance. Each application reads plan and account status from SDP at runtime.

---

## 1.4 Design Principles

- **Gatekeeper first** — no tenant account is valid in any application without SDP authorization
- **Single billing authority** — all charges originate from SDP, never from the applications themselves
- **Credential isolation** — security credentials never leave SDP, even in transit to application databases
- **Staff-operated** — SDP is built for internal staff efficiency, not public consumption
- **Application-agnostic** — SDP is designed to serve all current and future ServizmaDesk products without structural changes
- **Auditability** — every significant action in SDP is logged for internal review

---

## 1.5 What SDP Is Not

- SDP is not a customer-facing product dashboard
- SDP is not an application feature set — it contains no Work Orders, Invoices, Quotes, Assets, or any field service operational modules
- SDP does not store the day-to-day operational business data of tenants — things like customer records, work history, invoices, and payments live exclusively in the ServizmaDesk applications
- SDP stores only account-level data — who the tenant is, what plan they are on, how many seats they have, their billing history, and their security credentials
- SDP does not handle payments between tenants and their customers — that is managed through the tenant's own Stripe account within the ServizmaDesk application they are using

---

# 2. Architecture & Infrastructure

---

## 2.1 Application Architecture

SDP is a Django application backed by a PostgreSQL database. It shares the same server as the ServizmaDesk Tenant App (SDTA) but maintains a fully separate database. The two applications are independent — neither can write to the other's database.

**Tech Stack:**
- Framework: Django
- Database: PostgreSQL
- Server: Shared with SDTA (separate databases on the same PostgreSQL instance)

SDP runs as two functional surfaces within a single Django application:
- **Customer-facing surface** — self-service signup, billing portal, account management, and Administrator account recovery
- **Staff-facing back office** — ServizmaDesk staff tools for account management, support, and operations

Both surfaces are served by the same Django application and share the same database. Access control determines what each user can see and do.

---

## 2.2 Database Structure

SDP maintains its own PostgreSQL database separate from SDTA. The SDP database is the authoritative store for:

- Customer (tenant) account records
- Plan and subscription status
- Seat counts and storage allocations
- Billing history and Stripe subscription references
- Security verification credentials (PIN, security questions and answers)
- ServizmaDesk staff user accounts
- SDP-side audit log

SDP never writes to the SDTA database. SDTA never writes to the SDP database.

---

## 2.3 Relationship Between SDP and SDTA

To enforce absolute data isolation and prevent cross-contamination, SDP and SDTA maintain completely separate databases with no shared database users or permissions. **Direct database reads are strictly prohibited.**

Instead, all communication between SDP and SDTA occurs via an **Internal REST API**.

> **Decision:** Internal REST API from Day 1. To guarantee security and strict boundary isolation, SDP exposes a private, internal-only API (accessible only over the private server network/localhost). SDTA securely calls this API using an Internal API Key.

**Data flow summary:**

| Direction      | Method              | Purpose                                      |
|----------------|---------------------|----------------------------------------------|
| SDP → SDTA        | Internal REST API   | SDTA requests plan status, seat limits, account state from SDP |
| SDTA → SDP        | Internal REST API   | SDTA notifies SDP of seat changes, storage usage |
| SDP → SDTA        | Internal REST API   | SDP instructs SDTA to provision tenant or update account state |

If a tenant's SDTA instance is ever compromised, the attacker has no SQL access to the SDP database. The maximum exposure is strictly limited to whatever the Internal API allows the SDTA instance to request regarding its own specific Tenant UUID.

---

## 2.4 Security & Access Model

### Customer-Facing Surface
- Customers authenticate using their billing email and a password set during signup
- Customer sessions are managed independently from SDTA sessions — logging into SDP does not log the customer into SDTA
- Customer access is scoped strictly to their own account — no customer can view or affect another customer's data

### Staff-Facing Back Office
- ServizmaDesk staff authenticate using staff credentials managed within SDP
- Staff roles control what actions each staff member can perform (see Section 10)
- Staff access is not customer-scoped — staff can look up and manage any customer account within their role permissions

### Separation of Concerns
- Customer credentials for SDP (billing email + password) are entirely separate from their SDTA login credentials (company email + password)
- Administrator security credentials (PIN, security questions) are stored only in SDP and are never transmitted to or stored in SDTA
- SDP staff credentials are never shared with or accessible from SDTA

---

## 2.5 Governance Rules

1. SDP and SDTA share the same server but maintain fully separate PostgreSQL databases.
2. SDP never writes directly to the SDTA database except through designated provisioning and notification interfaces.
3. SDTA never writes directly to the SDP database except through designated notification interfaces.
4. All inter-application communication uses the Internal REST API. Direct database reads or cross-database queries are strictly prohibited.
5. Customer SDP credentials are separate from customer SDTA credentials.
6. Administrator security credentials are stored only in SDP and never replicated to SDTA.
7. Staff credentials are managed within SDP and are not accessible from SDTA.

---

# 3. Customer-Facing Surface

---

## 3.1 Overview

Customers interact with ServizmaDesk through two touchpoints:

1. **Signup flow** — before the customer has a ServizmaDesk account, hosted by SDP
2. **Billing section within SDTA** — after signup, the customer manages their account and billing from inside their ServizmaDesk application without ever knowing they are talking to SDP behind the scenes

There is no separate customer-facing SDP portal. Once a customer is signed up and provisioned, all their interactions happen inside SDTA. The Billing section in SDTA queries SDP, displays the relevant data, accepts changes, and pushes those changes back to SDP. SDP processes the change and confirms back to SDTA.

The only exceptions are:
- **Signup** — must happen before an SDTA account exists
- **Administrator account recovery** — must happen outside SDTA because the Administrator is locked out

---

## 3.2 Self-Service Signup Flow

The signup flow begins on the ServizmaDesk.com marketing website. Customers learn about ServizmaDesk products, compare plans, and make their purchase decision there. When they are ready to sign up they click a signup or "Get Started" link on the marketing site which hands them off to the SDP-hosted signup flow to complete registration.

The ServizmaDesk.com website itself is outside the scope of this specification. This section covers the SDP-hosted signup flow that begins after the customer clicks through from the marketing site.

### Signup Steps

1. **Plan Selection**
   - Customer selects ServizmaDesk Lite (or other available plan)
   - Monthly or annual billing option is presented with pricing clearly displayed
   - Customer may arrive with a plan pre-selected if the marketing site link specifies one

2. **Business Information**
   - Company legal name
   - Display name
   - Business address
   - Primary contact name
   - Contact email (becomes the billing email and SDP login)
   - Contact phone

3. **Password Setup**
   - The Administrator sets their SDP account password during signup
   - Password rules:
     - Minimum 10 characters
     - Must include at least one uppercase letter
     - Must include at least one lowercase letter
     - Must include at least one number
     - Must include at least one special character (e.g. ! @ # $ % ^ & *)
   - Passwords are never stored in plaintext — hashed using bcrypt or equivalent
   - This password is used to access the Billing section in SDTA — it is separate from the SDTA login password

4. **Payment via Stripe Checkout**
   - Customer is redirected to Stripe Checkout to enter card details
   - **Founding Partner Program:** If the customer holds a Founding Partner invite, they enter their Stripe Promo/Coupon Code here to apply the discounted rate (e.g., $17/seat/month). Stripe automatically handles the recurring discount calculation against the standard plan limits.
   - Card data never touches SDP servers — Stripe returns a Customer ID and Subscription ID to SDP on success
   - On payment failure the customer is returned to the signup flow with an error message
   - SDP stores: Stripe Customer ID, Stripe Subscription ID, last 4 digits, card brand, expiry month/year (all provided safely by Stripe — no raw card data)

5. **Security Verification Setup (required — non-skippable)**
   - Customer selects 4 security questions from the predefined list
   - Customer provides an answer for each question
   - Customer sets a 6-digit numeric Security PIN
   - These credentials are stored in SDP only and are never sent to SDTA

6. **Account Provisioning**
   - SDP generates a Tenant UUID
   - SDP provisions the SDTA account atomically (see Section 4)
   - On provisioning failure the customer is notified and ServizmaDesk support is alerted

7. **Confirmation**
   - Customer receives a welcome email with their SDTA login URL and instructions
   - Customer is redirected to the SDTA login page

> **Decision:** Stripe Billing + Stripe Checkout is used for all payment collection. Card data never touches SDP servers at any point in the signup flow.

---

## 3.3 Billing Section (Within SDTA)

The Billing section in SDTA is the primary place where existing customers manage their account and billing. It is rendered inside SDTA but all data is sourced from and written back to SDP.

### How It Works
1. Customer navigates to the Billing section in SDTA
2. SDTA queries SDP and retrieves the customer's current billing data
3. Customer views their information and makes changes
4. SDTA pushes the changes back to SDP
5. SDP processes the change, updates Stripe where necessary, and confirms back to SDTA

### What Customers Can Do in the Billing Section

**Plan & Subscription:**
- View current plan (ServizmaDesk Lite / Plus / Pro)
- View billing cycle (monthly / annual)
- View next billing date
- View current seat count and cost
- Upgrade or downgrade plan (see Section 5)

**Payment Method:**
- View current card on file (last 4 digits, brand, expiry — no full card number)
- Update payment method — redirected to Stripe Checkout to enter new card details, card data never touches SDP

**Billing History:**
- View past invoices and receipts
- Download individual invoices (Stripe-generated)

**Storage:**
- View current storage usage
- Purchase storage add-ons

**Account:**
- Update company name and contact information
- Update billing email address
- Cancel account (see Section 5.5)

---

## 3.4 Administrator Account Recovery

When an Administrator is locked out of SDTA they cannot log into SDTA to resolve it. Recovery is handled through a standalone SDP-hosted page that is accessible without an SDTA session.

### Recovery Entry Point
- A "Forgot access / Account locked" link on the SDTA login page directs the Administrator to the SDP recovery flow
- The recovery flow is hosted by SDP and requires no prior authentication

### Recovery Process
1. Administrator enters their billing email address to identify the account
2. SDP presents the recovery verification steps (see Section 7 for full detail)
3. On successful verification, SDP unlocks the SDTA Administrator account
4. Administrator is redirected to the SDTA login page with a prompt to reset their password
5. The unlock action is logged in the SDP audit log and the SDTA audit log

---

## 3.5 Customer SDP Authentication

Customers authenticate into the Billing section using credentials separate from their SDTA login.

- **Username:** Billing email address (set at signup)
- **Password:** Set during signup, manageable from within the Billing section
- SDP customer sessions are independent from SDTA sessions
- Logging into the Billing section does not log the customer into SDTA and vice versa

> **Note:** In Lite, the Billing section is accessed from within SDTA after the customer is already logged in. A separate SDP login is not required for the Billing section in Lite — SDTA passes the authenticated tenant context to SDP when querying billing data. A standalone SDP customer login may be introduced in a future version if needed.

---

## 3.6 Governance Rules

1. Card data never touches SDP servers at any point — all card collection is handled by Stripe Checkout.
2. SDP stores only Stripe-provided references: Customer ID, Subscription ID, last 4 digits, card brand, and expiry month/year.
3. The signup flow is hosted by SDP and is the only customer interaction that happens outside of SDTA.
4. The Billing section in SDTA queries and writes to SDP behind the scenes — the customer never navigates to a separate SDP portal.
5. Administrator account recovery is hosted by SDP and is accessible without an SDTA session.
6. Customer SDP credentials (billing email + password) are separate from SDTA login credentials.
7. All customer-initiated changes in the Billing section are processed by SDP and confirmed back to SDTA before being displayed.

---

# 4. Tenant Provisioning

---

## 4.1 Overview

Tenant provisioning is the process by which a new customer account is created across both SDP and SDTA after a successful signup. 

The provisioning sequence follows a strict **verify first, bill second** model. Payment is authorized during signup but is not captured until all provisioning steps have been validated and are ready to commit. If anything fails before that point the payment authorization is cancelled and the customer is never charged.

This guarantees that no customer is ever billed for a failed or incomplete account.

---

## 4.2 Provisioning Sequence (Atomic)

Provisioning executes in two phases:

### Phase 1 — Validation & Preparation (Before Payment Capture)

The following steps are completed and validated before payment is captured:

1. **Collect Signup Information**
   - Business information, contact details, plan selection, and billing cycle are collected and validated

2. **Collect Payment Authorization (Stripe)**
   - Customer completes Stripe Checkout — card details are entered and an authorization hold is placed
   - Funds are reserved but not yet captured
   - If the card authorization fails, signup stops here — no records are created, no charge is made

3. **Generate Tenant UUID**
   - SDP generates a UUID that will uniquely identify this tenant across all ServizmaDesk systems
   - The UUID is never reused, even if the account is later cancelled

4. **Validate All Provisioning Steps**
   - SDP verifies that all required data is present and valid
   - SDP confirms that SDTA is available and can accept the new tenant
   - SDP confirms that all required records can be created successfully

### Phase 2 — Commit & Capture (After All Checks Pass)

Only after all Phase 1 steps pass successfully does Phase 2 execute.

1. **Capture Payment**
   - SDP instructs Stripe to capture the authorized payment.
   - If capture fails, the entire Phase 2 transaction is aborted — no records are created.

2. **Create Tenant Record in SDP**
   - SDP creates the authoritative tenant account record.
   - Status is marked as `PROVISIONING_IN_PROGRESS`.

3. **Create Workspace in SDTA (The 3-Retry Flow)**
   - SDP calls the Internal API of SDTA to create the Tenant Workspace, Administrator Employee Record, Preferences, and Lookup Data.
   - **Retry Logic:** If SDTA fails to respond successfully, SDP waits 5 seconds and retries. If it fails again, it waits 15 seconds and retries. If it fails a third time, it waits 30 seconds for a final retry.

4. **On Success:**
   - Account status in SDP is updated to `ACTIVE`.
   - The Welcome Email is sent to the customer with their login URL.
   - ServizmaDesk staff are notified of a successful signup.

5. **On Total Failure (Split Brain scenario):**
   - If SDTA completely fails after 3 retries, **the Stripe payment remains captured and the SDP record remains intact.**
   - SDP flags the account status as `PROVISIONING_FAILED`.
   - **The Welcome Email is NOT sent.** Instead, the customer sees a message: *"Your payment was successful, but your workspace is taking longer than expected to build. Our support team has been notified and will email you shortly."*
   - A **Critical System Alert** is immediately generated on the SDP Staff Dashboard (see Section 8.12).

> **Decision:** We use a resilient "Human Intervention" (Option B) model. If software fails to provision the workspace, we do not throw away the customer's payment. We capture the payment, raise a Critical Alert, and allow staff to fix the underlying issue and trigger a manual retry.

---

## 4.3 Provisioning Failure Handling

### Phase 1 Failure (Before Payment Capture)
If any Phase 1 validation step fails:
- The payment authorization is cancelled — the customer is never charged
- No records are created in SDP or SDTA
- The customer is shown a clear error message on the signup page
- If the failure is a card authorization issue, the customer is prompted to try a different card
- If the failure is a system issue, the customer is advised to try again or contact support
- ServizmaDesk staff are alerted if the failure is due to a system or provisioning validation issue

### Phase 2 Failure (After Payment Capture)
If Phase 2 SDTA provisioning completely fails after the 3 automated retries:
- The Phase 2 transaction is **not** rolled back.
- SDP retains the caught payment and the master tenant record.
- The account status is set to `PROVISIONING_FAILED`.
- A **Critical System Alert** is raised on the SDP dashboard.
- Staff must investigate the raw SDTA logs linked to the alert, fix the infrastructure issue, and press "Retry Provisioning" from the SDP dashboard. Once successful, the account becomes `ACTIVE` and the welcome email is sent.

> **Note:** We prioritize retaining the customer. A human-in-the-loop fix is preferred over a hard rollback that forces the customer to sign up again.

---

## 4.4 Staff-Initiated Provisioning

In exceptional circumstances ServizmaDesk staff may need to manually trigger or re-trigger provisioning for a customer from the SDP back office. This is a staff-only action and requires Administrator-level staff access.

Manual provisioning follows the same two-phase sequence as self-service provisioning. Staff must confirm that no partial account records exist in SDP or SDTA before triggering.

---

## 4.5 Governance Rules

1. Payment is authorized during signup but captured only after all Phase 1 validation steps pass successfully.
2. The customer is never charged if any Phase 1 step fails.
3. All Phase 2 database operations execute as a single atomic transaction — partial provisioning is not permitted.
4. If Phase 2 fails after payment capture, a full Stripe refund is initiated immediately.
5. Tenant UUIDs are never reused, even after cancellation or failed provisioning.
6. The welcome email and staff notification are sent only after Phase 2 commits successfully.
7. ServizmaDesk staff are alerted on every provisioning failure and must investigate and resolve manually.
8. Staff-initiated provisioning follows the same two-phase sequence as self-service provisioning.

---

# 5. Plan Management

---

## 5.1 Plans Overview

ServizmaDesk offers the following ServizmaDesk plans. All plans are managed through SDP.

| Plan              | Status         | Application |
|-------------------|----------------|-------------|
| ServizmaDesk Lite      | In development | SDTA          |
| ServizmaDesk Plus      | Planned        | SDTA          |
| ServizmaDesk Pro       | Planned        | SDTA          |
| ServizmaDesk Enterprise| Future         | TBD         |

Plan definitions, limits, and pricing are maintained in SDP. SDTA reads plan status and limits from SDP at runtime. Changes to plan definitions in SDP are reflected in SDTA automatically.

---

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

---

## 5.3 Billing Cycles

Customers choose between monthly and annual billing at signup. Billing cycle rules, pricing, and switching behavior are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 3.2**.

**SDP Implementation:**
- Monthly billing: Charged per seat per month on anniversary of signup date
- Annual billing: Charged as lump sum annually on anniversary of signup date
- Customers may switch billing cycles from SDTA Billing section
- Changes take effect at end of current billing period
- Stripe handles all billing cycle transitions

For complete billing cycle details and pricing, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 3.2**

---

## 5.4 Upgrades

A customer may upgrade from a lower plan to a higher plan at any time from the Billing section in SDTA.

### Upgrade Behavior
- Takes effect immediately upon confirmation
- Prorated billing is applied — the customer is charged for the remainder of the current billing period at the new plan rate, minus any unused credit from the current plan
- Stripe handles proration calculation automatically
- The customer's SDTA account is updated immediately to reflect the new plan limits
- SDP updates the tenant record with the new plan and Stripe subscription details
- A plan change confirmation email is sent to the billing email address

---

## 5.5 Downgrades

A customer may downgrade from a higher plan to a lower plan from the Billing section in SDTA.

### Downgrade Behavior
- Takes effect immediately upon confirmation
- Prorated billing is applied — the customer receives a credit for unused time on the higher plan, applied against the lower plan charge
- Stripe handles proration calculation automatically
- The customer's SDTA account is updated immediately to reflect the lower plan limits

### Downgrade Restrictions
Before a downgrade can be processed SDP must verify that the customer's current usage is within the limits of the lower plan:

| Check                  | Rule                                                      |
|------------------------|-----------------------------------------------------------|
| Seat count             | Active + On Leave + Inactive employees must be within the lower plan seat limit |
| Storage usage          | Current storage used must be within the lower plan storage limit |

If any check fails the downgrade is blocked and the customer is shown a clear message explaining what must be resolved first:

> *"Your account cannot be downgraded to ServizmaDesk Lite at this time. The following must be resolved first:"*
> - You have 12 active seats. ServizmaDesk Lite allows a maximum of 10.

---

## 5.6 Cancellations

A customer may cancel their account from the Billing section in SDTA or by contacting ServizmaDesk support.

### Cancellation Behavior
- Access to SDTA continues until the end of the current billing period
- No further charges are made after cancellation is confirmed
- Stripe subscription is cancelled immediately — no future invoices are generated
- The tenant account status in SDP is updated to Cancelled — Pending Expiry
- A cancellation confirmation email is sent to the billing email address including the date access will end

### Post-Cancellation Access
- The customer retains full read access to SDTA until the billing period end date
- No new records can be created after cancellation is confirmed
- The customer can export their data via CSV at any time during this period

### Data Retention After Cancellation
- On the billing period end date the tenant account in SDP moves to status Cancelled — Expired and SDTA access is revoked
- All tenant data in SDTA is retained for **60 days** from the expiry date
- During the 60-day grace period the customer may reactivate their account and regain full access to all their data (see Section 5.7)
- After 60 days all tenant data in SDTA is permanently deleted via an **asynchronous background worker** (e.g., Celery or chron job) during off-hours, ensuring the heavy database operation does not impact live application performance.
- This deletion is permanent and cannot be recovered.
- A data deletion warning email is sent to the billing email address 14 days before permanent deletion

---

## 5.7 Reactivation

A customer whose account is in Cancelled — Expired status may reactivate at any time within the 60-day grace period.

### Reactivation Behavior
- Customer contacts ServizmaDesk support or uses a reactivation link in the data deletion warning email
- Customer selects a plan and completes payment via Stripe Checkout
- SDP reactivates the tenant account and restores full SDTA access
- All data that existed at the time of cancellation is fully restored
- Reactivation follows the same verify first, bill second model as initial signup (see Section 4)

After the 60-day grace period has elapsed reactivation is not possible. The customer would need to sign up as a new account.

---

## 5.8 Governance Rules

1. All plan changes (upgrades, downgrades, cancellations) are processed through SDP.
2. Upgrades and downgrades take effect immediately with prorated billing via Stripe.
3. Downgrades are blocked if current usage exceeds the lower plan limits.
4. Cancellations take effect at the end of the current billing period — access continues until then.
5. No new records can be created in SDTA after a cancellation is confirmed.
6. Tenant data is retained for 60 days after the billing period end date following cancellation.
7. Customers may reactivate and regain full data access at any time within the 60-day grace period.
8. After 60 days all tenant data is permanently deleted and cannot be recovered.
9. A data deletion warning email is sent 14 days before permanent deletion.
10. Reactivation follows the same verify first, bill second provisioning model as initial signup.

---

# 6. Billing & Subscription Management

---

## 6.1 Overview

All billing for ServizmaDesk products is managed through SDP using ServizmaDesk's own Stripe account. ServizmaDesk is the merchant of record for all customer charges. Customers are billed by ServizmaDesk — not by the ServizmaDesk applications themselves.

Stripe Billing manages the subscription lifecycle including recurring charges, seat proration, payment retries, and receipt generation. SDP instructs Stripe on what to charge and when, and listens to Stripe webhooks to update account status accordingly.

---

## 6.2 ServizmaDesk Stripe Account

ServizmaDesk maintains a single Stripe account used to bill all ServizmaDesk customers. This is entirely separate from the Stripe accounts that tenants use within SDTA to bill their own customers.

- ServizmaDesk is the merchant of record for all ServizmaDesk subscription charges
- All subscription billing flows through the ServizmaDesk Stripe account
- Stripe Customer IDs and Subscription IDs are stored in SDP per tenant
- Stripe generates and sends payment receipts to customers automatically
- ServizmaDesk never stores raw card data — see Section 6.8 for full PCI posture

---

## 6.3 Billing Model

ServizmaDesk uses per-seat subscription billing with both monthly and annual options. Complete billing model details, pricing, and seat counting rules are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 3**.

**SDP Implementation:**
- Stripe Billing manages all recurring charges automatically
- Seat count changes trigger immediate Stripe subscription quantity updates
- Stripe applies proration automatically for mid-cycle changes
- Billing anniversary date is set at initial signup

For complete billing model details, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 3**

---

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

---

## 6.5 Storage Add-On Billing

Storage add-on pricing and limits are defined in **ServizmaDesk Pricing & Billing Specification V1, Section 4**.

**SDP Implementation:**
- Storage add-ons are billed as separate Stripe subscription line items
- When customer purchases storage add-on in SDTA, SDTA notifies SDP, SDP creates new subscription line item in Stripe
- Proration applies for mid-cycle storage changes
- Storage add-ons can be removed at any time — removal takes effect at end of current billing period
- If storage usage exceeds new limit after removing add-on, uploads are blocked until usage is reduced

For complete storage pricing, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 4**

---

## 6.6 Payment Failure Handling
### Stripe Webhooks, Signatures, & Idempotency
Because network requests can fail, duplicate, or arrive out of order, SDP must handle Stripe webhooks securely:
1. **Webhook Signatures:** SDP will calculate the cryptographic signature of the incoming request and compare it to Stripe’s signature to guarantee the payload wasn't spoofed.
2. **Idempotency:** Every Stripe event has a unique `Event_ID`. SDP logs every processed event in an `sdp_webhook_events` table. If SDP receives an `Event_ID` it has already processed, it safely ignores it to prevent double-processing (e.g., suspending an account twice). These logs are retained for **180 days** and then pruned to prevent database bloat.


### On Initial Payment Failure
When a recurring payment fails Stripe notifies SDP via webhook. SDP initiates the following process:

1. **Immediate notification to customer**
   - A banner notification appears in SDTA informing the Administrator that the payment failed
   - A payment failure email is sent to the billing email address with instructions to update their payment method
   - The email includes a direct link to the Billing section in SDTA

2. **7-day grace period**
   - The customer retains full access to SDTA for 7 days from the payment failure date
   - SDP flags the account as Payment Failed — Grace Period in SDP
   - Stripe automatically retries the payment during this period per its retry schedule

3. **Suspension after grace period**
   - If payment has not been resolved after 7 days the account is suspended
   - Account status in SDP is updated to Suspended — Payment Failed
   - See Section 6.7 for suspension behavior

### Payment Retry Schedule
Stripe retries failed payments automatically. The default Stripe retry schedule is:
- Retry 1: 3 days after initial failure
- Retry 2: 5 days after initial failure
- Retry 3: 7 days after initial failure

If all retries fail within the 7-day grace period the account is suspended.

### Resolving a Payment Failure
The customer resolves a payment failure by updating their payment method in the Billing section in SDTA:
- Customer navigates to Billing in SDTA (accessible even during grace period and suspension)
- Customer updates their card via Stripe Checkout
- Stripe immediately retries the outstanding payment with the new card
- On success SDP removes the Payment Failed flag and restores normal account status
- A payment success confirmation email is sent to the billing email address

---

## 6.7 Account Suspension (Payment Failed)

When an account is suspended due to payment failure:

### Customer Access During Suspension
- Full SDTA access is suspended for all employees
- The Administrator can still log into SDTA but has access to the Admin Area only
- A prominent warning banner is displayed across the entire SDTA interface:

> *"Your account has been suspended due to a failed payment. Please update your payment method in the Billing section to restore full access."*

- All other employees attempting to log in are shown:

> *"Your account is currently suspended. Please contact your Administrator."*

### ServizmaDesk Staff Notification
- SDP flags the account as suspended in the back office
- ServizmaDesk staff are notified of the suspension via the SDP staff notification system

### Restoring Access After Suspension
- The Administrator updates their payment method and the outstanding payment is resolved
- SDP immediately restores full SDTA access for all employees
- The suspension warning banner is removed
- A restoration confirmation email is sent to the billing email address

### Suspension to Cancellation
- If a suspended account remains unresolved for 30 days SDP automatically cancels the account
- The standard cancellation and 60-day data retention process applies (see Section 5.6)
- A final warning email is sent 7 days before automatic cancellation

---

## 6.8 PCI Compliance Posture

Handling payment card data is subject to PCI DSS (Payment Card Industry Data Security Standard) regulations. ServizmaDesk's architecture is specifically designed to minimize PCI scope and risk by ensuring that raw card data never touches ServizmaDesk systems at any point.

### How Card Data Is Handled
- All card data entry is handled exclusively through **Stripe Checkout** — a Stripe-hosted payment page
- When a customer enters their card details they are entering them directly into Stripe's systems, not ServizmaDesk's
- Stripe returns only safe, tokenized references to SDP — never raw card data

### What SDP Stores (Stripe-Provided References Only)
| Field                  | Source         | Purpose                        |
|------------------------|----------------|--------------------------------|
| Stripe Customer ID     | Stripe API     | Links tenant to Stripe customer|
| Stripe Subscription ID | Stripe API     | Manages recurring billing      |
| Stripe Payment Method ID | Stripe API   | References saved payment method|
| Last 4 digits          | Stripe API     | Display only — card identification |
| Card brand             | Stripe API     | Display only (Visa, Mastercard, etc.) |
| Expiry month / year    | Stripe API     | Display only — expiry awareness|

### What SDP Never Stores
- Full card number (PAN)
- CVV / CVC security code
- Raw card data of any kind
- Magnetic stripe data

### Card Entry Rules
- Card data is collected exclusively via Stripe Checkout at signup and when updating a payment method
- SDP never renders a custom card entry form that posts card data to ServizmaDesk servers
- No ServizmaDesk staff member ever has access to a customer's full card number

> **Decision:** ServizmaDesk's use of Stripe Checkout for all card collection dramatically reduces PCI DSS scope. ServizmaDesk operates as a SAQ A merchant — the lowest PCI compliance tier — because card data never touches ServizmaDesk servers or staff at any point.

---

## 6.9 Governance Rules

1. All ServizmaDesk subscription billing flows through the ServizmaDesk Stripe account — ServizmaDesk is the merchant of record.
2. Raw card data never touches SDP servers at any point — all card collection is handled by Stripe Checkout.
3. SDP stores only Stripe-provided tokenized references — never raw card data.
4. Seat count at the time of billing is used to calculate charges — Terminated employees are excluded.
5. Stripe Billing handles all seat proration automatically when seat count changes.
6. Storage add-ons are billed as additional Stripe subscription line items.
7. Payment failure triggers a 7-day grace period before account suspension.
8. Suspended accounts retain Administrator-only access to SDTA with a prominent warning banner displayed.
9. Suspended accounts that remain unresolved for 30 days are automatically cancelled.
10. Stripe generates and sends payment receipts to customers automatically — ServizmaDesk does not send separate billing receipts.
11. All billing status changes are communicated to the customer via email from SDP.

---

# 7. Security Verification Credentials

---

## 7.1 Overview

Security Verification Credentials are the identity verification mechanism used exclusively for Administrator account recovery. They are established during the signup flow and stored only in SDP — they are never transmitted to or stored in SDTA.

These credentials exist to answer one question: when an Administrator is locked out of SDTA and cannot log in, how does ServizmaDesk verify that the person requesting recovery is the legitimate account owner?

There are two credential types:
- **Security PIN** — a 6-digit numeric code set by the Administrator at signup
- **Security Questions & Answers** — 4 questions selected from a predefined list with answers provided by the Administrator at signup

---

## 7.2 Credential Storage

All security credentials are stored exclusively in SDP.

| Credential             | Storage Location | Encrypted at Rest | Transmitted to SDTA |
|------------------------|------------------|-------------------|-------------------|
| Security PIN           | SDP only          | Yes               | Never             |
| Security Questions     | SDP only          | Yes               | Never             |
| Security Answers       | SDP only          | Yes (hashed)      | Never             |

### Storage Rules
- Security answers are stored as hashed values — they are never stored in plaintext
- Answer comparison during verification uses hash comparison — answers are never decrypted for comparison
- The Security PIN is stored encrypted at rest
- No ServizmaDesk staff member can view the plaintext value of any security answer or PIN

---

## 7.3 Predefined Security Question List

The Administrator selects 4 questions from the following predefined list during signup. No two selections may be the same question.

1. What was the name of your first pet?
2. What city were you born in?
3. What is your mother's maiden name?
4. What was the make of your first car?
5. What was the name of your elementary school?
6. What is the name of the street you grew up on?
7. What was your childhood nickname?
8. What was the name of your first employer?
9. What city did you meet your spouse or significant other?
10. What is the middle name of your oldest sibling?
11. What was the name of the hospital where you were born?
12. What was the first concert you attended?
13. What is the name of your favorite childhood friend?
14. What was the model of your first computer?
15. What is your oldest cousin's first name?

> **Note:** This list is managed in SDP and is shared across all ServizmaDesk plans. It may be expanded in future versions.

---

## 7.4 Credential Verification Process

Security credentials are verified by ServizmaDesk support staff during the Administrator account recovery process (see Section 8.3 for the full recovery workflow).

### Verification Steps

**Step 1 — Security PIN**
- The Administrator provides their 6-digit Security PIN
- SDP compares the provided PIN against the stored encrypted value
- If correct, proceed to Step 2
- If incorrect, fall back to Billing Verification (see below)

**Step 2 — Security Questions**
- The Administrator is presented with their 4 security questions
- The Administrator must answer **2 of 4 questions correctly**
- Answers are case-insensitive and leading/trailing whitespace is ignored
- SDP compares each answer against the stored hash
- If 2 of 4 answers match, identity is verified and recovery proceeds

### Billing Verification Fallback
If the Administrator cannot provide the correct PIN, they must instead verify their identity using billing details:

- Business name on the account (must match exactly)
- Billing email address (must match exactly)
- Last 4 digits of the card on file (must match exactly)

All three billing details must match. Partial matches are not accepted.

> **Decision:** PIN verification is attempted first. Security questions are the primary second factor. Billing details are the last resort fallback only. All three methods require ServizmaDesk staff involvement — there is no fully automated self-service recovery path.

---

## 7.5 Credential Update Process

The Administrator may update their security credentials at any time from the Billing section in SDTA. Credential updates are processed and stored in SDP.

### Updating Security Questions and Answers
- Requires the current Security PIN to confirm the update
- The Administrator may update any or all of the 4 questions and answers
- All updates are logged in the SDP audit log

### Updating the Security PIN
- Requires correctly answering 2 of 4 current security questions to confirm the update
- The new PIN must be 6 digits numeric
- The update is logged in the SDP audit log

---

## 7.6 Governance Rules

1. Security credentials are stored only in SDP and are never transmitted to or stored in SDTA.
2. Security answers are stored as hashed values and are never stored or compared in plaintext.
3. No ServizmaDesk staff member can view the plaintext value of any security credential.
4. Administrator recovery requires ServizmaDesk staff involvement — there is no fully automated self-service recovery path.
5. PIN verification is attempted before security questions during recovery.
6. Billing details are the fallback verification method only — used when PIN verification fails.
7. All credential updates are logged in the SDP audit log.
8. Updating security questions requires the current PIN to confirm.
9. Updating the PIN requires correctly answering 2 of 4 current security questions to confirm.
10. Answer comparison is case-insensitive and ignores leading and trailing whitespace.

---

# 8. ServizmaDesk Staff Tools (Back Office)

---

## 8.1 Overview

The ServizmaDesk Staff Back Office is the internal face of SDP. It is used exclusively by ServizmaDesk staff to manage customer accounts, resolve support issues, and perform operational tasks that cannot be done through the customer-facing surface.

All ServizmaDesk staff have full access to all back office functions. There are no role-based restrictions within the staff back office in the initial version — access control is covered in Section 10.

Every action taken by a staff member in the back office is logged in the SDP audit log.

---

## 8.2 Account Lookup

Staff can search for customer accounts using any of the following criteria:

| Search Field              | Notes                                      |
|---------------------------|--------------------------------------------|
| Company name              | Partial match supported                    |
| Billing email address     | Exact or partial match                     |
| Primary account holder name | First name, last name, or full name      |
| Tenant UUID               | Exact match                                |
| Plan type                 | Filter by ServizmaDesk Lite / Plus / Pro        |
| Account status            | Filter by Active / Suspended / Cancelled   |

Search results display a summary list showing company name, primary contact, plan, account status, and signup date. Clicking a result opens the full account detail view.

### Account Detail View
The account detail view displays all information SDP holds for a tenant:

- Company name and billing email
- Primary account holder name and contact details
- Plan, billing cycle, and next billing date
- Current seat count and storage usage
- Stripe Customer ID and Subscription ID (read-only reference)
- Last 4 digits of card on file, card brand, expiry
- Account status and status history
- Signup date and last activity date
- Full billing history
- SDP audit log entries for this account

---

## 8.3 Administrator Account Unlock

When an Administrator is locked out of SDTA they contact ServizmaDesk support. Staff handle the recovery from the back office.

### Recovery Process

1. Staff locates the customer account using Account Lookup
2. Staff initiates an Administrator Recovery request on the account
3. Staff verifies the Administrator's identity using the Security Verification process (see Section 7.4)
4. Once identity is verified:
   - Staff unlocks the Administrator account in SDTA
   - Staff forces a password reset — the Administrator must set a new password on next login
   - The unlock action is logged in both the SDP audit log and the SDTA audit log
5. Staff confirms to the Administrator that their account has been unlocked and they may log in

### Rules
- Staff cannot unlock an Administrator account without completing identity verification
- All unlock actions are logged with the staff member's identity, timestamp, and verification method used
- Staff cannot bypass the identity verification process regardless of circumstances

---

## 8.4 Administrator Password Reset

In exceptional circumstances staff may need to reset an Administrator's password directly from the back office — for example if the Administrator has lost access to their temporary password after provisioning.

### Process
1. Staff locates the customer account
2. Staff verifies identity using the Security Verification process (see Section 7.4)
3. Staff triggers a password reset — SDP forces a password reset flag on the Administrator account in SDTA
4. The Administrator is sent a password reset link to their billing email address
5. The Administrator sets their new password via the reset link
6. The action is logged in both the SDP and SDTA audit logs

---

## 8.5 Plan Changes (Staff-Initiated)

Staff may change a customer's plan on their behalf from the back office — for example at the customer's request via a support channel.

### Process
1. Staff locates the customer account
2. Staff selects the new plan and billing cycle
3. Staff confirms the change — SDP updates the Stripe subscription and the tenant record in SDTA
4. Proration is applied automatically by Stripe
5. The plan change is logged in the SDP audit log
6. A plan change confirmation email is sent to the customer's billing email address

### Downgrade Restrictions
Staff-initiated downgrades are subject to the same usage checks as customer-initiated downgrades (see Section 5.5). Staff cannot bypass usage limit checks.

---

## 8.6 Seat Management (Staff-Initiated)

Staff may add or remove seats on a customer account from the back office at the customer's request.

### Process
1. Staff locates the customer account
2. Staff adjusts the seat count within the plan limit (maximum 10 for ServizmaDesk Lite)
3. SDP updates the Stripe subscription quantity — Stripe applies proration automatically
4. The SDTA account reflects the new seat limit immediately
5. The change is logged in the SDP audit log

---

## 8.7 Account Suspension and Unsuspension

Staff may manually suspend or unsuspend a customer account from the back office.

### Manual Suspension
- Used for exceptional circumstances such as suspected fraud or terms of service violations
- Staff records a reason for the suspension — this is required and cannot be skipped
- The account status in SDP is updated to Suspended — Staff Initiated
- The same partial-access suspension behavior applies as payment failure suspension (see Section 6.7)
- A suspension notification email is sent to the billing email address
- The suspension reason and staff identity are logged in the SDP audit log

### Unsuspension
- Staff may unsuspend an account at any time
- Staff records a reason for the unsuspension
- Full SDTA access is restored immediately
- A restoration notification email is sent to the billing email address
- The action is logged in the SDP audit log

---

## 8.8 Account Cancellation (Staff-Initiated)

Staff may cancel a customer account from the back office at the customer's request or for operational reasons.

### Process
1. Staff locates the customer account
2. Staff selects Cancel Account and records a cancellation reason — required
3. SDP cancels the Stripe subscription immediately — no further charges
4. The standard cancellation behavior applies (see Section 5.6):
   - Access continues to end of billing period
   - 60-day data retention grace period applies
5. A cancellation confirmation email is sent to the billing email address
6. The cancellation and reason are logged in the SDP audit log

---

## 8.9 Manual Refund (Staff-Initiated)

Staff may issue a manual refund to a customer via Stripe from the back office.

### Process
1. Staff locates the customer account and views billing history
2. Staff selects the charge to refund from the billing history
3. Staff enters the refund amount (full or partial) and records a reason — required
4. SDP instructs Stripe to issue the refund
5. Stripe processes the refund to the customer's card on file
6. The refund and reason are logged in the SDP audit log
7. Stripe sends a refund confirmation to the customer automatically

### Rules
- Refunds can only be issued against charges that appear in the customer's Stripe billing history
- Partial refunds are permitted
- Staff cannot issue a refund greater than the original charge amount
- All refunds require a recorded reason

---

## 8.10 Manual Provisioning (Staff-Initiated)

Staff may manually trigger provisioning for a customer account in exceptional circumstances — for example to recover from a failed signup or to set up an account on behalf of a customer.

### Process
1. Staff verifies that no partial account records exist in SDP or SDTA for this customer
2. Staff enters all required account details manually
3. Staff triggers provisioning — the same two-phase verify first, bill second sequence applies (see Section 4)
4. On success the welcome email is sent and the account is active
5. The manual provisioning action is logged in the SDP audit log

---

## 8.11 SDP Audit Log (Staff Actions)

Every action taken by a staff member in the back office is recorded in the SDP audit log.

### Fields Captured Per Entry
- `audit_event_uuid`
- `staff_user_uuid` (the staff member who took the action)
- `timestamp`
- `event_type` (see taxonomy below)
- `tenant_uuid` (the affected customer account)
- `summary` (human-readable description of the action)
- `reason` (required for suspension, cancellation, refund, and manual actions)

### Staff Audit Event Taxonomy

| Event Type                  | Trigger                                      |
|-----------------------------|----------------------------------------------|
| ACCOUNT_VIEWED              | Staff opens a customer account detail view   |
| ACCOUNT_EDITED              | Staff edits company name or billing email    |
| PLAN_CHANGED                | Staff changes a customer's plan              |
| SEATS_ADJUSTED              | Staff changes seat count                     |
| ACCOUNT_SUSPENDED           | Staff manually suspends an account           |
| ACCOUNT_UNSUSPENDED         | Staff unsuspends an account                  |
| ACCOUNT_CANCELLED           | Staff cancels an account                     |
| ADMIN_UNLOCKED              | Staff unlocks an Administrator account       |
| ADMIN_PASSWORD_RESET        | Staff resets an Administrator password       |
| REFUND_ISSUED               | Staff issues a manual refund                 |
| PROVISIONING_TRIGGERED      | Staff triggers manual provisioning           |

### Retention
SDP audit log entries are retained for 36 months on a rolling basis.

---

## 8.12 Critical System Alerts & Trouble Tickets (Dashboard)

To ensure proactive resolution of system failures (such as a `PROVISIONING_FAILED` event or internal API sync failure), SDP includes a robust Critical System Alerts dashboard. This acts as a lightweight, built-in incident tracking system for ServizmaDesk staff.

### The "Requires Attention" Banner
- Any open alert triggers a massive, highly visible **WARNING banner** across the top of the SDP dashboard for all staff members.
- The banner displays the count of actionable items (e.g., "1 ACTION REQUIRED: Provisioning Failed for Acme Corp").
- The warning remains until all alerts are resolved.

### The Alert Detail View (The "Ticket")
Clicking an alert opens its detail view, which displays:
- **Context:** Which tenant is affected and what failed (e.g., after 3 retries).
- **Raw Log:** The exact technical error returned by the system (e.g., "Database connection timeout").
- **Status:** The ticket workflow state.

### Ticket Status Workflow
Alerts move through three distinct states, color-coded for visibility:
1. **Open (Red):** The alert has been generated; no one is working on it. (Triggers the global warning banner).
2. **Working (Yellow):** A staff member has acknowledged the alert and is actively investigating the fix.
3. **Resolved (Green):** The issue is fixed, and normal operations have resumed.

### Resolution Governance
- **Mandatory Notes:** A staff member cannot change an alert status from Working to Resolved without filling out a required **"Resolution Notes"** text field detailing exactly what was done to fix the issue.
- **Audit Loop:** These notes are permanently archived in the SDP Audit Log. This provides a clear feedback loop for engineering to identify and fix recurring infrastructure bugs.

---

## 8.13 Governance Rules

1. All ServizmaDesk staff have full access to all back office functions.
2. Every staff action in the back office is logged in the SDP audit log with staff identity and timestamp.
3. Administrator account unlock and password reset require completed identity verification — staff cannot bypass this.
4. Suspension, cancellation, refund, and manual provisioning actions require a recorded reason.
5. Staff-initiated plan downgrades are subject to the same usage limit checks as customer-initiated downgrades.
6. Staff cannot issue a refund greater than the original charge amount.
7. SDP audit log entries are retained for 36 months.
8. All significant staff actions trigger a notification email to the affected customer's billing email address.

---

# 9. Transactional Communications

---

## 9.1 Overview

SDP is responsible for all transactional communications between ServizmaDesk and its customers. These are operational emails triggered by account and billing events — not marketing emails.

All emails are sent from SDP using a third-party transactional email provider. The provider has not been selected yet and is a decision to be made before development begins. The email provider must support:
- Reliable transactional email delivery
- Basic HTML email templates
- Delivery tracking and bounce handling
- A Django-compatible SDK or API

All emails use basic HTML templates with ServizmaDesk branding — company name, logo, and consistent styling. Full design templates are deferred to a future version.

Payment receipts are generated and sent by Stripe automatically. SDP does not send a separate receipt for successful recurring charges.

---

## 9.2 Email Events & Templates

The following events trigger an outbound email from SDP to the customer's billing email address:

---

### E01 — Welcome Email (Post-Signup)
- **Trigger:** Successful account provisioning (Phase 2 commit)
- **Recipient:** Billing email address
- **Purpose:** Confirm account creation and provide login details
- **Content:**
  - Welcome message and confirmation that the account is active
  - Plan selected and billing cycle
  - SDTA login URL
  - Link to getting started guide (ServizmaDesk.com)
  - ServizmaDesk support contact

---

### E02 — Payment Failure Notification
- **Trigger:** Stripe webhook — recurring payment failed
- **Recipient:** Billing email address
- **Purpose:** Alert the customer and prompt them to update their payment method
- **Content:**
  - Notification that a payment has failed
  - Amount that was attempted
  - Direct link to the Billing section in SDTA to update payment method
  - Clear statement that the account will be suspended in 7 days if not resolved
  - ServizmaDesk support contact

---

### E03 — Account Suspended Notification
- **Trigger:** Account suspended (payment failure after 7-day grace period, or staff-initiated)
- **Recipient:** Billing email address
- **Purpose:** Inform the customer their account has been suspended
- **Content:**
  - Notification that the account has been suspended
  - Reason for suspension (payment failure or ServizmaDesk-initiated)
  - For payment failure: direct link to Billing section in SDTA to resolve
  - Statement that data is preserved and access will be restored on resolution
  - ServizmaDesk support contact

---

### E04 — Account Unsuspended Notification
- **Trigger:** Account suspension lifted (payment resolved or staff-initiated)
- **Recipient:** Billing email address
- **Purpose:** Confirm that full access has been restored
- **Content:**
  - Confirmation that the account suspension has been lifted
  - Confirmation that full access to SDTA has been restored
  - ServizmaDesk support contact

---

### E05 — Cancellation Confirmation
- **Trigger:** Account cancellation confirmed (customer or staff-initiated)
- **Recipient:** Billing email address
- **Purpose:** Confirm cancellation and communicate access end date and data retention window
- **Content:**
  - Confirmation that the account has been cancelled
  - Date access to SDTA will end (end of current billing period)
  - Statement that data will be retained for 60 days after access ends
  - Instructions for exporting data via CSV before access ends
  - Reactivation information — account can be reactivated within the 60-day window
  - ServizmaDesk support contact

---

### E06 — Data Deletion Warning
- **Trigger:** 14 days before permanent data deletion (60-day grace period minus 14 days after access end)
- **Recipient:** Billing email address
- **Purpose:** Final warning before all tenant data is permanently deleted
- **Content:**
  - Warning that all account data will be permanently deleted in 14 days
  - Exact deletion date
  - Statement that this action is irreversible
  - Reactivation link — account can still be reactivated before deletion
  - ServizmaDesk support contact

---

### E07 — Plan Change Confirmation
- **Trigger:** Plan change processed (upgrade, downgrade — customer or staff-initiated)
- **Recipient:** Billing email address
- **Purpose:** Confirm the plan change and communicate billing impact
- **Content:**
  - Confirmation of the plan change
  - Previous plan and new plan
  - Effective date (immediate)
  - Prorated charge or credit applied
  - New recurring billing amount going forward
  - ServizmaDesk support contact

---

### E08 — Account Reactivation Confirmation
- **Trigger:** Successful account reactivation within the 60-day grace period
- **Recipient:** Billing email address
- **Purpose:** Confirm reactivation and restore confidence
- **Content:**
  - Confirmation that the account has been reactivated
  - Plan selected and billing cycle
  - Confirmation that all previous data has been fully restored
  - SDTA login URL
  - ServizmaDesk support contact

---

### E09 — Payment Receipt
- **Trigger:** Successful recurring payment processed by Stripe
- **Recipient:** Billing email address (sent by Stripe directly)
- **Purpose:** Provide a receipt for the charge
- **Content:** Handled entirely by Stripe — SDP does not send a separate receipt for successful recurring charges
- **Note:** ServizmaDesk should configure Stripe to send automatic receipt emails to customers. No SDP development is required for this email type.

---

## 9.3 Email Sending Rules

1. All emails are sent to the billing email address on the account — not to individual employee email addresses in SDTA
2. Emails are sent immediately upon the triggering event unless otherwise noted
3. The data deletion warning (E06) is scheduled 46 days after the access end date (14 days before the 60-day deletion deadline)
4. If an email delivery fails SDP logs the failure and alerts ServizmaDesk staff
5. SDP does not retry failed email deliveries automatically — staff must investigate and resend if necessary

---

## 9.4 Email Provider Selection

The transactional email provider has been selected. SDP uses **Postmark** to ensure reliable transactional email delivery with high deliverability rates.

> **Decision:** Postmark is the designated email provider for **internal SDP communications** only (Welcome emails, billing alerts, password resets). 
> **Tenant-Side Emails:** Email sending functionality for the Tenant Application (e.g., sending invoices) will offer two options: User-supplied SMTP or a Point-based system (1 point = 1 email). The Point System will be defined in the SDTA/SDTP specification documents.

The following requirements are met by Postmark:
- Reliable transactional email delivery with high deliverability rates
- Basic HTML template support
- Delivery status tracking (sent, delivered, bounced, failed)
- Bounce and complaint handling
- Django-compatible SDK or REST API
- Reasonable pricing for low-to-moderate email volume at MVP stage

---

## 9.5 Governance Rules

1. All transactional emails are sent from SDP to the customer's billing email address.
2. Payment receipts for successful recurring charges are handled by Stripe — SDP does not send duplicate receipts.
3. All emails use basic HTML templates with ServizmaDesk branding.
4. Email delivery failures are logged and ServizmaDesk staff are alerted.
5. The data deletion warning email is sent 14 days before permanent deletion.
6. The email provider must be selected before SDP development begins — it is a dependency.
7. SDP does not send marketing emails — transactional operational emails only.

---

# 10. ServizmaDesk Staff Roles & Access

---

## 10.1 Purpose

This section defines how ServizmaDesk staff authenticate into the SDP back office and how their accounts are managed. All ServizmaDesk staff have full access to all back office functions — there are no role-based restrictions within the staff back office at this stage.

---

## 10.2 Staff Authentication

ServizmaDesk staff authenticate into the SDP back office using a username and password.

- **Username:** ServizmaDesk staff email address
- **Password:** Set by the staff member on first login after account creation
- Staff sessions are managed independently from customer SDP sessions and SDTA sessions
- A staff login does not grant access to any customer SDTA account

### Password Rules (Staff Accounts)
- Minimum 10 characters
- Must include at least one uppercase letter
- Must include at least one lowercase letter
- Must include at least one number
- Must include at least one special character (e.g. ! @ # $ % ^ & *)
- Passwords are never stored in plaintext — hashed using bcrypt or equivalent

### Session Rules
- Staff sessions expire after a period of inactivity (duration to be defined at build time)
- Staff are required to log in again after session expiry
- All staff login attempts (success and failure) are recorded in the SDP audit log

---

## 10.3 Staff Account Management

Staff accounts are created and managed manually by the SDP Administrator — the designated ServizmaDesk staff member responsible for managing the SDP back office itself.

### Account Creation
1. SDP Administrator creates a new staff account with the staff member's name and email address
2. System sends a password setup link to the staff member's email address
3. Staff member clicks the link and sets their password
4. Password setup link expires after 24 hours if not used
5. Staff member can log into the SDP back office immediately after setting their password
6. Account creation is logged in the SDP audit log

### Account Deactivation
- When a staff member leaves ServizmaDesk the SDP Administrator deactivates their account immediately
- Deactivated staff accounts cannot log in
- Deactivated accounts are retained for audit integrity — they are never deleted
- Any audit log entries referencing the deactivated staff member remain intact
- Account deactivation is logged in the SDP audit log

### Password Reset
- The SDP Administrator may trigger a password reset for any staff account
- System sends a password reset link to the staff member's email address
- Reset link expires after 24 hours if not used
- The reset action is logged in the SDP audit log

---

## 10.4 SDP Administrator

The SDP Administrator is the designated ServizmaDesk staff member responsible for managing the SDP back office itself. This is an internal designation — not a separate system role.

Responsibilities include:
- Creating and deactivating staff accounts
- Resetting staff passwords
- Maintaining the SDP back office operational health
- Reviewing the SDP audit log

There must always be at least one designated SDP Administrator at ServizmaDesk. If the SDP Administrator leaves the company a replacement must be designated before the departing Administrator's account is deactivated.

---

## 10.5 Access Control

All ServizmaDesk staff have full access to all SDP back office functions. There are no role-based restrictions in the initial version.

> **Note:** Role-based access control for ServizmaDesk staff may be introduced in a future version as the team grows and operational needs require it. The architecture should not preclude this being added later.

---

## 10.6 Governance Rules

1. All ServizmaDesk staff authenticate using a username and password — no self-registration is permitted.
2. Staff accounts are created manually by the SDP Administrator only.
3. Staff passwords follow the same rules as SDP customer passwords — minimum 10 characters with uppercase, lowercase, number, and special character.
4. Passwords are never stored in plaintext — hashed using bcrypt or equivalent.
5. Staff accounts are never deleted — deactivated accounts are retained for audit integrity.
6. Deactivated staff accounts cannot log in.
7. All staff login attempts and account management actions are logged in the SDP audit log.
8. There must always be at least one designated SDP Administrator at ServizmaDesk.
9. Password setup and reset links expire after 24 hours.

---

# 11. Data Retention & Security

---

## 11.1 Overview

This section defines how SDP handles data retention, credential security, and ServizmaDesk's overall security posture. Many of the rules in this section are a direct consequence of decisions made in earlier sections — they are consolidated here as the authoritative reference.

---

## 11.2 Customer Data Retention

### Active Accounts
- All customer account data in SDP is retained for the lifetime of the account
- Billing history and SDP audit log entries are retained for 36 months on a rolling basis
- Stripe transaction records are retained by Stripe indefinitely and are accessible via the ServizmaDesk Stripe dashboard

### Cancelled Accounts
| Phase                         | Duration                          | Data State                              |
|-------------------------------|-----------------------------------|-----------------------------------------|
| Active                        | Billing period end date           | Full SDTA access, no new records after cancellation confirmed |
| Cancelled — Pending Expiry    | Until billing period end date     | Read-only SDTA access, CSV export available |
| Cancelled — Expired           | 60 days from billing period end   | SDTA access revoked, data preserved in SDTA database |
| Permanently Deleted           | After 60-day grace period         | All tenant data in SDTA permanently deleted (via background worker) |

- SDP account records (billing history, audit log) are retained for 36 months after cancellation regardless of SDTA data deletion
- A data deletion warning email is sent 14 days before permanent deletion (see Section 9 — E06)
- Permanent deletion is irreversible — there is no backup or restore capability

### Terminated Employees in SDTA
- Employee records in SDTA are never deleted — they are retained for audit integrity regardless of account status
- This is governed by the ServizmaDesk Lite specification (Section 18)

---

## 11.3 Credential Security

### SDP Customer Passwords
- Minimum 10 characters
- Must include uppercase, lowercase, number, and special character
- Never stored in plaintext — hashed using bcrypt or equivalent
- No ServizmaDesk staff member can view a customer's plaintext password

### SDTA Employee Passwords
- Minimum 8 characters
- Must include uppercase, lowercase, number, and special character
- Never stored in plaintext — hashed using bcrypt or equivalent
- No ServizmaDesk staff member can view an employee's plaintext password

### ServizmaDesk Staff Passwords
- Same rules as SDP customer passwords — minimum 10 characters with uppercase, lowercase, number, and special character
- Never stored in plaintext — hashed using bcrypt or equivalent

### Security Verification Credentials (PIN & Security Questions)
- Stored only in SDP — never transmitted to or stored in SDTA
- Security PIN stored encrypted at rest
- Security question answers stored as hashed values — never stored or compared in plaintext
- No ServizmaDesk staff member can view the plaintext value of any security credential
- Full credential security rules are defined in Section 7

---

## 11.4 PCI Compliance Posture

ServizmaDesk's architecture is specifically designed to minimize PCI DSS scope by ensuring raw card data never touches ServizmaDesk systems at any point.

### Approach
- All card data entry is handled exclusively through Stripe Checkout — a Stripe-hosted payment page
- Card data is entered directly into Stripe's systems — it never passes through SDP servers
- Stripe returns only safe, tokenized references to SDP

### What SDP Stores (Stripe-Provided References Only)
| Field                    | Purpose                             |
|--------------------------|-------------------------------------|
| Stripe Customer ID       | Links tenant to Stripe customer     |
| Stripe Subscription ID   | Manages recurring billing           |
| Stripe Payment Method ID | References saved payment method     |
| Last 4 digits            | Display only — card identification  |
| Card brand               | Display only (Visa, Mastercard etc.)|
| Expiry month / year      | Display only — expiry awareness     |

### What SDP Never Stores
- Full card number (PAN)
- CVV / CVC security code
- Raw card data of any kind
- Magnetic stripe data

### PCI Compliance Tier
ServizmaDesk operates as a **SAQ A merchant** — the lowest and simplest PCI compliance tier. This is achievable because:
- Card data never touches ServizmaDesk servers
- No ServizmaDesk staff member ever has access to a customer's full card number
- All card collection is delegated entirely to Stripe

> **Important:** ServizmaDesk must never introduce a custom card entry form that posts card data to SDP servers. Doing so would immediately invalidate SAQ A status and dramatically increase PCI compliance obligations. All card collection must always go through Stripe Checkout.

---

## 11.5 Data Isolation & Tenant Security

- Every tenant account in SDTA is isolated by Tenant UUID — no tenant can access another tenant's data
- Tenant isolation is enforced at three layers: application middleware, database row-level security, and field-level constraints
- SDP never exposes one customer's data to another customer through any surface
- Staff back office access is scoped to viewing and managing individual accounts — bulk cross-tenant data access is not a feature of the back office

---

## 11.6 Audit Log Retention Summary

| Log                        | Retention Period     | Location  |
|----------------------------|----------------------|-----------|
| SDP audit log               | 36 months rolling    | SDP        |
| SDTA audit log               | 18 months rolling    | SDTA        |
| Stripe transaction records | Indefinite           | Stripe    |
| Staff login attempts       | 36 months rolling    | SDP        |

---

## 11.7 Governance Rules

1. All passwords across SDP and SDTA are hashed using bcrypt or equivalent — never stored in plaintext.
2. Security verification credentials are stored only in SDP and are never transmitted to SDTA.
3. Raw card data never touches SDP servers at any point — all card collection uses Stripe Checkout.
4. SDP stores only Stripe-provided tokenized references — never raw card data.
5. ServizmaDesk must always use Stripe Checkout for card collection — custom card entry forms are strictly prohibited.
6. Tenant data in SDTA is retained for 60 days after account expiry then permanently deleted.
7. SDP account records and audit logs are retained for 36 months after cancellation.
8. Permanent data deletion is irreversible — there is no backup or restore capability.
9. Tenant isolation is enforced at application, database, and field levels in SDTA.
10. No ServizmaDesk staff member can view the plaintext value of any password or security credential.

---

# 12. MVP Completion Criteria

SDP is complete when all of the following criteria are met:

---

## 12.1 Customer-Facing Surface

1. The signup flow is accessible from ServizmaDesk.com via a signup link and completes successfully end to end — plan selection, business information, password setup, Stripe Checkout payment, security verification setup, provisioning, and welcome email.
2. Payment authorization and capture follow the verify first, bill second model — no customer is charged for a failed provisioning.
3. The Billing section in SDTA correctly queries SDP, displays current billing data, and pushes changes back to SDP.
4. Administrator account recovery is accessible from the SDTA login page and completes successfully using all three verification methods — PIN, security questions, and billing details fallback.

---

## 12.2 Tenant Provisioning

5. Provisioning is fully atomic — a successful signup results in a complete, fully initialized tenant account in both SDP and SDTA with no manual intervention required.
6. A failed provisioning leaves no partial records in SDP or SDTA and triggers an immediate staff alert.
7. Manual staff-initiated provisioning works correctly from the back office.

---

## 12.3 Plan & Billing Management

8. Monthly and annual billing subscriptions are created correctly in Stripe on signup.
9. Upgrades and downgrades take effect immediately with correct Stripe proration applied.
10. Downgrade usage checks correctly block downgrades when seat count or storage exceeds lower plan limits.
11. Cancellation stops future billing, access continues to end of billing period, and the 60-day data retention countdown begins correctly.
12. Seat additions and removals notify Stripe correctly and proration is applied automatically.
13. Storage add-ons are added and removed as Stripe subscription line items correctly.
14. Payment failure triggers the 7-day grace period, correct retry behavior, and account suspension if unresolved.
15. Suspended accounts correctly restrict SDTA access to Administrator-only with the warning banner displayed.
16. Accounts suspended for 30 days without resolution are automatically cancelled.
17. Manual refunds can be issued from the back office and are processed correctly through Stripe.

---

## 12.4 Security & Credentials

18. Security verification credentials are stored only in SDP and are never present in the SDTA database.
19. All passwords are hashed — no plaintext passwords exist anywhere in SDP or SDTA databases.
20. Card data never touches SDP servers at any point — all card collection uses Stripe Checkout exclusively.
21. Credential update process works correctly — updating questions requires PIN, updating PIN requires 2 of 4 questions.

---

## 12.5 Staff Back Office

22. All account lookup search criteria return correct results.
23. All staff-initiated account actions work correctly — plan changes, seat adjustments, suspension, unsuspension, cancellation, unlock, password reset, refund, and manual provisioning.
24. Administrator unlock requires completed identity verification and cannot be bypassed.
25. Every staff action generates a correctly structured SDP audit log entry.

---

## 12.6 Transactional Communications

26. All nine email events fire correctly on their triggering conditions.
27. The data deletion warning email is scheduled and sent correctly 14 days before permanent deletion.
28. Email delivery failures are logged and staff are alerted.

---

## 12.7 Data Retention & Cleanup

29. Tenant data in SDTA is permanently deleted after the 60-day grace period expires.
30. SDP audit log and billing records are retained for 36 months on a rolling basis.
31. Account reactivation within the 60-day grace period fully restores SDTA access and data.

---

## 12.8 Integration with SDTA

32. SDP correctly provisions and initializes a new SDTA tenant account atomically on signup.
33. SDTA correctly reads plan status, seat limits, and storage limits from SDP at runtime.
34. SDTA correctly notifies SDP of seat changes and storage usage updates.
35. SDP account status changes (suspension, cancellation, reactivation) are reflected in SDTA immediately.

---

**End of ServizmaDesk Platform (SDP) V1 Specification**