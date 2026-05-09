from django.db import models

class ValueList(models.Model):
    """
    A category or group of values, e.g., 'Customer Type', 'Ticket Priority'.
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Unique identifier for retrieving this list in code.")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class ValueItem(models.Model):
    """
    A specific option within a ValueList, e.g., 'Business', 'Personal'.
    """
    value_list = models.ForeignKey(ValueList, related_name='items', on_delete=models.CASCADE)
    value = models.CharField(max_length=255, help_text="The actual text value stored in other models.")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True, help_text="If false, this item won't appear in new dropdowns.")

    class Meta:
        ordering = ['sort_order', 'value']

    def __str__(self):
        return self.value
