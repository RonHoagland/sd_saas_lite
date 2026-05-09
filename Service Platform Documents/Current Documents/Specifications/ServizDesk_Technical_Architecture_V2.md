# ServizDesk Technical Architecture
**Document Status:** Working Draft
**Document Version:** V2
**Classification:** Internal — Technical Dependency
**Last Updated:** March 2026

---

# 1. Executive Summary

This document defines the complete technical architecture, technology stack, infrastructure, and third-party integrations required to build and deploy the ServizDesk software suite. It serves as the foundational engineering blueprint for both the **ServizDesk Platform (SDP)** and the **ServizDesk Tenant App (SDTA)**.

All technical decisions listed here are aligned with and validated against the following specification documents:

- ServizDesk Product Tier Map V2
- ServizDesk Lite MVP V4 Specification
- ServizDesk Platform (SDP) Specification V2
- ServizDesk Pricing & Billing Specification V2
- ServizDesk SDTA Data Models V6

This document supersedes the open technical decisions listed in Section 10 of the Product Tier Map V2. Those decisions are now codified herein. This document also supersedes Technical Architecture V1.

---

# 2. Application Architecture Overview

The ServizDesk ecosystem consists of two distinct Django applications deployed on shared infrastructure but maintaining completely isolated databases and codebases.

## 2.1 ServizDesk Platform (SDP)

SDP is the central control system and back-office for the entire ServizDesk product family. It is not a customer-facing product; it is an internal operations platform with a limited self-service surface for signup, billing management, and account recovery.

SDP serves five roles:

- **Gatekeeper** — no tenant account exists in any ServizDesk application without SDP provisioning it first
- **Single Source of Truth** — authoritative record for every customer account, plan status, seat counts, storage limits, and security credentials
- **Billing System** — all customer charges flow through SDP via the ServizDesk Stripe account
- **Security Authority** — Administrator security credentials (PIN and security questions) are stored exclusively in SDP and never replicated to SDTA
- **Staff Operations Hub** — all account management actions performed by ServizDesk staff

SDP runs as two functional surfaces within a single Django application:

- **Customer-facing surface** — self-service signup, billing portal, account management, Administrator account recovery
- **Staff-facing back office** — ServizDesk staff tools for account management, support, and operations

## 2.2 ServizDesk Tenant App (SDTA)

SDTA is the customer-facing field service management application. It is the product that tenants use daily to manage their service business — customers, assets, quotes, work orders, invoices, and payments.

SDTA is a multi-tenant application. All tenants share the same database schema and application codebase, with data isolation enforced at three distinct layers (see Section 5). SDTA contains three completely distinct UI parts — one for Lite, one for Plus, and one for Pro — routing users to the UI corresponding to their active plan.

## 2.3 Application Boundary Rules

- SDP and SDTA maintain completely separate PostgreSQL databases on the same database server instance
- Neither application may write to the other's database under any circumstances
- All inter-application communication occurs exclusively via the Internal REST API (see Section 7)
- Direct database reads across application boundaries are strictly prohibited

---

# 3. Core Technology Stack

## 3.1 Backend Framework

