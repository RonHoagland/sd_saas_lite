# ServizmaDesk Document Reorganization Plan
**Purpose:** Eliminate duplication, establish proper sequencing, and create a cross-referenced document hierarchy

**Status:** Proposed Reorganization Plan  
**Date:** March 2026

---

# Executive Summary

The ServizmaDesk project currently has **9 final documents** with significant duplication across pricing, architecture, and feature definitions. This plan:

1. **Identifies all duplicate content** across documents
2. **Establishes proper document sequencing** (1-9)
3. **Defines which document owns each piece of information**
4. **Specifies exact cross-reference patterns** to eliminate duplication

---

# Current Document Inventory

## Active Documents (9 Total)

1. ServizmaDesk_Product_Tier_Map_V1.md
2. ServizmaDesk_Technical_Architecture_V1.md
3. ServizmaDesk_SDTA_Data_Models_V1.md
4. ServizmaDesk_Platform__SDP__Specification_V1.md
5. ServizmaDesk_Lite___MVP_V3_Specification.md
6. ServizmaDesk_Pricing_and_Billing_Specification_V1.md
7. ServizmaDesk_SaaS_Operational_Plan_V2.md
8. ServizmaDesk_Enterprise_Top_Down_Design_V2.md
9. ServizmaDesk_Pricing_Spec_Update_Guide.md (Implementation guide, not core spec)

---

# Proposed Document Hierarchy & Sequencing

## Foundation Layer (Documents 1-3)
**These documents define WHAT is being built and WHY**

### Document 1: Product Tier Map V1 ✓ ALREADY DESIGNATED
**Owner:** Feature definitions, tier boundaries, product identity  
**Status:** Finalized, some sections need to defer to Pricing Spec

**Owns:**
- Product identity and differentiator (Service Item asset-centric model)
- Target market definition
- Feature matrix by tier (Lite, Plus, Pro, Enterprise)
- Module definitions and tier availability
- Cross-tier design principles
- Tier enforcement strategy (distinct UIs)
- Multi-tenancy architecture overview

**References (does not duplicate):**
- Pricing → Pricing & Billing Specification V1
- Technical stack details → Technical Architecture V1
- Data models → SDTA Data Models V1
- Platform provisioning → Platform (SDP) Specification V1

---

### Document 2: Pricing & Billing Specification V1 ✓ COMPLETE
**Owner:** All pricing, billing, and Founding Partner program details  
**Status:** Complete — supersedes pricing sections in all other docs

**Owns:**
- Standard tier pricing (Lite, Plus, Pro, Enterprise)
- Monthly vs. annual billing models
- Founding Partner programs (Lite and Plus)
- Storage pricing and add-ons
- Trial structure and conversion flow
- Competitive positioning rationale
- SMS point pricing (future)

**References:**
- Feature definitions → Product Tier Map V1
- Stripe implementation → Platform (SDP) Specification V1

---

### Document 3: Technical Architecture V1 ✓ COMPLETE
**Owner:** Technology stack, infrastructure, third-party integrations  
**Status:** Complete

**Owns:**
- Backend framework (Django 5.x, Python 3.12+)
- Frontend stack (HTMX, Tailwind CSS)
- Database (PostgreSQL 16+, UUIDs mandatory)
- Hosting (DigitalOcean)
- Third-party services (Stripe, Postmark, DO Spaces, Redis, Celery)
- Multi-tenancy three-layer isolation model
- Security & compliance (authentication, webhooks, data retention)
- SDP/SDTA communication (Internal REST API)
- Tier-gating implementation pattern
- Development & staging environments

**References:**
- Tier feature boundaries → Product Tier Map V1
- Data model implementation → SDTA Data Models V1

---

## Implementation Layer (Documents 4-5)
**These documents define HOW the foundation is implemented**

### Document 4: SDTA Data Models V1 ✓ COMPLETE
**Owner:** Complete database schema for ServizmaDesk Tenant App  
**Status:** Complete — high-level architecture

**Owns:**
- Architectural mandates (UUIDs, no GFKs, tenant_id everywhere)
- Lite tier models (complete list)
- Identity & access models
- Core CRM triad architecture
- Service delivery & financials models
- Attachments (exclusive arc pattern)
- System utilities & operations models
- Tenant infrastructure models
- Plus & Enterprise directional models

