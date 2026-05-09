# ServizDesk Lite — Block Reference

**Status:** Tier 1 spec (defined, mostly not yet implemented)
**Last updated:** May 1, 2026
**Owner:** Ron Hoagland

This document is the **canonical specification** for the building blocks of every page in ServizDesk Lite. **Every page is composed of universal chrome (sidebar + header) + a body assembled from typed blocks placed in named grids.** No bespoke page layouts — if a block doesn't exist for what you need, define a new one here first, then build it.

Reading guide:
- §1 — Architecture
- §2 — Page archetypes (which blocks to use)
- §3 — Block catalog (the actual building blocks)
- §4 — Grid primitives (where blocks go)
- §5 — Archetype chrome (sub-headers + footers)
- §6 — A11y contract (every block must comply)
- §7 — Adding a new block
- §8 — Implementation status

---

## 1. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Page                                                        │
│ ┌─────────┬───────────────────────────────────────────────┐ │
│ │         │ Header  (universal chrome)                    │ │
│ │         ├───────────────────────────────────────────────┤ │
│ │ Side-   │ Sub-header  (archetype chrome — opt-in)       │ │
│ │ bar     ├───────────────────────────────────────────────┤ │
│ │         │ Body                                          │ │
│ │ (univ.  │   ┌────────┬────────┬────────┐                │ │
│ │ chrome) │   │ block  │ block  │ block  │ ← in a grid    │ │
│ │         │   ├────────┴────────┴────────┤                │ │
│ │         │   │ block  │ block           │                │ │
│ │         │   └────────┴─────────────────┘                │ │
│ │         ├───────────────────────────────────────────────┤ │
│ │         │ Footer  (archetype chrome — Detail only)      │ │
│ └─────────┴───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

Four layers, four responsibilities:

| Layer | Responsibility | Defined where | When present |
|---|---|---|---|
| **Universal chrome** | Sidebar + Header — identical on every page | `templates/base.html`, `templates/includes/app_sidebar.html` | Always |
| **Archetype chrome** | Sub-header (above body) + Footer (below body) — varies per archetype, opt-in | `templates/includes/_subheader_*.html`, `templates/includes/_footer_*.html` | When the archetype calls for it |
| **Page archetype** | The conventional shape of a page (which blocks, in what order, in what grid) | **§2 of this doc** — convention, not a skeleton template. Pages extend `base.html` directly and follow the archetype's documented shape. | Always (every page belongs to one archetype) |
| **Block** | The smallest reusable unit of UI | `templates/blocks/_*.html` | Many per page |

**Decoupling rules:**
- A **block** doesn't know what grid it's in. It fills `width: 100%; height: 100%`.
- A **grid** doesn't know what blocks it holds. It just sets columns/rows.
- A **page** picks a grid and puts blocks in cells. Nothing else.
- **Chrome** (universal or archetype) is parallel to the body, never inside it.

**Naming conventions:**

| Concept | Pattern | Example |
|---|---|---|
| Block partial | `templates/blocks/_<name>.html` | `templates/blocks/_kpi.html` |
| Chrome partial | `templates/includes/<name>.html` or `templates/includes/_<name>.html` | `templates/includes/app_sidebar.html`, `templates/includes/_footer_detail.html` |
| CSS root class | `.sd-<name>` | `.sd-kpi`, `.sd-footer-detail` |
| CSS inner element | `.sd-<name>-<part>` (**single** hyphen) | `.sd-kpi-label`, `.sd-kpi-value` |
| CSS structural variant | `.sd-<name>--<variant>` (**double** hyphen) | `.sd-kpi--vertical`, `.sd-sidebar-brand-mark--initials` |
| CSS interactive state | direct class or `:pseudo-class` (no `is-` prefix) | `.editing`, `.active`, `:focus-visible`, `:hover` |
| Caller invocation | `{% include "blocks/_<name>.html" with key=value … %}` | |

**Variant vs state — when to use which:**
- **Variant** = a structural/visual choice baked in at render time (KPI vertical layout, brand mark showing initials, nav item nested). Use `--<variant>`.
- **State** = a transient interactive condition (card is editing, nav item is active for the current route, button is hovered). Use a direct class or pseudo-class.

This distinction is already in the existing CSS (e.g. `.sd-sidebar-brand-mark--initials` is a variant; `.sd-section-card.editing` is a state). The convention is: **variants describe what the element *is*; states describe what it's *doing right now*.**

---

## 2. Page archetypes

Three archetypes cover the Lite MVP scope. A fourth (Kanban) is deferred pending the workflow system. Anything outside these is a deliberate exception (a wizard, a settings form, etc.).

| Archetype | Purpose | Sub-header | Footer | Typical blocks |
|---|---|---|---|---|
| **List** | Browse records of one entity | Filter strip (deferred — see §5.1.3) | none | KPI strip + Master List |
| **Detail** | View / edit one record | Record context (§5.1.2) | Detail audit (§5.2.1) | Field + Sub List + Tab Panel + Metric Data |
| **Report** | Aggregated overview spanning multiple entities | Optional — varies by page (Dashboard uses Greeting §5.1.1) | none | KPI + Sub List + Metric Data |
| **Kanban** | Records grouped by stage/status | — | — | Deferred until workflow system lands |

**Archetypes are conventions, not template files.** Every page extends `base.html` directly and composes blocks in `{% block content %}` following the archetype's documented shape. There is no `_list.html` / `_detail.html` / `_report.html` skeleton — that would be one layer of indirection for diminishing return at this scale. Reviewer enforces convention; the doc is the spec.

The next four subsections describe each archetype's shape (chrome, layout, grid, typical blocks).

---

### 2.1 List archetype

**Use when:** the page exists to let the user browse, search, and select records of a single entity.

**Examples (Lite scope):** Customers list, Assets list, Jobs list, Quotes list, Invoices list, Payments list, Tasks list, Time entries list, Products & Services list.

**Layout:**
```
[Header (universal chrome)]
[Filter strip (sub-header — TBD)]
─────────────────────────────────────────────
KPI strip — sd-grid-4up (or sd-grid-3up)
[KPI] [KPI] [KPI] [KPI]
─────────────────────────────────────────────
Master List Block (full-width)
─────────────────────────────────────────────
```

**Page setup:** extends `base.html` directly. Sets `{% block page_title %}`, `{% block breadcrumb %}`, `{% block content %}`. Sub-header and footer blocks left empty (filter strip deferred per §5.1.3).

**Context vars (typical, declared by the view):**

| Key | Type | Description |
|---|---|---|
| `kpis` | iterable of dicts | One per KPI in the strip — passed to `_kpi.html` |
| `list_data` | dict | List Block payload (`title`, `columns`, `rows`, `new_record`, `filters`, `pagination`) — passed to `_list.html` with `variant="full"` |

