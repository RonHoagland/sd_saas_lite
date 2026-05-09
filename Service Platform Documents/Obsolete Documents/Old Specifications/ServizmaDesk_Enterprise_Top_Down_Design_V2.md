# ServizmaDesk Enterprise Top-Down Design
**Subtitle:** The "ServiceTitan Killer" Blueprint
**Document Status:** Working Draft — Conceptual Design
**Document Version:** V2
**Classification:** Internal — Confidential

---

# 1. Executive Summary & Design Philosophy

## 1.1 Top-Down Design, Bottom-Up Build
ServizmaDesk is being built via a "bottom-up" approach, starting with the strictly constrained **Lite** tier. However, the data models constructed for Lite must not artificially restrict the system from scaling to its ultimate ceiling. 

This document outlines the **Top-Down Design**—the highest functional capability of the platform (the "Enterprise" tier).

## 1.2 The Ultimate Vision
The long-term objective is to dethrone the industry leader, **ServiceTitan**. ServizmaDesk will be specifically engineered for trade services (Electrical, Plumbing, HVAC) and large commercial service organizations. It is an operational ERP that dominates Intake, Dispatch, Field Execution, Quoting, and Inventory. 

*Note on Boundaries:* While ServizmaDesk handles deep operational financials (Invoicing, AR, POs, Time Tracking, Job Costing, Commission rules), it intentionally stops at the General Ledger. True Tax/GL accounting and IRS-compliant Payroll are explicitly pushed to deep integrations (e.g., QuickBooks Enterprise, Sage Intacct, NetSuite, ADP, Gusto), avoiding massive legal liability while maintaining operational dominance.

---


# 2. The Competitive Differentiators (How We Beat ServiceTitan)

Feature parity alone will not dethrone the industry leader. The architectural mandates in this document are designed to attack ServiceTitan's core vulnerabilities:

### 2.1 The Onboarding Nightmare (Our Advantage: "Bottom-Up" Simplicity)
- **The Problem:** ServiceTitan's implementation takes 3 to 6 months. It requires a dedicated onboarding team and setting up dozens of configuration profiles before a single Work Order can be dispatched.
- **The Solution:** By building "bottom-up" from our **Lite** tier, our core workflows are fundamentally simple. A new commercial customer can sign up, connect Stripe, add a Company, and dispatch a Work Order in 15 minutes. Advanced features unlock seamlessly as the tenant scales.

### 2.2 The Offline Mobile App Disaster (Our Advantage: True UUID Edge Sync)
- **The Problem:** Legacy ERP mobile apps suffer from sync failures resulting in massive data conflicts when a technician reconnects to cellular service after working deeply offline.
- **The Solution:** By explicitly mandating **UUIDs** and an offline-first architecture from Day 1, our tablet app avoids database merge conflicts entirely. Technicians in basements experience zero lag when capturing photos or generating invoices.

### 2.3 Nested Assets for Real Commercial Work (Our Advantage: Parent/Child Structures)
- **The Problem:** Competing software, built initially for residential calls (e.g., swapping a toilet), struggles to manage complex commercial facilities where a single HVAC chiller unit has 50 trackable sub-components with independent warranties.
- **The Solution:** We designed the **Nested Service Item** (Parent/Child architecture) into the fundamental blueprint. ServizmaDesk tracks the 2-year warranty of a condenser coil uniquely within the 10-year warranty of its rooftop parent unit.

### 2.4 Custom Extensibility (Our Advantage: Open Architecture)
- **The Problem:** End-users are trapped in a walled garden, forced to adapt their business processes to the software's hardcoded workflows.
- **The Solution:** ServizmaDesk's native IFTTT Automation Engine and full Webhook/REST API support empowers fast-moving organizations to mold the software precisely to their operational model.

---
# 3. Core Platform & CRM

The nervous system. Without a rock-solid foundation, the ERP turns into spreadsheet soup.