| Component | Selection |
|-----------|-----------|
| Language | Python 3.12+ |
| Framework | Django 6.x |
| Application Philosophy | Fat Models, Thin Views — business logic resides in the model layer or dedicated service classes, never directly in views |
| Password Hashing | bcrypt or Argon2 (Django's PBKDF2 default is acceptable minimum) — plaintext storage is strictly prohibited across SDP and SDTA |

## 3.2 Frontend Stack

| Component | Selection |
|-----------|-----------|
| Rendering Architecture | Server-Side Rendered (SSR) HTML via Django Templates |
| Dynamic Interactions | HTMX v2.x — Alpine.js and Hyperscript are explicitly ruled out to keep the frontend bundle minimal and strictly driven by Django templates |
| Styling Engine | **Bootstrap 5.3** — provides pre-built accessible components (offcanvas/drawer, modal, tabs, forms, tables, toasts, nav). No build step required; vendor or CDN-included CSS + bundle JS. A small `static/css/site.css` carries ServizDesk-specific branding (colors, spacing overrides) via Sass variable or direct overrides. Vanilla CSS beyond `site.css` is discouraged. |
| Icons | Lucide (via `lucide.min.js`) — current standard across all ServizDesk templates |
| PDF Output (Lite) | CSS Print Media Queries — developers must write robust `@media print` CSS rules so that browser-printed invoices and quotes produce clean, stripped-down 8.5x11 output without UI chrome, navigation, or buttons |
| PDF Generation (Plus/Pro) | WeasyPrint (Python library) — the designated server-side PDF engine when automated PDF generation is introduced in Plus/Pro tiers; the codebase must use WeasyPrint exclusively for this purpose |
| Live / Real-Time Updates | **HTMX polling** for periodic board/counter refresh. **Pusher** for push event notifications. **SSE (Server-Sent Events) and WebSockets are explicitly prohibited** — persistent server-side connections are incompatible with PgBouncer transaction mode and add unnecessary infrastructure complexity. See Section 6.6. |

### Frontend evolution — React as a post-release option

Bootstrap 5 + HTMX is the frontend stack across all tiers (Lite → Plus → Pro → Enterprise) through initial release. React is **not pre-committed**. It is a post-release option, considered only when a specific capability gap appears that Bootstrap/HTMX plus targeted libraries (FullCalendar, Chart.js, SortableJS, Alpine.js) cannot cover. Trigger conditions include: offline / local-first capability (PWA), heavy real-time multi-user collaboration on the same record, complex client-side state that outlives a page (undo stacks, virtualized scroll with sticky filters, cross-page drag-drop), or a native mobile app built with shared React Native components. The backend REST API (200+ DRF endpoints) already supports an eventual React frontend — the option stays open without being pre-paid.

**Superseded guidance:** earlier versions of this document named Tailwind CSS as the styling engine. That decision was reversed on 2026-04-24; see `Architecture & Planning/LITE_DECISIONS.md` §I for rationale.

## 3.3 Database Layer

| Component | Selection |
|-----------|-----------|
| Database Engine | PostgreSQL 16+ |
| Primary Keys | UUIDv4 is mandatory for all primary and foreign keys globally — auto-incrementing integers are strictly prohibited to support future offline-mobile syncing |
| Tenant Isolation Field | `tenant_id` (UUID) — non-nullable on every tenant-scoped table in SDTA |
| Row-Level Security | PostgreSQL RLS is enabled on all SDTA tables as the final enforcement layer |
| ORM | Django ORM with a custom model manager that automatically injects `tenant_id` scoping on all querysets |
| SQLite Usage | Strictly prohibited in all environments including local development — SQLite does not support PostgreSQL RLS and breaks the required isolation architecture |
| Generic Foreign Keys (GFKs) | Prohibited — Django's content-types framework is not used; RLS enforcement requires explicit foreign keys |

---

# 4. Infrastructure & Hosting

## 4.1 Cloud Provider & Compute

| Component | Selection |
|-----------|-----------|
| Cloud Provider | DigitalOcean (recommended for bootstrapped scaling; migration to AWS deferred until scale warrants it) |
| Compute | DigitalOcean Droplets (Ubuntu 22.04 LTS+) or DigitalOcean App Platform |
| Web Server | Nginx — acts as reverse proxy and static file server |
| Application Server (WSGI) | Gunicorn — WSGI HTTP server serving the Django application |
| Redis | Managed Redis instance on DigitalOcean (preferred) or a dedicated standard Droplet — running Redis on the same Droplet as the web server is prohibited |
| Domains | ServizDesk.com (primary), Servizma.com (redirects to ServizDesk.com) |

## 4.2 Environment Strategy

Three environments are required and must be maintained concurrently:

| Environment | Purpose and Configuration |
|-------------|--------------------------|
| Local Development | Docker/Docker Compose workflow spinning up Django, PostgreSQL 16+, and Redis together. SQLite is banned. Stripe Test Mode. Local filesystem for media storage (`MEDIA_ROOT` via `FileSystemStorage`) to avoid object storage friction and unnecessary API costs during development. Both SDP and SDTA run locally. |
| Staging | Dedicated exact replica of production architecture on a separate subdomain (e.g., `staging.servizdesk.com`). Connected to Stripe Test Mode for all pre-deployment validation. Both SDP and SDTA must maintain mirrored staging instances. |
| Production | Full production environment. Stripe Live Mode. DigitalOcean Spaces for object storage. Managed Redis. Fully hardened configuration. |

## 4.3 Configuration Management

All secrets and environment-specific configuration must be injected as environment variables. The `python-decouple` library (or equivalent) must be used for all settings. Hardcoded secrets in `settings.py` are strictly prohibited in all environments.

## 4.4 Infrastructure Scaling Plan

| Stage | Tenant Volume | Estimated Monthly Infrastructure Cost |
|-------|---------------|---------------------------------------|
| Pre-Launch | 0 (dev + staging) | ~$100/month |
| Stage 2 | 10–30 tenants | ~$250–$350/month |
| Stage 3 | 50+ tenants | ~$500–$800/month |
| Stage 4 | 100+ tenants | ~$1,000–$1,500/month |

> **Deployment Requirement:** PgBouncer **must** be configured in **transaction mode**. Session mode will cause `SET LOCAL app.current_tenant_id` to leak between requests, silently breaking RLS tenant isolation. See Database Specification V2 Section 4.3 for pooler configuration.

---

# 5. Multi-Tenancy Architecture (SDTA)

ServizDesk uses a **Shared Database, Shared Schema** multi-tenant architecture. All tenants share the same tables. Data isolation is the responsibility of the application and database layers, not schema separation.

## 5.1 Three-Layer Isolation Model

Tenant isolation is enforced at three distinct and independent layers. All three layers must be present and functioning simultaneously. No single layer is sufficient on its own.

| Layer | Mechanism | Description |
|-------|-----------|-------------|
| Layer 1 | Database Field Constraint | Every table in SDTA contains a non-nullable `tenant_id` (UUID) foreign key. This is an absolute architectural mandate — no table may be created without this field. |
| Layer 2 | Django Application Middleware | A custom Django middleware extracts the `tenant_id` from the authenticated user's session and automatically scopes all ORM queries to that specific tenant using a custom model manager. For implementation details, see the ServizDesk Multi-Tenancy Specification V1. |
| Layer 3 | PostgreSQL Row-Level Security (RLS) | RLS is enabled on all tables in the PostgreSQL database. This is the final failsafe. Even if a developer accidentally writes a raw SQL query that bypasses the Django ORM, the database user itself is scoped to the current tenant. It is physically impossible for tenant A to query tenant B's data. |

## 5.2 Tier-Gating Implementation

Feature access is gated at two layers to prevent unauthorized access to higher-tier capabilities:

- **Backend Enforcement (Primary Shield):** A custom `@tier_required('plus')` decorator is applied to Django view functions. If a Lite-tier user attempts to access a Plus view via direct URL manipulation, the system raises a `TierUpgradeRequired` exception. This is the enforcement layer that cannot be bypassed.
- **Frontend UI (Secondary Shield):** Django Template Conditionals (`{% if request.tenant.tier == 'plus' %}`) are used to conditionally render, gray out, or hide UI elements. This guides user behavior and prevents exposure of broken application states, but is not the primary security mechanism.

The SDTA database schema is designed upfront to contain all tables required for all tiers. Tables for Plus and Pro features (such as Locations, Purchase Orders, Leads, and Opportunities) exist in the database from day one, even though the Lite UI does not expose them. Upgrading a tenant changes which UI part is served and which controllers permit writes — it does not require a database migration.

## 5.3 Distinct UI Parts Per Tier

There are three completely distinct UI parts built for SDTA — one for Lite, one for Plus, and one for Pro. The application routes the user to the UI part corresponding to their active plan. Backend controllers explicitly reject any write request to a higher-tier feature if the tenant's current plan does not allow it.

## 5.4 Tenant State Synchronization

SDTA maintains local `TenantState` and `TenantAddOn` tables that cache the tenant's current tier, seat limit, account status, and active features/add-ons. This local cache eliminates the need to call the SDP API on every page load. The cache is updated via webhooks or background workers when SDP changes a tenant's account state. All enforcement decisions in SDTA (tier-gating, seat limits, storage limits, add-on feature gating) are made against this local cache.

---

# 6. Third-Party Integrations & Services

## 6.1 Payment Processing — Stripe

Stripe is the exclusive payment processing platform for ServizDesk. Two distinct Stripe integration patterns are used depending on the payment context.

| Context | Integration Type | Purpose |
|---------|-----------------|---------|
| ServizDesk Corporate Billing (SDP) | Stripe Billing + Stripe Checkout | Used to charge tenants their monthly or annual subscription fees, seat additions, and storage add-ons. Stripe Checkout is used for all card collection — custom card entry forms that post card data to SDP servers are strictly prohibited. Maintains SAQ A PCI compliance. |
| Tenant Payment Processing (SDTA) | Stripe Connect (Standard Integration) | Tenants securely link their own Stripe accounts via OAuth in Plus and above. SDTA generates Stripe Payment Links via the Stripe API for tenant invoices. No embedded card forms are used in Lite. |

- **Application Fee (Stripe Connect):** ServizDesk charges a **0.5% application fee** on all tenant payment transactions processed through Stripe Connect. This fee is collected automatically by Stripe on each transaction and remitted to ServizDesk. See Pricing & Billing Specification V2 Section 9.3.
- **SDK:** Official Stripe Python SDK (`stripe>=11.0.0`)
- **PCI Compliance:** ServizDesk operates as an SAQ A merchant. Raw card data never touches ServizDesk servers at any layer. SDP stores only Stripe-provided tokenized references: Customer ID, Subscription ID, Payment Method ID, last 4 digits, card brand, expiry month/year.
- **What is Never Stored:** Full card number (PAN), CVV/CVC, raw card data of any kind, magnetic stripe data.
- **Webhook Security:** All incoming Stripe webhooks must verify the cryptographic signature using `STRIPE_WEBHOOK_SECRET` before parsing the payload. All webhook endpoints must be fully idempotent — safe to process the same event twice.
- **Proration:** Stripe manages all proration calculations for mid-cycle seat changes and storage add-on changes. ServizDesk does not perform independent proration calculations.

## 6.2 Transactional Email — Postmark

Postmark is the exclusive transactional email provider for all ServizDesk system-generated emails.

| Scope | Details |
|-------|---------|
| Managed Emails | Welcome email on account creation; password reset links for employees; provisioning success/failure notifications; payment failure alerts; account suspension warnings; data deletion warnings (7-day pre-deletion notice); critical system alerts to ServizDesk staff |
| Lite Tier Scope | SDTA does not send emails on behalf of tenants in the Lite tier. Tenant-to-customer communication in Lite is handled by tenants from their own email clients. |
| Plus/Pro/Enterprise Tenant Email | Point-based system. 1 point = 1 outbound email. Default mode sends from ServizDesk's platform domain via Postmark. Custom Domain authentication (emails from tenant's own domain via DNS-verified Postmark) is a paid add-on on Pro and Enterprise. BYOS (Bring Your Own SMTP) is not supported. See Pricing & Billing Specification V2 Section 10A and 11.4, and Email Specification V1. |
| Delivery Logging | All platform emails are tracked in the `EmailDeliveryLog` table capturing delivery status and hard bounces. |

## 6.3 SMS / Telephony

> **Scope clarification — tenant-to-customer SMS vs. platform MFA SMS:** This section covers **tenant-to-customer outbound SMS** (appointment reminders, notifications, etc.). It is separate from **platform-level SMS delivery for MFA authentication** (Section 8.1). MFA OTP delivery via SMS is a platform security function that operates independently of the tenant's SMS entitlement. Twilio must be provisioned for MFA delivery regardless of tier — even a Lite tenant whose Administrator has enabled MFA requires SMS OTP delivery.

Tenant-to-customer outbound SMS is available on all tiers via the point system. See Pricing & Billing Specification V2 Section 10 for the authoritative allocation and pricing details.

| Item | Status |
|------|--------|
| Lite Tier Tenant SMS | 100 points/month included. Manual outbound only — no automated triggers. See Pricing & Billing Specification V2, Section 10. |
| Plus/Pro Tenant SMS | Point-based system. 1 point = 1 outbound SMS segment. Plus includes 350 points/month; Pro includes 750 points/month. Automated triggers included. Overage charged at $0.035/point. Point packages available post-launch after usage patterns are confirmed. See Pricing & Billing Specification V2 Section 10. |
| Provider Selection | Twilio (A2P 10DLC). ServizDesk registers as the ISV brand; each tenant registered as a campaign under the ServizDesk A2P umbrella. Twilio must also be provisioned for platform-level MFA SMS delivery (all tiers). |
| International SMS | Pricing and point multipliers deferred to Plus specification. |

