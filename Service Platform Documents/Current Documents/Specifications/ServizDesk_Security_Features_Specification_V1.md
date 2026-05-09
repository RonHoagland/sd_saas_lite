# ServizDesk — Security Features Specification V1
**Document Version:** V1
**Status:** Working Draft
**Date:** March 2026
**Classification:** Internal — Confidential
**Scope:** ServizDesk Tenant App (SDTA) — Tenant-Facing Security Controls

---

## Document Purpose

This document defines the complete set of security features available to ServizDesk tenant Administrators. It serves two purposes: an internal reference for implementation, and a basis for customer-facing security communications. The central promise of ServizDesk's security model is:

> **"ServizDesk gives you the tools to protect your data. The controls are in your hands."**

This document covers the administrator-controllable protections, the infrastructure-level protections that run automatically, and the data isolation guarantees that apply to every tenant regardless of configuration.

---

# 1. Administrator-Controlled Security Features

These settings are accessible to the **Administrator role only**, located in the Organization Security section of Settings. Standard users and Read-Only users have no access to these controls.

## 1.1 Multi-Factor Authentication (MFA)

| Setting | Location | Default |
|---------|----------|---------|
| `Require MFA for all employees` | Settings → Security | Off |

When enabled, every employee in the organization must complete a second verification step after entering their password. MFA applies to all roles — no employee is exempt when the organization setting is on.

**Method:** An OTP (one-time passcode) is sent via SMS to the employee's registered MFA phone number. If SMS is unavailable, or the employee requests it, the OTP is sent to their registered work email address instead. OTP codes expire after 10 minutes and can only be used once.

**UI Recommendation:** The Settings page prominently displays a recommendation to enable MFA. The recommendation remains visible until the setting is turned on.

**What this protects against:** A stolen or guessed password alone is not enough to access the account. An attacker who obtains an employee's credentials still cannot log in without also controlling the employee's phone or email.

**MFA Recovery (employee loses access to phone and email):** If an employee cannot receive the OTP through either channel, an Administrator can temporarily disable MFA for that individual employee, allow them to log in, update their MFA phone number or email address, and then re-enable MFA. This recovery action is recorded in the audit log. The Administrator's own account is not subject to this bypass — Administrator recovery always goes through the ServizDesk Platform (SDP) using their Security PIN.

## 1.2 Session Timeout

| Setting | Location | Default | Range |
|---------|----------|---------|-------|
| `Session timeout` | Settings → Security | 30 minutes | 15 min – 8 hours |

Controls how long an employee can remain idle before being automatically logged out. On timeout, the employee is returned to the login page. Their work is not lost — drafts and open forms are preserved in most views.

**What this protects against:** Unattended workstations. If an employee walks away from a shared computer without logging out, the session expires automatically.

## 1.3 Force Session Revocation

Session revocation immediately terminates all active sessions for an employee across every device and browser. The employee is forced back to the login screen on their next request, typically within seconds. It happens in two ways:

**Manual — Administrator action:**

| Action | Location | Who Can Use |
|--------|----------|-------------|
| `Force Logout All Devices` | Settings → Employees → [Employee record] | Administrator only |

Use this for a suspected compromised account (stolen phone, leaked password) or any situation where an Administrator needs immediate certainty that an employee can no longer access the system.

**What this does not do:** Manual revocation does not lock the account or change the password. If a password compromise is also suspected, combine Force Logout with a forced password reset.

**Automatic — Status change:**

When an employee's status is set to `Terminated`, `On Leave`, or `Inactive`, all their active sessions are **automatically revoked at the moment the status change is saved** — no separate manual action is required. For terminated employees this means access ends instantly, not at the next natural session expiry (which could be up to 8 hours later).

| Status Change | Sessions Revoked | Can Log Back In |
|--------------|-----------------|----------------|
| → On Leave | ✓ Immediately | No — while On Leave |
| → Inactive | ✓ Immediately | No — while Inactive |
| → Terminated | ✓ Immediately | No — while Terminated |

