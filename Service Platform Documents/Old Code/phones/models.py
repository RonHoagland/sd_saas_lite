from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Phone(BaseModel):
    """
    Phone number associated with a Client OR Contact.
    """
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='phones',
        null=True, blank=True
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='phones',
        null=True, blank=True
    )
    
    phone_type = models.CharField(
        max_length=50,
        help_text="Type (e.g., Office, Mobile). Controlled by Value List."
    )
    phone_number = models.CharField(max_length=50) # Raw string for now, formatted by UI/Utils
    extension = models.CharField(max_length=10, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["phone_number"]),
        ]

    def clean(self):
        """Ensure at least one parent is set."""
        if not self.client and not self.contact:
            raise ValidationError("Phone must belong to a Client or a Contact.")
        if self.client and self.contact:
             raise ValidationError("Phone cannot belong to both Client and Contact simultaneously.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone_number} ({self.phone_type})"
