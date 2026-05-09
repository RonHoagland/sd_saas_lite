from django.db import models
from django.utils import timezone
from core.models import BaseModel
from numbering.utils import generate_number  # Assumed utility from existing Numbering app

class Client(BaseModel):
    """
    Represents a business entity (Customer/Account).
    Acts as the anchor for Contacts, Addresses, Phones, etc.
    """
    
    # Identification
    account_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False, 
        help_text="Unique system-generated account number (ACYYNNN)."
    )
    
    name = models.CharField(
        max_length=255, 
        help_text="Business Name or Display Name."
    )
    
    # Key Dates
    date_started = models.DateField(
        default=timezone.now,
        help_text="Date the relationship started (defaults to today, editable)."
    )
    
    # Classification (Value Lists stored as strings)
    status = models.CharField(
        max_length=50,
        default='Active',
        help_text="Lifecycle status (e.g., Prospect, Active). Controlled by Value List."
    )
    
    client_type = models.CharField(
        max_length=50,
        help_text="Classification (e.g., Commercial, Residential). Controlled by Value List."
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["account_number"]),
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate Account Number on instantiation if not present
        if not self.account_number:
             # TODO: Ensure 'clients:AC:YY' domain exists in Numbering
            self.account_number = generate_number('client') 

    def __str__(self):
        return f"{self.name} ({self.account_number})"
