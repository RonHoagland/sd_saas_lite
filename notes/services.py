# notes/services.py
# Source: Note & Document Implementation Specification V1
#
# Service functions for Note operations.

from django.core.exceptions import ValidationError
from .models import Note, NoteType
from documents.models import Document, ScanStatus
from config.base_models import PARENT_FK_FIELDS


def create_note(tenant_id, note_type, body, parent_field, parent_id, user_display="System"):
    """
    Create a Note with exclusive arc validation.

    Args:
        tenant_id: UUID of the tenant
        note_type: NoteType enum value (e.g., NoteType.INTERNAL_NOTE)
        body: String content of the note
        parent_field: Field name without '_id' suffix (e.g., 'customer', 'work_order')
        parent_id: UUID of the parent entity
        user_display: Display name of the user creating the note (default: "System")

    Returns:
        Note: The created Note instance

    Raises:
        ValidationError: If parent_field is not recognized
    """
    # Normalize parent_field (remove _id suffix if present)
    if parent_field.endswith('_id'):
        parent_field = parent_field[:-3]

    # Validate parent_field
    if parent_field not in PARENT_FK_FIELDS:
        raise ValidationError(
            f"Invalid parent_field '{parent_field}'. "
            f"Must be one of: {', '.join(PARENT_FK_FIELDS)}"
        )

    # Build kwargs with the appropriate FK field
    kwargs = {
        'tenant_id': tenant_id,
        'note_type': note_type,
        'body': body,
        'created_by': user_display,
        'updated_by': user_display,
        f'{parent_field}_id': parent_id,
    }

    # Create Note (clean() validates exclusive arc)
    note = Note(**kwargs)
    note.save()
    return note


def get_notes_for_entity(entity_type, entity_id, tenant_id):
    """
    Retrieve all Notes for a given entity.

    Args:
        entity_type: Entity type string (e.g., 'customer', 'work_order')
        entity_id: UUID of the entity
        tenant_id: UUID of the tenant

    Returns:
        QuerySet of Notes filtered by entity and tenant
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

    # Filter by the appropriate FK field
    filter_kwargs = {
        'tenant_id': tenant_id,
        f'{entity_type}_id': entity_id,
    }

    return Note.objects.filter(**filter_kwargs).order_by('-created_on')


def get_documents_for_entity(entity_type, entity_id, tenant_id):
    """
    Retrieve all Documents for a given entity.
    """
    if entity_type.endswith('_id'):
        entity_type = entity_type[:-3]

    if entity_type not in PARENT_FK_FIELDS:
        raise ValidationError(
            f"Invalid entity_type '{entity_type}'. "
            f"Must be one of: {', '.join(PARENT_FK_FIELDS)}"
        )

    filter_kwargs = {
        'tenant_id': tenant_id,
        f'{entity_type}_id': entity_id,
    }

    return Document.objects.filter(
        **filter_kwargs,
        scan_status=ScanStatus.CLEAN,
    ).order_by('-created_on')
