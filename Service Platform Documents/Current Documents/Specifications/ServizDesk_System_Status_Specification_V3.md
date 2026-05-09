# ServizDesk System Status Specification V3

**Date:** March 2026
**Scope:** SDTA Backend Lifecycle & State Machine
**Status:** Working Draft
**Supersedes:** V2

---

## 1. Overview
This document defines the lifecycle, state transitions, locking mechanisms, and audit requirements for all major entities within the ServizDesk ecosystem. These rules ensure operational flexibility while maintaining strict accounting integrity and a reliable audit trail.

---

## 2. Customer Lifecycle
**Transitions:** `Active` ↔ `Inactive` (reversible), `Active` → `Hold` → `Active` (reversible), `Active`/`Inactive` → `Closed` (terminal)

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Standard operating state. | Sales and Work Orders can be created freely. |
| **Inactive** | No sales activity for an extended period. | A review is required before new sales/Work Orders are initiated. Can be reactivated to Active. |
| **Hold** | Operational or financial issue identified. | **Blocked**: No new work or sales permitted without explicit permission. Requires a `hold_date` and `hold_reason`. Can be released back to Active. |
| **Closed** | Account terminated. | Record is locked for new activity. Requires a `closed_at` timestamp and `closed_reason`. **Terminal** — cannot be reopened; a new Customer record must be created if the relationship resumes. |

> [!IMPORTANT]
> All Customer status changes must be performed by an Administrator.

---

## 3. Quote Lifecycle
**Transitions:** `Draft` → `Sent` → `Viewed` → `Accepted` / `Rejected` → `Converted` / `Expired`

*   **Locking**: Once a quote reaches `Sent`, `Viewed`, `Accepted`, `Rejected`, `Converted`, or `Expired`, it is **Locked** and cannot be edited.
*   **Reversion**: An Admin is required to move a quote out of `Converted`. A `reason` is mandatory.
*   **Expiration**: A Quote moves to `Expired` automatically if not `Accepted` by its `expiration_date`.
*   **Date Handling**: Moving a quote backward in the progression clears any previously set status dates (Sent Date, Accepted Date, etc.).

---

## 4. Work Order Lifecycle
**Transitions:** `Draft` → `Scheduled` → `In Progress` → `On Hold` → `Completed` / `Closed` / `Cancelled`

*   **Trigger (Scheduled)**: Automatically set when a `due_date` is assigned.
*   **Trigger (In Progress)**: Set when a `start_date` is added or any `TimeEntry` is recorded. **Blocked**: Cannot revert to `Draft` once work has started.
*   **Hold Logic**: Requires a `hold_date` and `reason`. A Work Order on "Hold" can only transition back to `In-Progress`.
*   **Locking**: `Completed`, `Closed`, and `Cancelled` statuses are **Locked**. Reversion requires an Admin and a `reason`, and can only move back to `In Progress`.
*   **Closed**: Automatically set or manually triggered when all work and documentation are verified. Requires a `closed_at` timestamp.

---

## 5. Sales & Invoice Management

### 5.1 Invoice Lifecycle
**Transitions:** `Draft` → `Issued` → `Viewed` → `Partially Paid` → `Paid` / `Overdue` → `Void` / `Written Off`

*   **Issued**: Triggers an `issued_date`. Line items are **Locked**.
    *   **Corrections**: If changes are needed, a new invoice must be created (marked as a **Credit Memo**) to preserve the audit trail.
*   **Viewed**: Set when the customer opens the invoice or Stripe payment link. Informational — does not block payment or other transitions.
*   **Payment Reversion**: If a payment fails or is voided, an invoice may move back from `Paid` to `Partially Paid` or `Issued`.
*   **Paid**: Once total payments $\ge$ invoice total, the record is **Locked** permanently.
*   **Overdue**: Automatically set when current date > `due_date` and status is not `Paid`.
*   **Void**: Requires a `void_date` and reason. Once voided, a new invoice must be issued if the work is still billable.
*   **Written Off**: Final state for uncollectible debt. Requires Admin approval and a reason. Locked.

