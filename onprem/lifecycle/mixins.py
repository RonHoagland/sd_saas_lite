# lifecycle/mixins.py
# Mixin class for models that use the Lifecycle Framework.
# Source: Lifecycle Framework Specification V1, Section 4.


class LifecycleMixin:
    """
    Mixin to add lifecycle transition methods to a model.

    Usage:
        class Task(TenantModel, LifecycleMixin):
            lifecycle_entity_type = 'task'
            status = models.CharField(...)
            ...

    Then call:
        task.execute_transition('APPROVED', user, reason='Looks good')
        available = task.get_available_transitions(user)
        history = task.get_transition_history()
    """

    lifecycle_entity_type = None

    def execute_transition(self, to_state, user, reason="", ip_address=None):
        """
        Execute a state transition on this entity.

        Args:
            to_state: Target state name
            user: User performing transition
            reason: Optional reason/comment
            ip_address: Optional originating IP

        Returns:
            LifecycleTransitionAudit record
        """
        from .services import execute_transition
        return execute_transition(self, to_state, user, reason, ip_address)

    def get_available_transitions(self, user):
        """
        Get available transitions from current state for user.

        Args:
            user: User instance

        Returns:
            List of transition dicts
        """
        from .services import get_available_transitions
        return get_available_transitions(self, user)

    def get_transition_history(self):
        """
        Get audit trail for this entity.

        Returns:
            QuerySet of LifecycleTransitionAudit records
        """
        from .services import get_transition_history
        return get_transition_history(
            self.lifecycle_entity_type or self._meta.model_name,
            self.id,
            self.tenant_id
        )