**References:**
- Multi-tenancy architecture → Technical Architecture V1
- Feature requirements → Product Tier Map V1
- Lite module details → Lite MVP V3 Specification

---

### Document 5: Platform (SDP) Specification V1 ⚠️ NEEDS DEDUPLICATION
**Owner:** ServizmaDesk Platform (back-office/billing system)  
**Status:** Needs pricing sections removed

**Owns:**
- Platform identity and core roles
- SDP architecture and infrastructure
- Database structure (SDP-specific)
- Security & access model
- Customer-facing surface (signup, billing portal, account recovery)
- Staff-facing back office
- Tenant provisioning process
- Plan & billing management (Stripe integration)
- Security verification (PIN, questions)
- Data retention & cleanup
- Transactional communications
- MVP completion criteria

**References (should defer to):**
- Pricing → Pricing & Billing Specification V1 ✓ Already has update guide
- Technical stack → Technical Architecture V1
- Tier features → Product Tier Map V1

**Deduplication Required:**
- Remove pricing tables → Reference Pricing Spec
- Remove billing cycle details → Reference Pricing Spec
- Remove storage pricing → Reference Pricing Spec

---

## Application Layer (Document 6)
**This document defines the FIRST IMPLEMENTATION (Lite tier)**

### Document 6: Lite MVP V3 Specification ⚠️ NEEDS DEDUPLICATION
**Owner:** Complete Lite tier functional specification  
**Status:** Needs architecture/pricing sections removed

**Owns:**
- Lite-specific module functionality (detailed)
- UI/UX specifications
- Workflows and user interactions
- Field specifications
- Validation rules
- Status lifecycles (detailed)
- CSV export specifications
- Onboarding flow
- Trial period user experience
- Read-only mode behavior
- Employee seat counting logic (Section 18.8)

**References (should defer to):**
- Pricing → Pricing & Billing Specification V1 ✓ Update guide exists
- Architecture → Technical Architecture V1
- Data models → SDTA Data Models V1
- Platform integration → Platform (SDP) Specification V1
- Tier boundaries → Product Tier Map V1

**Deduplication Required:**
- Remove architecture sections (duplicates Technical Architecture V1)
- Remove multi-tenancy description (duplicates Technical Architecture V1)
- Remove SDP/SDTA communication (duplicates Technical Architecture V1)
- Update pricing references → Reference Pricing Spec

---

## Planning & Vision Layer (Documents 7-8)
**These documents provide business context and future vision**

### Document 7: SaaS Operational Plan V2 ⚠️ NEEDS MAJOR DEDUPLICATION
**Owner:** Business planning, financial projections, timeline  
**Status:** Needs complete rewrite to remove duplicated content

**Owns:**
- Company structure (ISBMG LLC)
- Tax considerations
- Development timeline and phases
- Revenue projections
- Customer acquisition model
- Operating cost estimates
- Year 1-3 financial planning
- Founder relocation planning

**References (should defer to):**
- Pricing → Pricing & Billing Specification V1
- Tier structure → Product Tier Map V1
- Technical decisions → Technical Architecture V1

**Deduplication Required:**
- Remove complete tier structure section → Reference Product Tier Map V1
- Remove pricing details → Reference Pricing & Billing Specification V1
- Remove Founding Partner details → Reference Pricing & Billing Specification V1
- Remove trial flow details → Reference Pricing & Billing Specification V1

---

### Document 8: Enterprise Top-Down Design V2 ✓ NO CHANGES NEEDED
**Owner:** Long-term vision (4-5 years out)  
**Status:** Standalone visionary document — no duplication issues

**Owns:**
- Enterprise tier vision
- ServiceTitan competitive positioning
- Advanced feature concepts
- Multi-location architecture
- Advanced CRM capabilities
- Dispatch engine vision
- Mobile offline-first architecture
- Inventory & procurement vision
- Financial depth boundaries

**References:**
- Foundation tiers → Product Tier Map V1

**No deduplication needed** — this is a forward-looking vision document

---

