# ServizmaDesk Dashboard Counter Specification (SDTA)
**Document Version:** V1
**Status:** Approved (Resolves Gap 2.8)

## 1. Overview
This document defines the exact database query logic for the five operational counters displayed on the SDTA Dashboard. These counters provide real-time visibility into the tenant's operations and financial health.

## 2. Global Calculation Rules
- **Tenant Isolation**: All queries MUST be scoped to the active `tenant_id`.
- **Timezone Awareness**: Date-based filters (e.g., "Today") MUST be calculated relative to the `timezone` defined in the `TenantPreference` table.
- **Aggregation**: These values are intended for display-only and should be calculated using efficient ORM aggregation (e.g., `.count()` and `.aggregate(Sum('amount'))`).

## 3. Counter Definitions

### 3.1 Work Orders Today
Displays the volume of service delivery scheduled for the current day.
- **Logic**: Count of `WorkOrder` records.
- **Filter**: 
    - `scheduled_date` == Current Date (Tenant Local)
    - `status` != `Cancelled`
- **Includes**: Both incomplete and completed work orders for the day to show total daily throughput.

### 3.2 Open Work Orders
Displays the current operational backlog.
- **Logic**: Count of `WorkOrder` records.
- **Filter**: 
    - `status` IN (`Draft`, `Scheduled`, `In Progress`, `On Hold`)

### 3.3 Open Invoices
Displays the volume of receivables currently "in the wild."
- **Logic**: Count of `Invoice` records.
- **Filter**: 
    - `status` IN (`Issued`, `Partially Paid`)
- **Note**: `Draft` invoices are excluded as they have not yet been presented for payment.

### 3.4 Overdue Invoices
Displays the count of late payments requiring collection effort.
- **Logic**: Count of `Invoice` records.
- **Filter**: 
    - `status` IN (`Issued`, `Partially Paid`)
    - `due_date` < Current Date (Tenant Local)

### 3.5 Revenue This Month
Displays actual cash collected during the current calendar month.
- **Logic**: Sum of `amount` from `Payment` records.
- **Filter**: 
    - `payment_date` >= First Day of Current Month (Tenant Local)
    - `payment_date` <= Last Day of Current Month (Tenant Local)
- **Note**: This tracks "Cash Basis" revenue.

## 4. Performance Mandate
Because these counters appear on the landing page, they must be highly performant.
1. **Indexes**: Ensure database indexes exist on `tenant_id` combined with `status`, `scheduled_date`, `due_date`, and `payment_date`.
2. **Caching**: Results may be cached at the session level for 60 seconds to prevent redundant database hits on rapid page refreshes.
