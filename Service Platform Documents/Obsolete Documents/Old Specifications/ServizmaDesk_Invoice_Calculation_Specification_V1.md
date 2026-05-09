# ServizmaDesk Invoice Calculation Specification V1

**Date:** March 11, 2026
**Scope:** SDTA Backend Invoice & Quote Calculations
**Status:** Approved

---

## 1. Overview
This specification defines the mathematical order of operations for calculating Invoice and Quote totals. It moves from header-level discounts/surcharges to a line-item based model, ensuring precision and auditability.

---

## 2. Line Item Logic

Each line item (`QuoteLine`, `WorkOrderLine`, `InvoiceLine`) now carries three core behavioral flags:

| Field | Description | Behavior |
| :--- | :--- | :--- |
| `is_discount` | Boolean | If `True`, the line amount is **subtracted** from the subtotal. |
| `is_surcharge` | Boolean | Purely for labeling/reporting; no impact on standard math. |
| `is_tax_charged` | Boolean | If `True`, the line amount is included in the tax calculation. |

### 2.1 Default States
*   `is_tax_charged`: Default **Checked (True)**.
*   `is_discount`: Default **Unchecked (False)**.
    *   **Rule**: If `is_discount` is toggled to `True`, `is_tax_charged` MUST be automatically forced to `False`. Discounts are not taxed.

---

## 3. Calculation Order of Operations

The system calculates the final totals using the following sequence:

### Step 1: Line Item Base Amount
For each line $i$:
$$LineAmount_i = Quantity_i \times UnitPrice_i$$

### Step 2: Line Item Subtotal
The subtotal is the sum of all non-discount lines minus the sum of all discount lines.
$$Subtotal = \sum_{non\_discount} LineAmount_i - \sum_{discount} LineAmount_i$$

### Step 3: Tax Calculation
Tax is calculated only on line items where `is_tax_charged` is `True`. The tax rate $R$ is derived from the Customer's specific rate (or the Tenant default).
$$TaxTotal = \sum_{tax\_charged} (LineAmount_i \times R)$$

### Step 4: Grand Totals
$$InvoiceTotal = Subtotal + TaxTotal$$

---

## 4. Database Storage (Invoice Header)
To ensure performance for list views and reporting, the following values MUST be stored on the `Invoice` header and updated whenever line items are modified:

1.  **`line_item_total`**: The value from **Step 2** (The pre-tax subtotal).
2.  **`line_item_tax_total`**: The value from **Step 3** (Total tax calculated).
3.  **`invoice_total`**: The final value from **Step 4**.

---

## 5. Tax Rate Source Hierarchy
When an Invoice or Quote is created, the system resolves the `tax_rate` using this logic:
1.  **Customer Override**: If `Customer.tax_rate` is populated, use that value.
2.  **Tenant Default**: Otherwise, use `TenantPreference.default_tax_rate`.

Once the record is **Issued**, the `tax_rate` used at the time is frozen on the header to ensure the math never changes even if the Customer moves to a different state later.
