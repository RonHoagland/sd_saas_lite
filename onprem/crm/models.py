# crm/models.py
# Source: Data Models V6, Sections 1.2, 2.1.
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

import uuid
from django.db import models
from config.base_models import TenantModel
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Person(TenantModel):
    """Permanent human identity. Source: Data Models V6, Section 1.2."""

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'crm_person'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Customer(TenantModel, NumberingMixin, LifecycleMixin):
    """Source: Data Models V6, Section 1.2."""
    numbering_entity_type = 'customer'
    lifecycle_entity_type = 'customer'

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        HOLD = 'Hold', 'Hold'
        CLOSED = 'Closed', 'Closed'

    class AccountTypeChoices(models.TextChoices):
        RESIDENTIAL = 'Residential', 'Residential'
        COMMERCIAL = 'Commercial', 'Commercial'

    class CreditStatusChoices(models.TextChoices):
        GOOD = 'Good', 'Good'
        FAIR = 'Fair', 'Fair'
        POOR = 'Poor', 'Poor'

    customer_number = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)
    account_type = models.CharField(max_length=20,
                                    choices=AccountTypeChoices.choices,
                                    default=AccountTypeChoices.RESIDENTIAL)
    company_name = models.CharField(max_length=200, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_customers')
    lead_source = models.CharField(max_length=100, blank=True)
    tax_exempt = models.BooleanField(default=False)
    customer_since = models.DateField(null=True, blank=True)
    hold_date = models.DateTimeField(null=True, blank=True)
    hold_reason = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.TextField(blank=True)  # Required when status=Closed (System Status V3 §2)
    account_number = models.CharField(max_length=50, blank=True)
    account_terms = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_status = models.CharField(max_length=10,
                                     choices=CreditStatusChoices.choices,
                                     default=CreditStatusChoices.GOOD)
    tax_rate = models.DecimalField(max_digits=7, decimal_places=4,
                                   null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'crm_customer'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assigned_to_id']),
        ]

    def __str__(self):
        return self.company_name or self.customer_number


class Contact(TenantModel):
    """Bridge: Person ↔ Customer/Vendor/Bank. Source: Data Models V6, Section 1.2."""

    class StatusChoices(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        LEFT = 'Left', 'Left'

    person = models.ForeignKey(Person, on_delete=models.PROTECT,
                               related_name='contacts')
    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.RESTRICT,
                                 related_name='contacts')
    vendor = models.ForeignKey('procurement.Vendor', null=True, blank=True,
                               on_delete=models.RESTRICT,
                               related_name='contacts')
    bank = models.ForeignKey('service.Bank', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='contacts')
    role_title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_primary = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                              default=StatusChoices.ACTIVE)
    start_date = models.DateField(null=True, blank=True)
    left_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'crm_contact'

    def __str__(self):
        return str(self.person)


class Address(TenantModel):
    """Shared address. Source: Data Models V6, Section 1.2."""

    class AddressTypeChoices(models.TextChoices):
        SERVICE = 'Service', 'Service'
        BILLING = 'Billing', 'Billing'
        MAILING = 'Mailing', 'Mailing'
        OTHER = 'Other', 'Other'

    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.RESTRICT,
                                 related_name='addresses')
    contact = models.ForeignKey(Contact, null=True, blank=True,
                                on_delete=models.RESTRICT,
                                related_name='addresses')
    vendor = models.ForeignKey('procurement.Vendor', null=True, blank=True,
                               on_delete=models.RESTRICT,
                               related_name='addresses')
    bank = models.ForeignKey('service.Bank', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='addresses')
    asset = models.ForeignKey('maintenance.Asset', null=True, blank=True,
                              on_delete=models.RESTRICT,
                              related_name='addresses')
    user = models.ForeignKey('users.User', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='addresses')
    warehouse = models.ForeignKey('warehouse.Warehouse', null=True, blank=True,
                                  on_delete=models.RESTRICT,
                                  related_name='addresses')
    work_group = models.ForeignKey('workforce.WorkGroup', null=True, blank=True,
                                   on_delete=models.RESTRICT,
                                   related_name='addresses')
    address_type = models.CharField(max_length=20,
                                    choices=AddressTypeChoices.choices,
                                    default=AddressTypeChoices.SERVICE)
    is_primary = models.BooleanField(default=False)
    street = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zip = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'crm_address'

    def __str__(self):
        return f'{self.street}, {self.city}'


