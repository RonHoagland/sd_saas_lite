# ServizmaDesk Permission Enforcement Specification (SDTA)
**Document Version:** V1
**Status:** Working Draft (Resolves Gap 3.8)

## 1. Overview
This document defines the "Double Guard" architecture for feature access in SDTA. It combines **Tier-based Entitlements** (plan-level locks) and **Role-based CRUD Permissions** (user-level locks).

## 2. The Permission Registry
To ensure consistency, we define a central registry of "Resources" in the codebase. Every resource has 4 possible CRUD actions.

### 2.1 Modules & resources
| Module | Resource Key | Description |
|---|---|---|
| **CRM** | `crm_customer` | Customers, Contacts, Persons |
| **Service** | `service_quote` | Quotes and Quote Lines |
| **Service** | `service_workorder` | Work Orders and WO Lines |
| **Service** | `service_invoice` | Invoices and Invoice Lines |
| **Procurement** | `proc_vendor` | Vendors and Vendor Bills |
| **Fleet** | `fleet_vehicle` | Business Vehicles |
| **Inventory** | `inv_item` | Parts, Supplies, and Equipment |

## 3. Data Models

### 3.1 `EmployeeRole` (The Junction)
As per the ERD (V3/V4), a user can hold **multiple roles**. This is enforced via a junction table.

| Field | Type | Note |
|---|---|---|
| `employee_id` | UUID FK | Links to the User/Employee record |
| `role_id` | UUID FK | Links to the Role record |

### 3.2 `RolePermission`
This table defines what a specific `Role` can do.

| Field | Type | Note |
|---|---|---|
| `role_id` | UUID FK | |
| `resource_key` | CharField | From the Registry (e.g., `service_invoice`) |
| `can_create` | Boolean | |
| `can_view` | Boolean | |
| `can_edit` | Boolean | |
| `can_delete` | Boolean | |

## 4. Permission Logic: The "Additive Union"
When a user has multiple roles, the system calculates their **Effective Permissions** using "OR" logic (Least Restrictive).

*   **Rule**: If **any** of the user's roles have a "True" bit for an action (e.g., `can_delete`), the user is granted that action.
*   **Example**: 
    *   Role A: `can_edit = True`, `can_delete = False`
    *   Role B: `can_edit = False`, `can_delete = True`
    *   **Result**: The user can both Edit and Delete.

### 4.1 Layer 1: The Tier Lock (Entitlement)
Before checking an individual's role, the system checks the **Tenant's Tier**. 

*   **Logic**: If the resource belongs to the `Procurement` module but the tenant is on the **Lite Tier**, the system denies access immediately (e.g., `402 Payment Required`).
*   **Enforcement**: Use a decorator: `@tier_required('plus')`.

### 4.2 Layer 2: The Role Lock (CRUD)
If the Tier lock passes, the system then checks the **Employee's Role**.

*   **Logic**: Checks if a row exists in `RolePermission` for that resource with the required action bit set to True.
*   **Enforcement**: Use a decorator: `@permission_required('service_invoice', 'edit')`.

## 5. Composition (The Decorator Pattern)
In a real-world scenario (e.g., Editing an Invoice in the Plus Tier), the view is protected by both guards:

```python
@tier_required('plus')
@permission_required('service_invoice', 'edit')
def edit_invoice_view(request, invoice_id):
    # Process invoice edit...
    pass
```

## 6. Custom Roles & The Permission Matrix (Plus/Pro+)
In higher tiers, the "How" of custom permissions is driven by a **Tenant-Managed Matrix**.

### 6.1 The Developer Contract (UI/UX)
For a developer building the "Role Management" screen:
1.  **Registry-Driven**: The UI must dynamically iterate through the `Registry` (Section 2) to generate a row for every Resource.
2.  **Checkbox Grid**: Each row presents 4 checkboxes (Create, View, Edit, Delete).
3.  **Persistence**: Every checkbox toggle creates or updates a row in the `RolePermission` table (Section 3.1).

### 6.2 System vs. Custom Roles
| Role Flag | Behavior |
|---|---|
| `is_custom = False` | **Immutable**. The UI must block any attempt to change these permissions. The developer must ensure these roles are "Locked" in the database. |
| `is_custom = True` | **Mutable**. The tenant-admin can toggle all 4 bits for any resource. |

### 6.3 Resolution Logic
1.  **The "Safety Lock"**: A developer must ensure a tenant can NEVER delete the last "Administrator" role or remove "Edit" permissions from the only admin roles.
2.  **Additive Privilege**: As defined in Section 4, if a user has multiple roles, their effective permissions are the **OR-Union** of all assigned roles. There is no concept of "Deny" taking precedence (since these are all "Allow" bits).
3.  **Conflict Resolution**: Since roles are purely additive, a user simply gains the maximum permission level available across all their assigned roles.

## 7. Performance & Caching
Permission checks happen on every request. To avoid database overhead:
1.  User permissions are fetched once per login.
2.  The resulting "Permission Matrix" is cached in the **User Session** (Redis).
3.  The decorators check the session cache instead of the database.

## 8. Session-Level Permission Snapshots
For forensic and audit purposes, the `SessionLog` record must capture the state of the user's permissions at the moment of login.

1.  **Storage**: The `SessionLog` contains a `permission_snapshot` (JSONB) field.
2.  **Contents**: A flat dictionary of `{ resource_key: "CRU-", ... }` strings representing the exact bits allowed.
3.  **Rationale**: If an Admin changes a user's role mid-session, we can see exactly what the user was authorized to do *during that specific session* without having to reconstruct historical role changes.

## 9. Security Audit Logging
Every attempt to bypass the permission system must be logged to the `AuditEvent` table.

### 9.1 Failed Access (Unauthorized)
*   **Action**: `PermissionDenied`
*   **Trigger**: When a `@tier_required` or `@permission_required` guard fails.
*   **Captured Data**: Resource Key, Requested Action, User ID, and Session ID.

## 10. Financial & Critical Action Logging
*   **CRUD enforcement**: As mandated by the core architecture, every `Create` and `Delete` action MUST emit an `AuditEvent` (Action: `Created`, `Deleted`).
*   **Financial Safeguard**: Any write to the `Ledger` or `Invoice` module triggers a mandatory audit event, regardless of the user's role.

## 11. Resource Isolation Mandate (Anti-Bleed Rule)
To prevent accidental security gaps, permissions are **strictly bound to the Data Resource**, not the UI Context.

### 11.1 Prohibition of "Contextual Bleed"
Developers are strictly prohibited from granting access based on the "Page" the user is currently viewing.

*   **Rule**: Access to a resource (e.g., `service_invoice`) must ALWAYS be checked against its own dedicated Resource Key, even if that data is being displayed or edited inside a different module's view (e.g., the `crm_customer` details page).
*   **Example**: Having `Edit` permission for `crm_customer` DOES NOT grant the right to edit an Invoice that appears in the customer's "Recent Invoices" list. The Invoice edit button must still be guarded by the `@permission_required('service_invoice', 'edit')` check.
*   **Mandate**: All backend view-logic and API endpoints must independently verify the specific permissions for every unique resource they attempt to modify.
