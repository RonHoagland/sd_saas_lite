from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Vendor, VendorAccount


@receiver(post_save, sender=Vendor)
def create_vendor_account(sender, instance, created, **kwargs):
    if not created:
        return

    defaults = {
        'tenant_id': instance.tenant_id,
        'created_by': instance.created_by,
    }

    from users.models import TenantPreference
    pref = TenantPreference.objects.filter(tenant_id=instance.tenant_id).first()
    if pref is not None:
        defaults['payment_terms'] = pref.default_payment_terms or ''
        defaults['tax_rate'] = pref.default_tax_rate

    VendorAccount.objects.create(vendor=instance, **defaults)