### 5.2 Invoice Payments
**Statuses:** `Paid` \| `Failed` \| `Voided`

Each payment record tracks two distinct totals:
1.  **Amount Paid**: The amount successfully captured and applied to the invoice balance ($0$ to total).
2.  **Amount Tried**: The amount attempted during the transaction (always positive, up to total).

---

## 6. Procurement (Purchase Orders)

### 6.1 Purchase Order Lifecycle
**Transitions:** `Draft` → `Sent` → `Partially Received` → `Received` → `Cancelled`

*   **Draft**: PO is being assembled. Vendor, line items, and expected dates can be edited freely.
*   **Sent**: PO has been submitted to the vendor. Triggers a `sent_date`. Line items are **Locked**.
    *   **Billing**: Sending a PO automatically generates a **Vendor Bill** record in `Draft` status.
*   **Received**: Set automatically when all `PO Line Items` are marked as `Received`. The record is then **Locked**.
*   **Cancelled**: Reversion requires an Admin and a `reason`. Automatically cancels the associated `Vendor Bill` record.

### 6.2 PO Line Items (POLI)
**Transitions:** `Open` → `Partially Received` → `Received`

*   **Status Mapping**: Driven by `Receiving` records. Once total received quantity $\ge$ total ordered, status moves to `Received`.
*   **Override**: Users can manually override a status, but a `reason` is required.

---

## 7. Vendor Bills (Accounts Payable)
**Transitions:** `Draft` → `Received` → `Partially Paid` → `Paid` / `Overdue` → `Void`

| Status | Trigger |
| :--- | :--- |
| **Draft** | Default state upon PO issuance. System-generated record anticipating the vendor invoice. |
| **Received** | Vendor invoice received and matched to the PO. Automatically set when the linked PO/POLI are fully received and invoice is recorded. |
| **Partially Paid** | Payment(s) issued to vendor < Total Bill. |
| **Paid** | Total payments $\ge$ Vendor Invoice Total. |
| **Overdue** | Automatically set when current date > `due_date` and bill is not `Paid`. |
| **Void** | Bill cancelled or voided. Requires a `reason`. **Locked**. Reversion requires Admin. |

---

## 8. Asset Lifecycle
**Transitions:** `Active` → `Inactive` → `Decommissioned`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Equipment is operational and in service. | Work Orders and PMs can be created freely against this asset. |
| **Inactive** | Equipment is temporarily out of service. | Not available for new Work Orders or PM scheduling. Historical records preserved. Can be reactivated to Active. |
| **Decommissioned** | Equipment permanently retired. | **Locked**: No new Work Orders, PMs, or Agreements. Record preserved for service history. Reversion to Active requires Admin and a `reason`. |

---

## 9. Service Request Lifecycle
**Transitions:** `New` → `Triaged` → `Converted to Work Order` / `Converted to Quote` / `Cancelled`

*   **New**: Default state on creation (phone intake, portal submission, web widget).
*   **Triaged**: Dispatcher has reviewed and assessed the request. Notes and asset identification may be added.
*   **Converted to Work Order**: A Work Order has been generated from this Service Request. The WO carries a backlink FK. **Locked** — Service Request cannot be edited after conversion.
*   **Converted to Quote**: A Quote has been generated instead. **Locked**.
*   **Cancelled**: Request was cancelled or determined invalid. Requires a `reason`. **Locked**.

---

## 10. CRM Pipeline

### 10.1 Lead Lifecycle
**Transitions:** `New` → `Contacted` → `Qualified` → `Converted` / `Lost`

*   **New**: Lead entered into the system.
*   **Contacted**: Initial outreach completed.
*   **Qualified**: Lead meets criteria for a sales opportunity.
*   **Converted**: Lead has been converted to a Customer and/or Opportunity. **Locked**.
*   **Lost**: Lead determined to be non-viable. Requires a `reason`. Can be reopened by Admin.