**Audit trail:** Every revocation — manual or automatic — is recorded in the audit log with the responsible Administrator's name, the affected employee, the trigger (manual or status change), and the timestamp.

## 1.4 Account Lockout

Account lockout is automatic and does not require administrator configuration. After **5 consecutive failed login attempts**, the employee account is locked. Locked accounts **auto-unlock after 30 minutes**, or can be immediately unlocked by an Administrator from the employee's record — whichever comes first.

The lockout system catches two distinct attack patterns: a single IP repeatedly targeting one account, and distributed attacks where many different IP addresses each make a small number of attempts against the same account. Both patterns trigger a lockout.

For Administrator accounts that are locked and cannot be unlocked internally, recovery is available through the ServizDesk Platform (SDP) using the Administrator's Security PIN.

> **Clarification — Two Separate Lockout Mechanisms:**
> 1. **Account lockout** (5 consecutive failed password attempts): Blocks the login form entirely. 30-minute auto-unlock or administrator manual unlock.
> 2. **MFA session lockout** (3 consecutive failed OTP attempts): Invalidates the current intermediate authentication token. The user must restart the login process from the password step. Does not trigger account lockout.
> These are independent counters. A user who passes the password step but fails MFA 3 times is not locked out of their account — they simply need to re-enter their password and request a new OTP.

## 1.5 Login Attempt Audit Log

| Feature | Location | Who Can View |
|---------|----------|-------------|
| Login attempt history | Settings → Employees → [Employee record] → Login History | Administrator only |

Every login attempt for every employee is recorded — successful logins, failed attempts, MFA completions, and MFA failures. Each entry shows the date and time, IP address, device type, browser, and outcome.

**What this gives you:** Visibility into suspicious patterns. If an employee account is being targeted — repeated failures from an unusual IP, logins from unexpected locations — Administrators can see it and take action before a breach occurs.

---

# 2. Automatic Infrastructure Protections

These protections run automatically for all tenants and require no configuration. They cannot be turned off.

## 2.1 Brute-Force Rate Limiting (Two Layers)

Login, password reset, and MFA verification endpoints are protected by two independent rate limiting systems:

**Layer 1 — Network level (Nginx):** Limits the raw number of requests per IP address before they reach the application. Blocks volumetric attacks — automated bots hammering the login page — without consuming application resources.

**Layer 2 — Application level (django-axes):** Tracks failed login attempts by both IP address and username. This catches credential stuffing attacks that distribute requests across thousands of different IP addresses to avoid per-IP limits. If 5 failures are recorded for a specific account regardless of how many different IPs were used, the account is locked.

Together, these two layers address both bulk automated attacks and targeted account attacks.

## 2.2 HTTPS Everywhere

All connections to ServizDesk are encrypted with TLS. Unencrypted HTTP connections are redirected to HTTPS automatically. Credentials, session tokens, and all data in transit are always encrypted.

## 2.3 Secure Session Cookies

Session cookies are configured with three mandatory security attributes:

- **Secure** — the cookie is only transmitted over HTTPS, never over plain HTTP
- **HttpOnly** — the cookie cannot be read by JavaScript, preventing theft via cross-site scripting
- **SameSite: Lax** — the cookie is not sent with cross-site requests, preventing cross-site request forgery attacks

## 2.4 CSRF Protection

All state-changing requests (form submissions, record creation, updates, deletions) require a valid CSRF token. This prevents malicious third-party websites from tricking an authenticated employee's browser into making unauthorized requests to ServizDesk.

## 2.5 Session Fixation Prevention

When an employee successfully logs in, ServizDesk issues a brand-new session token and discards the pre-login token. This prevents "session fixation" attacks, where an attacker pre-plants a session token and waits for a legitimate user to authenticate with it.