## 3.1 Core System Administration
- **Multi-Location Hierarchy:** True Multi-company and multi-branch management.
- **Enterprise Security:** SSO / Identity provider support, granular role/permission enforcement.
- **Audit & Compliance:** Immutable audit logs, detailed API key management, Webhooks / event subscriptions.
- **Extensibility:** Custom fields / metadata engine, global search, robust localization (taxes/currencies/timezones).
- **Environment:** Feature flags, Sandbox / test environments for safe onboarding.

## 3.2 CRM / Customer Management
- **Property Centricity:** Rich residential and commercial customer profiles, mapping multiple properties to a single master billing account.
- **Commercial Context:** Building managers, AP contacts, contract pricing, PO-required flags, and site-specific compliance tracking (COIs).
- **History & Intelligence:** Service history timelines, communication logging, customer segmentation, membership tracking, and satisfaction/review tracking.

---

# 4. Intake, Scheduling & Dispatch

Where chaos enters through the phone, ServizmaDesk must bring instant order.

## 4.1 Call Center & Service Intake
- **Smart Intake:** Inbound call logging, caller ID auto-matching, job type classification, and priority/severity scoring.
- **Omnichannel:** Web booking, self-service portals, chat, and SMS intake.
- **Emergency Handling:** Triage scripts, missed call recovery workflows, and after-hours answering service integrations.
- *Dream State:* AI-assisted intake that suggests job categories from the customer's raw, non-technical words.