## 6.4 File & Attachment Storage — DigitalOcean Spaces

| Item | Details |
|------|---------|
| Production Provider | DigitalOcean Spaces (S3-compatible object storage). AWS S3 is an acceptable alternative if migration is warranted. |
| Django Integration | `django-storages` with the `boto3` backend. All `FileField` and `ImageField` uploads are routed automatically to the object storage bucket in production. |
| Local Development | Standard local filesystem (`MEDIA_ROOT` via `FileSystemStorage`) to avoid friction and unnecessary API costs during development. |
| Prohibited Pattern | Storing tenant attachments on the production server's local filesystem is strictly prohibited. It prevents horizontal scaling and risks filling the server disk. |
| Storage Tracking | A `StorageTracker` table maintains a running tally of total bytes consumed per tenant. This eliminates the need to query object storage on every page load to enforce tier storage caps. |
| Lite Storage Cap | 3 GB included. In-app alerts at 80% and 100% usage. Uploads blocked at 100%. Add-ons: +3 GB ($10/month), +4 GB ($15/month). Maximum: 10 GB. |
| Plus Storage Cap | 10 GB included. Maximum 75 GB. Add-ons: +15 GB ($25/month), +25 GB ($45/month), +25 GB ($60/month). |
| Pro Storage Cap | 25 GB included. Maximum 500 GB. Add-ons: +25 GB ($40/month), +25 GB ($55/month), +25 GB ($100/month), +400 GB ($200/month). |
| Enterprise Storage Cap | 50 GB included. Maximum 1,500 GB. Add-ons: +50 GB ($75/month), +250 GB ($175/month), +500 GB ($300/month), +750 GB ($450/month). |

### 6.4.1 Secure File Access — Pre-Signed URLs

The S3/Spaces bucket is configured with **no public access**. All objects are private by default. Files can only be accessed through Django-issued pre-signed URLs.

**Why direct S3 URLs are prohibited:** A raw object storage URL would make tenant files accessible to anyone who knows the path, with no authentication check and no expiry. The tenant-scoped path format (`/tenant-{uuid}/...`) does not provide security — it is obscurity only, and obscurity is not access control.

**The access flow:**

Every file download or inline preview goes through a Django endpoint (`GET /files/<document_uuid>/download/`). Django looks up the `Document` record, verifies the requesting user is authenticated and belongs to the same tenant as the document, verifies the file has passed virus scanning (`scan_status = Clean`), then calls `boto3` to generate a signed URL with a 15-minute expiry. Django returns a 302 redirect to the signed URL. The S3 object key is never returned directly to the client.

**Key constraints:**

| Constraint | Value |
|-----------|-------|
| Pre-signed URL expiry | 15 minutes |
| Bucket visibility | Private — no public ACL on any object |
| `file_key` exposure | Never included in API responses or HTML. Only `document_uuid` is sent to the frontend. |
| Tenant verification | `Document.tenant_id` must match `request.user.tenant_id` before any URL is generated |
| Scan gate | Only `scan_status = Clean` files are eligible |
| URL caching | Pre-signed URLs are generated fresh on each request — never stored |

## 6.5 Asynchronous Workers — Celery + Redis

Tasks that must not block the web response cycle are handled by Celery workers consuming from a Redis message broker.

| Component | Details |
|-----------|---------|
| Message Broker | Redis — Managed Redis instance on DigitalOcean in production. Running Redis on the same Droplet as the web server is prohibited. |
| Task Queue | Celery |
| Primary Use Cases | Background data deletion worker after account cancellation (fires after 90-day total window: 30-day read-only + 60-day retention — see Section 8.3 and Pricing & Billing Specification V2 Section 8); heavy CSV exports; Stripe webhook processing; storage usage reconciliation; TenantState cache synchronization between SDP and SDTA; scheduled data deletion warning emails (7-day pre-deletion) |

### 6.5.1 Redis Security Requirements

Redis is a common attack vector when left in its default configuration. An exposed or unauthenticated Redis instance allows an attacker to read and inject arbitrary task messages, potentially executing code on workers or leaking queued data. The following requirements are mandatory in all staging and production environments.

**Network Isolation — Internal Private Network Only**

Redis must never be publicly accessible. In DigitalOcean, the Redis instance must be bound to the private VPC network interface, not the public IP. The Redis port (6379) must not appear in any public firewall rule. Django, Celery workers, and the Redis instance must all reside on the same private VPC, communicating over internal IP addresses only.

No external client — developer workstation, CI pipeline, or any other service — should ever connect directly to the production Redis instance. All task management is done through Django management commands and Celery inspection tools running from within the same private network.

**Authentication — requirepass**

Redis must be configured with a strong password via `requirepass`. Clients must authenticate with `AUTH <password>` before any commands are accepted. The Redis password must be stored as an environment variable (`REDIS_PASSWORD`) and never hardcoded in source code, configuration files, or committed to version control.

The broker URL format in Django settings:

```python
# settings.py
# rediss:// prefix = TLS connection (required in production)
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
# Expected value format: rediss://:password@internal-host:6379/0
```

**TLS — Encrypted Redis Connections**

All connections to Redis in staging and production must use TLS (`rediss://` prefix, not `redis://`). DigitalOcean Managed Redis provides TLS by default. The `rediss://` scheme in the broker URL activates TLS negotiation in the `redis-py` client.

For Celery, TLS is activated automatically when the broker URL uses the `rediss://` scheme. No additional Celery configuration is required when using DigitalOcean Managed Redis.

**What Happens Without These Controls**

| Missing Control | Risk |
|----------------|------|
| Redis on public network | Any internet host can connect to the message broker, read queued tasks (including Stripe payloads, tenant IDs), and inject malicious tasks onto the queue |
| No requirepass | Unauthenticated clients can issue any Redis command — including `FLUSHALL` (delete all queued tasks) or `CONFIG SET` (modify server behaviour) |
| No TLS | Task payloads — which may contain tenant data and webhook content — are transmitted in plaintext over the network |

**Development Environment**

In local development (Docker Compose), Redis runs without TLS and without `requirepass` by default for developer convenience. `docker-compose.yml` must never be used as a reference for production Redis configuration. The `CELERY_BROKER_URL` environment variable in production always uses the `rediss://` scheme with a strong password.

## 6.6 Real-Time Push Events — Pusher

ServizDesk uses **Pusher** as the push event delivery service for UI notifications that must reach the user without waiting for a polling interval. Pusher handles persistent browser connections on its infrastructure — Django servers remain fully stateless.

### Design Decision

SSE (Server-Sent Events) and WebSockets are explicitly prohibited in SDTA. Persistent server-side connections are incompatible with PgBouncer transaction mode (tenant context set via `SET LOCAL` is scoped to a single transaction and would be lost across the lifetime of a persistent connection). Pusher eliminates this problem entirely — Django fires a small outbound HTTP event to Pusher from within a normal request or Celery task, and Pusher delivers it to subscribed clients.

### Reliability & Degraded Mode

Pusher operates at 99.99%+ uptime. If Pusher is unavailable, push notifications stop arriving — but the application continues functioning normally. All boards and counters fall back to their HTMX polling intervals automatically. Pusher is a notification hint layer only; it never carries data that the application depends on to function.

### What Uses Pusher vs. HTMX Polling

| Feature | Update Mechanism | Interval / Trigger |
|---------|-----------------|-------------------|
| Dashboard counters | HTMX polling | Every 60 seconds |
| Kanban boards | HTMX polling | Every 30 seconds |
| Gantt charts | HTMX polling | Every 30 seconds |
| New inbound service request | Pusher push event | On creation |
| Work order status changed to urgent / critical | Pusher push event | On status change |
| Payment received | Pusher push event | On `payment.succeeded` Stripe webhook processed |
| System alert / notification | Pusher push event | On notification record creation |
| General record updates (non-urgent) | HTMX polling (next cycle) | Per board interval |

### Event Architecture

Pusher events are **hints only** — the payload carries the event type and the affected record ID, not the record data. On receiving a Pusher event, the client fires a targeted HTMX request to fetch only the updated fragment from Django. This keeps Pusher payloads minimal and ensures all data delivery goes through the normal RLS-secured Django stack.

