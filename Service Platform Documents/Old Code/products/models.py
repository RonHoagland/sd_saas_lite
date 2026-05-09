from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel
# from audit.service import AuditService  # TODO: Import once available/mocked

class Product(BaseModel):
    """
    Represents an item in the catalog (Part, Service, Asset).
    Quantity On Hand is informational/audited only in Lite.
    """
    sku = models.CharField(
        max_length=100, 
        unique=True, 
        blank=True, 
        null=True,
        help_text="Stock Keeping Unit or unique product code."
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    date_started = models.DateField(
        default=timezone.now,
        help_text="Date the product was started/introduced."
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Product image"
    )
    
    # Value Lists (stored as strings)
    product_type = models.CharField(
        max_length=50,
        help_text="Type of product (e.g., Part, Service, Asset). Controlled by Value List."
    )
    status = models.CharField(
        max_length=50,
        default='Active',
        help_text="Status of the product (e.g., Active, Deprecated). Controlled by Value List."
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="technical active status" # Keep simple boolean for queries
    )

    quantity_on_hand = models.IntegerField(
        default=0,
        help_text="Current stock level. Audited field."
    )

    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Unit price"
    )

    category = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product category (e.g. Electronics, Furniture)"
    )

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["product_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})" if self.sku else self.name

    def save(self, *args, **kwargs):
        # Auto-generate SKU if missing
        if not self.sku:
            from numbering.utils import generate_number
            try:
                # User tracking for audit
                user = kwargs.pop('user', None) # Pass user via save(user=request.user) pattern if possible
                self.sku = generate_number('product', user=user)
            except Exception:
                # If numbering fails (e.g. no rule), leave blank or handle gracefully
                pass
        
        # Ensure 'user' is not passed to super().save() as it causes TypeError
        if 'user' in kwargs:
             kwargs.pop('user')

        super().save(*args, **kwargs)