### 10.2 Opportunity Lifecycle
**Transitions:** `Open` → `Won` / `Lost`

*   **Open**: Active sales opportunity. Quotes can be generated against it.
*   **Won**: Deal closed — customer accepted. **Locked**. Reversion requires Admin and `reason`.
*   **Lost**: Opportunity did not close. Requires a `reason`. Can be reopened by Admin.

---

## 11. Service Agreements & Preventative Maintenance

### 11.1 Agreement Lifecycle
**Transitions:** `Pending` → `Active` → `Inactive` / `Expired` / `Cancelled`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Pending** | Agreement created but not yet in effect. | Start date has not been reached. PM records can be created in preparation. |
| **Active** | Agreement is in force. | PMs generate Work Orders per schedule. Billing active. |
| **Inactive** | Agreement template retired from active offering. | No longer available for new CustomerAgreements. Existing CustomerAgreements linked to this template continue to function. Can be reactivated to Active by Admin. |
| **Expired** | End date has passed. | **Locked** for new PM generation. Existing WOs in progress may be completed. Can transition to Active on renewal. |
| **Cancelled** | Agreement terminated early. | Requires a `reason` and `cancelled_at` timestamp. **Locked**. Reversion requires Admin. |

### 11.2 Preventative Maintenance Lifecycle
**Transitions:** `Active` → `Paused` → `Expired` / `Cancelled`

*   **Active**: PM schedule is running. Auto-generates Work Orders per schedule.
*   **Paused**: Temporarily suspended. No new WOs generated. Can resume to Active.
*   **Expired**: Parent Agreement has expired or PM end date reached. **Locked** for generation.
*   **Cancelled**: PM terminated. Requires a `reason`. **Locked**. Reversion requires Admin.

### 11.3 CustomerAgreement Lifecycle (Per-Customer Instance)
**Transitions:** `Pending` → `Active` → `Expired` / `Cancelled`

*   **Pending**: Agreement coverage has been set up for the customer/asset pair but the `start_date` has not been reached.
*   **Active**: Coverage is in effect. PM schedules linked to this enrollment are generating Work Orders per the Agreement template's configuration.
*   **Expired**: End date has passed. **Locked** for new PM generation. Requires manual renewal (or Auto-Renew trigger) to return to Active.
*   **Cancelled**: Enrollment terminated early. Requires a `reason` and `cancelled_at` timestamp. **Locked**. Reversion requires Admin.

> [!NOTE]
> Unlike the Agreement template lifecycle (Section 11.1), `CustomerAgreement` does not have an `Inactive` status. The `Inactive` status applies only to the Agreement template — to retire it from new enrollments while allowing existing `CustomerAgreement` enrollments to continue functioning.

---

## 12. WorkGroup Lifecycle
**Transitions:** `Open` → `In Progress` → `Completed` / `Cancelled`

*   **Open**: WorkGroup created, Work Orders being assembled.
*   **In Progress**: At least one Work Order in the group has started.
*   **Completed**: All Work Orders in the group are Completed or Closed. **Locked**.
*   **Cancelled**: Group cancelled. Requires a `reason`. Does not automatically cancel individual Work Orders — those must be handled independently.

---

## 13. Requisition Lifecycle
**Transitions:** `New` → `Approved` → `Partially Fulfilled` → `Fulfilled` / `Cancelled`

*   **New**: Technician has submitted the parts request.
*   **Approved**: Purchasing agent or Warehouse Manager has reviewed and approved.
*   **Partially Fulfilled**: Some line items have been fulfilled (via PO or inventory transfer), others pending.
*   **Fulfilled**: All line items fulfilled. **Locked**.
*   **Cancelled**: Request cancelled. Requires a `reason`. **Locked**.

---

