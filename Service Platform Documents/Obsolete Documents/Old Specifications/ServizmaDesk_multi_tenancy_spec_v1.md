# ServizmaDesk Multi-Tenancy Technical Specification (SDTA)
**Document Version:** V1
**Status:** Working Draft (Resolves Gap 3.2)

## 1. Overview
This document defines the implementation details for multi-tenant isolation in the ServizmaDesk Tenant App (SDTA). It ensures that all data access is automatically scoped to the correct tenant at the ORM layer, with PostgreSQL Row-Level Security (RLS) as the final enforcement layer.

## 2. Global Tenant Context
To ensure async-safety and thread-safety in Django 5.x, we use `asgiref.local.Local` to store the active tenant ID for the current request context.

```python
from asgiref.local import Local

_thread_locals = Local()

def set_current_tenant_id(tenant_id):
    _thread_locals.tenant_id = tenant_id

def get_current_tenant_id():
    return getattr(_thread_locals, 'tenant_id', None)

def clear_current_tenant_id():
    if hasattr(_thread_locals, 'tenant_id'):
        del _thread_locals.tenant_id
```

## 3. Tenant Manager (`TenantManager`)
The `TenantManager` overrides `get_queryset` to automatically inject the `tenant_id` filter.

```python
from django.db import models

class TenantManager(models.Manager):
    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        # If no tenant is set (e.g., system task), return all rows
        # but RLS will still block unauthorized access in production.
        if tenant_id:
            return super().get_queryset().filter(tenant_id=tenant_id)
        return super().get_queryset()
```

### 3.1 Bulk Creation & Filtering
- **`.create()`**: The manager does not need to override `.create()` directly, as the `TenantModel.save()` method handles auto-injection (see Section 4).
- **`.raw()`**: Raw SQL bypasses the manager. These queries MUST be manually scoped by the developer, with PostgreSQL RLS serving as the fallback enforcement.

## 4. Base Tenant Model (`TenantModel`)
All tenant-scoped models must inherit from `TenantModel`.

```python
class TenantModel(models.Model):
    tenant_id = models.UUIDField(db_index=True, editable=False)
    
    objects = TenantManager()
    all_objects = models.Manager() # Bypass filter for system use

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_tenant_id = get_current_tenant_id()
        
        if not self.tenant_id:
            if current_tenant_id:
                self.tenant_id = current_tenant_id
            else:
                raise ValueError("Cannot save TenantModel without a tenant_id in context.")
        
        # Security Guard: Prevent cross-tenant data corruption
        if current_tenant_id and self.tenant_id != current_tenant_id:
            raise PermissionError("Tenant ID mismatch: Attempted to save data for a different tenant.")
            
        super().save(*args, **kwargs)
```

## 5. Middleware Injection
The `TenantMiddleware` extracts the `tenant_id` from the authenticated user and sets the global context.

```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # tenant_id is retrieved from the User/Employee record
            set_current_tenant_id(request.user.tenant_id)
        
        try:
            response = self.get_response(request)
        finally:
            # CRITICAL: Always clear context to prevent leak to next request
            clear_current_tenant_id()
            
        return response
```

## 6. Exclusive Arc Integration
When dealing with the "Exclusive Arc" pattern (Notes, Documents), the `TenantModel` logic ensures that even if a developer provides a parent object (e.g., `Note.objects.create(customer=customer_obj)`), the `tenant_id` is validated to ensure it matches the note's context.

## 7. Security Constraints Summary
| Action | Enforcement Mechanism |
|---|---|
| **ORM Query** | `TenantManager` injects `.filter(tenant_id=...)` |
| **ORM Create** | `TenantModel.save()` auto-populates `tenant_id` |
| **Cross-Tenant Write** | `TenantModel.save()` raises `PermissionError` on mismatch |
| **Raw SQL** | PostgreSQL Row-Level Security (Layer 3) |
| **System Tasks** | Use `model.all_objects` to bypass ORM filtering |