```python
# Example: firing a Pusher event from a Django view or Celery task
import pusher

pusher_client = pusher.Pusher(
    app_id=env('PUSHER_APP_ID'),
    key=env('PUSHER_KEY'),
    secret=env('PUSHER_SECRET'),
    cluster=env('PUSHER_CLUSTER'),
    ssl=True
)

def notify_new_service_request(tenant_id: str, service_request_id: str):
    pusher_client.trigger(
        f'private-tenant-{tenant_id}',   # Private channel — server auth required
        'service-request.created',        # Event name
        {'id': service_request_id}         # Minimal payload — client re-fetches
    )
```

### Channel Naming Convention & Security

All channels are **Pusher Private Channels** (prefixed with `private-`). Private channels require the browser to authenticate with your Django server before Pusher will allow the subscription. This prevents any client that happens to know a `tenant_id` from subscribing to another tenant's events.

| Channel Pattern | Purpose |
|----------------|---------|
| `private-tenant-{tenant_id}` | All tenant-wide events (service requests, payments, alerts) |
| `private-tenant-{tenant_id}-user-{user_id}` | Per-user events (personal notifications) |

### Pusher Auth Endpoint

Django must expose a `/pusher/auth/` endpoint. Pusher calls this endpoint automatically when a client attempts to subscribe to a private channel. The endpoint applies two levels of verification:

1. **Tenant check** — the channel must belong to the authenticated user's tenant. This applies to all channel types.
2. **User check** — for per-user channels (`-user-{user_id}` suffix), the `user_id` embedded in the channel name must match the authenticated user. This prevents Employee A from subscribing to Employee B's personal notification channel even though they are in the same tenant.

```python
@login_required
def pusher_auth(request):
    channel_name = request.POST.get('channel_name')
    socket_id = request.POST.get('socket_id')

    # Layer 1: Verify the channel belongs to the authenticated user's tenant.
    # Covers both tenant-wide and per-user channels.
    expected_tenant_prefix = f'private-tenant-{request.user.tenant_id}'
    if not channel_name.startswith(expected_tenant_prefix):
        return HttpResponseForbidden('Channel not authorized for this tenant.')

    # Layer 2: For per-user channels, additionally verify the user_id segment.
    # Channel format: private-tenant-{tenant_id}-user-{user_id}
    # Prevents an employee subscribing to a co-worker's personal channel.
    if '-user-' in channel_name:
        try:
            channel_user_id = channel_name.split('-user-')[1]
        except IndexError:
            return HttpResponseForbidden('Malformed channel name.')
        if str(request.user.id) != channel_user_id:
            return HttpResponseForbidden('Channel not authorized for this user.')

    auth = pusher_client.authenticate(
        channel=channel_name,
        socket_id=socket_id
    )
    return JsonResponse(auth)
```

### Client-Side HTMX Integration

On receiving a Pusher event, the browser triggers an HTMX re-fetch of the relevant panel without a full page reload:

```javascript
// In the Django template for the notifications panel
const channel = pusher.subscribe('private-tenant-{{ tenant_id }}');
channel.bind('service-request.created', function(data) {
    htmx.trigger('#service-request-panel', 'refresh');
});
```

---

# 7. SDP / SDTA Internal Communication

Communication between SDP and SDTA occurs exclusively via an **Internal REST API**. Direct database reads across applications are strictly prohibited at all times.

## 7.1 API Architecture

SDP exposes a private, internal-only REST API accessible only over the private server network or localhost. SDTA authenticates its requests to this API using a secure Internal API Key (or JWT shared secret). No external traffic reaches this API.

| Direction | Method | Examples |
|-----------|--------|---------|
| SDTA → SDP | Internal REST API | Request current plan status; request seat limit; request storage allocation; notify SDP of new seat added; notify SDP of seat terminated; notify SDP of storage usage update |
| SDP → SDTA | Internal REST API | Provision new tenant; update account status (suspend, reactivate, cancel); push plan change notification; push storage limit change |

## 7.2 Provisioning Flow

New tenant provisioning is fully atomic. A successful signup results in a complete, fully initialized tenant account in both SDP and SDTA with no manual intervention required. If provisioning fails at any step, no partial records remain in SDP or SDTA and ServizDesk staff are alerted immediately.

The provisioning sequence follows a **verify-first, bill-second** model:

1. Customer completes Stripe Checkout (payment authorized but not yet captured)
2. SDP generates Tenant UUID
3. SDP calls SDTA Internal API to initialize the tenant (Tenant record, Administrator Employee record, default Preferences, required system lookup data)
4. On successful SDTA initialization, SDP captures the Stripe payment
5. Welcome email dispatched via Postmark
6. Customer redirected to SDTA login page

> **Rule:** A customer is never charged for a failed provisioning. If SDTA initialization fails, the Stripe payment authorization is released and the customer receives an error notification.

---

# 8. Security & Compliance

## 8.1 Authentication