## 14. RMA Lifecycle
**Transitions:** `Initiated` → `Shipped` → `Received by Vendor` → `Credited` / `Closed` / `Denied`

*   **Initiated**: RMA created, awaiting shipment back to vendor.
*   **Shipped**: Item sent to vendor. Tracking info recorded.
*   **Received by Vendor**: Vendor has acknowledged receipt.
*   **Credited**: Vendor has issued credit. Credit amount recorded. **Locked**.
*   **Closed**: RMA process complete (no credit scenario, or replacement received). **Locked**.
*   **Denied**: Vendor rejected the return. Requires a `reason`. **Locked**.

---

## 15. WorkFlow & Safety

### 15.1 WorkFlow Lifecycle
**Transitions:** `Draft` → `Active` → `Inactive`

*   **Draft**: WorkFlow is being defined. Steps, ToDos, Tools, and Inventory can be edited freely.
*   **Active**: WorkFlow is available for assignment to PMs and Work Orders. Structure is **Locked** — changes require creating a new version or reverting to Draft (Admin only, `reason` required).
*   **Inactive**: WorkFlow retired from active use. Existing PMs/WOs referencing it continue to function. Cannot be assigned to new records.

### 15.2 SafetyForm Lifecycle
**Transitions:** `Draft` → `Active` → `Inactive`

*   **Draft**: Form being designed. Fields can be edited.
*   **Active**: Form available for assignment to Work Orders. Structure is **Locked** to preserve integrity of completed answers.
*   **Inactive**: Form retired. Completed WOSFAnswers referencing it are preserved. Cannot be assigned to new Work Orders.

---

## 16. Equipment Lifecycle
**Transitions:** `Available` → `Checked Out` → `In Repair` → `Decommissioned`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Available** | Tool is in inventory, ready for checkout. | Can be checked out to an employee. |
| **Checked Out** | Tool is in an employee's custody. | Automatically set via Check In/Out record. Cannot be checked out to another employee until returned. |
| **In Repair** | Tool is being repaired or serviced. | Not available for checkout. |
| **Decommissioned** | Tool permanently retired. | **Locked**: Cannot be checked out. Record preserved for history. Reversion requires Admin. |

---

## 17. Fleet Maintenance

### 17.1 Vehicle Lifecycle
**Transitions:** `Active` → `Out of Service` → `Decommissioned`

*   **Active**: Vehicle is operational and can be assigned to employees and Work Orders.
*   **Out of Service**: Vehicle temporarily unavailable (repair, inspection). Cannot be assigned to new Work Orders. Existing assignments preserved.
*   **Decommissioned**: Vehicle permanently retired from fleet. **Locked**: No new assignments, mileage logs, or maintenance records. Reversion requires Admin.

### 17.2 Vehicle Maintenance Lifecycle
**Transitions:** `Scheduled` → `Completed` / `Overdue` / `Cancelled`

*   **Scheduled**: Maintenance is planned for a future date or odometer threshold.
*   **Completed**: Service performed. Requires `completed_date` and `odometer_at_service`. **Locked**.
*   **Overdue**: Automatically set when `scheduled_date` has passed or `odometer_current` exceeds `next_service_odometer` without completion.
*   **Cancelled**: Maintenance no longer needed. Requires a `reason`. **Locked**.

---

## 18. Employee Lifecycle
**Transitions:** `Active` → `On Leave` → `Inactive` → `Terminated`

| Status | Definition | Seat Billing | Rules |
| :--- | :--- | :--- | :--- |
| **Active** | Employee is working and has full system access per their role. | Counts against purchased seats. | Default state on creation. Login enabled. |
| **On Leave** | Employee is temporarily away (medical, personal, seasonal). | Counts against purchased seats. | System access suspended. Record and history fully preserved. Can return to Active. |
| **Inactive** | Employee is no longer actively working but not formally terminated. | Counts against purchased seats. | System access suspended. Used for seasonal workers or long-term leave. Can return to Active. |
| **Terminated** | Employment has ended. | **Does not count against purchased seats.** Seat becomes vacant. | Requires a `termination_date`. System access immediately revoked — all active sessions automatically invalidated on save (see below). Record is preserved for history. A new employee may be invited into the vacated seat without triggering an additional Stripe charge. Reversion to Active requires Admin and a `reason`. |

