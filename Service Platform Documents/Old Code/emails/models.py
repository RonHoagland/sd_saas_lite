from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel

class Email(BaseModel):
    """
    Email address associated with a Client OR Contact.
    """
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='emails',
        null=True, blank=True
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='emails',
        null=True, blank=True
    )
    
    email_type = models.CharField(
        max_length=50,
        help_text="Type (e.g., Work, Personal). Controlled by Value List."
    )
    email_address = models.EmailField()

    class Meta:
        indexes = [
            models.Index(fields=["email_address"]),
        ]

    def clean(self):
        """Ensure at least one parent is set."""
        if not self.client and not self.contact:
            raise ValidationError("Email must belong to a Client or a Contact.")
        if self.client and self.contact:
             raise ValidationError("Email cannot belong to both Client and Contact simultaneously.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.email_address} ({self.email_type})"
