# Backend Implementation Definition ToDo

**Objective:** This document serves as a checklist and Q&A form to define all strict, low-level technical specifications required before a backend engineer can begin writing production-ready code for ServizmaDesk (SDP and SDTA). 

Please provide answers or confirmation for each line item below. Once completed, this document will serve as the "Backend Implementation Schema & API Contract."

---

## 1. Granular Django Model Definitions

We need exact database-level constraints for every field mentioned in the Top-Down Specifications.

### A. Field Types & Constraints
- [X] **String/Text Limits:** What is the maximum character length (`max_length`) for standard text fields? 
  - [X] Standard Name fields (e.g., First Name, Customer Name)? *(e.g., 255)*
  - [X] Short fields (e.g., Phone Numbers, ZIP Codes)? *(e.g., 20)*
  - [X] Long text areas (e.g., Notes, Descriptions)? *(e.g., TextField, unlimited)*
- [X] **Currency Constraints:** What are the `max_digits` and `decimal_placeXs` for monetary amounts? *(e.g., `DecimalField(max_digits=12, decimal_places=2)` handles up to $9,999,999,999.99)*
- [X] **Nullability Rules:** Which core fields are strictly required (`null=False, blank=False` at the DB schema level) vs. optional? (We assume fields flagged "required" in the UI spec map to `null=False`).

### B. Enums & Status Workflows
Define the exact, exhaustive list of valid choices (enums) for every stateful object.
- [X] **Quote Statuses:** *(e.g., Draft, Sent, Accepted, Declined, Canceled)*
- [X] **Work Order Statuses:** *(e.g., Draft, Scheduled, Dispatched, In Progress, Complete, Canceled)*
- [X] **Invoice Statuses:** *(e.g., Draft, Sent, Partially Paid, Paid, Void, Written-Off)*
- [X] **Task Statuses (Lite):** *(e.g., pending, completed)*
- [X] **Employee Statuses:** *(e.g., Active, On Leave, Inactive, Terminated)*

### C. Foreign Key 'On Delete' Behaviors
The spec requires a "hard-delete" model (no soft-delete or trash bin). How does the DB handle a request to delete a parent object that has children?
- [X] **Customer Deletion:** If a user clicks delete on a Customer record, does it `CASCADE` delete all their Quotes, Work Orders, and Invoices automatically, or does it `RESTRICT`, forcing the user to delete invoices first? *(Recommendation: RESTRICT if financial records exist, CASCADE if only Contacts/Addresses exist.)*
- [X] **Asset Deletion:** If an Asset is deleted, does it `CASCADE` delete historical Work Orders tied to it, or `SET_NULL` on the Work Order's asset FK to keep the service history?

---

## 2. PostgreSQL Row-Level Security (RLS) Strategy

The spec defines "Shared Database, Shared Schema with three-layer isolation (field, middleware, RLS)." Both SDP and SDTA are built on Django.

- [X] **Library Selection:** Do we write custom Django middleware that executes `SET app.current_tenant = %s` on every request, or do we implement a specific package like `django-rls` or `django-multitenant`?
- [X] **Superuser Override:** How do background workers (Celery) or admin scripts bypass RLS when performing system-wide updates (e.g., compiling global billing metrics)? *(e.g., `SET app.current_tenant = "system"`, or using a dedicated non-RLS database role?)*

---

## 3. Internal REST API Contract (SDP ↔ SDTA)

SDP issues commands to SDTA. We need exact endpoint paths and JSON payloads.

- [ ] **Provisioning Endpoint (`POST /internal/api/provision-tenant`):** 
  - Required payload from SDP? *(e.g., `{"tenant_id": UUID, "tenant_name": string, "admin_email": string, "admin_first_name": string, "admin_last_name": string, "hashed_password": string, "subdomain": string}`)*
- [ ] **Lock/Unlock Account Endpoint (`POST /internal/api/update-status`):**
  - Required payload? *(e.g., `{"tenant_id": UUID, "status": "ACTIVE" | "LOCKED"}`)*
- [ ] **Seat Update Endpoint (`POST /internal/api/update-limits`):**
  - Payload defining max purchased seats and storage limits?
- [ ] **Authentication Strategy:** How does SDTA verify the request came from SDP? *(e.g., A shared long-lived Bearer token established at deployment time?)*

---

## 4. Stripe Webhook Mapping to Database State

SDP is the source of truth for billing, reacting to Stripe webhooks.

- [ ] **`checkout.session.completed`:** Triggers Phase 2 provisioning (creates Tenant Workspace in SDTA).
- [ ] **`invoice.payment_succeeded`:** Extends subscription end dates, updates internal ledger. Does it process the 0.1% Loyalty Rebate calculation immediately, or does that only happen once a year?
- [ ] **`invoice.payment_failed`:** Does this trigger an immediate `LOCK` command to SDTA, or is there a dunning/grace period first? (If grace period, how long?)
- [ ] **`customer.subscription.deleted`:** (e.g., Churn). Triggers account status update to `READ_ONLY` or starts the 60-day permanent deletion countdown?

---

## 5. Object Storage (DigitalOcean Spaces) Pathing

- [ ] **File Path Structure:** To prevent tenant cross-talk, what is the defined folder structure inside the Space? *(e.g., `/{tenant_id}/documents/{table_name}/{object_id}/{uuidv4_filename}.ext`)*
- [ ] **Access Mechanism:** For downloading, does the SDTA backend generate short-lived, pre-signed AWS S3 URL links (offloading bandwidth to DigitalOcean), or does the Django backend proxy the file completely? *(Recommendation: Pre-signed URLs for performance)*

---

## 6. Background Task (Celery) Behaviors

- [ ] **Loyalty Reward Trigger:** Should the worker checking for `$100K+` volume run daily (scanning for any tenants renewing *tomorrow*) or monthly?
- [ ] **Retry Policy:** What is the standard Celery retry policy if a third-party API (like Postmark for emails or Stripe for billing) times out? *(e.g., Exponential backoff: Retry at 1 min, 5 min, 15 min, 1 hr, then fail and alert?)*
