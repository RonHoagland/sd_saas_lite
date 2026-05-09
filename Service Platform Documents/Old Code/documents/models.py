from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseModel
import uuid

class Document(BaseModel):
    """
    Represents a reference to a file.
    Does NOT store the file itself in a BinaryField, but tracks its path.
    """
    document_name = models.CharField(max_length=255)
    document_type = models.CharField(
        max_length=50,
        help_text="Type (e.g., Contract, Image). Controlled by Value List."
    )
    
    # File Metadata
    original_filename = models.CharField(max_length=255)
    stored_filename = models.CharField(
        max_length=255, 
        unique=True,
        default=uuid.uuid4,
        editable=False
    )
    storage_path = models.CharField(
        max_length=1024,
        editable=False,
        help_text="Full physical path or URL to the file."
    )
    
    # Creation Source (Immutable Traceability)
    created_from_table = models.CharField(
        max_length=50,
        editable=False,
        help_text="Table name where this document originated (e.g., 'clients')."
    )
    created_from_id = models.UUIDField(
        editable=False,
        help_text="ID of the record where this document originated."
    )

    def __str__(self):
        return self.document_name

    def generate_storage_path(self):
        """
        Generates the mandatory storage path per system specification:
        <root>/cols/<created_from_table>/<created_from_id>/<stored_filename>
        """
        from core.models import Preference
        from django.conf import settings
        import os

        # Get root path from preference or fallback to settings.BASE_DIR/docs
        try:
            root_path = Preference.objects.get(key='system_upload_path').value
        except Preference.DoesNotExist:
            root_path = os.path.join(settings.BASE_DIR, 'docs')

        return os.path.join(
            root_path,
            str(self.created_from_table),
            str(self.created_from_id),
            str(self.stored_filename)
        )

    def save(self, *args, **kwargs):
        # Ensure storage_path is always set correctly before save
        if not self.storage_path:
            self.storage_path = self.generate_storage_path()
        super().save(*args, **kwargs)

class DocumentLink(BaseModel):
    """
    Links a Document to a parent entity.
    Lite: Exactly one link per Document.
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='links'
    )
    
    # Potential Parents (Explicit FKs)
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='document_links',
        null=True, blank=True
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='document_links',
        null=True, blank=True
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='document_links',
        null=True, blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["document"]),
            models.Index(fields=["client"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["product"]),
        ]

    def clean(self):
        """Ensure exactly one parent is set."""
        parents = [self.client, self.contact, self.product]
        set_parents = [p for p in parents if p is not None]
        
        if len(set_parents) == 0:
            raise ValidationError("DocumentLink must be associated with exactly one parent.")
        if len(set_parents) > 1:
             raise ValidationError("DocumentLink cannot link to multiple parents simultaneously.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
