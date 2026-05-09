# Fleet Maintenance SaaS – Master Blueprint

## 1. Product Positioning

**Target Market:**
- Small to mid-size service companies (10–30 vehicles)
- HVAC, Plumbing, Electrical, Pest Control, Local Delivery

**NOT targeting:**
- Trucking / logistics
- GPS-heavy fleet tracking

**Core Idea:**
> Maintenance-first system focused on uptime, cost control, and simplicity

---

## 2. Strategic Fit (ServizmaDesk Alignment)

This system is NOT standalone long-term.

It maps directly to your existing architecture:

- Vehicles → Service Items
- Maintenance → Work Orders
- PM → Schedules

This becomes a **Service Module vertical** inside ServizmaDesk.

---

## 3. Core System Architecture

### Backend
- Django (multi-tenant)
- PostgreSQL
- Single DB with `tenant_id`

### Frontend
- React
- Mobile-first UI

### Hosting
- DigitalOcean (initial)

---

## 4. Core Data Model

### Vehicles
- id
- tenant_id
- vin
- make
- model
- year
- license_plate
- status
- current_odometer

### Work Orders
- id
- vehicle_id
- status
- opened_at
- completed_at
- labor_cost
- parts_cost

### Preventive Maintenance
- id
- vehicle_id
- type
- interval_miles
- interval_days
- last_service_date

### Inspections
- id
- vehicle_id
- performed_by
- date
- result

### Issues
- id
- vehicle_id
- source (inspection/manual)
- severity
- status

---

## 5. Business Logic Engine

### PM Engine
- Trigger by mileage or time
- Auto-create work orders

### Inspection Pipeline
- Failed inspection → issue
- Issue → work order

### Cost Engine
- Aggregate labor + parts + fuel
- Cost per mile

### Alert Engine
- Upcoming PM
- Overdue maintenance

---

## 6. MVP Scope

### Must Have
- Vehicles
- Work Orders
- Preventive Maintenance
- Inspections
- Dashboard

### Excluded (for now)
- Inventory
- Fuel tracking
- Telematics
- Advanced reporting

---

## 7. UX Strategy

### Design Principles
- Zero training required
- Mobile-first
- Workflow-driven

### Core Flow
Inspection → Issue → Work Order → Complete

---

## 8. Mobile Requirements

Users:
- Drivers
- Technicians
- Managers

Features:
- Inspections
- Odometer updates
- Work order updates

---

## 9. Pricing Strategy

### Option 1
- $5–$8 per vehicle/month

### Option 2 (Preferred)
- $49/month (up to 15 vehicles)
- $99/month (up to 50 vehicles)

---

## 10. Build Roadmap

### Phase 1 – Internal
- Build for your own use
- Validate workflows

### Phase 2 – MVP SaaS
- Multi-tenant
- Basic UI
- Core automation

### Phase 3 – Scale
- Reporting
- Integrations
- Optimization

---

## 11. Key Risks

- Overbuilding features
- Ignoring UX
- Trying to compete with enterprise tools

---

## 12. Critical Success Factor

> Simplicity beats features.

If a user cannot understand the system in 30 minutes, it fails.

---

## 13. Final Recommendation

Build this as:

**A Service Module inside ServizmaDesk that can also operate independently as a SaaS offering.**

