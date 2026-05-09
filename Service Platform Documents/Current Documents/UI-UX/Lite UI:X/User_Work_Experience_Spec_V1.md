# User Work Experience Specification (V1)

> **Scope (Lite Tier):** This document describes a **general user-centric work-hub pattern** (dashboards, tasks, calendars). It is **not** the Lite Tier **navigation map**, **screen inventory**, or **data model**. For Lite UI build work, use **`Lite Tier UI & Functionality Specification (v1).md`** and **`README.md`** in this same folder. Apply principles here (e.g. fewer clicks, avoid modal-heavy primary flows) only when they **do not conflict** with the Lite spec.

---

## 1. Product Philosophy
The system is a **user-centric work hub** focused on what the user needs to do now.

### Visibility Rules
A user can access an object if:
- Assigned to it
- Created it
- Member of its group

Group membership grants full access.

### Portfolio Visibility
- Portfolio access requires explicit membership
- Project access does NOT grant portfolio access

---

## 2. Global UX Rules
- Default lists show only user-relevant records
- Completed items hidden by default
- One-click to open, two-click max for actions
- No modal-based primary workflows

---

## 3. Layout Framework
- Header: user info + daily time
- Left: navigation
- Center: main workspace
- Right: agenda (day-based)

---

## 4. My Dashboard
The default landing page and personal work hub.

### Structure
- KPI Strip (awareness)
- Work Lists (execution)
- Calendar (selection)
- Agenda (detail)

### Key Rules
- Lists: 6 rows visible, scrollable
- View All: scoped to user access
- Calendar drives Agenda
- Agenda defaults to Today

---

## 5. My Tasks
Primary execution list.

### Behavior
- Grouped: Overdue / Today / Upcoming / No Date
- One-click to detail
- Simple filters and sorting

---

## 6. Task Detail
Primary execution screen.

### Behavior
- Full-page layout
- Inline edits
- Time logging
- Context visible

---

## 7. My Projects
User-scoped project list.

### Behavior
- Shows active relevant projects
- Sorted by urgency
- No portfolio leakage

---

## 8. Project Detail
Project workspace.

### Sections
- Overview
- Tasks
- Milestones
- Meetings
- Activity

---

## 9. My Calendar
Time navigation.

### Behavior
- Monthly view
- Icons + counts only
- Click day updates Agenda

---

## 10. My Meetings
Meeting list.

### Behavior
- Focus on Today + Upcoming
- One-click to detail

---

## 11. Meeting Detail
Meeting workspace.

### Behavior
- Shows schedule, notes, context
- Supports prep + follow-up

---

## 12. My Milestones
Deadline tracking list.

### Behavior
- Grouped by urgency
- One-click to detail

---

## 13. Milestone Detail
Milestone workspace.

### Behavior
- Shows status, date, context
- Links to tasks and project

---

## 14. Portfolio List
Visible only to members.

### Behavior
- No indirect access
- Sorted by health and timing

---

## 15. Portfolio Detail
Portfolio workspace.

### Sections
- Overview
- Projects
- Milestones
- Activity

---

## 16. My Time
Personal time tracking.

### Behavior
- Shows only user’s entries
- Daily + weekly summary
- Easy edit

---

## 17. Core UX Summary
System prioritizes:
- Awareness
- Execution
- Context
- Time

Result:
Fast, predictable, user-focused experience.
