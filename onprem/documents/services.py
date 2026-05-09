# documents/services.py
# Source: Note & Document Implementation Specification V1
#
# Service functions for Document operations.

from django.core.exceptions import ValidationError
from .models import Document, ScanStatus
from config.base_models import PARENT_FK_FIELDS


def get_documents_for_entity(entity_type, entity_id, tenant_id):
    """
    Retrieve all clean Documents for a given entity.

    Only returns documents with scan_status = CLEAN.

    Args:
        entity_type: Entity type string (e.g., 'customer', 'work_order')
        entity_id: UUID of the entity
        tenant_id: UUID of the tenant

    Returns:
        QuerySet of clean Documents filtered by entity and tenant
    """
    # Normalize entity_type (remove _id suffix if present)
    if entity_type.endswith('_id'):
        entity_type = entity_type[:-3]

    # Validate entity_type
    if entity_type not in PARENT_FK_FIELDS:
        raise ValidationError(
            f"Invalid entity_type '{entity_type}'. "
            f"Must be one of: {', '.join(PARENT_FK_FIELDS)}"
        )

    # Filter by the appropriate FK field and scan_status
    filter_kwargs = {
        'tenant_id': tenant_id,
        f'{entity_type}_id': entity_id,
        'scan_status': ScanStatus.CLEAN,
    }

    return Document.objects.filter(**filter_kwargs).order_by('-created_on')