## Implementation Guide (Document 9)
**This is a working document, not a core specification**

### Document 9: Pricing Spec Update Guide ✓ IMPLEMENTATION GUIDE ONLY
**Owner:** Step-by-step instructions for applying Pricing Spec changes  
**Status:** Complete — used to update other docs

**Purpose:**
- Shows exactly what to remove from each document
- Provides replacement text with proper references
- Implementation checklist

**This is NOT a core specification** — it's a one-time implementation guide

---

# Critical Duplication Issues Identified

## Issue 1: Pricing Scattered Across 4 Documents ✓ PARTIALLY RESOLVED

**Problem:** Pricing appears in:
- Product Tier Map V1 (Section 3)
- Platform (SDP) Specification V1 (Sections 5.2, 5.3, 6.3, 6.4, 6.5)
- SaaS Operational Plan V2 (Section 2)
- Lite MVP V3 Specification (Section 2, Section 18.8 references)

**Solution:** ✓ Pricing & Billing Specification V1 created  
**Remaining Work:** Apply the Update Guide to remove pricing from all 4 documents

---

## Issue 2: Architecture Duplicated in 3 Documents

**Problem:** Multi-tenancy, tech stack, and SDP/SDTA communication appear in:
- Technical Architecture V1 (authoritative source)
- Lite MVP V3 Specification (Sections 3.1, 3.2)
- Product Tier Map V1 (Section 8)

**Current State:**
- Technical Architecture V1 owns this content
- Product Tier Map V1 Section 8 provides overview only (acceptable)
- Lite MVP V3 Specification duplicates extensively (needs removal)

**Solution:** 
- Remove Sections 3.1 and 3.2 from Lite MVP V3 Specification
- Replace with: "Architecture defined in ServizmaDesk Technical Architecture V1"

---

## Issue 3: Tier Features Duplicated in 2 Documents

**Problem:** Tier feature lists appear in:
- Product Tier Map V1 (Section 6 — authoritative)
- SaaS Operational Plan V2 (Section 2 — duplicate)

**Solution:**
- Remove Section 2 from SaaS Operational Plan V2
- Replace with brief summary + reference to Product Tier Map V1

---

## Issue 4: Trial Flow Duplicated in 3 Documents

**Problem:** Trial structure and expiration flow appear in:
- Pricing & Billing Specification V1 (Section 6 — authoritative)
- Product Tier Map V1 (Section 4)
- SaaS Operational Plan V2 (trial expiration flow)

**Solution:**
- Remove Section 4 from Product Tier Map V1 → Reference Pricing Spec
- Remove trial flow from Operational Plan V2 → Reference Pricing Spec

---

## Issue 5: Founding Partner Program Duplicated in 3 Documents

**Problem:** Founding Partner details appear in:
- Pricing & Billing Specification V1 (Section 5 — authoritative)
- Product Tier Map V1 (Section 5)
- SaaS Operational Plan V2 (Section 3)

**Solution:**
- Remove Section 5 from Product Tier Map V1 → Reference Pricing Spec
- Remove Section 3 from Operational Plan V2 → Reference Pricing Spec

---

# Recommended Document Order (Reading Sequence)

For someone learning the ServizmaDesk project, documents should be read in this order:

## Phase 1: Foundation Understanding (Read First)
1. **Product Tier Map V1** — Understand what's being built and why
2. **Pricing & Billing Specification V1** — Understand business model
3. **Technical Architecture V1** — Understand how it's built

## Phase 2: Implementation Details (Read Second)
4. **SDTA Data Models V1** — Understand database structure
5. **Platform (SDP) Specification V1** — Understand back-office system
6. **Lite MVP V3 Specification** — Understand first implementation

## Phase 3: Business Context (Read Third)
7. **SaaS Operational Plan V2** — Understand business strategy
8. **Enterprise Top-Down Design V2** — Understand long-term vision

## Phase 4: Implementation Support (Reference Only)
9. **Pricing Spec Update Guide** — Use when applying pricing changes

---

# Specific Deduplication Actions Required

## Action 1: Update Product Tier Map V1 ✓ UPDATE GUIDE EXISTS

