from django.db import models
from core.models import BaseModel

class Contact(BaseModel):
    """
    Represents a Person's role at a Client.
    Links Identity (Person) to Business Context (Client).
    """
    client = models.ForeignKey(
        'clients.Client', 
        on_delete=models.CASCADE, 
        related_name='contacts'
    )
    person = models.ForeignKey(
        'people.Person', 
        on_delete=models.PROTECT, 
        related_name='contact_roles'
    )
    
    # Business Role Context
    role_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["person__last_name"]
        indexes = [
            models.Index(fields=["client", "person"]),
        ]
        # Lite Constraint: 1 Person <-> 1 Contact (implied by usage, enforcing unique link here for safety?)
        # unique_together = ('client', 'person') # Depending on strictness, but let's keep it flexible for Pro later

    def __str__(self):
        return f"{self.person} @ {self.client}"
