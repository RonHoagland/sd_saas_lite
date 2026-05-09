# ServizmaDesk Onboarding Checklist Specification (SDTA)
**Document Version:** V2
**Status:** Working Draft
**Supersedes:** V1

## 1. Overview
This document defines the automated triggers used to mark onboarding checklist items as "Complete" in the `OnboardingState` model. 

## 2. Onboarding Items & Triggers

### 2.1 Complete Tenant Profile
- **Logic**: Ensures the company's identity is established for document headers.
- **Trigger**: The `TenantPreference` record for the tenant must have the following fields **non-empty (not null or empty string)**:
    - `address`, `city`, `state`, `zip`, `country`, `phone`.
- **Note**: The `company_name` is seeded during provisioning and does not satisfy this trigger on its own.

### 2.2 Set Preferences
- **Logic**: Ensures localization and financial defaults are reviewed.
- **Trigger**: The `TenantPreference` record must have values that differ from the "null/placeholder" provisioning defaults for the following:
    - `timezone` (Must not be UTC/Null)
    - `date_format` (Must be explicitly selected)
    - `default_payment_terms` (Must be explicitly selected)

### 2.3 Add Your First Customer
- **Logic**: Encourages the user to enter data.
- **Trigger**: At least one record exists in the `Customer` table for this `tenant_id`.

### 2.4 Add Your First Asset
- **Logic**: Encourages the use of asset tracking.
- **Trigger**: At least one record exists in the `Asset` table for this `tenant_id`.

### 2.5 Add Your First Product or Service
- **Logic**: Ensures the product catalog has at least one entry so the user can create line items on Quotes, Work Orders, and Invoices.
- **Trigger**: At least one record exists in the `Product` table for this `tenant_id`.

### 2.6 Connect Stripe (Optional)
- **Logic**: Tracks payment readiness.
- **Trigger**: A record exists in the `StripeConnection` table with `is_active = True`.

### 2.7 Add Additional Employees (Optional)
- **Logic**: Encourages team expansion.
- **Trigger**: The count of `User` records for this `tenant_id` is **greater than 1**.

## 3. Automation Mandate
- **Triggers**: Whenever a write operation occurs on `TenantPreference`, `Customer`, `Asset`, `Product`, `StripeConnection`, or `User`, a background signal (e.g., Django `post_save`) MUST evaluate the corresponding logic and update the `checklist_items` JSONField in the `OnboardingState` record.
- **Visibility**: Once all non-optional items (2.1–2.5) are marked as `True`, the dashboard checklist widget should be automatically hidden for the tenant.
