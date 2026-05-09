# Lite Tier UI — documentation index

Use this folder as the **single handoff surface** for Lite UI implementation (product + UX + technical rules).

## Start here

1. **`Lite Tier UI & Functionality Specification (v1).md`** — **canonical** specification. Implement against this document unless an issue is filed to change it.
2. This **`README.md`** — how the pieces fit together and what is out of scope.

## Other files

| File | Purpose |
|------|---------|
| **`User_Work_Experience_Spec_V1.md`** | Cross-cutting UX principles only; **not** the Lite information architecture. See the notice at the top of that file. |
| **`lite_tier_ui_functionality_specification.md`** | **Stub only** — older filename; content was merged into the canonical v1 spec. |

## Key implementation anchors (in v1)

- **§3** — Navigation plus **information architecture** (where intake and Service Requests live relative to Jobs).
- **§6–16** — Core workflow, feature behavior, products/tasks UX rules, summary, and **intake** specification.
- **§17** — Service Request lifecycle (ties Quotes/Jobs to intake).
- **§18–20** — Quote, Job, and Invoice lifecycles (status machines and edits).
- **§21** — Upgrade hinting (Plus).
- **§22–23** — Asset and Customer technical rules.
- **§24** — Products & Services (master catalog + line items).
- **§25** — Payments (Lite: one payment per invoice, no partial pay).
- **§26** — Customer email / PDF send rules.
- **§27** — Roles (Admin / User), **tenant financial preferences** (tax rate, currency, rounding), visibility, screen-level behavior, Tasks / Time / Settings expectations.
- **§28** — Completion checklist for this spec.
- **§29** — Remaining decisions and backlog (asset types, search, void reasons, a11y, etc.).

## Principles for agents and developers

- If v1 and another note conflict, **v1 wins**.
- If something is missing from v1, check **§29** before inventing behavior; record new decisions there or in an issue tracker.