### 19.1 Automatic Session Revocation on Termination

When an employee's status transitions to `Terminated`, the system must **automatically revoke all active sessions** for that employee at the moment the status change is saved. This is not a manual step — it is a required side effect of the termination action.

**Implementation:** The `terminate_employee()` service function (called by the termination view) must execute the same revocation logic as the manual "Force Logout All Devices" action:

1. Delete all `django_session` records matching the employee's `user_id`.
2. Update all open `SessionLog` records for that employee: set `logout_at`, `force_logout_at` to now, and `force_logout_by` to the terminating Administrator's `user_id`.
3. Write a `SystemAudits` event: action `Terminated`, entity `User`, with the terminating Administrator's `user_id` recorded.

**Why this matters:** Without automatic revocation, a terminated employee with an active session could continue using the application for up to 8 hours (the maximum session timeout). This is unacceptable for offboarding — access must end at the moment of termination, not at the next natural session expiry.

**On Leave / Inactive transitions:** These statuses also suspend system access. When transitioning to `On Leave` or `Inactive`, active sessions should also be revoked using the same mechanism. The employee cannot log back in while in these states, but clearing existing sessions ensures there is no window of continued access after the status change.

> [!IMPORTANT]
> **Seat Billing Rule:** Active + On Leave + Inactive employee counts are summed to determine seat consumption against the tenant's purchased seat count. Terminated employees are excluded from this count. To reduce purchased seat count and lower billing, the tenant must explicitly remove a vacant seat in the Billing section — setting an employee to Terminated alone does not reduce the purchased seat count.

> [!IMPORTANT]
> **Lite Tier Seat Cap:** When Active + On Leave + Inactive employee count reaches 10, the system blocks creation of additional employees and displays: *"Maximum employee limit reached for Lite plan. Upgrade to Plus for unlimited seats."* An employee must be set to Terminated (with a populated `termination_date`) to free a seat.

---

## 19. Inventory Lifecycle
**Transitions:** `Active` → `Hold` → `Discontinued`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Item is available for use on Work Orders, Quotes, and Purchase Orders. | Default state. Stock flags evaluated continuously by the system. |
| **Hold** | Item is temporarily blocked from use. | **Blocked**: Cannot be added to new Work Orders, Quotes, or POs. Existing line items using the item are preserved. Requires a `reason`. Admin only. Can return to Active. |
| **Discontinued** | Item is permanently retired. | **Locked**: Cannot be added to any new records. Existing historical records preserved. Requires a `reason`. Reversion requires Admin. |

### 19.1 Inventory Stock Flags
Stock flags are **system-managed boolean fields** on the Inventory record. They are not statuses — they do not block usage but serve as triggers for the Communication and Notification system.

| Flag | Set By | Cleared By | Purpose |
| :--- | :--- | :--- | :--- |
| `is_low_stock` | System — automatically set when `quantity_on_hand` falls at or below `low_stock_threshold`. | System — automatically cleared when `quantity_on_hand` rises above `low_stock_threshold`. | Triggers low stock notification/alert to purchasing staff. |
| `is_out_of_stock` | System — automatically set when `quantity_on_hand` reaches 0. | System — automatically cleared when `quantity_on_hand` rises above 0 (e.g., via receiving or inventory transfer). | Triggers out of stock notification/alert. Can be used to block addition to new Work Orders if tenant policy requires. |

> [!NOTE]
> `low_stock_threshold` is a configurable field per Inventory record, set by the tenant. Both flags operate independently of the Inventory status — an item on `Hold` may also carry stock flags, and an `Active` item with `is_out_of_stock = true` remains Active unless manually placed on Hold.