class Phone(TenantModel):
    """Shared phone numbers. Source: Data Models V6, Section 1.2."""

    class PhoneTypeChoices(models.TextChoices):
        MOBILE = 'Mobile', 'Mobile'
        OFFICE = 'Office', 'Office'
        HOME = 'Home', 'Home'
        FAX = 'Fax', 'Fax'
        OTHER = 'Other', 'Other'

    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.RESTRICT,
                                 related_name='phones')
    contact = models.ForeignKey(Contact, null=True, blank=True,
                                on_delete=models.RESTRICT,
                                related_name='phones')
    vendor = models.ForeignKey('procurement.Vendor', null=True, blank=True,
                               on_delete=models.RESTRICT,
                               related_name='phones')
    bank = models.ForeignKey('service.Bank', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='phones')
    user = models.ForeignKey('users.User', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='phones')
    warehouse = models.ForeignKey('warehouse.Warehouse', null=True, blank=True,
                                  on_delete=models.RESTRICT,
                                  related_name='phones')
    phone_type = models.CharField(max_length=10, choices=PhoneTypeChoices.choices,
                                  default=PhoneTypeChoices.MOBILE)
    number = models.CharField(max_length=30)
    is_primary = models.BooleanField(default=False)
    extension = models.CharField(max_length=10, blank=True)

    class Meta:
        db_table = 'crm_phone'

    def __str__(self):
        return self.number


class Social(TenantModel):
    """Emails and social links. Source: Data Models V6, Section 1.2."""

    class TypeChoices(models.TextChoices):
        EMAIL = 'Email', 'Email'
        FACEBOOK = 'Facebook', 'Facebook'
        LINKEDIN = 'LinkedIn', 'LinkedIn'
        INSTAGRAM = 'Instagram', 'Instagram'
        TWITTER = 'Twitter/X', 'Twitter/X'
        YOUTUBE = 'YouTube', 'YouTube'
        WEBSITE = 'Website', 'Website'
        OTHER = 'Other', 'Other'

    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.RESTRICT,
                                 related_name='socials')
    contact = models.ForeignKey(Contact, null=True, blank=True,
                                on_delete=models.RESTRICT,
                                related_name='socials')
    vendor = models.ForeignKey('procurement.Vendor', null=True, blank=True,
                               on_delete=models.RESTRICT,
                               related_name='socials')
    person = models.ForeignKey(Person, null=True, blank=True,
                               on_delete=models.RESTRICT,
                               related_name='socials')
    user = models.ForeignKey('users.User', null=True, blank=True,
                             on_delete=models.RESTRICT,
                             related_name='socials')
    type = models.CharField(max_length=20, choices=TypeChoices.choices)
    value = models.CharField(max_length=500)

    class Meta:
        db_table = 'crm_social'

    def __str__(self):
        return f'{self.type}: {self.value}'


class Lead(TenantModel, NumberingMixin, LifecycleMixin):
    """Plus+ CRM Lead. Source: Data Models V6, Section 2.1."""
    numbering_entity_type = 'lead'
    lifecycle_entity_type = 'lead'

    class SourceChoices(models.TextChoices):
        REFERRAL = 'Referral', 'Referral'
        WEBSITE = 'Website', 'Website'
        ADVERTISEMENT = 'Advertisement', 'Advertisement'
        TRADE_SHOW = 'Trade Show', 'Trade Show'
        COLD_CALL = 'Cold Call', 'Cold Call'
        OTHER = 'Other', 'Other'

    class StatusChoices(models.TextChoices):
        NEW = 'New', 'New'
        CONTACTED = 'Contacted', 'Contacted'
        QUALIFIED = 'Qualified', 'Qualified'
        CONVERTED = 'Converted', 'Converted'
        LOST = 'Lost', 'Lost'

    lead_number = models.CharField(max_length=20, blank=True)
    customer = models.ForeignKey(Customer, null=True, blank=True,
                                 on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    source = models.CharField(max_length=20, choices=SourceChoices.choices,
                              blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.NEW)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_lead'

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.status})'


class Opportunity(TenantModel, NumberingMixin, LifecycleMixin):
    """Pro+ CRM Opportunity. Source: Data Models V6, Section 2.1."""
    numbering_entity_type = 'opportunity'
    lifecycle_entity_type = 'opportunity'

    class StatusChoices(models.TextChoices):
        OPEN = 'Open', 'Open'
        WON = 'Won', 'Won'
        LOST = 'Lost', 'Lost'

    opportunity_number = models.CharField(max_length=20, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    lead = models.ForeignKey(Lead, null=True, blank=True,
                             on_delete=models.SET_NULL)
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10, choices=StatusChoices.choices,
                              default=StatusChoices.OPEN)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2,
                                         default=0)
    expected_close_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='opportunities')
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_opportunity'

    def __str__(self):
        return self.name


class OpportunityContacts(TenantModel):
    """Pro+ junction: Opportunity ↔ Contact. Source: Data Models V6, Section 2.1."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE,
                                    related_name='opportunity_contacts')
    contact = models.ForeignKey(Contact, on_delete=models.RESTRICT)
    customer = models.ForeignKey(Customer, on_delete=models.RESTRICT)
    role_in_opportunity = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'crm_opportunitycontacts'

    def __str__(self):
        return f'{self.opportunity} ↔ {self.contact}'
