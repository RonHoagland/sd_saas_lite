# ServizmaDesk System Status Specification V2

**Date:** March 2026
**Scope:** SDTA Backend Lifecycle & State Machine
**Status:** Working Draft
**Supersedes:** V1

---

## 1. Overview
This document defines the lifecycle, state transitions, locking mechanisms, and audit requirements for all major entities within the ServizmaDesk ecosystem. These rules ensure operational flexibility while maintaining strict accounting integrity and a reliable audit trail.

---

## 2. Customer Lifecycle
**Transitions:** `Active` → `Inactive` → `Hold` → `Closed`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Standard operating state. | Sales and Work Orders can be created freely. |
| **Inactive** | No sales activity for an extended period. | A review is required before new sales/Work Orders are initiated. |
| **Hold** | Operational or financial issue identified. | **Blocked**: No new work or sales permitted without explicit permission. Requires a `hold_date` and `reason`. |
| **Closed** | Account terminated. | Record is locked for new activity. Requires a `closed_at` timestamp and `reason`. |

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
**Transitions:** `Draft` → `Issued` → `Partially Paid` → `Paid` / `Overdue` → `Void` / `Written Off`

*   **Issued**: Triggers an `issued_date`. Line items are **Locked**. 
    *   **Corrections**: If changes are needed, a new invoice must be created (marked as a **Credit Memo**) to preserve the audit trail.
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
**Transitions:** `Open` → `Issued` → `Partially Received` → `Received` → `Void`

*   **Issued**: Triggers an `issued_date`. Line items are **Locked**. 
    *   **Billing**: Creating an `Issued` PO automatically generates a **Vendor Billing** record in `Pending` status.
*   **Received**: Set automatically when all `PO Line Items` are marked as `Received`. The record is then **Locked**.
*   **Void**: Reversion requires an Admin and a `reason`. Automatically voids the associated `Vendor Billing` record.

### 6.2 PO Line Items (POLI)
**Transitions:** `Open` → `Partially Received` → `Received`

*   **Status Mapping**: Driven by `Receiving` records. Once total received quantity $\ge$ total ordered, status moves to `Received`.
*   **Override**: Users can manually override a status, but a `reason` is required.

---

## 7. Vendor Billings (Accounts Payable)
**Transitions:** `Pending` → `Received` → `Partially Paid` → `Paid`

| Status | Trigger |
| :--- | :--- |
| **Pending** | Default state upon PO issuance. Waiting for delivery or vendor invoice. |
| **Received** | Automatically set when the linked PO/POLI are fully received. |
| **Partially Paid** | Payment(s) issued to vendor < Total Bill. |
| **Paid** | Total payments $\ge$ Vendor Invoice Total. |

---

## 8. Asset Lifecycle
**Transitions:** `Active` → `Inactive` → `Decommissioned`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Active** | Equipment is operational and in service. | Work Orders and PMs can be created freely against this asset. |
| **Inactive** | Equipment is temporarily out of service. | Not available for new Work Orders or PM scheduling. Historical records preserved. Can be reactivated to Active. |
| **Decommissioned** | Equipment permanently retired. | **Locked**: No new Work Orders, PMs, or Agreements. Record preserved for service history. Reversion to Active requires Admin and a `reason`. |

---

## 9. TroubleCall Lifecycle
**Transitions:** `New` → `Triaged` → `Converted to Work Order` / `Converted to Quote` / `Cancelled`

*   **New**: Default state on creation (phone intake, portal submission, web widget).
*   **Triaged**: Dispatcher has reviewed and assessed the request. Notes and asset identification may be added.
*   **Converted to Work Order**: A Work Order has been generated from this TroubleCall. The WO carries a backlink FK. **Locked** — TroubleCall cannot be edited after conversion.
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
**Transitions:** `Pending` → `Active` → `Expired` / `Cancelled`

| Status | Definition | Rules |
| :--- | :--- | :--- |
| **Pending** | Agreement created but not yet in effect. | Start date has not been reached. PM records can be created in preparation. |
| **Active** | Agreement is in force. | PMs generate Work Orders per schedule. Billing active. |
| **Expired** | End date has passed. | **Locked** for new PM generation. Existing WOs in progress may be completed. Can transition to Active on renewal. |
| **Cancelled** | Agreement terminated early. | Requires a `reason` and `cancelled_at` timestamp. **Locked**. Reversion requires Admin. |

### 11.2 Preventative Maintenance Lifecycle
**Transitions:** `Active` → `Paused` → `Expired` / `Cancelled`

*   **Active**: PM schedule is running. Auto-generates Work Orders per schedule.
*   **Paused**: Temporarily suspended. No new WOs generated. Can resume to Active.
*   **Expired**: Parent Agreement has expired or PM end date reached. **Locked** for generation.
*   **Cancelled**: PM terminated. Requires a `reason`. **Locked**. Reversion requires Admin.

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

## 17. Fleet Management

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

## 18. Audit & Logging (Status Change Log)
Every status transition across the system must be recorded in the **Status Change Log**. This log is separate from the entity records to ensure that even if a date is cleared in the UI, the historical truth remains.

**Required Fields:**
*   **Entity Name** (e.g., "WorkOrder", "Invoice")
*   **Record ID** (UUID)
*   **Pre-Status** (Value before change)
*   **Post-Status** (Value after change)
*   **Timestamp** (UTC)
*   **User ID** (Who performed the action)
*   **Reason** (Captured when required by the lifecycle rules)