## 2.6 Account Enumeration Prevention

The password reset form always returns the same response — "If an account exists for that email, you'll receive a reset link shortly" — whether or not the submitted email address matched a registered employee. This prevents attackers from using the reset form to discover which email addresses have accounts in your organization.

## 2.7 Password Reset Token Expiry

Password reset links expire after **24 hours**. If an employee does not use the reset link within that window, it becomes permanently void and a new request must be made. Django's default expiry is 3 days — ServizDesk overrides this to 24 hours, which is the industry standard for business applications handling financial data.

Reset tokens are also **single-use** — once a link is clicked and the password is reset, the same link cannot be used again. This prevents replay attacks where an old reset email is used to take over an account after the fact.

## 2.8 Real-Time Push Event Channel Security (Pusher Private Channels)

ServizDesk uses Pusher for real-time UI notifications. All Pusher channels are **private** — before a browser is allowed to subscribe to any event channel, it must authenticate with the ServizDesk server. The server applies two layers of verification before granting access:

**Layer 1 — Tenant isolation.** The server verifies the user is logged in and that the channel belongs to their organization. Unauthenticated clients and clients from other tenants cannot subscribe to your organization's event channels under any circumstances.

**Layer 2 — Per-user channel isolation.** For personal notification channels (which carry notifications directed at a specific employee), the server additionally verifies that the `user_id` embedded in the channel name matches the authenticated user. This means an employee cannot subscribe to a co-worker's personal notification channel, even within the same organization. Organization-wide event channels (service requests, payments, alerts) are accessible to all authenticated members of the organization.

## 2.9 HTTP Security Headers

Every response from ServizDesk includes a set of browser-enforced security headers that provide defence against the most common web-based attacks. These apply to all pages and endpoints automatically.

| Header | Protection |
|--------|-----------|
| `X-Frame-Options: DENY` | **Clickjacking** — prevents your ServizDesk pages from being embedded in an iframe on any other website. An attacker cannot overlay an invisible iframe over a legitimate site to trick logged-in users into clicking buttons they can't see. |
| `X-Content-Type-Options: nosniff` | **MIME sniffing** — forces the browser to treat files as their declared type only. Prevents a maliciously crafted file from being executed as a script even if it was uploaded with a spoofed extension. |
| `Strict-Transport-Security` | **Protocol downgrade / SSL stripping** — instructs browsers to always connect to ServizDesk over HTTPS, even if a user types `http://`. Covers all tenant subdomains. Effective for 1 year per visit, auto-renewing. |
| `Referrer-Policy` | **URL leakage** — when an employee follows a link to an external site, only the domain name is shared, not the full URL. Record IDs and path information in ServizDesk URLs are not exposed to third parties. |
| `Permissions-Policy` | **Browser feature restriction** — explicitly disables camera, microphone, and geolocation access in the browser for ServizDesk pages. These APIs are not used and cannot be triggered. |
| `Content-Security-Policy` | **Script and resource injection** — controls exactly which scripts, styles, and external connections the browser is permitted to make. Prevents injected malicious scripts from executing even if an XSS vulnerability were somehow introduced. |

## 2.10 Secure File Access — Pre-Signed URLs

All files uploaded to ServizDesk are stored in a **private** object storage bucket. No file can ever be accessed via a direct storage URL — the bucket has no public read access. Every file download goes through a Django endpoint that performs three checks before issuing a temporary access link:

1. **Authentication** — the requesting user must be logged in.
2. **Tenant ownership** — the file must belong to the requesting user's organization. A user from one organization cannot obtain access to another organization's files, even if they somehow know the file's internal identifier.
3. **Virus scan gate** — only files that have passed virus scanning can be accessed. Files pending scan or flagged as infected cannot be downloaded.

Only after all three checks pass does the server generate a **pre-signed URL** — a time-limited, cryptographically signed link that grants access to one specific file for 15 minutes. The link expires automatically. It cannot be extended or reused once expired.

