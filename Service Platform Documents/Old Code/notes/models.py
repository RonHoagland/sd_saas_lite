from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel

class Note(BaseModel):
    """
    Represents a piece of text content.
    Independent of its parent (linked via NoteLink).
    """
    note_text = models.TextField()
    note_type = models.CharField(
        max_length=50,
        help_text="Type (e.g., General, Meeting). Controlled by Value List."
    )
    date_taken = models.DateField(
        default=timezone.now,
        help_text="Date the note refers to (editable)."
    )

    def __str__(self):
        return f"Note {self.id} ({self.date_taken})"

class NoteLink(BaseModel):
    """
    Links a Note to a parent entity.
    Lite: Exactly one link per Note.
    Pro: Multiple links per Note.
    """
    note = models.ForeignKey(
        Note,
        on_delete=models.CASCADE,
        related_name='links'
    )
    
    # Potential Parents (Explicit FKs)
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='note_links',
        null=True, blank=True
    )
    contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.CASCADE,
        related_name='note_links',
        null=True, blank=True
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='note_links',
        null=True, blank=True
    )
    # Add other parents here as modules are built (invoices, etc.)

    class Meta:
        indexes = [
            models.Index(fields=["note"]),
            models.Index(fields=["client"]),
            models.Index(fields=["contact"]),
            models.Index(fields=["product"]),
        ]
        # Lite Constraint: A note can be linked to a specific parent only once?
        # unique_together = ('note', 'client') etc. 
        # But for Lite, we enforce "1 link total" in application logic.

    def clean(self):
        """Ensure exactly one parent is set."""
        parents = [self.client, self.contact, self.product]
        set_parents = [p for p in parents if p is not None]
        
        if len(set_parents) == 0:
            raise ValidationError("NoteLink must be associated with exactly one parent.")
        if len(set_parents) > 1:
             raise ValidationError("NoteLink cannot link to multiple parents simultaneously.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
