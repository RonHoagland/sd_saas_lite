# numbering/services.py
# Service layer for numbering operations.
# Source: Numbering Service Specification V1, Sections 3.1-3.7.

from datetime import date
from django.db import transaction
from django.utils import timezone
from .models import NumberingRule, NumberSequence, AssignedNumber
from .exceptions import (
    NoRuleDefinedError,
    NumberingDisabledError,
    DuplicateAssignmentError,
    SequenceError,
)


def generate_number(tenant_id, entity_type, user_display='System'):
    """
    Generate a new formatted number for the given entity type.

    Steps:
    1. Look up NumberingRule for (tenant_id, entity_type).
    2. Check is_enabled.
    3. Get next sequence value.
    4. Format and return.

    Raises:
        NoRuleDefinedError: No rule exists for this entity type.
        NumberingDisabledError: Rule exists but is disabled.
    """
    try:
        rule = NumberingRule.objects.get(tenant_id=tenant_id, entity_type=entity_type)
    except NumberingRule.DoesNotExist:
        raise NoRuleDefinedError(
            f'No numbering rule defined for entity_type={entity_type} '
            f'in tenant {tenant_id}.'
        )

    if not rule.is_enabled:
        raise NumberingDisabledError(
            f'Numbering rule for {entity_type} is disabled.'
        )

    sequence_value = get_next_sequence_value(rule)
    formatted = format_number(rule, sequence_value)
    return formatted


def get_next_sequence_value(rule):
    """
    Get the next sequence value for the given rule.

    Within a transaction with SELECT FOR UPDATE:
    1. Get or create the NumberSequence row.
    2. Check if reset is needed.
    3. Increment and save.

    Returns the new sequence value (after increment).
    """
    with transaction.atomic():
        # Lock the sequence row to prevent race conditions
        sequence = NumberSequence.objects.select_for_update().get_or_create(
            rule=rule
        )[0]

        # Check if we need to reset
        check_reset_needed(sequence, rule)

        # Increment
        sequence.current_value += 1
        sequence.save()

        return sequence.current_value


def check_reset_needed(sequence, rule):
    """
    Check if the sequence needs to reset based on the rule's reset_behavior.

    - 'none': Never reset.
    - 'yearly': Reset if last_reset_date is None or year changed.
    - 'monthly': Reset if month/year changed.

    If reset is needed, set current_value=0 and update last_reset_date to today.
    """
    today = timezone.now().date()

    if rule.reset_behavior == 'none':
        return

    if rule.reset_behavior == 'yearly':
        if (
            sequence.last_reset_date is None
            or sequence.last_reset_date.year != today.year
        ):
            sequence.current_value = 0
            sequence.last_reset_date = today

    elif rule.reset_behavior == 'monthly':
        if (
            sequence.last_reset_date is None
            or sequence.last_reset_date.year != today.year
            or sequence.last_reset_date.month != today.month
        ):
            sequence.current_value = 0
            sequence.last_reset_date = today


def format_number(rule, sequence_value):
    """
    Format the sequence value into a human-readable number.

    Format: {prefix}{delimiter}{year}{delimiter}{month}{delimiter}{sequence}

    Components are only included if configured in the rule.
    Sequence is zero-padded to rule.sequence_length.
    """
    parts = [rule.prefix]

    now = timezone.now()

    if rule.include_year:
        if rule.year_format == 'YY':
            year_str = now.strftime('%y')
        else:  # YYYY
            year_str = now.strftime('%Y')
        parts.append(year_str)

    if rule.include_month:
        month_str = now.strftime('%m')
        parts.append(month_str)

    # Sequence always zero-padded
    seq_str = str(sequence_value).zfill(rule.sequence_length)
    parts.append(seq_str)

    return rule.delimiter.join(parts)


def assign_number(tenant_id, entity_type, entity_id, user_display='System'):
    """
    Assign a number to an entity and create an immutable AssignedNumber record.

    Steps:
    1. Check if entity already has an assigned number.
    2. Generate a new number.
    3. Create the AssignedNumber record.
    4. Return the record.

    Returns:
        AssignedNumber instance.

    Raises:
        DuplicateAssignmentError: Entity already has a number.
        NoRuleDefinedError: No rule for this entity type.
        NumberingDisabledError: Rule is disabled.
    """
    # Check for duplicate
    existing = AssignedNumber.objects.filter(
        tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id
    ).first()

    if existing:
        raise DuplicateAssignmentError(
            f'Entity {entity_id} already has an assigned number: {existing.number}'
        )

    # Generate the number
    number = generate_number(tenant_id, entity_type, user_display)

    # Get the rule
    rule = NumberingRule.objects.get(tenant_id=tenant_id, entity_type=entity_type)

    # Create the record
    assigned = AssignedNumber.objects.create(
        tenant_id=tenant_id,
        rule=rule,
        entity_type=entity_type,
        entity_id=entity_id,
        number=number,
        assigned_by=user_display,
        created_by=user_display,
    )

    return assigned


def get_assigned_number(tenant_id, entity_type, entity_id):
    """
    Retrieve the assigned number for an entity, or None if not assigned.

    Returns:
        String number, or None.
    """
    assigned = AssignedNumber.objects.filter(
        tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id
    ).first()

    return assigned.number if assigned else None


def has_assigned_number(tenant_id, entity_type, entity_id):
    """
    Check if an entity has an assigned number.

    Returns:
        Boolean.
    """
    return AssignedNumber.objects.filter(
        tenant_id=tenant_id, entity_type=entity_type, entity_id=entity_id
    ).exists()


def compute_inventory_item_prefix(year=None):
    """
    Compute the inventory item prefix by reverse-alphabet year encoding.

    Maps last two digits of year to letters using reverse alphabet:
        0 → Q, 1 → Z, 2 → Y, 3 → X, 4 → W, 5 → V, 6 → U, 7 → T, 8 → S, 9 → R

    Examples:
        2026 → YU (26: 2→Y, 6→U)
        2027 → YT (27: 2→Y, 7→T)
        2030 → YQ (30: 3→X, 0→Q) — wait, that's wrong. Let me recalculate:
                  30 % 100 = 30 → "30": 3→X, 0→Q → XQ

    Actually, let me verify the mapping:
        Digit 0 → Q, 1 → Z, 2 → Y, 3 → X, 4 → W, 5 → V, 6 → U, 7 → T, 8 → S, 9 → R

    If year=None, use current year.

    Returns:
        Two-letter string.
    """
    if year is None:
        year = timezone.now().year

    # Digit to letter mapping
    digit_to_letter = {
        '0': 'Q',
        '1': 'Z',
        '2': 'Y',
        '3': 'X',
        '4': 'W',
        '5': 'V',
        '6': 'U',
        '7': 'T',
        '8': 'S',
        '9': 'R',
    }

    # Get last two digits
    year_last_two = str(year)[-2:]

    # Map each digit
    prefix = ''.join(digit_to_letter[d] for d in year_last_two)

    return prefix
