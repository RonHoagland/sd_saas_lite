from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from products.models import Product
from audit.models import UserTransaction, Session
from audit.middleware import get_current_user

@receiver(pre_save, sender=Product)
def capture_previous_state(sender, instance, **kwargs):
    """Capture state before save for update comparison."""
    if not instance.pk:
        return
        
    try:
        current = sender.objects.get(pk=instance.pk)
        instance._original_state = current
    except sender.DoesNotExist:
        pass

@receiver(post_save, sender=Product)
def audit_product_update(sender, instance, created, **kwargs):
    """Log changes to Product quantity_on_hand."""
    if created or not hasattr(instance, '_original_state'):
        return
        
    original = instance._original_state
    
    changes = []
    
    # Track Quantity Changes
    if original.quantity_on_hand != instance.quantity_on_hand:
        changes.append(f"Quantity changed from {original.quantity_on_hand} to {instance.quantity_on_hand}")
        
    # Track SKU Changes
    if original.sku != instance.sku:
        if not original.sku:
             changes.append(f"SKU generated: {instance.sku}")
        else:
             changes.append(f"SKU changed from '{original.sku}' to '{instance.sku}'")
    
    if changes:
        user = get_current_user()
        if not user: 
            if instance.updated_by:
                user = instance.updated_by
            else:
                return # Can't log without user

        session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
        
        if not session: 
             return

        UserTransaction.objects.create(
            session=session,
            user=user,
            event_type='update',
            entity_type="Product",
            entity_id=instance.id,
            summary="; ".join(changes)
        )