The file's internal storage path (S3 key) is never returned to the browser. The browser only ever sees a `document_uuid`, and the server resolves that to a storage path server-side. This prevents storage path enumeration.

## 2.11 Redis Security (Task Queue Isolation)

ServizDesk uses Redis as the message broker for its background task queue (Celery). Three mandatory controls protect the Redis instance in all staging and production environments.

**Internal network only.** Redis is bound to the private VPC network interface and is never reachable from the public internet. The Redis port is not open in any public firewall rule. No external client can connect to the Redis instance directly.

**Authentication required.** Redis requires a strong password (`requirepass`). Any client — including Celery workers and Django — must authenticate before issuing any commands. The password is stored as a secret environment variable and is never hardcoded.

**TLS on all connections.** All connections to Redis use TLS encryption (`rediss://` scheme). Task payloads, which can contain tenant identifiers and operational data, are never transmitted in plaintext.

**What this protects against:** An unsecured, publicly accessible Redis instance is one of the most common attack vectors in web applications. Without these controls, an attacker who discovers the Redis host could read queued task payloads, inject malicious tasks onto the worker queue, or issue destructive commands (such as flushing all pending tasks). The combination of network isolation, authentication, and TLS closes all three attack surfaces.

## 2.12 Application Signing Key (Django SECRET_KEY)

Django uses a master signing key — the `SECRET_KEY` — as the cryptographic root of trust for the application. It is used internally to sign session cookies, CSRF tokens, password reset links, and all other server-generated signed values. It is never exposed to users or transmitted over the network.

Three requirements govern how this key is handled:

**Environment variable only.** The key is loaded from a secure environment variable at startup. It is never written into the application's source code or configuration files, and it is never committed to version control. Storing it in code would mean anyone with repository access could forge sessions and tokens.

**Unique per environment.** Development, staging, and production each have a completely different key. This ensures that a key leaked from a development machine has no effect on production accounts.

**Vault-stored.** The production key is stored in the same secrets vault as database passwords and API credentials. It is injected at deployment and is not present in plaintext on any server disk.

**What happens if the key is rotated or compromised:** Replacing the `SECRET_KEY` with a new value immediately invalidates every active session (all users are logged out) and every outstanding password reset link system-wide. This is intentional — key rotation is a security incident response tool. If the key is ever suspected to be exposed, rotating it is the fastest way to neutralise any forged sessions or tokens without needing to identify individual affected accounts.

---

# 3. Data Isolation Guarantee

Every tenant's data is isolated at multiple independent layers. No configuration is required — these guarantees apply to every tenant automatically and cannot be disabled.

## 3.1 Three-Layer Isolation Model

| Layer | Where | Mechanism |
|-------|-------|-----------|
| **Field Constraint** | Database | Every data record has a mandatory organization identifier. A record without this identifier cannot exist in the database. |
| **Application Filter** | Application | Every database query automatically includes an organization filter. A query that returns another organization's data cannot be constructed through normal application use. |
| **Row-Level Security (RLS)** | Database engine | PostgreSQL enforces a policy at the database level that physically prevents the application's database user from reading or writing another organization's rows — even if the application layer were completely bypassed. |

## 3.2 What This Means in Practice

If a user account in your organization is compromised:

- The attacker can only access data that belongs to your organization. They cannot see data belonging to any other ServizDesk customer, regardless of what they attempt.
- SQL injection attacks, if they somehow occurred, would still be subject to the database-level RLS policy. The database engine itself refuses to return another tenant's data.
- The only path to cross-organization data access would require compromising ServizDesk's own infrastructure credentials, which are vault-locked and never present in the running application.

## 3.3 Database Role Architecture

