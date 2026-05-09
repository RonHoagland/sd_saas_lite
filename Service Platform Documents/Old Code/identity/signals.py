from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

USER_LIMIT = 10

@receiver(pre_save, sender=User)
def check_user_limit(sender, instance, **kwargs):
    """
    Enforce Lite version user limit.
    Allow updates to existing users, but block creation of new ones if limit reached.
    """
    if not instance.pk:  # Only for new users
        current_count = User.objects.count()
        if current_count >= USER_LIMIT:
            raise ValidationError(f"Lite Version Restriction: Maximum {USER_LIMIT} users allowed.")

@receiver(pre_delete, sender=User)
def prevent_last_admin_delete(sender, instance, **kwargs):
    """Prevent deleting the last superuser."""
    if instance.is_superuser:
        admin_count = User.objects.filter(is_superuser=True).count()
        if admin_count <= 1:
            raise ValidationError("Cannot delete the last administrator.")

@receiver(pre_save, sender=User)
def prevent_last_admin_deactivation(sender, instance, **kwargs):
    """
    Prevent deactivating or demoting the last superuser.
    """
    if not instance.pk:
        return

    try:
        original = User.objects.get(pk=instance.pk)
        if original.is_superuser:
            # Check if we are removing superuser status or deactivating
            is_demoting = not instance.is_superuser
            is_deactivating = not instance.is_active
            
            if is_demoting or is_deactivating:
                admin_count = User.objects.filter(is_superuser=True, is_active=True).count()
                # If only 1 admin exists (us), blocking the change
                if admin_count <= 1:
                     raise ValidationError("Cannot deactivate or demote the last administrator.")
    except User.DoesNotExist:
        pass