---

## 20. Vendor Lifecycle
**Transitions:** `Active` → `Inactive` → `Do Not Use`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Vendor is approved and in good standing. | Purchase Orders can be created freely. |
| **Inactive** | Vendor is temporarily not in use. | A review is required before new POs are initiated. Existing open POs may be completed. |
| **Do Not Use** | Vendor is blocked from all new purchasing activity. | **Blocked**: No new POs can be created against this vendor. Existing open POs may be completed at Admin discretion. Requires a `reason`. Admin only. Reversion to Active requires Admin and a new `reason`. |

---

## 21. Communication Template Lifecycle
**Transitions:** `Draft` → `Active` → `Inactive`

*   **Draft**: Template is being authored. Body content, channel type (SMS/Email), subject line (Email only), and merge fields can be edited freely.
*   **Active**: Template is available for assignment to Communication Triggers. Content is **Locked** — changes require creating a new version or reverting to Draft (Admin only, `reason` required). An Active template may be assigned to multiple Triggers.
*   **Inactive**: Template retired from active use. Existing `TriggerTemplates` references are preserved and continue to function for historical log purposes. Cannot be assigned to new Triggers.

---

## 22. Communication Trigger Lifecycle
**Transitions:** `Draft` → `Active` → `Inactive`

*   **Draft**: Trigger is being configured. Event type, timing, channel, and conditions can be edited freely. No messages are fired while in Draft.
*   **Active**: Trigger is live. Evaluates configured conditions on the defined event and dispatches messages via the assigned templates. All fired messages are recorded in `TriggerLog`.
*   **Inactive**: Trigger is disabled. No messages are fired. Existing `TriggerLog` records are preserved. Can be returned to Active by Admin.

> [!NOTE]
> A Trigger must have at least one Active Template assigned via `TriggerTemplates` before it can be set to Active. Attempting to activate a Trigger with no assigned Active Templates returns a validation error.

---

## 23. Pricebook Entry Lifecycle
**Transitions:** `Active` → `Inactive` → `Discontinued`

*   **Active**: Entry is available for selection on Quotes, Work Order Line Items, and Invoices. Pricing is current.
*   **Inactive**: Entry is hidden from new record selection. Existing line items referencing this entry are preserved and display historical pricing. Can be returned to Active.
*   **Discontinued**: Entry permanently retired. Requires a `reason`. **Locked**: Cannot be reactivated. Cannot be added to any new records. Historical line items are preserved.

---

## 24. WorkGroup Division (Epic) Lifecycle
**Transitions:** `Open` → `In Progress` → `Completed` / `Cancelled`

*   **Open**: Division created within a WorkGroup. Tasks are being assembled and assigned.
*   **In Progress**: At least one Task within the Division has started.
*   **Completed**: All Tasks within the Division are Completed or Closed. **Locked**.
*   **Cancelled**: Division cancelled. Requires a `reason`. **Locked**. Does not automatically cancel individual Tasks — those must be handled independently.

---

## Version History

| Version | Date | Changes |
| :--- | :--- | :--- |
| V1 | March 2026 | Initial draft |
| V2 | March 2026 | Expanded lifecycle coverage across all core entities. Added Fleet Maintenance (Sections 17.1–17.2). |
| V3 | March 2026 | Added Employee Lifecycle (Section 18) including seat billing rules and Lite tier cap enforcement. Added Inventory Lifecycle (Section 19) with Hold status and system-managed stock flags (`is_low_stock`, `is_out_of_stock`). Added Vendor Lifecycle (Section 20) with Do Not Use status. Added Communication Template Lifecycle (Section 21). Added Communication Trigger Lifecycle (Section 22). Added Pricebook Entry Lifecycle (Section 23). Added WorkGroup Division Lifecycle (Section 24). Removed Section 18 Status Change Log — superseded by `SystemAudits`. |
