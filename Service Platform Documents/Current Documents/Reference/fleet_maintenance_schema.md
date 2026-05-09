# Fleet Maintenance System -- Relational Schema (MVP)

This document outlines a practical relational database design for
managing a fleet of \~30+ cargo vans.\
The structure balances simplicity with enough normalization to support
reporting, compliance tracking, and maintenance planning.

------------------------------------------------------------------------

# 1. Core Tables

## vehicles

Master record for each cargo van.

**Primary Key** - vehicle_id

**Fields** - vehicle_id - unit_number - vin - plate_number - year -
make - model - trim - fuel_type - purchase_date - in_service_date -
retired_date - status_id - location_id - current_odometer -
ownership_type - notes - created_at - updated_at

Notes: - VIN should be unique - unit_number is typically unique

------------------------------------------------------------------------

## vehicle_statuses

Lookup table for standardized status values.

**Primary Key** - status_id

**Fields** - status_id - status_name

Examples: - Active - In Service - Out of Service - In Repair - Retired -
Sold

------------------------------------------------------------------------

## locations

Where vehicles are based.

**Primary Key** - location_id

**Fields** - location_id - location_name - address1 - address2 - city -
state - postal_code - phone - notes

------------------------------------------------------------------------

## employees

Drivers, managers, requesters, coordinators.

**Primary Key** - employee_id

**Fields** - employee_id - employee_number - first_name - last_name -
department - job_title - phone - email - license_number -
license_expiration - active_flag - created_at - updated_at

------------------------------------------------------------------------

## vehicle_assignments

Tracks which employee had a vehicle and when.

**Primary Key** - assignment_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id - employee_id →
employees.employee_id

**Fields** - assignment_id - vehicle_id - employee_id - start_date -
end_date - primary_driver_flag - assignment_notes

Design Note: Do not only store current_driver_id on the vehicles table.\
Vehicle assignments must keep historical records.

------------------------------------------------------------------------

# 2. Maintenance Tables

## maintenance_types

Lookup table for maintenance categories.

**Primary Key** - maintenance_type_id

**Fields** - maintenance_type_id - type_name - category -
default_interval_days - default_interval_miles -
requires_compliance_flag - active_flag

Examples: - Oil Change - Brake Service - Tire Rotation - Preventive
Maintenance Inspection - Transmission Service - Annual Safety Inspection

------------------------------------------------------------------------

## work_order_statuses

Status lookup for maintenance work orders.

**Primary Key** - work_order_status_id

**Fields** - work_order_status_id - status_name

Examples: - Open - Scheduled - In Progress - Waiting Parts - Completed -
Cancelled

------------------------------------------------------------------------

## vendors

External service providers such as repair shops and dealers.

**Primary Key** - vendor_id

**Fields** - vendor_id - vendor_name - vendor_type - contact_name -
phone - email - address1 - address2 - city - state - postal_code -
active_flag - notes

------------------------------------------------------------------------

## work_orders

Main repair and maintenance table.

**Primary Key** - work_order_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id -
maintenance_type_id → maintenance_types.maintenance_type_id -
work_order_status_id → work_order_statuses.work_order_status_id -
vendor_id → vendors.vendor_id - requested_by_employee_id →
employees.employee_id - assigned_driver_id → employees.employee_id -
location_id → locations.location_id

**Fields** - work_order_id - vehicle_id - maintenance_type_id -
work_order_status_id - vendor_id - requested_by_employee_id -
assigned_driver_id - location_id - opened_date - scheduled_date -
date_in_shop - completed_date - odometer_in - odometer_out - priority -
complaint_description - diagnosis - repair_summary - downtime_hours -
subtotal_parts - subtotal_labor - subtotal_misc - tax_amount -
total_cost - invoice_number - warranty_flag - followup_required_flag -
notes - created_at - updated_at

------------------------------------------------------------------------

## work_order_lines

Detailed line items for each work order.

**Primary Key** - work_order_line_id

**Foreign Keys** - work_order_id → work_orders.work_order_id - part_id →
parts.part_id (nullable)

**Fields** - work_order_line_id - work_order_id - line_number -
line_type - part_id - description - quantity - unit_cost - labor_hours -
line_total - notes

------------------------------------------------------------------------

## parts

Catalog or inventory of common parts.

**Primary Key** - part_id

**Foreign Keys** - preferred_vendor_id → vendors.vendor_id

**Fields** - part_id - part_number - part_name - description -
preferred_vendor_id - unit_cost - quantity_on_hand - reorder_level -
active_flag

------------------------------------------------------------------------

## pm_rules

Preventive maintenance rules.