| Item | Implementation |
|------|---------------|
| SDTA Authentication | Standard Django session-backed authentication. Username (work email) and password. |
| SDP Customer Authentication | Separate session from SDTA. Customers log into SDP with their billing email and SDP password. Logging into SDP does not log the customer into SDTA. |
| Password Hashing | bcrypt or Argon2 preferred (Django's PBKDF2 default is acceptable minimum). Plaintext passwords are strictly prohibited in all databases. |
| Password Rules | Minimum 8 characters. Must include uppercase, lowercase, number, and special character. |
| Session Timeout | Configurable by Administrator. Minimum 15 minutes, maximum 8 hours, default 30 minutes. On timeout, user is logged out and returned to the login page. **Implementation note:** Django's `SESSION_COOKIE_AGE` is a global setting and cannot be per-tenant. Per-tenant idle timeout must be implemented in `TenantMiddleware`: on each authenticated request, store the last-activity timestamp in the session (`request.session['last_activity'] = now()`), then read `TenantPreference.session_timeout_minutes` and compare against `now() - last_activity`. If the idle time exceeds the timeout, call `auth.logout(request)` and redirect to the login page. This replaces `SESSION_COOKIE_AGE` for idle timeout enforcement. |
| Failed Login Lockout | 5 consecutive failed attempts locks the employee account. Tracked by `django-axes` at both the IP address and username level — distributed attacks targeting one account from many IPs are caught. Locked accounts auto-unlock after 30 minutes, or can be immediately unlocked by an Administrator from the employee record. Administrator accounts that are locked follow the SDP recovery path instead. |
| Administrator Recovery | Locked Administrator accounts are recovered through SDP using Security PIN and security questions established at signup. Billing verification available as fallback. All recovery actions logged in SDP. |
| Security Credentials | Administrator Security PIN and security question answers are stored exclusively in SDP. They are never transmitted to or stored in the SDTA database. |
| Multi-Factor Authentication (MFA) | SMS OTP is the primary MFA method. Email OTP is the fallback if SMS is unavailable or the employee requests it. MFA is **Administrator-controlled** — Administrators may enable or disable MFA for their entire organization. When enabled, all employees must complete MFA at login. The UI prominently recommends enabling MFA. OTP codes expire after 10 minutes and are single-use. |
| Session Cookie Security | `SESSION_COOKIE_SECURE = True` — cookies sent over HTTPS only. `SESSION_COOKIE_HTTPONLY = True` — not readable by JavaScript. `SESSION_COOKIE_SAMESITE = 'Lax'` — cross-site request protection. CSRF cookie: `CSRF_COOKIE_SECURE = True`, `CSRF_COOKIE_HTTPONLY = True`. These settings are mandatory in staging and production and must never be overridden. |
| CSRF Protection | Django's `CsrfViewMiddleware` is enabled globally. HTMX is configured to include the CSRF token on all non-GET requests via the `htmx:configRequest` event listener in the base template. Exempting any view from CSRF is prohibited unless explicitly justified and reviewed. |
| Account Enumeration Prevention | The password reset endpoint always returns the same response — "If an account exists for that email, you'll receive a reset link" — regardless of whether the email matched a registered user. This prevents attackers from using the reset form to discover valid employee email addresses. |
| Password Reset Token Expiry | Reset links expire after **24 hours**. Django's default is 3 days — this must be explicitly overridden: `PASSWORD_RESET_TIMEOUT = 86400` (seconds) in `settings.py`. Tokens are single-use; Django invalidates the token the moment it is consumed. A reset link sitting unused in an inbox longer than 24 hours is automatically void. |
| Session Fixation Prevention | Django's `login()` automatically calls `cycle_key()` on authentication, invalidating the pre-login session token and issuing a new one. This is Django default behavior and must never be disabled. |
| Force Session Revocation | Administrators can immediately invalidate all active sessions for any employee from the User management screen. Required response to a suspected compromised account. See Permission Management Specification V2 Section 12. |
| Login Attempt Audit Log | All login attempts — successful and failed — are recorded in `LoginAttemptLog`, capturing IP address, user agent, outcome, failure reason, and whether MFA was involved. Viewable by Administrators in the employee management area. See Data Models V6. |

## 8.2 PCI DSS Compliance

ServizDesk operates as an **SAQ A merchant** — the lowest and simplest PCI compliance tier. This is maintained by ensuring raw card data never touches ServizDesk servers at any point.

- All card collection uses Stripe Checkout (for ServizDesk billing) or Stripe Connect (for tenant payment processing in Plus/Pro)
- Custom card entry forms that post card data to ServizDesk servers are strictly prohibited and would immediately invalidate SAQ A status
- SDP stores only Stripe-provided tokenized references — never raw card data, PAN, CVV, or magnetic stripe data

## 8.3 Data Retention

| Data Type | Retention Rule |
|-----------|---------------|
| Active tenant data (SDTA) | Retained indefinitely while account is active |
| Cancelled/expired tenant data (SDTA) | 30-day `Cancelled (Read Only)` window (all users can log in; no writes), then 60-day `Cancelled` data retention period (SDTA access revoked). After the 60-day retention countdown expires, Celery workers permanently hard-delete all data for that Tenant UUID. Total: 90 days from billing period end. See Pricing & Billing Specification V2, Section 8. |
| SDP audit log | 36 months rolling |
| SDTA audit log | 18 months rolling |
| SDP account records (post-cancellation) | 36 months rolling |
| Stripe transaction records | Indefinite (managed by Stripe) |
| Staff login attempts (SDP) | 36 months rolling |
| Trial account data (unconverted) | Day 15: read-only mode. Day 45: flagged for cleanup (60-day grace begins). Day 105: permanent deletion. |

Soft-delete is generally prohibited unless explicitly specified by a status lifecycle. Records are hard-deleted unless blocked by relational integrity constraints (e.g., a Customer with attached Invoices cannot be deleted). Permanent deletion is irreversible — there is no backup or restore capability exposed in the SaaS product.

## 8.4 Stripe Webhook Security

- All incoming webhooks from Stripe must verify the cryptographic signature using `STRIPE_WEBHOOK_SECRET` before parsing the payload
- Webhook endpoints must be fully idempotent — processing the same Stripe event twice must produce no adverse effects
- Incoming event IDs are stored in the `WebhookLog` table to prevent duplicate payment processing

## 8.5 Audit Logging

Both SDP and SDTA maintain comprehensive audit logs. Audit events are immutable once written.

| System | Scope |
|--------|-------|
| SDTA `SystemAudits` table | Records who did what and when for all significant tenant-side actions: record creation, deletion, status changes, financial-impact actions (invoices issued/voided, payments applied). Event-level logging — not field-level diff logging. |
| SDP audit log | Records all staff actions, account management events, provisioning actions, recovery actions, and plan changes. |
| `SessionLog` (SDTA) | Tracks active authenticated sessions with login time, IP address, user-agent, and expiration. 18-month rolling retention. |

## 8.6 Multi-Tenant Login Flow (Pre-Authentication Subdomain Resolution)

SDTA is a subdomain-based multi-tenant application. Each tenant accesses their instance at a unique subdomain (e.g., `acme.servizdesk.com`). Because `User` records are protected by PostgreSQL Row-Level Security (RLS), the system must resolve the tenant from the subdomain **before** attempting any database query — the standard `TenantMiddleware` only runs for already-authenticated requests.

### Login Flow

```
1. User navigates to: https://acme.servizdesk.com/login/
2. Login view extracts subdomain ("acme") from request host.
3. Queries SubdomainIndex (RLS-exempt table): SELECT tenant_id WHERE subdomain = 'acme'
4. Set tenant context (both layers required):
   a. Call set_current_tenant_id(tenant_id) — sets the Python-level context variable (used by TenantManager query filtering).
   b. Within transaction.atomic(), execute SET LOCAL app.current_tenant_id = '{tenant_id}' — sets the PostgreSQL session variable (used by RLS policies).
   Both layers must be set on every authenticated request. See Multi-Tenancy Specification V1 for the authoritative middleware pattern.
5. Calls Django authenticate() — validates email + password.
   User table lookup is now RLS-scoped to the correct tenant.

6a. On password failure: record attempt in LoginAttemptLog (success=False).
    Increment User.failed_login_count by 1.
    Return login error. Clear tenant context in finally block.

6b. On password success — session is NOT yet established:
    Reset User.failed_login_count to 0 (mirrors AXES_RESET_ON_SUCCESS behavior).
    IF MFA is disabled for this organization:
      → Call Django login() immediately. Session established.
      → TenantMiddleware takes over for the remainder of the session.
    IF MFA is enabled for this organization:
      → Store verified user identity in a temporary signed intermediate token
        (not a full session cookie — no access to protected resources yet).
      → Dispatch OTP via SMS to employee's registered MFA phone.
        If SMS unavailable: send OTP to registered work email instead.
      → Display MFA challenge screen.

7. MFA verification (only reached if MFA is enabled):
   User submits OTP code.
   Verify: correct value, not expired (10-minute window), not previously used.

   IF OTP invalid or expired:
     → Record attempt in LoginAttemptLog (mfa_failed). Return MFA error.
     → Increment MFA failure counter. Invalidate intermediate token after 3 failures.
   IF OTP valid:
     → Call Django login() — full session established. Intermediate token discarded.
     → TenantMiddleware takes over for the remainder of the session.
     → Record in LoginAttemptLog (success=True, mfa_used=True).

8. Always clear tenant context in finally block on any failure path.
```

> **Session Fixation:** Django's `login()` calls `cycle_key()` automatically, discarding the pre-login session token and issuing a new one. When MFA is enabled, `login()` is called only after OTP verification — not after password verification. This ensures the full session token is never issued until both factors are complete.

> **`failed_login_count` vs. django-axes:** These are two independent systems that must be kept in sync by the login view. `django-axes` is the **enforcement layer** — it intercepts authentication attempts through the `AxesStandaloneBackend`, tracks failures internally, and raises `AxesSignalPermissionDenied` when the threshold is exceeded. `User.failed_login_count` is the **display mirror** — it shows the current count in the Administrator's employee record UI, allowing Administrators to see how many recent failures occurred without querying axes internals. The login view must: (1) increment `failed_login_count` on each failed `authenticate()` call, (2) reset it to 0 on any successful authentication (matching `AXES_RESET_ON_SUCCESS = True`). Account unlock (Section 12.3 of Permission Management Spec V2) resets both.

### Password Reset Flow

The same pre-authentication resolution applies to password reset. The tenant must be resolved from the subdomain before the `User` record can be looked up by email to dispatch the reset link.

```
1. User submits email on: https://acme.servizdesk.com/password-reset/
2. View resolves tenant_id from subdomain via SubdomainIndex.
3. Sets tenant context (same pattern as login flow above).
4. Queries User by email — RLS-scoped to the resolved tenant.
5. If found: generate a signed, time-limited reset token and dispatch reset email.
   If not found: do nothing — no error raised.
6. Always return identical response: "If an account exists for that email,
   you'll receive a reset link shortly." — same status code, same body,
   regardless of whether the email matched a user.
7. Always clear tenant context in finally block.
```

> **Token Expiry:** Reset tokens expire after 24 hours (`PASSWORD_RESET_TIMEOUT = 86400`). Django's default of 3 days must be explicitly overridden. Tokens are also single-use — Django invalidates the token the moment the user completes the reset, so a link cannot be replayed.

> **Account Enumeration Rule:** The response must be identical whether or not the email was found — same HTTP status, same body, and same approximate response time. Any observable difference allows an attacker to probe for valid employee email addresses. Constant-time response behavior must be verified during code review.

### SubdomainIndex Table

`SubdomainIndex` is a non-tenant-scoped system table with no `tenant_id` column. It is the only SDTA table exempt from tenant RLS for this purpose. It is populated by the provisioning flow when a tenant is created and removed when the tenant is deleted.

| Column | Type | Notes |
|--------|------|-------|
| `subdomain` | `VARCHAR(63)` | Unique index. Extracted from request host at login time. |
| `tenant_id` | `UUID` | The resolved tenant UUID. Not a FK — decoupled from tenant records. |

See Multi-Tenancy Specification V1 Section 9 for the full code pattern.

### OTP Storage and Single-Use Enforcement

The login flow stores OTP values ephemerally in Redis. No OTP value is written to the PostgreSQL database. This avoids creating a `PendingMFA` table and eliminates the need for a cleanup background task.

#### Intermediate Signed Token

After successful password verification (step 6b), if MFA is enabled, the login view issues an **intermediate signed token** using Django's `django.core.signing.dumps()`. This token:

- Is stored as a short-lived HTTP-only cookie or a hidden form field passed through the MFA challenge page — **not** a session cookie.
- Contains: `{ "user_id": "<uuid>", "nonce": "<random 32-byte hex string>", "tenant_id": "<uuid>" }`
- Is signed with Django's `SECRET_KEY` — tamper-evident but not encrypted (contains no secrets).
- Expires after 15 minutes (`max_age=900` in `signing.loads()`).
- Is discarded immediately when: OTP verified successfully (step 7 success), or after 3 MFA failures (step 7 failure branch).

The nonce is generated fresh for each MFA challenge. It serves as the Redis key component, ensuring each challenge session is isolated even if the same user retries.

#### OTP Value — Redis Storage Pattern

```
Key:   mfa_otp:{user_id}:{nonce}
Value: SHA-256 hash of the OTP (6-digit numeric string)
TTL:   600 seconds (10 minutes — matches the "not expired" check in step 7)
```

- The OTP is generated using `pyotp.random_base32()` seeded TOTP or `secrets.randbelow(1_000_000)` for a plain 6-digit code, formatted as a zero-padded string.
- **Only the SHA-256 hash** is stored in Redis. The plaintext OTP is dispatched to the user and never persisted.
- On verification: the submitted code is hashed and compared to the stored hash.

#### Single-Use Enforcement

Single-use is enforced via an **atomic Redis delete**:

```
1. Look up: GET mfa_otp:{user_id}:{nonce}
   If key does not exist → OTP expired or already used → reject.
2. Compare submitted hash against stored hash.
   If mismatch → increment failure counter (see below) → reject.
3. If match → DEL mfa_otp:{user_id}:{nonce}  ← atomic delete before session is created.
4. Call Django login() → full session established.
```

The delete in step 3 happens before `login()` is called. If `login()` subsequently fails (extremely rare), the OTP key is already gone — the user must restart from the password step. This is acceptable; it prevents replay even in failure edge cases.

#### MFA Failure Counter — Redis Storage Pattern

The MFA failure counter is stored in Redis alongside the OTP key, not on the `User` model:

```
Key:   mfa_failures:{user_id}:{nonce}
Value: integer (count of failed OTP submissions for this challenge)
TTL:   600 seconds (same TTL as the OTP key — expires with the challenge)
```

- On each failed OTP submission: `INCR mfa_failures:{user_id}:{nonce}`.
- If the counter reaches 3: delete both `mfa_otp:*` and `mfa_failures:*` keys and invalidate the intermediate signed token (done by not accepting it for further requests — the token itself contains no state to revoke, so invalidation is enforced by deleting the Redis keys it references).
- After 3 failures the user must restart from the password step.

> **Why Redis and not PostgreSQL?** OTP values are ephemeral security credentials with a 10-minute lifespan. Storing them in PostgreSQL would require a `PendingMFA` table, background cleanup tasks, and careful handling to avoid write amplification on every login attempt. Redis TTL handles expiry atomically with zero application logic. The tradeoff is that a Redis restart loses in-flight MFA challenges — affected users must restart from the password step, which is an acceptable UX cost for the security and simplicity gains.

> **Implementation Note — Two Separate Lockout Counters:**
> Account lockout (5 failed password attempts, tracked by django-axes) and MFA lockout (3 failed OTP attempts, tracked in Redis) are independent mechanisms. Account lockout blocks the login form; MFA lockout invalidates the intermediate token and requires restarting login. Neither triggers the other.

---

## 8.7 Rate Limiting

Two complementary rate limiting layers protect all authentication endpoints. Neither alone is sufficient.

| Layer | Tool | Protects Against | Scope |
|-------|------|-----------------|-------|
| **Network layer** | Nginx `limit_req` | Volumetric attacks — bots hammering endpoints before application code runs | Per source IP |
| **Application layer** | `django-axes` | Credential stuffing — distributed attacks from many IPs targeting one account | Per IP + per username |

### Nginx Configuration (Reference)

```nginx
http {
    # Rate limit zones — keyed by client IP
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=password_reset:10m rate=3r/m;
    limit_req_zone $binary_remote_addr zone=mfa:10m rate=10r/m;

    server {
        location /login/ {
            limit_req zone=login burst=5 nodelay;
        }
        location /password-reset/ {
            limit_req zone=password_reset burst=3 nodelay;
        }
        location /mfa/ {
            limit_req zone=mfa burst=10 nodelay;
        }
    }
}
```

### django-axes Configuration (Reference)

```python
from datetime import timedelta

INSTALLED_APPS = [..., 'axes']

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AXES_FAILURE_LIMIT = 5                 # Lock after 5 failures
AXES_COOLDOWN_TIME = timedelta(minutes=30)  # Auto-unlock after 30 min
AXES_RESET_ON_SUCCESS = True           # Reset failure count on successful login

# Lock on EITHER (ip_address + username composite) OR (username alone).
# The composite key catches a single IP brute-forcing one account.
# The username-alone key catches distributed attacks: many IPs, each making
# a small number of attempts against the same username.
AXES_LOCKOUT_PARAMETERS = [['ip_address', 'username'], ['username']]
```

> **Rule:** Both layers must be deployed in production. Nginx handles raw volume cheaply at the network edge. `django-axes` catches account-targeted attacks — including distributed credential stuffing that spreads attempts across many different IP addresses to evade per-IP limits.

> **URL Synchronization:** The Nginx `location` blocks (`/login/`, `/password-reset/`, `/mfa/`) must exactly match the URL patterns defined in Django's URL configuration. If the Django MFA verification URL is `/login/mfa/` or `/accounts/mfa/`, the Nginx location block must be updated to match — a mismatch means the rate limit silently does not apply to that endpoint.

---

## 8.8 HTTP Security Headers

> **Scope:** This section applies to **SDTA only** (tenant subdomains). SDP requires its own header configuration. The critical difference is CSP: SDP's `script-src` must include `https://js.stripe.com` and `connect-src` must include `https://api.stripe.com`. Applying the SDTA CSP to SDP would block Stripe Checkout and break the billing flow.

Security headers are split across two implementation layers based on whether they require dynamic per-request values:

**Static headers (set at Nginx):** `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Referrer-Policy`, and `Permissions-Policy` have fixed values that never change. These are set in Nginx so they apply to every response — including error pages, static files, and redirects.

**Content Security Policy (set by Django middleware):** CSP requires a unique cryptographic nonce generated fresh for every request. This nonce is embedded in the CSP header and in every inline `<script>` tag that Django renders. Nginx cannot generate dynamic per-request values, so CSP **must not** be set at the Nginx layer. Use the `django-csp` package (`pip install django-csp`) or a custom middleware.

### Required Headers

| Header | Value | Set At |
|--------|-------|--------|
| `X-Frame-Options` | `DENY` | Nginx |
| `X-Content-Type-Options` | `nosniff` | Nginx |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Nginx |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Nginx |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Nginx |
| `Content-Security-Policy` | See below | Django middleware |

### Nginx Configuration — Static Headers Only (Reference)

```nginx
# Add to the SDTA server block in nginx.conf
# DO NOT set Content-Security-Policy here — it must come from Django middleware
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

> **`always` keyword:** Ensures the header is sent on all responses including error pages (4xx, 5xx). Without `always`, Nginx omits the header on error responses.

### Django Middleware — Content Security Policy (Reference)

```python
# settings.py — using django-csp
MIDDLEWARE = [
    ...
    'csp.middleware.CSPMiddleware',
    ...
]

# CSP directives for SDTA
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "https://js.pusher.com")  # nonce added automatically
CSP_CONNECT_SRC = ("'self'", "wss://*.pusher.com", "https://sockjs-*.pusher.com")
CSP_STYLE_SRC = ("'self'",)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_INCLUDE_NONCE_IN = ('script-src',)  # Auto-generates nonce per request
```

In Django templates, inline `<script>` blocks must carry the nonce attribute:

```html
<script nonce="{{ request.csp_nonce }}">
  // Pusher subscription code here