**Remove:**
- Section 3 (Pricing and Billing)
- Section 4 (Free Trial Structure)
- Section 5 (Founding Partner Program)

**Replace with:**
- Brief summary + references to Pricing & Billing Specification V1

**Keep:**
- Section 6 (Tier Definitions) — this is feature definitions, not pricing
- Section 8 (Architecture Notes) — this is overview only, acceptable

---

## Action 2: Update Platform (SDP) Specification V1 ✓ UPDATE GUIDE EXISTS

**Remove:**
- Section 5.2 (Plan Limits Table) — duplicates Product Tier Map
- Section 5.3 (Billing Cycles) — duplicates Pricing Spec
- Section 6.3 (Billing Model) — duplicates Pricing Spec
- Section 6.4 (Seat Billing) — duplicates Pricing Spec
- Section 6.5 (Storage Add-On Billing) — duplicates Pricing Spec

**Replace with:**
- References to Pricing & Billing Specification V1 and Product Tier Map V1

---

## Action 3: Update Lite MVP V3 Specification ⚠️ NEW WORK REQUIRED

**Remove:**
- Section 3.1 (Application Architecture) — duplicates Technical Architecture V1
- Section 3.2 (Multi-Tenancy) — duplicates Technical Architecture V1
- Section 3.3 (Communication Between SDP and SDTA) — duplicates Technical Architecture V1

**Replace with:**
```markdown
# 3. Architecture & Infrastructure

ServizmaDesk Lite is built on the foundation defined in **ServizmaDesk Technical Architecture V1**.

**Key Architectural Points for Lite:**
- SDTA uses shared-schema multi-tenancy with three-layer isolation
- PostgreSQL 16+ with mandatory UUIDs
- Django 5.x backend with HTMX frontend
- Internal REST API communication between SDP and SDTA

For complete architectural details, see:
→ **ServizmaDesk Technical Architecture V1**

For complete data model specifications, see:
→ **ServizmaDesk SDTA Data Models V1**
```

**Update:**
- Section 18.8 pricing references → Reference Pricing Spec V1 ✓ UPDATE GUIDE EXISTS

---

## Action 4: Update SaaS Operational Plan V2 ⚠️ NEW WORK REQUIRED

**Remove:**
- Section 2 (Product Tier Structure) — duplicates Product Tier Map V1
- Section 3 (Founding Partner Program) — duplicates Pricing Spec V1

**Replace Section 2 with:**
```markdown
# 2. Product Structure Overview

ServizmaDesk offers four tiers designed for progressive growth:

**Tier Summary:**
- **Lite:** Entry-level tier for solo operators (max 10 seats)
- **Plus:** Growth tier with automation and scheduling (unlimited seats)
- **Pro:** Advanced tier for scaling businesses (unlimited seats)
- **Enterprise:** Future tier for multi-location ERP needs (4-5 years out)

For complete tier feature definitions, see:
→ **ServizmaDesk Product Tier Map V1, Section 6**

For complete pricing details, see:
→ **ServizmaDesk Pricing & Billing Specification V1**
```

**Replace Section 3 with:**
```markdown
# 3. Founding Partner Program

ServizmaDesk offers two Founding Partner tiers with exclusive legacy pricing:
- **FP Lite:** $200/seat/year (10 slots available)
- **FP Plus:** $400/seat/year (10 slots available)

For complete program details and revenue projections, see:
→ **ServizmaDesk Pricing & Billing Specification V1, Section 5**
```

**Keep:**
- Section 4 (Development Timeline) — unique to this document
- Financial projections — unique to this document
- Operating cost analysis — unique to this document

---

# Cross-Reference Pattern Standards

## Standard Reference Format

When referencing another document, use this format:

```markdown
For [topic], see:
→ **[Document Name], Section [X.X]**
```

## Quick Reference Summaries

When deferring to another document, provide a brief quick reference:

```markdown
**Quick Reference — [Topic]:**
- Key point 1
- Key point 2
- Key point 3

For complete [topic] details, see:
→ **[Document Name], Section [X.X]**
```

## Example Implementation

