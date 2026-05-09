from django.db import models
from core.models import BaseModel

class Person(BaseModel):
    """
    Represents a human identity.
    Stores only name-level data. Contact methods (phones, emails) are separate.
    """
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Name the person prefers to be called, if different from first name."
    )

    class Meta:
        verbose_name_plural = "people"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
        ]

    def __str__(self):
        if self.preferred_name:
            return f"{self.preferred_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