</script>
```

### Content Security Policy Notes

**`script-src`:** Allows scripts from the application itself (`'self'`) and Pusher's CDN (`https://js.pusher.com`). The nonce is appended automatically by `django-csp`, allowing inline `<script>` blocks that carry the matching `nonce="{{ request.csp_nonce }}"` attribute. Any inline script without the nonce is blocked.

**`connect-src`:** Allows the Pusher WebSocket and SockJS fallback connections used by the Pusher JavaScript client.

**`frame-ancestors 'none'`:** Equivalent to `X-Frame-Options: DENY` but enforced via CSP. Both headers are set for compatibility with older browsers.

**`form-action 'self'`:** Prevents forms from submitting to third-party URLs — an additional CSRF defence layer.

**`base-uri 'self'`:** Prevents `<base>` tag injection attacks that could redirect all relative URLs.

### HSTS Preload (Optional — Future)

After the domain has been live with HSTS for 12+ months with no issues, consider submitting `servizdesk.com` to the HSTS preload list (`hstspreload.org`). Preloaded domains are hardcoded into browsers as HTTPS-only before the first visit, eliminating the window of vulnerability that exists on a user's very first connection. This is a one-way commitment — removal from the preload list takes months.

### Verification

After any Nginx configuration change, verify headers using:
```bash
curl -I https://acme.servizdesk.com/login/
```
Or use `securityheaders.com` to scan the domain and confirm all headers are present and correctly configured. This check must be part of the production deployment checklist.

