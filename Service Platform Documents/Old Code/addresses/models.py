from django.db import models
from core.models import BaseModel

class Address(BaseModel):
    """
    Physical address associated with a Client.
    Lite: Client-owned only (Billing/Shipping).
    """
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    
    address_type = models.CharField(
        max_length=50,
        help_text="Type (e.g., Billing, Shipping). Controlled by Value List."
    )
    
    # Address Fields
    address_1 = models.CharField(max_length=255)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(
        max_length=100,
        help_text="Country name/code. Defaulted from Preferences."
    )

    class Meta:
        verbose_name_plural = "addresses"
        indexes = [
            models.Index(fields=["client", "address_type"]),
        ]

    def __str__(self):
        return f"{self.address_type}: {self.address_1}, {self.city}"
