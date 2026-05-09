# ServizmaDesk Technical Architecture
**Document Status:** Working Draft
**Document Version:** V1
**Classification:** Internal — Technical Dependency

---

# 1. Executive Summary

This document defines the core technical architecture, technology stack, and third-party integrations required to build and deploy the ServizmaDesk software suite. It serves as the foundational engineering blueprint for both the **ServizmaDesk Platform (SDP)** and the **ServizmaDesk Tenant App (SDTA)**.

All technical decisions listed here reflect the constraints and boundaries defined in the *ServizmaDesk Product Tier Map V2* and the *ServizmaDesk Lite MVP V4 Specification*.

---

# 2. Core Technology Stack

## 2.1 Backend Framework
- **Language:** Python 3.12+
- **Framework:** Django 5.x
- **Philosophy:** "Fat Models, Thin Views." Business logic resides in the model layer or dedicated service classes, never directly in the views.

## 2.2 Frontend Stack
- **Architecture:** Server-Side Rendered (SSR) HTML via Django Templates.
- **Dynamic Interactions:** HTMX v2.x. (Explicitly ruling out Alpine.js or Hyperscript to keep the frontend bundle minimal and strictly driven by Django templates).
- **Styling:** Tailwind CSS (via Tailwind CLI/PostCSS) is the official styling engine. Vanilla CSS is not to be used as a replacement, only for extreme edge cases.
- **Icons:** SVG icons (e.g., Heroicons).

## 2.3 Database Layer
- **Relational Database:** PostgreSQL 16+ (Required in all environments. SQLite is strictly prohibited even for local development, as it breaks the requisite Row-Level Security architecture).
- **Primary Keys:** UUIDv4 is **mandatory** for all primary and foreign keys globally. Auto-incrementing integers are strictly prohibited to support future offline-mobile syncing.

## 2.4 Server & Hosting (Infrastructure)
- **Cloud Provider:** DigitalOcean (Recommended for bootstrapped scaling before migrating to AWS).
- **Compute:** DigitalOcean Droplets (Ubuntu 22.04 LTS+) or DigitalOcean App Platform.
- **Web Server:** Nginx (acting as a reverse proxy and static file server).
- **Application Server:** Gunicorn (WSGI HTTP Server).

---

# 3. Third-Party Integrations & Services

## 3.1 Payment Processing (Stripe)
- **SDK Variant:** Official Stripe Python SDK (`stripe>=11.0.0`).
- **ServizmaDesk Corporate Billing (SDP):** Uses **Stripe Billing** and **Stripe Checkout**. Used to charge the tenants their monthly/annual subscription fees. ServizmaDesk does not touch raw card data.
- **Tenant Payment Processing (SDTA):** Uses **Stripe Connect (Standard integration)**. Tenants securely link their own Stripe accounts via OAuth. SDTA generates **Stripe Payment Links** via the Stripe API for invoices. No deep embedded card forms are used in the Lite tier.

## 3.2 Transactional Email (Postmark)
- **Provider:** Postmark
- **Purpose:** All internal platform emails (Welcome emails, Password Resets, Provisioning failures, Critical System Alerts).
- SDTA does not send emails on behalf of tenants in the Lite tier.

## 3.3 SMS / Telephony (Deferred implementation)
- **Decision:** SMS messaging is explicitly out of scope for the Lite tier. 
- **Future:** Provider selection (e.g., Twilio vs Plivo) and architectural decisions are deferred to the corresponding Plus Tier specification.

## 3.4 File & Attachment Storage
- **Provider:** DigitalOcean Spaces (S3-Compatible Object Storage) or AWS S3.
- **Local Dev Fallback:** During local development, developers must use the standard local filesystem (`MEDIA_ROOT` via `FileSystemStorage`) to avoid friction and unnecessary API costs.
- **Reasoning:** Storing tenant attachments (PDFs, images) on the production Droplet filesystem is strictly prohibited. It prevents horizontal scaling and risks filling up the server's disk space.
- Django leverages `django-storages` with the `boto3` backend to natively route all `FileField` and `ImageField` uploads directly to the object storage bucket in production.

## 3.5 Asynchronous Workers & Queues
- **Message Broker:** Redis (In production, a horizontally scalable Managed Redis service instance on DigitalOcean is preferred, or a separate standard Droplet. Running Redis on the same Droplet as the Web Server is prohibited).
- **Task Queue:** Celery
- **Purpose:** Handling tasks that must not block the web response cycle. Example: The 60-day background data deletion worker, heavy CSV exports, and Stripe Webhook processing.

