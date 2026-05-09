# numbering/mixins.py
# Mixin for models that support numbering.
# Source: Numbering Service Specification V1, Section 2.4.


class NumberingMixin:
    """
    Mixin for entity models that support automatic number assignment.

    Usage:
        class Customer(TenantModel, NumberingMixin):
            numbering_entity_type = 'customer'
            ...

        customer = Customer.objects.create(...)
        assigned = customer.assign_number('user@example.com')
        print(assigned.number)  # e.g., 'C-26-001'
    """

    numbering_entity_type = None  # Subclass must set this

    def assign_number(self, user_display='System'):
        """
        Assign a number to this entity.

        Returns:
            AssignedNumber instance.

        Raises:
            DuplicateAssignmentError: Already has a number.
        """
        from .services import assign_number
        return assign_number(
            self.tenant_id, self.numbering_entity_type, self.id, user_display
        )

    def get_assigned_number(self):
        """
        Get the assigned number for this entity.

        Returns:
            String number, or None.
        """
        from .services import get_assigned_number
        return get_assigned_number(
            self.tenant_id, self.numbering_entity_type, self.id
        )

    def has_assigned_number(self):
        """
        Check if this entity has an assigned number.

        Returns:
            Boolean.
        """
        from .services import has_assigned_number
        return has_assigned_number(
            self.tenant_id, self.numbering_entity_type, self.id
        )