- **Sub-header:** Filter strip (§5.1.3) — deferred. Filters likely end up inside the List Block's filter toolbar (full variant); decided when we build the first List page.
- **Footer:** none.
- **Default grid:** KPI strip uses `sd-grid-4up` (or `sd-grid-3up` if only 3 KPIs); the List Block sits full-width below, no grid needed.

---

### 2.2 Detail archetype

**Use when:** the page exists to view and edit a single record.

**Examples (Lite scope):** Customer Detail, Asset Detail, Job Detail, Service Request Detail, Quote Detail, Invoice Detail, Payment Detail, Task Detail.

**Layout:**
```
[Header (universal chrome)]
[Sub-header: Record context (§5.1.2)]
─────────────────────────────────────────────
sd-grid-2-1
┌─ Main canvas (2fr) ──────┬─ Context panel (1fr) ─┐
│ Field blocks             │ Activity timeline       │
│ Field blocks             │ (Sub List variant)      │
│ Sub List (line items)    │                         │
│ Tab Panel                │ Notes (Sub List)        │
│   ↳ tabs (SRs, Quotes,…) │ Status actions          │
└──────────────────────────┴─────────────────────────┘
─────────────────────────────────────────────
[Footer: Detail audit (§5.2.1)]
```

**Page setup:** extends `base.html` directly. Fills `{% block subheader %}` (record context partial), `{% block content %}` (main + context blocks in `sd-grid-2-1`), and `{% block page_footer %}` (Detail audit footer partial).

**Context vars (typical, declared by the view):**

| Key | Type | Description |
|---|---|---|
| `record` | model instance | The record being viewed (Customer, Asset, Job, etc.) |
| `record_meta` | dict | For sub-header §5.1.2 — `record_name`, `record_meta`, `status_label`, `status_variant`, `actions` |
| `record.created_by` / `created_at` / `modified_by` / `modified_at` | — | Audit fields for the footer §5.2.1 |

The page itself is responsible for choosing which blocks fill the main canvas (Field blocks for record fields, List blocks for line items / sub-records, Tab Panel for sub-collections) and the context panel (List blocks for Notes / status actions). No standardized "main_blocks" / "context_blocks" abstractions — each Detail page composes directly.

- **Sub-header:** Record context (§5.1.2) — required.
- **Footer:** Detail audit (§5.2.1) — required (Detail pages always show audit info).
- **Default grid:** `sd-grid-2-1` (main canvas + context panel, per Lite spec §23 Customer Detail layout rules).

---

### 2.3 Report archetype

**Use when:** the page is an aggregated overview spanning multiple entities, not focused on a single record.

**Examples (Lite scope):** Dashboard (the canonical Report). **Future Reports** (post-MVP): Sales Performance, Service Performance, Financial Summary, Tech Productivity.

**Layout:** **flexible.** Reports are the "composable" archetype — blocks are arranged in whatever grid the report needs. The Dashboard's shape is one common pattern:

```
[Header (universal chrome)]
[Sub-header: Greeting §5.1.1 — Dashboard only; other Reports may omit]
─────────────────────────────────────────────
KPI strip — sd-grid-4up
[KPI] [KPI] [KPI] [KPI]
─────────────────────────────────────────────
sd-grid-2-1
┌─ Sub List (2fr) ──────┬─ Metric Data (1fr) ─┐
│ Today's Schedule      │ Business Performance │
└───────────────────────┴──────────────────────┘
─────────────────────────────────────────────
```

**Page setup:** extends `base.html` directly. Sub-header and footer optional per page. Body composed freely from any block(s) in any grid(s).

**Context vars:** **variable.** Each Report page declares its own context. There is no required structure.

- **Sub-header:** optional. Dashboard uses Greeting §5.1.1; other Reports may have none or a Report-specific filter strip (designed when needed).
- **Footer:** none.
- **Default grid:** none — Reports compose freely. Use whichever grid primitives from §4 fit the data.

---

### 2.4 Kanban archetype (deferred)

**Status: deferred** until the workflow system is designed.

A Kanban view groups records by workflow stage/status (e.g., Quotes by Draft → Sent → Accepted → Declined; Jobs by Open → Scheduled → In Progress → Complete). When the workflow system lands, this archetype will need:

- A new **Column Block** in §3 — vertical list of record cards per status column, drag-to-reorder within column, drag-between columns to change status
- A new column-grid primitive in §4 — CSS Grid with horizontally-scrolling columns
- Sub-header treatment — likely a filter strip plus the entity's status set as toggleable column visibility

When workflow lands, this section gets fully specified and Kanban joins the active archetypes.

---

## 3. Block catalog

Five block types cover the Lite scope:

| # | Block | Purpose |
|---|---|---|
| 3.1 | KPI Block | A single quantitative metric with accent stripe |
| 3.2 | List Block | Sortable list/table of records with primary-identifier link to detail. Two size variants (compact, full). Replaces what was previously two blocks (Sub List + Master List). |
| 3.3 | Metric Data Block | Vertical rows of model field/property + drilldown |
| 3.4 | Field Block | Label + value pair (view + edit modes) for Detail pages |
| 3.5 | Tab Panel Block | Bootstrap tabs styled to brand for Detail sub-collections |

---

### 3.1 KPI Block

A single quantitative metric. The most common block on Report pages and List pages.

**Visual:**
```
┌─────────────────────┐
│▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔▔│  ← accent stripe (3px, --sd-kpi-accent)
│ ⊞ Open Requests     │  ← label (with optional icon)
│ 12                  │  ← value (large, ~1.75rem)
│ Open                │  ← sub (small, muted)
└─────────────────────┘
```

**Partial:** `templates/blocks/_kpi.html`

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `label` | yes | string | Top-row label (e.g. "Open Requests"). Caller is responsible for any localization/casing. Block applies one-line ellipsis if it overflows the cell. |
| `value` | yes | string \| int | Big number or short text. **Caller is responsible for formatting** (e.g. `"1,234"` / `"$5,250.00"`). The block renders it verbatim. |
| `sub` | no | string | Bottom-row qualifier (e.g. "Open"). |
| `icon` | no | string | Lucide icon name (e.g. "inbox") — decorative; provides visual flair only. |
| `accent` | no | string | **Token name** from the accent palette (preferred) or a raw hex (escape hatch — discouraged, but allowed for one-offs). Defaults to `brand`. |
| `href` | no | url | If set, the entire card becomes a single link. |

**Accent token palette — the universal color-token set.** Used by KPI accents here, status badge variants in §5.1.2, action button variants, and any future colored-pill thing. One palette, one place to verify contrast.