**BEFORE (Duplicate Content):**
```markdown
# 3. Pricing and Billing

## 3.1 Pricing Table

|                    | Lite   | Plus   | Pro    |
|--------------------|--------|--------|--------|
| Monthly Price/Seat | $35    | $59    | $118   |
| Annual Price/Seat  | $29    | $49    | $98    |
[...full table with 20 rows...]
```

**AFTER (Proper Cross-Reference):**
```markdown
# 3. Pricing and Billing

All pricing, billing cycles, and Founding Partner program details are defined in **ServizmaDesk Pricing & Billing Specification V1**.

**Quick Reference — Standard Tier Pricing (Annual):**
- Lite: $29/seat/month (max 10 seats)
- Plus: $49/seat/month (unlimited seats)
- Pro: $98/seat/month (unlimited seats)

For complete pricing details, see:
→ **ServizmaDesk Pricing & Billing Specification V1**
```

---

# Document Status Matrix

| Document | Duplication Status | Action Required | Priority |
|----------|-------------------|-----------------|----------|
| 1. Product Tier Map V1 | Has pricing duplication | Apply Update Guide | HIGH |
| 2. Pricing & Billing Spec V1 | ✓ Clean | None | N/A |
| 3. Technical Architecture V1 | ✓ Clean | None | N/A |
| 4. SDTA Data Models V1 | ✓ Clean | None | N/A |
| 5. Platform (SDP) Spec V1 | Has pricing duplication | Apply Update Guide | HIGH |
| 6. Lite MVP V3 Spec | Has architecture duplication | Remove Sections 3.1-3.3 | HIGH |
| 7. Operational Plan V2 | Has tier & pricing duplication | Remove Sections 2-3 | MEDIUM |
| 8. Enterprise Design V2 | ✓ Clean | None | N/A |
| 9. Pricing Update Guide | Implementation guide only | Use to update others | N/A |

---

# Implementation Checklist

## ✓ Already Complete
- [x] Pricing & Billing Specification V1 created
- [x] Update Guide created for pricing changes
- [x] Technical Architecture V1 finalized
- [x] SDTA Data Models V1 finalized

## ⚠️ High Priority (Blocking Issues)
- [ ] Apply Pricing Update Guide to Product Tier Map V1
- [ ] Apply Pricing Update Guide to Platform (SDP) Specification V1
- [ ] Remove architecture sections from Lite MVP V3 Specification (Sections 3.1-3.3)
- [ ] Update Lite MVP V3 Specification Section 18.8 pricing references

## 📋 Medium Priority (Quality Improvements)
- [ ] Update SaaS Operational Plan V2 Section 2 (tier structure)
- [ ] Update SaaS Operational Plan V2 Section 3 (Founding Partner)
- [ ] Add "Document Relationships" section to all documents showing dependencies

## 📝 Nice to Have (Documentation Polish)
- [ ] Create master document index with reading order guide
- [ ] Add visual document dependency diagram
- [ ] Standardize all cross-reference formatting

---

# Post-Deduplication Document Relationships

## Foundation Documents (No Dependencies)
- Pricing & Billing Specification V1
- Technical Architecture V1

## Tier 1 Dependencies
- Product Tier Map V1 → References Pricing Spec, Tech Architecture
- SDTA Data Models V1 → References Tech Architecture, Tier Map

## Tier 2 Dependencies
- Platform (SDP) Spec V1 → References Pricing Spec, Tech Architecture, Tier Map
- Lite MVP V3 Spec → References all foundation + Tier 1 documents

## Tier 3 Dependencies (Business Layer)
- Operational Plan V2 → References Pricing Spec, Tier Map
- Enterprise Design V2 → References Tier Map

---

# Success Criteria

Deduplication is complete when:

1. ✓ **Single Source of Truth:** Every piece of information has exactly ONE authoritative document
2. ✓ **No Copy/Paste:** No content is duplicated across documents
3. ✓ **Clear References:** All documents reference dependencies rather than duplicating content
4. ✓ **Proper Sequencing:** Documents can be read in logical order (1-8)
5. ✓ **Easy Updates:** Changing pricing/architecture/features requires updating only ONE document
6. ✓ **Consistent Format:** All cross-references use standardized format

---

**END OF REORGANIZATION PLAN**
