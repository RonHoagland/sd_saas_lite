# ServizmaDesk System Status Specification V1

**Date:** March 11, 2026
**Scope:** SDTA Backend Lifecycle & State Machine
**Status:** Approved

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

## 8. Audit & Logging (Status Change Log)
Every status transition across the system must be recorded in the **Status Change Log**. This log is separate from the entity records to ensure that even if a date is cleared in the UI, the historical truth remains.

**Required Fields:**
*   **Entity Name** (e.g., "WorkOrder", "Invoice")
*   **Record ID** (UUID)
*   **Pre-Status** (Value before change)
*   **Post-Status** (Value after change)
*   **Timestamp** (UTC)
*   **User ID** (Who performed the action)
*   **Reason** (Captured when required by the lifecycle rules)