| Token | Canonical color | Typical use |
|---|---|---|
| `brand` | `--sd-brand-primary` (#2563eb blue) | Default; neutral KPIs |
| `success` | #22c55e (green) | Positive / on-track (e.g. Job complete, Customer active) |
| `warning` | #f97316 (orange) | Requires attention (e.g. open Requests, Job in progress) |
| `danger` | #ef4444 (red) | Urgent / destructive / failed (e.g. Quote declined, Delete buttons) |
| `info` | #eab308 (amber) | Informational / financial (e.g. unpaid Invoices, Quote sent) |
| `neutral` | #64748b (slate-500) | Muted / non-categorized (e.g. Quote draft, Customer inactive) |

Tokens map to CSS custom properties (`--sd-accent-success`, etc.) defined in `site.css`. **Adding a new token is a §6 contrast-checked decision, not a one-off.** Raw hex is allowed as `accent="#f59e0b"` but every such use is technical debt — prefer adding a token.

**Where the variant token comes from depends on whether the status set is user-controlled or hardcoded.** Most statuses in ServizDesk are user-controlled (the tenant defines them via ValueLists / Settings). Some are hardcoded system states (lifecycle states that drive business logic — Quote Draft→Sent→Accepted, Invoice Draft→Sent→Paid). Both end up at the same destination — the block receives a token string — but the source differs:

| Source | Use when | Where the mapping lives |
|---|---|---|
| **Data field on the status record** | Status set is user-controlled (most cases) — Customer Type, Priority, custom Job substatuses, Asset Type, etc. | `ValueListItem.color_variant` (or similar) is a field the admin sets when creating/editing the status. The view reads `record.status.color_variant` and passes it to the block. |
| **Hardcoded mapping** | Status set is fixed in code because business logic depends on it — Quote/Invoice/Job lifecycle states. | Small Python mapping module per entity, e.g. `service/status_variants.py` with `QUOTE_STATUS_VARIANT = {'Draft': 'neutral', 'Sent': 'info', ...}`. |

In both cases, the **block doesn't care where the token came from** — it just renders whatever color token it's handed. This separation keeps the block reusable across entities with very different status models.

**Constraint:** the admin UI for user-controlled statuses must restrict color choice to the universal palette tokens (no free-form hex pickers). This preserves the contrast guarantees in §6.

**Caller example (token-based, preferred):**
```django
{% include "blocks/_kpi.html" with label="Open Requests" value=stats.requests sub="Open" icon="inbox" accent="warning" href=requests_url %}
```

**Caller example (escape hatch — discouraged):**
```django
{% include "blocks/_kpi.html" with label="Special metric" value=42 accent="#a855f7" %}
```

**A11y:**
- When `href` is set, root is `<a>` (entire card is one link, one tab stop, announced as a link).
- When `href` is absent, root is `<div role="group" aria-label="{{ label }}: {{ value }}">`.
- Icon is `aria-hidden="true"` (label provides the accessible name).
- Inherits `:focus-visible` ring via `--sd-focus-ring`.

**Future variants (not implemented):**
- **Trend indicator** — small ↑/↓ delta + change-since text ("12 ↑ 3 vs last week"). Add as `trend_value` + `trend_direction` keys when first needed.
- **Click-to-action (no navigation)** — when a KPI should open a modal/drawer instead of navigating, add a `data-action` key. Defer until first use case.

---

### 3.2 List Block

A list/table of records with sortable column headers and a primary-identifier cell linking to each record's detail page. **The single block for any tabular display of records**, regardless of size — replaces what were previously separate Sub List and Master List blocks.

**Two size variants:**

| Variant | Use | Filters / search / pagination |
|---|---|---|
| `compact` | Sits in a body grid cell (e.g. "Today's Schedule" on Dashboard) | none |
| `full` | Full-page width (e.g. Customers list page, Customer's Notes tab) | yes |

**Anatomy — two stacked sections:**

1. **Top action strip** — transparent, no border, sits **above** the block proper. Holds the `+ New <Entity>` button on the left; filters / search on the right (full variant only). **Auto-hidden** when nothing would render in it (no `new_record`, no `filters`, no `search`) — useful for static logs that the user can't add to.
2. **Block proper** — a bordered, white card containing:
   - Title row (block name only — no buttons here; actions live in the top action strip)
   - Sub-header row (column titles; each is a sort button when the column is `sortable`)
   - Rows (the data; **capped height with internal scroll on compact**, page-level scroll on full)
   - Pagination (full variant only, below rows, inside the card)

**Both variants have:**
- The optional top action strip (auto-hidden when empty)
- Sortable column headers (per-column flag — Notes case has every column non-sortable)
- A primary-identifier cell per row that links to the record's Detail page
- Built-in empty state with optional CTA

**Record IDs (UUIDs / PKs) are never rendered visually.** They are used in URL construction for the primary-identifier link target only.

---

#### Visual (compact variant — sits inside a body grid cell)

```
  [+ New Job]                                                  ← top action strip (transparent, no border)
┌──────────────────────────────────────────────────────────┐
│ Today's Schedule                                         │  ← block proper title (white card)
├──────────────────────────────────────────────────────────┤
│ Customer ↕      Description ↕         Time ↕             │  ← sortable column headers
├──────────────────────────────────────────────────────────┤  ─┐
│ John Smith      HVAC tune-up           10:00 AM          │   │
│ Acme Corp       Boiler replacement     2:00 PM           │   │ rows region (capped height, scrolls)
│ Greenfield LLC  Furnace inspection     3:30 PM           │   │
│ … more rows scroll within the card …                     │   │
└──────────────────────────────────────────────────────────┘  ─┘
```

#### Visual (full variant — full-page width)

```
  [+ New Customer]                          [Search… 🔍]  [Status ▼]  [Type ▼]    ← top action strip
┌────────────────────────────────────────────────────────────────────────┐
│ Customers                                                              │  ← block proper title
├────────────────────────────────────────────────────────────────────────┤
│ Name ↕         Phone ↕       Status ↕     Type ↕        Last Job ↕     │
├────────────────────────────────────────────────────────────────────────┤
│ John Smith     (555) 1234    Active       Residential   Apr 24, 2026   │
│ Acme Corp      (555) 5678    Active       Commercial    Apr 22, 2026   │
│ ... (page-level scroll, no inner cap)                                  │
├────────────────────────────────────────────────────────────────────────┤
│                          ◀ Page 1 of 5 ▶                                │
└────────────────────────────────────────────────────────────────────────┘
```

#### Visual (action strip auto-hidden — static log)

When the caller passes no `new_record`, no `filters`, and no `search`, the entire top action strip is omitted (not just empty — gone, no vertical space taken). Block proper sits flush.

```
┌──────────────────────────────────────────────────────────┐
│ System Audit Log                                         │  ← no top strip above
├──────────────────────────────────────────────────────────┤
│ Timestamp ↕    Action ↕         By ↕                     │
├──────────────────────────────────────────────────────────┤
│ 2:34 PM        Updated record   Alex Kim                 │
│ ...                                                      │
└──────────────────────────────────────────────────────────┘
```

#### Visual (empty state — both variants)

Top action strip stays (if it would render). Block proper title and column headers stay. Rows region shows a dashed-bordered empty-state with `empty_text` and optional CTA.

```
  [+ New Job]
┌──────────────────────────────────────────────────────────┐
│ Today's Schedule                                         │
├──────────────────────────────────────────────────────────┤
│ Customer        Description            Time              │
├──────────────────────────────────────────────────────────┤
│   ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┐      │
│   │ You have no visits scheduled today.          │      │
│   │ [+ Schedule a Job]                           │      │
│   └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘      │
└──────────────────────────────────────────────────────────┘
```

---

#### Partial: `templates/blocks/_list.html`

#### Data contract

| Key | Req | Type | Description |
|---|---|---|---|
| `variant` | no | string | `compact` or `full` (default `compact`) |
| `title` | yes | string | Block heading (e.g. "Today's Schedule", "Customers") |
| `heading_level` | no | int | `2` (default — for List / Report archetype pages) or `3` (for Detail archetype pages, where the §5.1.2 sub-header already provides an `<h2>`). See §6.2 Heading hierarchy. |
| `columns` | yes | iterable of column dicts | Column definitions — see below |
| `rows` | yes | iterable of row dicts | Row data — see below |
| `new_record` | no | dict | Top action strip — left side. `{label, href, icon}` (e.g. `{label: "New Customer", href: "/customers/new/", icon: "plus"}`). Available on both variants. |
| `filters` | no | iterable of filter dicts | Top action strip — right side. **Full variant only** — filter pills (Status / Type / etc.). |
| `search` | no | dict | Top action strip — right side. **Full variant only** — `{placeholder, name, value}` for the search input. |
| `pagination` | no | dict | Inside block proper, below rows. **Full variant only** — `{page, total_pages, has_prev, has_next, prev_url, next_url}`. |
| `current_sort` | no | dict | `{column_key, direction}` where direction is `asc` or `desc` |
| `max_height` | no | string | **Compact variant** — CSS height value for the rows region (default `24rem`). Set to `none` to disable the scroll cap. Ignored on full variant. |
| `empty_text` | no | string | Empty-state message (default: "No records.") |
| `empty_action` | no | dict | Empty-state CTA: `{label, href, icon}` |

**Top action strip auto-hide:** if `new_record`, `filters`, and `search` are all absent, the entire top action strip is omitted — no transparent space, nothing rendered. Block proper sits flush against whatever's above it. Useful for static logs (audit, read-only history).

#### Column dict

| Key | Req | Type | Description |
|---|---|---|---|
| `key` | yes | string | Matches the row dict key for this column's value |
| `label` | yes | string | Column header text |
| `is_primary` | no | bool | If true, this cell renders as a link to `row._href`. **Exactly one column per List Block must have `is_primary=true`.** |
| `sortable` | no | bool | If true, column header is a sort button. Default: `true` |
| `align` | no | string | `start` / `center` / `end` (default `start`) |
| `width` | no | string | CSS width hint (e.g. `"30%"`, `"8rem"`). Optional — Bootstrap auto-widths if absent. |

#### Row dict

| Key | Req | Type | Description |
|---|---|---|---|
| `<column_key>` | yes for each column | various | Value to display in that column. Caller pre-formats (numbers, dates, currency). |
| `_href` | yes | url | URL the primary-identifier cell links to (the record's Detail page). Caller constructs from record ID. |

#### Sort behavior

- **Tri-state per sortable column:** none → asc → desc → none
- **One column at a time** — clicking a different column resets the previous one
- Click sends a request with `?sort=<column_key>&dir=asc|desc` query params (server re-sorts and re-renders) — or HTMX swap once HTMX is wired
- The server passes `current_sort` back so the block knows which column to render arrow-up/down on
- **Notes case:** every column gets `sortable: false`. The sub-header still shows column titles, just no sort buttons. Notes render in their natural order (chronological, by `created_at desc`).

#### Filters / search / pagination (full variant only)

- `filters` is an iterable of filter pill dicts: `{label, name, options: [{value, label}], value}`. Renders in the top action strip on the right. Bootstrap dropdown style.
- `search` is a single text input rendered in the top action strip on the right (typically leftmost in that group). Submits on Enter.
- `pagination` shows page-X-of-Y with prev/next links inside the block proper, below rows. Active page state via `aria-current="page"`.
- All three submit via `GET` query params; server filters/searches/paginates and re-renders.

#### Caps + scrollbars

- **Compact variant:** the rows region (between sub-header and pagination) is capped at `max_height` (default `24rem`). When rows exceed the cap, the rows region scrolls vertically inside the block; the title and column headers remain fixed above the scroll. The block itself has a stable height so neighbors in the grid don't shift.
- **Full variant:** no inner cap. Long lists rely on page-level scroll. Title and column headers can be made sticky with `position: sticky; top: <header height>;` later if scroll feels disorienting on long lists — defer until first painful list.

#### Empty state (block-owned)

Caller passes `empty_text` (and optional `empty_action`). Block renders standardized empty markup. Caller never writes the empty UI directly.

#### Caller examples

**Compact (Today's Schedule on Dashboard):**

```django
{% include "blocks/_list.html" with variant="compact" title="Today's Schedule" new_record=schedule_new_button columns=schedule_columns rows=schedule_rows current_sort=schedule_sort empty_text="You have no visits scheduled today." empty_action=schedule_empty_action %}
```

Where the view sets:
```python
schedule_columns = [
    {"key": "customer_name", "label": "Customer", "is_primary": True, "sortable": True},
    {"key": "description", "label": "Description", "sortable": True},
    {"key": "scheduled_time", "label": "Time", "sortable": True, "align": "end"},
]
schedule_rows = [
    {"customer_name": "John Smith", "description": "HVAC tune-up", "scheduled_time": "10:00 AM", "_href": f"/jobs/{job.id}/"},
    ...
]
schedule_new_button = {"label": "New Job", "href": "/jobs/new/", "icon": "plus"}
schedule_empty_action = {"label": "Schedule a Job", "href": "/jobs/new/", "icon": "calendar-plus"}
```

**Full (Customers list page):**

```django
{% include "blocks/_list.html" with variant="full" title="Customers" new_record=customer_new_button columns=customer_columns rows=customer_rows filters=customer_filters search=customer_search pagination=customer_pagination current_sort=customer_sort %}
```

#### A11y

- Real `<table>` with `<thead>`, `<tbody>`, `<th scope="col">`.
- Sortable column headers are a `<button>` inside the `<th>` with `aria-sort="ascending" | "descending" | "none"` based on current state.
- The primary-identifier cell is an `<a>` (semantic link to the record). Other cells are plain `<td>`.
- Title is an `<h2>` (compact) or `<h2>` (full — page `<h1>` is in topbar; List Block title is one level down).
- Filter toolbar (full variant) is a labeled `<form>` or labeled `<div role="search">` for the search portion.
- Pagination is a labeled `<nav aria-label="Pagination">`.
- Empty state inside `<tbody>` uses a single full-row cell with `role="status"` so AT announces it.
- Filter pills are `<button>` (not `<a>`) with `aria-pressed` reflecting active state.
- New Record button is a real `<a>` (it navigates) or `<button>` (if it opens a drawer/modal — caller picks).

#### Future variants (not implemented)

- **Inline-edit mode** — clicking a non-primary cell switches to inline edit (Sub List / Detail-page sub-records). Defer until first use case (likely Quote/Invoice line items).
- **Selection mode** — checkboxes per row + bulk-action bar. Defer until needed.
- **Card layout (no table)** — for lists where the row-as-card pattern reads better than a table. Could be a `--cards` variant of this block, OR a separate block. Defer the decision.

---

### 3.3 Metric Data Block

A vertical list of label → value rows with optional drilldown chevrons. Bound to **model fields/properties** (not aggregations like KPI).

**Visual:**
```
┌───────────────────────────────────────┐
│ Business Performance                  │
├───────────────────────────────────────┤
│ Receivables                       →   │  ← row with drilldown
│ 0 clients owe you                     │
├───────────────────────────────────────┤
│ Upcoming Jobs                     →   │
│ This week                             │
├───────────────────────────────────────┤
│ Revenue                           →   │
│ This month                            │
│ $0                                    │
└───────────────────────────────────────┘
```

**Partial:** `templates/blocks/_metric_data.html`

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `title` | yes | string | Card heading |
| `heading_level` | no | int | `2` (default) or `3` (Detail pages). See §6.2 Heading hierarchy. |
| `metrics` | yes | iterable of dicts | Each: `label`, `caption` (optional), `value` (optional, prominent number), `href` (optional) |

**A11y:**
- When a metric has `href`, the row is an `<a>` (one tab stop per row, announced as a link).
- Chevron is `aria-hidden="true"`.
- Card root is `<section aria-labelledby="…">`.

---

### 3.4 Field Block

Label + value pair for Detail pages. Supports view-mode and edit-mode (toggled by the inline-edit pattern from `base.html`).

**Visual (view-mode):**
```
Phone (Primary)
(555) 123-4567
```

**Visual (edit-mode):**
```
Phone (Primary)
[ (555) 123-4567        ]
help text if any
```

**Partial:** `templates/blocks/_field.html`

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `label` | yes | string | Field label |
| `value` | yes | string | Display value (view-mode) |
| `name` | no | string | Form input name (edit-mode) — required if section is editable |
| `input_type` | no | string | "text" / "email" / "tel" / "number" / "select" / "textarea" (default: "text") |
| `options` | no | iterable | For `select`: list of `{value, label}` dicts |
| `required` | no | bool | Marks required + adds `aria-required="true"` |
| `help_text` | no | string | Below the input, linked via `aria-describedby` |
| `error` | no | string | Validation error, linked via `aria-describedby`, sets `aria-invalid="true"` |

**A11y:**
- `<label for="…">` always paired with the input.
- Required marker is text + `aria-required="true"` (color alone is never the indicator).
- Errors via `aria-describedby` + `aria-invalid="true"`.
- Help text via `aria-describedby`.

---

### 3.5 Tab Panel Block

Bootstrap tabs styled to brand. Used on Detail pages for sub-collections (Service Requests, Quotes, Jobs, Invoices, Assets).

**Visual:**
```
┌───────────────────────────────────────┐
│ ┃Service Requests┃ Quotes  Jobs  …    │  ← active tab has bottom border + bold
├───────────────────────────────────────┤
│  (active tab content)                 │
│                                       │
└───────────────────────────────────────┘
```

**Partial:** `templates/blocks/_tab_panel.html`

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `tabs` | yes | iterable of dicts | Each: `id`, `label`, `count` (optional badge), `panel_template` (template path) |
| `active` | no | string | id of initially active tab (defaults to first) |

**A11y:**
- Bootstrap tabs ship `role="tab"`, `aria-selected`, `aria-controls`, `role="tabpanel"`.
- We layer brand styles only — do not override Bootstrap's ARIA wiring.
- Tab list is in a `<nav aria-label="…">`.

---

## 4. Grid primitives

Named CSS Grid classes for in-body block layout. Live in `static/css/site.css`.

### 4.1 Grid classes

| Class | Columns | Use case |
|---|---|---|
| `sd-grid-1up` | `1fr` | Single block per row |
| `sd-grid-2up` | `1fr 1fr` | Equal halves |
| `sd-grid-3up` | `1fr 1fr 1fr` | Equal thirds |
| `sd-grid-4up` | `1fr 1fr 1fr 1fr` | Equal quarters — Lite KPI strip is 4-up |
| `sd-grid-2-1` | `2fr 1fr` | 2/3 + 1/3 — Detail main + context panel (Lite spec §23) |
| `sd-grid-1-2` | `1fr 2fr` | 1/3 + 2/3 — context panel on left (rare but valid) |

**Naming convention:** `sd-grid-Nup` for N equal columns; `sd-grid-A-B` for asymmetric splits using fr units (so `2-1` means `2fr 1fr`).

All grids share:
```css
display: grid;
gap: 1rem;
align-items: stretch;  /* blocks fill cell height */
```

**Block contract on its side:** `.sd-<block> { width: 100%; height: 100%; }` — so any block fills any cell.

### 4.2 Vertical stacking — `.sd-stack`

For spacing **between** stacked grids on the same page (e.g., a `sd-grid-4up` KPI strip above a `sd-grid-2-1` row), use `.sd-stack` on the parent:

```css
.sd-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;  /* gap between grids — slightly larger than gap inside a grid */
}
```

Caller pattern:
```html
<div class="sd-stack">
  <div class="sd-grid-4up">…KPI blocks…</div>
  <div class="sd-grid-2-1">…sub-list + metric data…</div>
</div>
```

`gap` inside a grid is `1rem`; `gap` between grids in a stack is `1.5rem` — so vertical rhythm reads as "blocks tighter than rows."

### 4.3 Nesting

**Grids can nest.** A common pattern: a Detail page uses `sd-grid-2-1` at the top level; the 2fr main canvas internally uses `sd-grid-2up` for two side-by-side Field blocks.

```html
<div class="sd-grid-2-1">
  <div>  <!-- the 2fr cell -->
    <div class="sd-grid-2up">
      …two field blocks side by side…
    </div>
  </div>
  <div>  <!-- the 1fr cell -->
    …context blocks…
  </div>
</div>
```

No special syntax needed — CSS Grid handles nested containers naturally. Reviewer catches abuse (deep nesting that suggests a missing block type).

### 4.4 Responsive collapse

At narrow viewports, all multi-column grids collapse to a single column. Default rule:

```css
@media (max-width: 768px) {
  .sd-grid-2up,
  .sd-grid-3up,
  .sd-grid-4up,
  .sd-grid-2-1,
  .sd-grid-1-2 {
    grid-template-columns: 1fr;
  }
}
```

Per-grid breakpoints can be tuned later if needed (e.g., `sd-grid-4up` collapsing to 2-up at tablet width before going single-column on phone). Defer until first real responsive use case.

### 4.5 Future / out-of-scope

- **9-cell layout** — use three stacked `sd-grid-3up` rows, not a single 3×3 grid. The previous draft proposed `sd-grid-3x3` but real-world Reports compose row-by-row, not in a forced rectangle.
- **Asymmetric variants beyond 2-1 / 1-2** (e.g., `3-1` for 75/25, `1-1-2` for 25/25/50) — add when a real page needs one. Don't pre-build.
- **Auto-fit / wrapping grids** (`repeat(auto-fit, minmax(…))`) — defer until a use case appears. Most data we render has known cardinality.

---

## 5. Archetype chrome

Archetype chrome is opt-in chrome that varies per page archetype. Two kinds:

- **Sub-headers** — sit between Header and Body. Opted into via `{% block subheader %}` in `base.html`.
- **Footers** — sit below Body, at the natural bottom of `<main>` (not sticky). Opted into via `{% block page_footer %}` in `base.html`.

Each kind has a catalog of variants below — every variant gets the same treatment as a block in §3 (visual + data contract + ARIA).

---

### 5.1 Sub-headers

Transparent strip between Header and Body. Two variants documented; one implemented. (List archetype has no sub-header — its filter strip and `+ New Record` button live in the List Block's top action strip per §3.2.)

#### 5.1.1 Greeting (Report archetype)

Used by Dashboard. Time-of-day greeting with the user's name.

**Visual:**
```
Good Morning, Ron
```

**Partial:** `templates/includes/_subheader_greeting.html` (TBD — currently inlined in `home.html`)

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `greeting` | yes | string | "Good Morning" / "Good Afternoon" / "Good Evening" — from context processor |
| `user_display_name` | yes | string | First name → username fallback — from context processor |

**Caller (current — Dashboard inlines it):**
```django
{% block subheader %}
  <div class="sd-subheader">
    <p class="sd-greeting">{{ greeting }}, {{ user_display_name }}</p>
  </div>
{% endblock %}
```

**A11y:** Greeting is a `<p>`, not a heading (the page `<h1>` is in the header center). Plain text, no ARIA needed.

**Status:** CSS in place (`.sd-subheader`, `.sd-greeting`); markup currently inline in `home.html`. Extract to partial when we refactor Dashboard.

---

#### 5.1.2 Record context (Detail archetype)

Used by Customer Details, Asset Details, Job Details, etc. Three regions: record (left), tags (center), actions (right).

**Visual:**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ John Smith                  [Active] [Urgent]            [Export] [+ Quote] │
│ CU26-00125 · Residential                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

The tags region holds **one or more colored pills** — typically Status, Priority, Type, or any other classifying field that benefits from color coding. They are separate fields in the data, not folded into one.

**Partial:** `templates/includes/_subheader_detail.html` (TBD)

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `record_name` | yes | string | Display name of the record (e.g. customer name) |
| `record_meta` | no | string | Identifier + secondary classifier (e.g. "CU26-00125 · Residential") |
| `tags` | no | iterable of dicts | Tags region — each: `{label, variant}` where `variant` is a token from the §3.1 universal accent palette |
| `actions` | no | iterable of dicts | Actions region — each: `{label, href` or `onclick, variant, icon}` |

**Tag dict:**

| Key | Required | Type | Description |
|---|---|---|---|
| `label` | yes | string | Pill text (e.g. "Active", "Urgent", "Commercial") |
| `variant` | yes | string | Color token — one of the §3.1 palette (`success`, `warning`, `danger`, `info`, `neutral`, `brand`). Source per §3.1's user-controlled vs. hardcoded note. |

**Action dict:**

| Key | Required | Type | Description |
|---|---|---|---|
| `label` | yes | string | Button text |
| `href` | no | url | Navigation target. Mutually exclusive with `onclick`. |
| `onclick` | no | string | JS handler / drawer trigger. Mutually exclusive with `href`. |
| `variant` | no | string | `primary` (default), `secondary`, or `destructive`. `destructive` renders red — used for Delete and similar irreversible actions. |
| `icon` | no | string | Lucide icon name (e.g. "trash-2" for Delete) |

**Caller example:**
```django
{% block subheader %}
  {% include "includes/_subheader_detail.html" with record_name=customer.display_name record_meta=customer.identifier_meta tags=customer_tags actions=detail_actions %}
{% endblock %}
```

Where the view sets:
```python
customer_tags = [
    {'label': customer.status.label, 'variant': customer.status.color_variant},
    {'label': customer.priority.label, 'variant': customer.priority.color_variant},
]
detail_actions = [
    {'label': 'Export', 'variant': 'secondary', 'icon': 'download', 'href': customer.export_url},
    {'label': 'New Quote', 'variant': 'primary', 'icon': 'plus', 'href': customer.new_quote_url},
    {'label': 'Delete', 'variant': 'destructive', 'icon': 'trash-2', 'onclick': 'sdConfirmDelete()'},
]
```

**Layout:** 3-column flex (record left / tags center / actions right). Long record names truncate with ellipsis; tags wrap to a second line if they overflow.

**A11y:**
- Record name is `<h2>` (page `<h1>` is in the header).
- Each tag combines color + label text (color is never the sole indicator).
- Action buttons are real `<button>` or `<a>` with `aria-label` if icon-only.
- Destructive action gets `aria-describedby` pointing to a confirmation tooltip if no modal interrupts the click.

**Status:** Spec'd, not implemented. CSS classes (`.sd-subheader--detail`, `.sd-tag`, `.sd-tag--<variant>`) defined here but not in `site.css` yet.

---

### 5.2 Footers

Sit below Body at the natural bottom of `<main>` content. Not sticky — visible only after scrolling to bottom of page. One variant documented.

#### 5.2.1 Detail audit footer (Detail archetype)

Records who created and last modified the record, with timestamps. Persistent on every Detail page.

**Visual:**
```
─────────────────────────────────────────────────────────────────
 Modified by Alex Kim · May 1, 2026 2:34 PM    Created by Ron Hoagland · Apr 18, 2026 9:12 AM
```

Modified-by is **left-justified**; Created-by is **right-justified** (per Ron's spec).

**Partial:** `templates/includes/_footer_detail.html` (TBD)

**Data contract:**

| Key | Required | Type | Description |
|---|---|---|---|
| `created_by` | yes | User | Foreign key to user who created the record |
| `created_at` | yes | datetime | When the record was created |
| `modified_by` | yes | User | Foreign key to user who last modified the record. **Never null** — populated to the creator's value at record creation, then updated on each subsequent edit. |
| `modified_at` | yes | datetime | When the record was last modified. **Never null** — populated to `created_at` at record creation, then updated on each subsequent edit. |

**Both lines always render**, even on never-edited records (in which case `modified_*` mirrors `created_*`). Layout stays stable; the eye learns where to look.

**Caller example:**
```django
{% block page_footer %}
  {% include "includes/_footer_detail.html" with created_by=customer.created_by created_at=customer.created_at modified_by=customer.modified_by modified_at=customer.modified_at %}
{% endblock %}
```

**Layout:** 2-column flex (Modified left, Created right). Top border to separate from body.

**A11y:**
- Root is `<footer>` (semantic landmark).
- Timestamps are `<time datetime="2026-05-01T14:34:00-05:00">May 1, 2026 2:34 PM</time>` — machine-readable + human-readable.
- `<footer>` carries `aria-label="Audit information"` so the landmark has a name in screen-reader rotor.

**Behavior:** Natural-bottom (sits at the end of `<main>` content; user scrolls to see it). Not sticky.

**Base.html change required:** Add `{% block page_footer %}{% endblock %}` immediately after `{% block content %}` and inside `<main>`. Pages without an audit footer leave the block empty.

---

## 6. A11y contract (every block)

The block system enforces **WCAG 2.1 AA**. Every block partial — and every chrome variant in §5 — must satisfy the requirements below. Reviewer holds the line; new blocks fail review until they comply.

### 6.1 Required guarantees

- **Semantic root** — `<section>`, `<article>`, `<a>`, `<button>`, `<table>`, etc. as appropriate. Never a bare `<div>` for an interactive element.
- **Labels** — every form input has `<label for="…">`. Icon-only buttons have `aria-label`. Landmarks (`<nav>`, `<aside>`, `<section>`) carry `aria-label` or `aria-labelledby` when more than one of the same type appears on a page.
- **Decorative icons** — Lucide icons accompanied by visible text are `aria-hidden="true"`. Icon-only interactive elements rely on `aria-label`.
- **Focus visible** — interactive elements inherit `:focus-visible` styling (`--sd-focus-ring` on light bg, `--sd-focus-ring-dark` on the sidebar). Custom interactive classes are added to the focus-ring selector list in `site.css`. Never remove the outline without a visible replacement.
- **Touch target ≥ 24×24 px** — interactive elements meet WCAG 2.5.8 (AA). Where a smaller visual indicator is needed (a 16px icon), expand the click target via padding.
- **Color is not the only indicator** — status badges combine color + label text; required fields show `*` + `aria-required="true"`; errors show text + icon + color; sortable columns show arrow + `aria-sort`.
- **Contrast** — every fg/bg pair must meet WCAG AA (4.5:1 normal, 3:1 large/bold). Use only colors from the universal palette in §3.1. New colors require updating the verified-pairs table in `site.css`.
- **Empty state announced** — empty state markup lives inside the same labeled region as the data so AT announces "Today's Schedule: empty…" rather than silence.
- **Reduced motion** — blocks with custom animations or transitions must honor `prefers-reduced-motion: reduce`. The universal rule in `site.css` short-circuits `transition-duration` and `animation-duration` to 0.01ms — block-level animations either inherit standard CSS transitions (covered automatically) or include their own `@media` block.
- **Dynamic announcements** — validation errors appearing, async data loads, status updates from form submission all need `aria-live` regions or `role="alert"`. `aria-describedby` on inputs pairs static help text but doesn't trigger AT announcements when the description changes.
- **Language** — page lang is set on `<html lang="en">` in `base.html`. Blocks must not include text in a different language without a `lang` attribute on that subtree.

### 6.2 Heading hierarchy

Page heading levels are **structurally fixed** by the chrome:

| Level | What | Where |
|---|---|---|
| `<h1>` | Page title | Header center (universal chrome) — exactly one per page |
| `<h2>` | Sub-header record name (Detail) **OR** top-level body heading (List title, Report greeting) | Either the §5.1.2 sub-header on Detail, or the first top-level heading inside `<main>` on other archetypes |
| `<h3>` | Block titles when nested under an `<h2>` sub-header | List / Metric Data / Sub-list block titles on Detail pages |
| `<h4>` | Headings inside Tab Panel content | Within tab content on Detail pages |

**The heading-level rule:** block titles default to `<h2>`. On **Detail pages** — where the §5.1.2 sub-header already provides an `<h2>` for the record name — block titles must drop to `<h3>` so the hierarchy doesn't double up at h2.

Block partials with a title expose a `heading_level` parameter in their data contract (default `2`; caller passes `3` on Detail pages). See §3.2 (List) and §3.3 (Metric Data) for the contract entries.

**Levels never skip.** Going h1 → h3 is a violation, even if the page layout makes it look reasonable.

### 6.3 Testing process

Every new block (and every page using one) goes through this checklist before merging:

1. **Keyboard-only walk** — close trackpad/mouse. Tab through every interactive element. Verify:
   - Focus is visible at every step
   - Tab order matches visual order (no surprise jumps)
   - Esc closes any open drawer / modal
   - Enter / Space activates focused buttons and links
   - Arrow keys navigate within tab lists, dropdowns, sortable column headers
2. **Screen reader spot-check** — VoiceOver on Mac (Cmd+F5) or NVDA on Windows. Read the page once. Verify:
   - Landmarks announced (`main`, `navigation`, `complementary`, `contentinfo`)
   - Headings announced in correct order with correct levels
   - Buttons announced as "button", links as "link"
   - Empty states announced
   - Status changes announced (form submission feedback, sort changes, etc.)
3. **axe DevTools scan** — Chrome/Firefox extension. **Goal: 0 violations.** Each violation reported has a fix suggestion; address before merging.
4. **Lighthouse a11y audit** — Chrome DevTools → Lighthouse → Accessibility. Target score ≥ 95. Most issues overlap with axe; a few are unique (e.g., document title quality, viewport meta).
5. **Contrast verification** — for any new color, run the pair through [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/). New colors require updating the verified-pairs table in the `site.css` header.
6. **Reduced-motion check** — toggle macOS System Settings → Accessibility → Display → Reduce Motion (or Windows equivalent). Verify animations short-circuit.
7. **Color-blindness sanity** — use a browser color-blindness simulator extension or macOS Color Filters. Status badges and other color-coded elements remain distinguishable (label text carries the meaning; color is supportive).

### 6.4 Tooling

| Tool | Purpose | Install / link |
|---|---|---|
| **axe DevTools** | Violation scanner — single-click check on any page | Chrome / Firefox extension store |
| **Lighthouse** | Per-page a11y score + recommendations | Built into Chrome DevTools |
| **WAVE** | Visual overlay of a11y issues on the rendered page | Chrome / Firefox extension store |
| **WebAIM Contrast Checker** | Contrast ratio verification for new colors | webaim.org/resources/contrastchecker |
| **VoiceOver** | macOS native screen reader | Cmd+F5 |
| **NVDA** | Free Windows screen reader | nvaccess.org |
| **Color Filters** | macOS color-blindness simulation | System Settings → Accessibility → Display |

No automated a11y tests in the test suite for now — that needs a headless browser, which conflicts with the no-Playwright decision in `LITE_DECISIONS.md` §J. Manual + browser tools is sufficient at MVP scale; revisit when a customer requires VPAT.

### 6.5 Future considerations

- **HTMX swaps** — once HTMX is wired (Lite Phase 2+), partial page swaps need `aria-live` regions on the swap target so screen readers announce the change. Likely use `hx-swap-oob` for status-bar feedback. Detailed when the first HTMX page lands.
- **Focus management on navigation** — when a Detail page loads from a List click, focus should move to the page heading (not stay where it was). Implement via small JS on `DOMContentLoaded` or on HTMX swap.
- **VPAT** — formal Voluntary Product Accessibility Template still deferred per `LITE_DECISIONS.md` §E. Generate when a customer requires one; not before MVP launch.

The full a11y baseline (color palette with verified contrast pairs, focus tokens, reduced-motion rule) is documented in the `static/css/site.css` header comment.

---

## 7. Adding a new block (or chrome variant)

When an existing block can't carry what you need, follow this sequence:

1. **Add a §3.x entry** to this doc — visual sketch + data contract + a11y notes.
2. **Create the partial:** `templates/blocks/_<name>.html`.
3. **Add CSS:** `.sd-<name>` + child classes in `static/css/site.css`. Block must obey `width: 100%; height: 100%`.
4. **Wire focus styles:** add the block's interactive root to the appropriate `:focus-visible` selector list.
5. **Self-test:**
   - Render in isolation in a real page.
   - Tab through it. Focus visible everywhere.
   - Resize browser. Block fills its cell at every breakpoint.
   - axe DevTools = 0 violations.
   - Try OS reduce-motion preference.
6. **Bump `SERVIZDESK_UI_ASSET_VERSION`** in `config/settings.py` to bust CSS cache.

If a new block is essentially a variant of an existing block (e.g., "KPI but vertical"), prefer a modifier class (`.sd-kpi--vertical`) over a brand-new block type.

**Adding a new chrome variant (sub-header or footer):** same recipe, with two differences:
- §5.x entry (instead of §3.x).
- Partial lives in `templates/includes/_<name>.html` (instead of `templates/blocks/`).

---

## 8. Implementation status

### ✅ Defined (this doc)
- Architecture (§1) — 4-layer model + naming conventions
- Page archetypes ×4 (§2) — documented as conventions, not skeleton templates
- Block catalog ×5 (§3) — KPI, List, Metric Data, Field, Tab Panel
- Universal accent token palette (§3.1) — shared by KPI accents and tag/badge variants
- Grid primitives ×6 + `.sd-stack` + responsive collapse rule (§4)
- Archetype chrome (§5) — 2 sub-header variants + 1 footer variant
- A11y contract (§6)

### ✅ Implemented
- Universal chrome — `templates/base.html`, `templates/includes/app_sidebar.html`
- Header (3-col grid + live datetime + breadcrumb + page title + search)
- Skip-link (`.sd-skip-link`) + main landmark
- Sub-header §5.1.1 (greeting variant) — markup currently inline in `templates/home.html`
- Inline-edit pattern (CSS hooks for `.sd-section-card.editing`, drawer offcanvas)
- A11y foundation: rem sizing, `:focus-visible` rings, contrast palette, reduced-motion, ARIA on chrome
- Brand tokens (`--sd-brand-*`, `--sd-sidebar-*`, `--sd-card-border`, `--sd-focus-ring`, etc.)

### ⬜ Remaining Tier 1 build (what gets built next)
- [ ] Grid primitives in `site.css` (`sd-grid-1up` through `sd-grid-3x3`)
- [ ] Accent token palette in `site.css` (`--sd-accent-success/warning/danger/info/neutral`)
- [ ] `templates/blocks/_kpi.html` — extract from `home.html` stat strip
- [ ] `templates/blocks/_list.html` — unified List Block (compact + full variants)
- [ ] `templates/blocks/_metric_data.html` — extract from `home.html` Business Performance
- [ ] `templates/blocks/_field.html`
- [ ] `templates/blocks/_tab_panel.html`
- [ ] Sub-header §5.1.1 partial extraction — `templates/includes/_subheader_greeting.html`
- [ ] Sub-header §5.1.2 (record context) — partial + CSS
- [ ] Footer §5.2.1 (Detail audit footer) — partial + CSS + `{% block page_footer %}` slot in `base.html`
- [ ] Refactor `home.html` to use the extracted blocks via grid primitives (Today's Schedule becomes a compact List Block)

### ⬜ Tier 2 (future)
- Forms styling (Bootstrap form-control overrides)
- Status badges + tag pills (`.sd-tag`, `.sd-tag--<variant>`) — used by §5.1.2 record context
- Action button variants — `.btn-sd-destructive` (red) added on top of Bootstrap
- Toasts (Django messages framework styled)
- **Status data model: `color_variant` field on user-controlled status records** (e.g., `ValueListItem.color_variant`) so admins can pick the universal palette token when defining a status. Hardcoded lifecycle statuses get a small Python mapping module per entity.
- Status admin UI — restrict color choice to the universal palette (no free-form hex pickers) to preserve contrast guarantees.

> Note: an earlier draft proposed a "Tier 2 archetype skeletons" layer (`templates/archetypes/_*.html`). That layer was intentionally **not built** — page archetypes are documented conventions in §2. Pages extend `base.html` directly. Re-evaluate if duplication across pages becomes painful.

---

## Appendix — Cross-references

- A11y baseline + verified contrast palette → header comment of `static/css/site.css`
- Lite tier UI scope and §29 product decisions → `Architecture & Planning/LITE_DECISIONS.md`
- Build phase ordering → `Architecture & Planning/LITE_BUILD_TODO.md`
- Visual prototype reference (Tailwind-era, supersedes apply Bootstrap mapping) → `UI-UX/UIX Prototypes/lite-shell-prototype.html` (if still present after the doc reorg)

---

**End of Block Reference.**
