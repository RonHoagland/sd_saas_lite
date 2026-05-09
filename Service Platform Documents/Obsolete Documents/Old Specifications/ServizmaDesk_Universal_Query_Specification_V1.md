# ServizmaDesk Universal Query Specification (Top-Down Design)
**Document Version:** V1
**Status:** Approved (Resolves Gaps 3.6, 3.7)

## 1. Overview
Instead of defining unique search/sort logic for every list in the system, ServizmaDesk utilizes a **Universal Query Interface (UQI)**. This allows the frontend to request data using a standardized JSON payload that the backend handles dynamically based on the target entity's metadata.

## 2. API Interface
All `GET /api/v1/{entity}/` list endpoints support the following query parameters (sent as a JSON-encoded `query` param or individual params):

### 2.1 JSON Payload Structure
```json
{
  "q": "optional global search string",
  "filters": [
    { "field": "status", "op": "eq", "value": "active" }
  ],
  "sort": [
    { "field": "created_at", "dir": "desc" }
  ],
  "cursor": "opaque_base64_token_ext",
  "page_size": 25
}
```

### 2.2 Global Search (`q`)
- **Behavior**: The backend performs a case-insensitive `ILIKE` search across an index of "primary identifiers" for that entity.
- **Example Profiles**:
    - **Customer**: `name`, `email`, `account_number`.
    - **Work Order**: `work_order_number`, `description`, `customer__name`.
    - **Asset**: `asset_number`, `serial_number`, `make`, `model`.

### 2.3 Supported Filter Operators (`op`)
| Operator | Logic | Usage |
|---|---|---|
| `eq` | Equals | `status == 'active'` |
| `ne` | Not Equals | `type != 'labor'` |
| `gt` / `lt` | Greater/Less Than | Numeric/Date comparisons |
| `in` | In List | `status IN ['draft', 'issued']` |
| `contains`| Partial String Match | `name ILIKE '%term%'` |
| `isnull` | Null Check | `assigned_to IS NULL` |

### 2.4 Multi-Level Sorting (`sort`)
- The system supports sorting by any field exposed via the API.
- Multiple sort keys can be provided (e.g., Sort by `priority` then by `due_date`).

## 3. Pagination Strategy (Cursor-Based)
Following the **Top-Down Design** for enterprise scalability, ServizmaDesk mandates **Cursor-based Pagination** (Keyset Pagination) for all major list views to ensure consistent performance regardless of dataset depth.

### 3.1 Mechanism
1. **Opaque Cursor**: The server returns a `next_cursor` token in the response metadata.
2. **Sequential Access**: The frontend sends this token in the subsequent request to retrieve the next page.
3. **Stability**: Unlike Offset pagination (`LIMIT/OFFSET`), Cursor pagination is unaffected by record insertions/deletions during a user's session.

### 3.2 Standards
- **Default Page Size**: 25 items.
- **Maximum Page Size**: 100 items (enforced at gateway).
- **Default Sort**: If no `sort` is provided, the system defaults to `created_at DESC`.

## 4. Backend Enforcement
1. **Schema Validation**: The filter backend MUST verify that the requested `field` exists on the model and is permitted for filtering.
2. **Type Safety**: The `value` provided must be cast-safe to the field's underlying type.
3. **Tenant Scoping**: All queries are automatically wrapped in a `tenant_id` filter by the `TenantModelManager` (Mandate 3.2).

## 5. Performance Standards
- **Maximum API Response Time**: 500ms for p95 of paginated requests.
- **Query Timeout**: Queries exceeding 3,000ms are forcibly aborted.