**Primary Key** - pm_rule_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id -
maintenance_type_id → maintenance_types.maintenance_type_id

**Fields** - pm_rule_id - vehicle_id - maintenance_type_id -
interval_days - interval_miles - last_service_date -
last_service_odometer - next_due_date - next_due_odometer -
active_flag - notes

------------------------------------------------------------------------

# 3. Operational Tables

## fuel_transactions

Tracks fuel purchases and consumption.

**Primary Key** - fuel_transaction_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id - employee_id →
employees.employee_id

**Fields** - fuel_transaction_id - vehicle_id - employee_id -
transaction_date - odometer - gallons - cost_per_gallon - total_cost -
fuel_vendor - fuel_card_number - receipt_number - full_tank_flag - notes

------------------------------------------------------------------------

## inspections

Vehicle safety and operational inspections.

**Primary Key** - inspection_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id - employee_id →
employees.employee_id - related_work_order_id →
work_orders.work_order_id

**Fields** - inspection_id - vehicle_id - employee_id -
inspection_type - inspection_date - odometer - result - issues_found -
related_work_order_id - notes

------------------------------------------------------------------------

## vehicle_documents

Tracks registrations, insurance, warranties, and permits.

**Primary Key** - vehicle_document_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id

**Fields** - vehicle_document_id - vehicle_id - document_type -
document_number - provider_name - issue_date - expiration_date -
file_name - file_path - status - notes

------------------------------------------------------------------------

## incidents

Vehicle accidents, damage reports, or insurance claims.

**Primary Key** - incident_id

**Foreign Keys** - vehicle_id → vehicles.vehicle_id - employee_id →
employees.employee_id

**Fields** - incident_id - vehicle_id - employee_id - incident_date -
location_description - incident_type - description -
police_report_number - insurance_claim_number - estimated_cost -
actual_cost - status - notes

------------------------------------------------------------------------

# 4. Relationship Overview

Key relationships:

-   One vehicle → many assignments

-   One vehicle → many work orders

-   One vehicle → many fuel transactions

-   One vehicle → many inspections

-   One vehicle → many documents

-   One vehicle → many incidents

-   One vehicle → many preventive maintenance rules

-   One employee → many assignments

-   One employee → many inspections

-   One employee → many fuel transactions

-   One employee → many requested work orders

-   One work order → many work order lines

-   One maintenance type → many work orders

-   One maintenance type → many PM rules

-   One vendor → many work orders

-   One vendor → many parts

------------------------------------------------------------------------

# 5. Minimum Table Set for MVP

Recommended minimum set:

-   vehicles
-   vehicle_statuses
-   employees
-   vehicle_assignments
-   vendors
-   maintenance_types
-   work_order_statuses
-   work_orders
-   work_order_lines
-   pm_rules
-   fuel_transactions
-   inspections
-   vehicle_documents
-   incidents
-   locations

This supports: - maintenance history - service scheduling - fuel
tracking - compliance tracking - cost analysis

------------------------------------------------------------------------

# 6. Design Rules

## Separate Master Data from Event Data

Keep vehicle master information separate from historical activity
tables.

Good: - vehicles - work_orders - fuel_transactions - inspections

Bad: - one large "vehicle_activity" table

------------------------------------------------------------------------

## Use Lookup Tables

Use standardized lookup tables for: - vehicle_statuses -
work_order_statuses - maintenance_types

Avoid inconsistent free‑text values.

------------------------------------------------------------------------

## Track History

Maintain historical records for: - driver assignments - inspections -
maintenance - fuel usage

Current state alone is not enough for reporting.

------------------------------------------------------------------------

## Track Odometer Readings

Odometer readings should appear in: - work_orders - fuel_transactions -
inspections

This supports mileage calculations and PM triggers.

------------------------------------------------------------------------

## Store Costs at Line Level

Work order costs should be stored as detailed line items.

This enables analysis such as: - labor vs parts cost - vendor
comparison - service category cost trends

------------------------------------------------------------------------

# 7. Recommended Phase 2 Tables

Future enhancements may include:

-   technicians
-   parts_transactions
-   vehicle_meter_readings
-   reminders or alerts
-   attachments
-   tire_lifecycle

These are helpful but not required for initial deployment.

------------------------------------------------------------------------

# 8. Key Reports Supported

A correctly implemented schema supports reports such as:

-   maintenance cost by vehicle
-   maintenance cost by month
-   fuel cost by vehicle
-   cost per mile by vehicle
-   vehicles overdue for service
-   inspection failures
-   vehicles currently out of service
-   open work orders
-   expiring registrations or insurance
-   incident history by vehicle

------------------------------------------------------------------------

End of document.