## 3.6 Document Printing & PDF Generation
- **Lite Tier (Current):** CSS Print Media Queries. Developers must write robust `@media print` CSS rules so that when a user prints an Invoice directly from Google Chrome, the output is a pristine 8.5x11 document without UI buttons or navigation menus.
- **Plus/Pro Tier (Future):** **WeasyPrint** (Python library) will be the designated engine when server-side automated PDF generation is ultimately introduced.

---

# 4. Multi-Tenancy Architecture (SDTA)

ServizmaDesk uses a **Shared Database, Shared Schema** multi-tenant architecture. 

## 4.1 The Three-Layer Isolation Model
To ensure enterprise-grade security and prevent data leakage between tenants, isolation is enforced at three distinct layers:

1. **Database Schema (Foreign Keys):** Every table in SDTA must include a `tenant_id` (UUID) foreign key.
2. **Application Middleware (Django):** A custom Django middleware extracts the `tenant_id` from the authenticated user's session and automatically scopes all ORM queries (e.g., `Customer.objects.all()`) to that specific tenant using a custom model manager.
3. **Database Security (PostgreSQL RLS):** **Row-Level Security (RLS)** is enabled on all tables in the PostgreSQL database. This acts as the final failsafe. Even if a developer accidentally writes a raw SQL query or bypasses the Django ORM, the database user itself is scoped to the current tenant, making it physically impossible for tenant A to query tenant B's data.

---

# 5. Security & Compliance

## 5.1 Authentication
- **Session Management:** Standard Django session-backed authentication.
- **Password Hashing:** PBKDF2 (Django default) or Argon2.

## 5.2 Webhooks (Stripe)
- All incoming webhooks from Stripe must verify the cryptographic signature (`STRIPE_WEBHOOK_SECRET`) before parsing the payload.
- Webhook endpoints must be fully idempotent (processing the same event twice safely).

## 5.3 Data Retention
- Logical Soft-Delete is generally prohibited unless explicitly specified by the status lifecycle.
- Records are hard-deleted unless blocked by relational integrity constraints (e.g., cannot delete a Customer with an attached Invoice).
- Deleted tenant accounts enter a 60-day grace period before Celery workers permanently hard-delete the corresponding UUID data.

---

# 6. SDTA / SDP Internal Communication

Communication between the ServizmaDesk Tenant App (SDTA) and the ServizmaDesk Platform (SDP) relies on an **Internal REST API**.

- Direct database reads across applications are strictly prohibited.
- SDTA securely queries the SDP API at runtime to verify a tenant's subscription status, seat counts, storage limits, and active features.
- A secure internal token (e.g., JWT or shared secret) is used to authenticate requests between the two internal services.

---

# 7. Tier-Gating Implementation Pattern

To enforce tier limits (e.g., blocking Lite users from accessing Plus features), developers must rely on a standardized tier-gating approach within the SDTA Django application.

1. **Backend Enforcement (Primary Shield):** Core enforcement happens at the middleware and decorator level. A custom `@tier_required('plus')` decorator will be applied to Django view functions. If a Lite user attempts to hit a Plus view directly via URL, the system throws a standardized `TierUpgradeRequired` exception.
2. **Frontend UI (Secondary Shield):** Django Template Conditionals (`{% if request.tenant.tier == 'plus' %}`) are used to conditionally render, gray out, or hide UI elements (like the "Automations" button) to guide behavior securely without exposing broken application states.

---

# 8. Development & Staging Environments

1. **Environment Variables:** All secrets and environment-specific configs must be injected as environment variables. The `python-decouple` (or identical library) must be used. Hardcoded secrets in `settings.py` are strictly prohibited.
2. **Local Environment:** Development should parallel production closely using a Docker/Docker Compose workflow (spinning up Django, PostgreSQL 16+, and Redis). As established in Section 2.3, local SQLite falls short of testing PostgreSQL RLS policies and is banned.
3. **Staging Environment:** A dedicated exact replica of the production architecture must be maintained on a separate subdomain (e.g., `staging.servizmadesk.com`) and connected to Stripe Test Mode for all pre-deployment validation. Both SDP and SDTA must maintain mirrored staging instances.

---

# 9. Document Relationships

This architectural blueprint acts continuously alongside other system documentation:
- **Depends On / Validates against:** *ServizmaDesk Product Tier Map V2* and the *ServizmaDesk Lite MVP V4 Specification*.
- **Supersedes:** The "Open Technical Decisions" listed in Section 10 of the Tier Map. Those decisions are now considered closed and codified within this document.
- **Defers To:** Future Plus/Pro Specifications for detailed architectures regarding SMS, system email sending, and advanced external integrations.
- **Precedes / Governs:** Any repository `README.md` or code-level technical implementation document built during Phase 1.

---
**End of Document**
