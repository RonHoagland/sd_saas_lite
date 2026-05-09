# Backend Readiness Gap Report

**Objective:** Determine if sufficient information exists in the current specifications to begin building the ServizmaDesk backend (database queries, APIs, background workers, and business logic) without the UI.

## Executive Summary
While the business logic, architectural boundaries, and high-level data models are extremely well-defined, a backend engineer needs **strict, low-level technical specifications** to write production-ready code. Building the backend right now would require making dozens of assumptions about data types, API payloads, and third-party integrations.

## Missing Technical Requirements

Before backend development can begin, the following technical details must be defined:

### 1. Granular Django Model Definitions
The [ServizmaDesk_Top_Down_Specifications.md](file:///Volumes/SolDev_10/SaaS/ServizmaDesk_Top_Down_Specifications.md) lists fields (e.g., "Amount — Currency", "Status — Dropdown"), but backend code requires exact constraints.
*   **Data Types & Constraints:** What is the `max_length` for string fields? What are the `max_digits` and `decimal_places` for currency fields (e.g., 10,2)? Which fields are `null=True` vs `null=False` at the database level?
*   **Enums/Choices:** We need the exact, exhaustive list of statuses for every stateful object (e.g., Work Order Statuses: Draft, Scheduled, In Progress, Complete, Canceled? Invoice Statuses: Draft, Sent, Partially Paid, Paid, Void, Written-Off?).
*   **Foreign Key Behaviors:** The spec mentions a "hard-delete" model. Does deleting a `Customer` trigger a database-level `CASCADE` delete of all their `Assets`, `WorkOrders`, and `Invoices`, or is it a `RESTRICT` that prevents deletion until children are manually deleted?

### 2. Multi-Tenancy Row-Level Security (RLS) Implementation
The architecture specifies "Shared Database, Shared Schema with three-layer isolation (field, middleware, RLS)."
*   **Implementation Strategy:** How exactly is the PostgreSQL RLS being enforced via Django? Are we using a specific package (like `django-tenant-schemas` or `django-multitenant`), or writing custom middleware that sets a PostgreSQL session variable (e.g., `SET app.current_tenant = 'uuid'`)? This foundational decision must be made before creating the first migration.

### 3. Internal REST API Contract (SDP <-> SDTA)
The SDP controls provisioning and billing, sending commands to SDTA. We need the exact OpenAPI/Swagger-style contract for this internal communication.
*   **Endpoints:** E.g., `POST /api/internal/provision-tenant`, `POST /api/internal/lock-tenant`, `POST /api/internal/update-seat-count`.
*   **Payloads:** What exact JSON payload does SDP send to SDTA to provision a tenant? (e.g., Tenant Name, Admin First Name, Admin Last Name, Admin Email, Admin Hashed Password, Subdomain?).
*   **Authentication:** How do SDP and SDTA authenticate with each other? (e.g., A shared secret token in the `Authorization` header?).

### 4. Stripe Webhook Mapping
SDP relies heavily on Stripe for billing and the loyalty reward.
*   **Events Strategy:** Which specific Stripe webhook events must the SDP backend listen to? (e.g., `checkout.session.completed`, `customer.subscription.updated`, `invoice.payment_succeeded`, `invoice.payment_failed`).
*   **State Transitions:** Exactly how do these webhooks map to SDP database state changes? (e.g., If `invoice.payment_failed` is received, does SDP immediately call the SDTA internal API to lock the account, or is there a grace period?).

### 5. Object Storage (DigitalOcean Spaces) Structure
The SDTA application handles document uploads.
*   **Pathing Strategy:** What is the folder structure inside the DO Space? (e.g., `/{tenant_id}/documents/{object_id}/{uuid}-{filename}`).
*   **Pre-signed URLs:** Will the backend generate short-lived pre-signed URLs for clients to download documents securely, or proxy the files through Django?

### 6. Background Task (Celery) Definitions
*   **Triggers:** When exactly does the Celery worker check for the Loyalty Reward? (e.g., Does it run a nightly cron job checking all tenants whose renewal date is tomorrow?).
*   **Retry Logic:** If a background task fails (e.g., Postmark API is down when sending a welcome email), what is the Celery retry policy? (e.g., Exponential backoff, max 5 retries?).

---
**Conclusion:** To begin backend development securely and accurately, we need a **"Backend Implementation Schema & API Contract"** document that defines these exact data types, API payloads, and integration mappings.