## 4.2 The Dispatch Engine Room
- **Visual Dispatch Board:** Drag-and-drop scheduling, capacity planning, and zone/territory enforcement.
- **Smart Rules:** GPS technician tracking, skill-based assignment (don't send a plumber to a high-voltage call), and multi-tech/project scheduling.
- **Dynamic Routing:** Travel time calculation, traffic-aware route optimization.
- *Dream State:* Algorithmically assigning jobs based on a weighted matrix of tech skill, inventory on their truck, live traffic, and account margin.

---

# 5. Field Execution & Quoting

If the field app is weak, the entire ERP is just a fancy office toy. Software becomes money in the technician's hands.

## 5.1 Technician Mobile App (Offline-First)
- **True Offline Mode:** Technicians must be able to complete safety forms, checklists, and invoices in a basement with zero cellular service.
- **Rich Context:** Access to full customer/asset history, wiring/plumbing diagrams, and part requests from the field.
- **Field Capture:** Photos (Before/After), videos, voice notes, and signature capture.
- **Compliance:** Code-related prompts, permit flag warnings, and safety hazard acknowledgments.

## 5.2 Estimating & Good/Better/Best Quoting
- **Option Quoting:** Building multi-option visual proposals (Good/Better/Best) instantly.
- **Prebuilt Assemblies:** One-click quoting for complex jobs (e.g., "Water Heater Replacement" automatically pulls the heater, pipes, valves, venting, and labor hours).
- **Sales Power:** E-signature, deposit requests, deep financing integrations, and geo-based margin-target pricing.

## 5.3 Work Order Management (The Record of Truth)
- Deep linkage between the Scope of Work, Labor lines, and Material lines.
- Links to installed Equipment/Assets, warranty flags, required permits, and inspections.
- *Dream State:* Enforcing quality rules—blocking a technician from closing out a specific job category until mandatory "After" photos are uploaded.

---

# 6. Service Agreements & Asset Lifecycle

The recurring revenue engine and commercial stronghold.

## 6.1 Memberships & Contacts
- Preventive maintenance agreements with auto-renewals, automated billing schedules, and SLA tracking.
- Deferred revenue tracking and contract-linked dispatch prioritization (NTE tracking for commercial).

## 6.2 Asset & Equipment Management
- **Nested Assets:** Parent/Child asset tracking (e.g., Rooftop HVAC Unit contains a Blower Motor).
- Serial/model tracking, warranty expiration tracking, and lifecycle cost tracking natively linked to the property.

---

# 7. Supply Chain: Inventory & Purchasing

Where trade businesses bleed cash quietly.

## 7.1 Multi-Warehouse & Truck Stock
- True Item Master / SKU management with unit-of-measure conversions.
- Multiple physical warehouses, exact bin locations, and every technician's truck mapped as a rolling warehouse.
- Cycle counts and physical counts with shrinkage/variance tracking.

## 7.2 Advanced Procurement
- Backorder flagging, automatic Purchase Order creation based on live Reorder Min/Max Par levels.
- Technician field-requests for parts routing directly to the purchasing manager.
- Vendor profiles, price list tracking, and return/credit management.

---

# 8. Project Management (Commercial Jobs)
For panel upgrades, tenant improvements, and heavy installations.
- **Hierarchy:** Job-to-Project rollups, milestones, and phases.
- **AIA / Progress Billing:** Invoicing by percentage of completion, tracking retainage, and managing change orders.
- Subcontractor coordination, permit tracking, and WIP (Work in Progress) tracking.

---

# 9. Operational Finance & Labor Costing
- **AR & Billing:** Batch invoicing, consolidated monthly billing for commercial accounts, split-billing, T&M, and flat-rate tracking.
- **Payments:** Credit/ACH acceptance, mobile field capture, payment plans, and auto-dunning / collections workflows.
- **Time & Labor Costing:** Mobile clock-in/out, job labor allocation, overtime rules, prevailing wage support, commission, and spiff (bonus) tracking. (Integrates to third-party Payroll).

---

# 10. Enterprise Premium Add-Ons
These highly specialized modules will be developed as separated, paid additions to the core Enterprise suite.
- **Fleet & Vehicle Management:** GPS telematics integration, maintenance schedules, fuel tracking.
- **Tool / Equipment Tracking:** Barcode/QR scanning for expensive tools (calibrations, loss tracking) checked out to specific trucks.
- **Risk & Compliance Management:** OSHA logs, safety incident tracking, permit-to-work controls.

---

# 11. Portals & Communication

## 11.1 Customer Portal (Self-Service)
- A white-labeled portal for customers to request service, approve estimates, pay invoices, and download property service history / contracts.
- Commercial managers can submit POs and view multi-site rolled-up histories.

## 11.2 Workflow & Automation Engine
- True automation: "IF [event] THEN [action]".
- Automated dispatch texts ("Tech is on the way"), appointment reminders, review requests, and renewal notices.

## 11.3 Document Management System (DMS)
- Deep SOP libraries, wiring diagrams, code references, and troubleshooting guides natively linked and searchable from within the Work Order based on the asset being repaired.

---

# 12. Business Intelligence (BI)

- Dashboards for Executive Revenue, Tech Productivity (First-Time Fix Rate, Callback Rate, Average Ticket).
- Inventory turn forecasting, SLA compliance rates, and marketing attribution models.

---

# 13. Architectural Takeaways for Development Day 1

To ensure the MVP (Lite) does not block this ServiceTitan-killer vision:

1. **UUIDs Only:** The use of UUIDs for foreign keys is absolute. The offline-first mobile app in Phase 4 will require devices to generate database keys while disconnected from cell service. Auto-incrementing integers will completely break sync conflict resolution.
2. **Abstracted Pricing:** Base objects (Items, Labor) must link to intermediate pricing models (Price Books) rather than hardcoded prices, supporting multi-tier commercial contract pricing in the future.
3. **Many-to-Many Relationships:** A Work Order must structurally be able to link to multiple Service Items, and an Invoice to multiple Work Orders (Progress / Batch billing).
4. **Parent/Child Architecture:** Base tables (`Company`, `ServiceItem`) must include nullable `parent_id` foreign keys to support the retail franchise and nested-equipment structures required by commercial clients.

---
**End of Document**