---

## 8.9 Django SECRET_KEY Management

### What the SECRET_KEY Does

Django's `SECRET_KEY` is the cryptographic root of trust for the application. It is used to sign and verify:

| Mechanism | Dependency on SECRET_KEY |
|-----------|------------------------|
| Session cookies | Signed with SECRET_KEY. A tampered cookie is rejected. |
| CSRF tokens | Generated and verified using SECRET_KEY. |
| Password reset tokens | Signed with SECRET_KEY + timestamp. Expiry verification depends on this. |
| Any `django.core.signing` usage | All server-side signed payloads (e.g. email confirmation links). |

If the `SECRET_KEY` is exposed, an attacker can forge any of the above — crafting valid session cookies, bypassing CSRF protection, or generating valid password reset tokens for any account.

### Requirements

**Environment variable only.** `SECRET_KEY` must be loaded from the environment. It must never appear in `settings.py`, any configuration file, or version control. The correct pattern in `settings.py`:

```python
# settings.py
SECRET_KEY = env('DJANGO_SECRET_KEY')
```

**Unique per environment.** Development, staging, and production must each have a different `SECRET_KEY`. Sharing a key across environments means a key leaked from a development machine compromises production sessions and tokens.

**Cryptographically random, 50+ characters.** Use Django's built-in generator for all environments:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

This produces a 50-character string drawn from a safe character set. Do not use shorter strings, dictionary words, or keys generated by other tools.

**Stored in the secrets vault.** The production and staging `SECRET_KEY` values must be stored in the secrets vault (same vault that holds database passwords and Redis credentials), not in `.env` files committed to source control or stored in plaintext on the server.

### Key Rotation

Rotating the `SECRET_KEY` (replacing it with a new value and redeploying) immediately and permanently invalidates:

- All active user sessions (every logged-in user is logged out)
- All outstanding CSRF tokens (harmless — new ones are issued on the next request)
- All outstanding password reset links (users must request a new reset)

This is intentional and should be treated as a **security incident response tool**. If the key is ever suspected to be compromised, rotating it is the fastest way to invalidate any forged sessions or tokens system-wide without needing to identify individual affected accounts.

Key rotation should be planned as a brief maintenance window to avoid confusing users with unexpected logouts during peak hours.

---

# 9. Development Practices & Standards

## 9.1 Architecture Patterns

- **Fat Models, Thin Views** — business logic lives in model methods or dedicated service classes, never in view functions
- **No Generic Foreign Keys (GFKs)** — use explicit foreign keys on all tables to maintain PostgreSQL RLS enforcement compatibility
- **Exclusive Arc Pattern for Notes and Documents** — a single `Note` table and single `Document` table each contain nullable foreign keys pointing to every possible parent entity (Customer, Asset, Quote, Work Order, Invoice, etc.). A database constraint ensures exactly one FK is populated per row.
- **Isolated Line Items** — Quotes, Work Orders, and Invoices each have their own dedicated line item table (`QuoteLine`, `WorkOrderLine`, `InvoiceLine`). No shared generic line item table.
- **Universal Deletion Policy (The "Notes Only" Rule)** — No top-level record can be deleted if related child records exist. This is enforced via database-level `RESTRICT` constraints on all children except **Notes**, which remain the only entity allowed to `CASCADE` delete with a parent.

## 9.2 Record Numbering

Human-readable record numbers (e.g., `Q26-0001` for quotes, `W26-0001` for work orders) are generated using a `SequenceTracker` table that manages tenant-scoped auto-incrementing counters. This guarantees collision-free, per-tenant sequential numbering without relying on database auto-increment sequences, which are not per-tenant.

#### 9.2.1 Coordination Contract (The "Forward-Only" Rule)

To ensure data integrity and prevent duplicate record numbers when users modify their numbering settings, the following contract governs the interaction between `TenantPreference` (User Settings) and `SequenceTracker` (System Counter):

1.  **Initial Seeding**: At tenant provisioning, `SequenceTracker` rows are initialized for all entity types. The `last_value` is set to `[start_number] - 1` (default start is 1, so internal counter begins at 0).
2.  **Number Generation Workflow**: When a new record is created:
    *   The system performs an atomic increment on the `SequenceTracker` for the corresponding `entity_type` and `tenant_id` (and `year` if annual reset applies).
    *   The `last_value` is retrieved from the tracker.
    *   The prefix is retrieved from `TenantPreference`.
    *   The final record number is formatted: `[Prefix][Year_Code]-[Atomic_Sequence]` (e.g., `W26-1025`).
    *   The resulting string is permanently saved to the record's number field.
3.  **User Updates (Forward-Only)**: Users may modify their `*_start_number` in `TenantPreference` at any time, but the update is subject to a **Forward-Only Constraint**:
    *   The new `start_number` must be **greater than** the current `SequenceTracker.last_value`.
    *   Attempting to set a `start_number` lower than or equal to the current counter must be rejected by the validation layer.
    *   Setting a higher `start_number` immediately updates the `SequenceTracker.last_value` to `[new_start_number] - 1`.
4.  **Visibility**: The "Next Number" to be used for each sequence is displayed to the user in the Preference section, derived from `SequenceTracker.last_value + 1`.
5.  **Immutability**: Once generated and saved, a record number can never be changed. Modifications to prefixes or start numbers in `TenantPreference` apply only to records created after the change.

## 9.3 Record Conversion Logic

The ServizDesk Lite MVP supports the transformation of records across the service lifecycle (Quote → Work Order → Invoice). To maintain historical integrity while allowing operational flexibility, the following rules apply:

### 9.3.1 Conversion Pattern: "Clone & Link"
1.  **Immutability of Source**: The source record (e.g., Quote) is never deleted. It is marked with a terminal status (e.g., `Converted`).
2.  **Deep Copy logic**: Line items are **cloned** (deep copy) from the source table to the target table. Once converted, the new line items can be modified (quantities adjusted, parts added) without affecting the original source record.
3.  **Backlink Traceability**: The newly created record MUST store the ID of its parent in the corresponding backlink field (e.g., `Invoice.work_order_id`, `WorkOrder.quote_id`).

### 9.3.2 Specific Mapping Rules

| Conversion Type | Field Mapping | Line Item Mapping | Post-Conversion Status Change |
| :--- | :--- | :--- | :--- |
| **Quote → Work Order** | Customer, Project, Contact, Assigned To, Address | All QuoteLines → WorkOrderLines | Quote: `Converted` |
| **Quote → Invoice** | Customer, Project, Contact, Assigned To, Address, Notes, Internal Notes, Tax Rate | All QuoteLines → InvoiceLines | Quote: `Converted` |
| **Work Order → Invoice** | Customer, Project, Assigned To, Address, Internal Notes | All WorkOrderLines → InvoiceLines | Work Order: no automatic status change — a WO may generate multiple invoices (deposit, progress, final) via `WorkOrderInvoice`; status is managed independently |

### 9.3.3 Labor Rolling (Work Order → Invoice)
At the time of Work Order to Invoice conversion, the system provides an option to "Roll Labor to Invoice". If selected, the system iterates through all `TimeEntry` records for the Work Order and generates a new `InvoiceLine` for each unique Employee/Date combination, using the Work Order's labor rate.