| Role | Access | RLS |
|------|--------|-----|
| Application runtime (`sdta_app`) | Your organization's data only | Subject to RLS |
| Reporting/read-only (`sdta_readonly`) | Your organization's data only | Subject to RLS |
| Migration/DDL (`sdta_migration`) | Schema changes only — not used at runtime | BYPASS (required for migrations) |
| Support staff (`sdta_support`) | Cross-organization DML for servicing — vault-locked, issued individually, rotated after use | BYPASS |
| Superuser (`postgres`) | Initial setup only — locked in vault after setup | N/A |

---

# 4. Audit & Visibility

ServizDesk maintains comprehensive, immutable logs so that Administrators always know what happened in their organization.

| Log | Contents | Retention | Who Can View |
|-----|----------|-----------|-------------|
| `SystemAudits` | Every significant action — record creation, deletion, status changes, financial actions (invoices issued/voided, payments applied) | 18 months rolling | Administrator |
| `SessionLog` | Every authenticated session — login time, device, IP, MFA method, permissions at login | 18 months rolling | Administrator |
| `LoginAttemptLog` | Every login attempt — success or failure, reason for failure, IP address, device | 18 months rolling | Administrator |

Audit records are immutable once written. The application database user has `UPDATE` and `DELETE` revoked on audit tables — records cannot be altered or deleted through normal application use.

---

# 5. Security Feature Summary (Customer-Facing Reference)

| Feature | Available | Administrator-Controlled |
|---------|-----------|-------------------------|
| Multi-Factor Authentication (SMS + Email fallback) | ✓ | ✓ — on/off per organization |
| Configurable session timeout (15 min – 8 hours) | ✓ | ✓ |
| Account lockout after 5 failed attempts | ✓ | Automatic |
| Force logout all devices for any employee | ✓ | ✓ — Admin action |
| Login attempt audit log | ✓ | View-only |
| Complete session history per employee | ✓ | View-only |
| SystemAudits — who did what and when | ✓ | View-only |
| Brute-force rate limiting (network + application) | ✓ | Automatic |
| HTTPS / TLS encryption on all connections | ✓ | Automatic |
| Secure, HttpOnly, SameSite session cookies | ✓ | Automatic |
| CSRF protection on all requests | ✓ | Automatic |
| Account enumeration prevention | ✓ | Automatic |
| Password reset tokens expire in 24 hours (single-use) | ✓ | Automatic |
| Tenant data isolation (3-layer RLS) | ✓ | Automatic |
| Pusher Private Channel authentication | ✓ | Automatic |
| HTTP security headers (anti-clickjacking, HSTS, CSP, MIME protection) | ✓ | Automatic |
| Redis task queue: internal network only, authenticated, TLS-encrypted | ✓ | Automatic |
| File downloads via pre-signed URLs (15-min expiry, tenant-verified) | ✓ | Automatic |
| Private S3 bucket — no public file access | ✓ | Automatic |
| Application signing key (SECRET_KEY): vault-stored, env-only, unique per environment | ✓ | Automatic |

---

# 6. Document Relationships

| Relationship | Document |
|---|---|
| Authentication implementation | ServizDesk Technical Architecture V2, Section 8 |
| Database role architecture | ServizDesk Database Specification V2, Section 3 |
| Session revocation implementation | ServizDesk Permission Management Specification V2, Section 12 |
| Data model definitions (MFA, SessionLog, LoginAttemptLog) | ServizDesk Data Models V6 |
| Multi-tenancy isolation implementation | ServizDesk Multi-Tenancy Specification V1 |
| Redis security requirements | ServizDesk Technical Architecture V2, Section 6.5.1 |
| Rate limiting configuration | ServizDesk Technical Architecture V2, Section 8.7 |
| File access security (pre-signed URLs) | ServizDesk File Upload Specification V1, Section 5; ServizDesk Technical Architecture V2, Section 6.4.1 |
| Django SECRET_KEY requirements | ServizDesk Technical Architecture V2, Section 8.9 |

---

*End of ServizDesk Security Features Specification V1*
