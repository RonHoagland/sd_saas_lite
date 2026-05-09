from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Customer, Account


@receiver(post_save, sender=Customer)
def create_customer_account(sender, instance, created, **kwargs):
    if not created:
        return

    defaults = {
        'tenant_id': instance.tenant_id,
        'created_by': instance.created_by,
    }

    from users.models import TenantPreference
    pref = TenantPreference.all_objects.filter(tenant_id=instance.tenant_id).first() \
        if hasattr(TenantPreference, 'all_objects') \
        else TenantPreference.objects.filter(tenant_id=instance.tenant_id).first()
    if pref is not None:
        defaults['account_terms'] = pref.default_payment_terms or ''
        defaults['tax_rate'] = pref.default_tax_rate

    Account.objects.create(customer=instance, **defaults)