## 9.4 Unified Ledger Logic

To ensure financial integrity and top-down architectural scaling, the ledger system follows a unified AR/AP engine approach.

### 9.4.1 Transactional Immutability
Ledger entries are strictly **immutable**. Once written, an entry cannot be edited or deleted. Financial corrections (Voiding an invoice, reversal of a payment) must be performed by creating a new **Reversing Entry**.

### 9.4.2 Entry Triggers
Financial events in the platform automatically generate ledger entries:
- **Invoices**: Triggered when status moves from `Draft` → `Issued`. Creates a **Debit** for the Customer.
- **Payments**: Triggered upon creation of a successful `Payments` record. Creates a **Credit** for the Customer.
- **Voids**: Triggered when an `Issued` invoice is moved to `Void`. Creates a **Credit** adjustment for the Customer.
- **Vendor Bills (Plus+)**: Triggered on Bill issuance. Creates a **Credit** for the Vendor.
- **Vendor Payments (Plus+)**: Triggered on Payment execution. Creates a **Debit** for the Vendor.

### 9.4.3 Running Balance (Net Position)
The `running_balance` field is calculated at **write-time** (insertion) to optimize read performance for customer/vendor statements.
- **Customer Balance**: Total Debits minus Total Credits (Positive = Money Owed To Us).
- **Vendor Balance**: Total Credits minus Total Debits (Positive = Money We Owe Them).

# 10. Domain-Driven Django App Structure (Top-Down)

To ensure the SDTA project scales from Lite to Enterprise without architectural debt, the project is organized into domain-specific applications. All business logic must reside within the `services.py` layer of these apps.

| App Name | Domain Description | Core Entities |
|---|---|---|
| `users/` | Multi-Tenant Auth, RBAC, Skills, and Positions. See **ServizDesk Permission Management Specification V2**. | User, Role, PermissionMatrix, Skill, Position |
| `crm/` | Customer/Person/Contact triad and Site/Location logic. | Customer, Person, Contact, Address, Site, Location |
| `inventory/` | Item management, Kits, Pricebooks, and **Equipment (Tools)**. | InventoryItem, StockLevel, Serial/Lot, Kit, Pricebook, Equipment |
| `warehouse/` | Physical/Mobile Warehouses, Bins, and **Inventory Transfers**. | Warehouse, StorageLocation (Bins/Areas), InventoryTransfer |
| `procurement/` | Purchasing, Receiving, **Vendor Bills**, and **RMAs**. | Vendor, PurchaseOrder, Receiving, VendorBill, RMA |
| `service/` | Quotes, **Service Requests**, WorkOrders, Invoices, and Ledger. | Quote, Service Request, WorkOrder, Invoice, LedgerEntry |
| `maintenance/` | Asset Lifecycle | Asset, MaintenancePlan, Warranty |
| `tasks/` | SOP-instantiated check-lists and labor tracking. | Task, TaskTodo, TaskTimeEntry, SOP |
| `scheduling/` | Resource Timing | Schedule, TechnicianAvailability, Appointment |
| `pricing/` | Financial Rules | Pricebook, MultiCurrency, TaxJurisdiction |
| `automation/` | **SOP Workflows**, Steps, and resource requirements. | Workflow, EventTrigger, Condition, Action, SOPWorkflow, SOPStep |
| `workforce/` | **WorkGroups**, **WGDivisions**, and Crew teams. | WorkGroup, WGDivision, Crew |
| `fleet/` | **Vehicle** maintenance, mileage, and mobile stock. | Vehicle, VehicleMaintenance, VehicleMileage, MobileStock |
| `infrastructure/`| Audit events, Sequences, and the 25-entity Note/Document Arc. | SystemAudits, SequenceTracker, StorageTracker, Note, Document |

## 10.1 Key Libraries & Packages
| Library / Package | Purpose |
|-------------------|---------|
| `django-storages` + `boto3` | Routes all `FileField` and `ImageField` uploads to DigitalOcean Spaces (S3-compatible) in production |
| `stripe>=11.0.0` | Official Stripe Python SDK for all Stripe API interactions (Billing, Checkout, Connect, Webhooks) |
| `celery` | Asynchronous task queue for background jobs |
| `redis` (via redis-py) | Celery message broker; session-level permission cache; MFA OTP ephemeral storage (see Section 8.6) |
| `python-decouple` | Environment variable management; all secrets and environment-specific config injected via environment variables, never hardcoded |
| `WeasyPrint` | Server-side PDF generation for Plus/Pro tier (not used in Lite) |
| Postmark Python SDK | Transactional email dispatch via Postmark |
| `django-axes` | Login lockout enforcement — tracks failed login attempts per IP and per username; auto-unlock after 30 minutes (see Section 8.7) |
| `django-csp` | Content Security Policy middleware — generates per-request nonces and sets the `Content-Security-Policy` header. Must not be replaced with a static Nginx header (see Section 8.8) |
| `pusher` (Python SDK) | Fires Pusher push events from Django views and Celery tasks to subscribed browser clients (see Section 6.6) |
| Twilio Python SDK | OTP SMS delivery for MFA authentication. Required for all tiers — MFA is available across all plan levels when the Administrator enables it. |
| `pyotp` (or equivalent) | Cryptographically random OTP generation. TOTP-compatible; generates 6-digit numeric codes with configurable validity windows. |

## 10.2 Prohibited Patterns

| Prohibited Pattern | Reason |
|--------------------|--------|
| SQLite in any environment | Does not support PostgreSQL RLS; breaks tenant isolation architecture |
| Auto-incrementing integer primary keys | Breaks future offline-mobile sync capability; UUIDv4 required everywhere |
| Hardcoded secrets in `settings.py` | Security risk; all secrets must be injected as environment variables |
| Generic Foreign Keys (GFKs) | Incompatible with PostgreSQL RLS enforcement |
| Direct database reads between SDP and SDTA | All inter-application data exchange must use the Internal REST API |
| Custom card entry forms posting to ServizDesk servers | Violates SAQ A PCI compliance; all card collection must use Stripe Checkout or Stripe Connect |
| Storing tenant attachments on production server filesystem | Prevents horizontal scaling; all file storage must use object storage in production |
| Running Redis on the same Droplet as the web server | Resource contention risk; Redis must run on a dedicated instance |
| Soft-delete by default | Hard-delete is the standard unless explicitly required by a status lifecycle specification |
| Vanilla CSS as primary styling mechanism | Bootstrap 5.3 is the standard; vanilla CSS permitted only in a small `site.css` for branding overrides |
| Alpine.js or Hyperscript | Ruled out through initial release; HTMX v2.x is the only approved dynamic interaction library. Alpine.js may be reconsidered as a targeted Plus-tier addition if a specific interactive component requires stateful local behavior (see §3.2 Frontend evolution note). |
| Cross-Module Permission Bleed | Access must be checked against the specific Resource Key (e.g., Invoice), regardless of the current UI context (e.g., Customer Page). |

---

# 11. Sales Tax Compliance

| Item | Details |
|------|---------|
| Minnesota | SaaS is taxable in Minnesota. Must register with MN Department of Revenue. File monthly or quarterly depending on volume. |
| Other States | Economic nexus generally triggered at $100,000 revenue or 200 transactions. Monitor thresholds annually. |
| Recommended Tool | Stripe Tax (~0.5% of taxable revenue) — integrates directly with Stripe Billing to automate tax calculation, collection, and reporting. |

---

# 12. Document Relationships

| Relationship | Document |
|--------------|----------|
| Supersedes | ServizDesk Technical Architecture V1 |
| Supersedes | Open Technical Decisions in Section 10 of ServizDesk Product Tier Map V2 |
| Depends On / Validates Against | ServizDesk Product Tier Map V2 |
| Depends On / Validates Against | ServizDesk Lite MVP V4 Specification |
| Depends On / Validates Against | ServizDesk Platform (SDP) Specification V2 |
| Depends On / Validates Against | ServizDesk Pricing & Billing Specification V2 |
| Depends On / Validates Against | ServizDesk SDTA Data Models V6 |
| Defers To | Plus Specification (future) — SMS provider international pricing |
| Defers To | Pro Specification (future) — REST API rate limits, advanced PDF generation scope |
| Precedes / Governs | Any repository README.md or code-level technical implementation document built during Phase 1 |

---

**End of Document**
