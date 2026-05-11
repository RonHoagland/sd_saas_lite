# crm/models.py
# Source: Data Models V6, Sections 1.2, 2.1.
#
# All audit fields (created_by, created_on, updated_by, updated_on) and
# the id / tenant_id PK fields are inherited from TenantModel (config/base_models.py).

import uuid
from django.db import models
from config.base_models import TenantModel
from config.fields import EncryptedCharField
from numbering.mixins import NumberingMixin
from lifecycle.mixins import LifecycleMixin


class Person(TenantModel):
    """Permanent human identity. Holds attributes that don't vary by role —
    role-specific data (title, department, etc.) lives on Contact.
    Source: Data Models V6, Section 1.2."""

    class PrefixChoices(models.TextChoices):
        MR = 'Mr', 'Mr'
        MRS = 'Mrs', 'Mrs'
        MS = 'Ms', 'Ms'
        MX = 'Mx', 'Mx'
        DR = 'Dr', 'Dr'
        PROF = 'Prof', 'Prof'
        REV = 'Rev', 'Rev'
        OTHER = 'Other', 'Other'

    class SuffixChoices(models.TextChoices):
        JR = 'Jr', 'Jr'
        SR = 'Sr', 'Sr'
        II = 'II', 'II'
        III = 'III', 'III'
        IV = 'IV', 'IV'
        PHD = 'PhD', 'PhD'
        MD = 'MD', 'MD'
        ESQ = 'Esq', 'Esq'
        OTHER = 'Other', 'Other'

    prefix = models.CharField(max_length=10, choices=PrefixChoices.choices, blank=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    suffix = models.CharField(max_length=10, choices=SuffixChoices.choices, blank=True)
    preferred_name = models.CharField(max_length=100, blank=True,
                                      help_text="What this person prefers to be called (display alternative to first_name).")
    date_of_birth = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'crm_person'

    def __str__(self):
        first = self.preferred_name or self.first_name
        return f'{first} {self.last_name}'

    def full_legal_name(self):
        """Formal name for legal documents / contracts.
        Format: '{prefix} {first} {middle} {last}, {suffix}' with empties skipped."""
        parts = [self.prefix, self.first_name, self.middle_name, self.last_name]
        name = ' '.join(p for p in parts if p)
        if self.suffix:
            name = f'{name}, {self.suffix}'
        return name


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

    class LegalEntityTypeChoices(models.TextChoices):
        LLC = 'LLC', 'LLC'
        CORP = 'Corp', 'Corporation'
        PARTNERSHIP = 'Partnership', 'Partnership'
        SOLE_PROP = 'SoleProp', 'Sole Proprietorship'
        NON_PROFIT = 'NonProfit', 'Non-Profit'
        GOVERNMENT = 'Government', 'Government'
        OTHER = 'Other', 'Other'

    class PreferredContactMethodChoices(models.TextChoices):
        EMAIL = 'Email', 'Email'
        PHONE = 'Phone', 'Phone'
        SMS = 'SMS', 'SMS'
        MAIL = 'Mail', 'Mail'
        NONE = 'None', 'None'

    class PreferredServiceWindowChoices(models.TextChoices):
        MORNING = 'Morning', 'Morning'
        AFTERNOON = 'Afternoon', 'Afternoon'
        EVENING = 'Evening', 'Evening'
        ANYTIME = 'Anytime', 'Anytime'

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
    customer_since = models.DateField(null=True, blank=True)
    hold_date = models.DateTimeField(null=True, blank=True)
    hold_reason = models.TextField(blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_reason = models.TextField(blank=True)  # Required when status=Closed (System Status V3 §2)
    inactive_at = models.DateTimeField(null=True, blank=True)
    inactive_reason = models.TextField(blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    tags = models.JSONField(default=list, blank=True)

    # ── Identity / display ──
    display_name = models.CharField(max_length=200, blank=True)
    dba = models.CharField(max_length=200, blank=True)
    legal_entity_type = models.CharField(
        max_length=20, choices=LegalEntityTypeChoices.choices, blank=True,
    )
    tax_id = EncryptedCharField(max_length=50, blank=True)
    ein = EncryptedCharField(max_length=20, blank=True)
    vat_number = EncryptedCharField(max_length=30, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    employee_count = models.PositiveIntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )

    # ── Person link (Residential) ──
    primary_person = models.ForeignKey(
        Person, null=True, blank=True,
        on_delete=models.PROTECT, related_name='primary_customers',
    )

    # ── Communication preferences ──
    preferred_contact_method = models.CharField(
        max_length=10, choices=PreferredContactMethodChoices.choices, blank=True,
    )
    do_not_contact = models.BooleanField(default=False)
    do_not_email = models.BooleanField(default=False)
    do_not_call = models.BooleanField(default=False)
    do_not_sms = models.BooleanField(default=False)
    marketing_opt_in = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=10, default='en')

    # ── Service operations ──
    service_route = models.CharField(max_length=50, blank=True)
    service_zone = models.CharField(max_length=50, blank=True)
    access_instructions = models.TextField(blank=True)
    preferred_technician = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='preferred_by_customers',
    )
    preferred_service_window = models.CharField(
        max_length=10, choices=PreferredServiceWindowChoices.choices, blank=True,
    )
    requires_appointment = models.BooleanField(default=False)

    # ── Portal / external IDs ──
    portal_user = models.OneToOneField(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='customer_portal',
    )
    external_id = models.CharField(max_length=100, blank=True)
    source_system = models.CharField(max_length=50, blank=True)

    class Meta:
        db_table = 'crm_customer'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assigned_to_id']),
            models.Index(fields=['tenant_id', 'industry']),
        ]

    def __str__(self):
        return self.display_name or self.company_name or self.customer_number

    def payments(self):
        """``Payments`` queryset for this customer (linked through ``Invoice``)."""
        from service.models import Payments
        return Payments.objects.filter(invoice__customer_id=self.pk)

    @property
    def total_payments_count(self):
        """Number of payment records across all invoices for this customer."""
        return self.payments().count()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Snapshot DNC fields so save() can detect which one the caller just
        # changed. New (unsaved) instances have no "prior" — treat as all False.
        if self._state.adding:
            self._dnc_snapshot = (False, False, False, False)
        else:
            self._dnc_snapshot = (
                self.do_not_contact, self.do_not_email,
                self.do_not_call, self.do_not_sms,
            )

    def clean(self):
        """Model-level validation. Called by ``full_clean()`` — ModelForm calls
        it automatically; DRF serializers do not (CustomerSerializer.validate
        mirrors this rule for API enforcement).

        Rule: Residential customers should be linked to a Person via
        ``primary_person`` (Commercial customers use the ``contacts`` table
        for people)."""
        super().clean()
        if (self.account_type == self.AccountTypeChoices.RESIDENTIAL
                and not self.primary_person_id):
            from django.core.exceptions import ValidationError
            raise ValidationError({
                'primary_person': 'Required for Residential customers.',
            })

    def save(self, *args, **kwargs):
        # Master/granular DNC sync (per Ron, Apr 2026):
        # - do_not_contact just promoted to True → cascade all granular True
        # - Any granular just demoted to False → clear master
        # The snapshot lets us detect *which* field the caller actually
        # changed, so the two rules don't fight each other on the same save.
        prev_master, prev_email, prev_call, prev_sms = self._dnc_snapshot
        if self.do_not_contact and not prev_master:
            self.do_not_email = True
            self.do_not_call = True
            self.do_not_sms = True
        elif ((not self.do_not_email and prev_email)
              or (not self.do_not_call and prev_call)
              or (not self.do_not_sms and prev_sms)):
            self.do_not_contact = False
        # Defense-in-depth: Hold and Closed require an explicit reason per
        # Data Models V6. The lifecycle service already enforces this on
        # transitions via the rule's requires_reason flag, but direct status
        # writes (`c.status = 'Hold'; c.save()`) bypass it. Inactive is *not*
        # in this list — V6 marks it as a soft pause with no required reason.
        from django.core.exceptions import ValidationError
        if self.status == self.StatusChoices.HOLD and not self.hold_reason:
            raise ValidationError({'hold_reason': 'Required when status is Hold.'})
        if self.status == self.StatusChoices.CLOSED and not self.closed_reason:
            raise ValidationError({'closed_reason': 'Required when status is Closed.'})
        super().save(*args, **kwargs)
        self._dnc_snapshot = (
            self.do_not_contact, self.do_not_email,
            self.do_not_call, self.do_not_sms,
        )

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync denormalized state-context fields. Called by
        ``lifecycle.services.execute_transition`` between status assignment
        and ``save()``. The audit log remains the canonical history; these
        fields are a synced cache for fast display.

        Direct writes to status (bypassing ``execute_transition``) WILL drift
        these fields out of sync — always go through the lifecycle service.
        """
        from django.utils import timezone
        now = timezone.now()
        if from_state == 'Hold':
            self.hold_date = None
            self.hold_reason = ''
        elif from_state == 'Closed':
            self.closed_at = None
            self.closed_reason = ''
        elif from_state == 'Inactive':
            self.inactive_at = None
            self.inactive_reason = ''
        if to_state == 'Hold':
            self.hold_date = now
            self.hold_reason = reason or ''
        elif to_state == 'Closed':
            self.closed_at = now
            self.closed_reason = reason or ''
        elif to_state == 'Inactive':
            self.inactive_at = now
            self.inactive_reason = reason or ''


class Account(TenantModel):
    """Customer's billing/credit relationship with the tenant. 1:1 with Customer.
    Auto-created on Customer creation via crm.signals. Source: Data Models V6, Section 1.2."""

    class CreditStatusChoices(models.TextChoices):
        GOOD = 'Good', 'Good'
        FAIR = 'Fair', 'Fair'
        POOR = 'Poor', 'Poor'

    customer = models.OneToOneField(Customer, on_delete=models.CASCADE,
                                    related_name='account')
    account_terms = models.CharField(max_length=50, blank=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    credit_status = models.CharField(max_length=10,
                                     choices=CreditStatusChoices.choices,
                                     default=CreditStatusChoices.GOOD)
    tax_rate = models.DecimalField(max_digits=7, decimal_places=4,
                                   null=True, blank=True)
    tax_exempt = models.BooleanField(default=False)
    pricing_tier = models.CharField(max_length=50, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    po_required = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_account'
        indexes = [
            models.Index(fields=['tenant_id', 'credit_status']),
        ]

    def __str__(self):
        return f'Account for {self.customer}'


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

    # ── Org hierarchy at the parent company ──
    reports_to = models.ForeignKey('self', null=True, blank=True,
                                   on_delete=models.SET_NULL,
                                   related_name='direct_reports')

    # ── Role flags (per-contact, since one Person can hold multiple roles
    # across customers/vendors with different responsibilities each time) ──
    is_decision_maker = models.BooleanField(default=False)
    is_billing_contact = models.BooleanField(default=False)
    is_technical_contact = models.BooleanField(default=False)
    is_emergency_contact = models.BooleanField(default=False)

    # ── Relationship management ──
    notes = models.TextField(blank=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True,
                                             help_text="Most recent successful outbound contact (call, email, meeting).")

    class Meta:
        db_table = 'crm_contact'
        indexes = [
            models.Index(fields=['tenant_id', 'customer_id', 'is_primary']),
            models.Index(fields=['tenant_id', 'reports_to_id']),
        ]

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
    street_2 = models.CharField(max_length=100, blank=True,
                                help_text="Apt/Suite/Floor — second address line.")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    state_code = models.CharField(max_length=10, blank=True,
                                  help_text="State/region abbreviation (CA, NY, TX). For dispatch routing.")
    zip = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=2, blank=True,
                                    help_text="ISO 3166-1 alpha-2 country code (US, GB, CA).")
    # ── Geocoding ──
    # Decimal precision: lat ±90, lng ±180; 7 decimal places ≈ 1.1cm at the equator.
    latitude = models.DecimalField(max_digits=10, decimal_places=7,
                                   null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=7,
                                    null=True, blank=True)
    geocoded_at = models.DateTimeField(null=True, blank=True)
    # ── Verification ──
    is_verified = models.BooleanField(default=False,
                                      help_text="Address has been validated against an authoritative source (USPS, etc.).")
    verified_at = models.DateTimeField(null=True, blank=True)

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
    country_code = models.CharField(max_length=5, blank=True,
                                    help_text="International dialing code, including '+' (e.g. '+1', '+44').")
    number = models.CharField(max_length=30)
    is_primary = models.BooleanField(default=False)
    extension = models.CharField(max_length=10, blank=True)
    sms_capable = models.BooleanField(default=False,
                                      help_text="Whether this number can receive SMS. Independent of phone_type.")
    is_verified = models.BooleanField(default=False,
                                      help_text="Number has been verified (e.g., SMS code).")
    verified_at = models.DateTimeField(null=True, blank=True)

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
    """Plus+ CRM Lead. Source: Data Models V6, Section 2.1.

    A Lead is the sales-tracking shell around a Customer + Person pair.
    The Customer holds all operational data (account_type, addresses,
    phones, socials, billing). The Person holds name/identity. The Lead
    holds only sales-workflow data (source, status, score, follow-up dates)
    and lifecycle history.

    Notes attach via the Note system (ExclusiveArc); communications via
    Customer's Phone/Social bridges. Lead does NOT duplicate any of that.
    """
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
    # Customer is required — the Customer record (Residential or Commercial,
    # already in the system or freshly created) is the anchor for everything.
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT,
                                 related_name='leads')
    # Person identifies which human at the customer this lead is about.
    # For Residential, typically the same as customer.primary_person.
    # For Commercial, a contact at the company (one of customer.contacts).
    person = models.ForeignKey(Person, on_delete=models.PROTECT,
                               related_name='leads')
    source = models.CharField(max_length=20, choices=SourceChoices.choices,
                              blank=True)
    status = models.CharField(max_length=20, choices=StatusChoices.choices,
                              default=StatusChoices.NEW)
    tags = models.JSONField(default=list, blank=True)

    # ── Sales workflow ──
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='assigned_leads')
    lead_score = models.DecimalField(max_digits=5, decimal_places=2,
                                     null=True, blank=True,
                                     help_text="Lead quality score, 0–100.")
    last_contacted_at = models.DateTimeField(null=True, blank=True)
    next_followup_at = models.DateTimeField(null=True, blank=True)

    # ── Lifecycle context (set by _apply_lifecycle_transition) ──
    qualified_at = models.DateTimeField(null=True, blank=True)
    converted_at = models.DateTimeField(null=True, blank=True)
    lost_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_lead'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assigned_to_id']),
            models.Index(fields=['tenant_id', 'customer_id']),
        ]

    def __str__(self):
        return f'{self.person} ({self.status})'

    def save(self, *args, **kwargs):
        # Defense-in-depth: Lost requires lost_reason. Lifecycle service
        # enforces on transitions; this catches direct status writes.
        if self.status == self.StatusChoices.LOST and not self.lost_reason:
            from django.core.exceptions import ValidationError
            raise ValidationError({'lost_reason': 'Required when status is Lost.'})
        super().save(*args, **kwargs)

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync denormalized lifecycle context. Lead lifecycle is forward-only
        per the seed — no need to clear timestamps when leaving a state."""
        from django.utils import timezone
        now = timezone.now()
        if to_state == self.StatusChoices.QUALIFIED:
            self.qualified_at = now
        elif to_state == self.StatusChoices.CONVERTED:
            self.converted_at = now
        elif to_state == self.StatusChoices.LOST:
            self.lost_at = now
            self.lost_reason = reason or ''


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
    actual_value = models.DecimalField(max_digits=12, decimal_places=2,
                                       null=True, blank=True,
                                       help_text="Realized value when Won. Defaults to estimated_value if unset.")
    probability = models.DecimalField(max_digits=5, decimal_places=2,
                                      null=True, blank=True,
                                      help_text="Conversion likelihood, 0–100.")
    expected_close_date = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey('users.User', null=True, blank=True,
                                    on_delete=models.SET_NULL,
                                    related_name='opportunities')
    next_step = models.CharField(max_length=300, blank=True,
                                 help_text="The next action to advance this opportunity.")
    competitor = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    # ── Lifecycle context (set by _apply_lifecycle_transition) ──
    won_at = models.DateTimeField(null=True, blank=True)
    lost_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'crm_opportunity'
        indexes = [
            models.Index(fields=['tenant_id', 'status']),
            models.Index(fields=['tenant_id', 'assigned_to_id']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Defense-in-depth: Lost requires lost_reason.
        if self.status == self.StatusChoices.LOST and not self.lost_reason:
            from django.core.exceptions import ValidationError
            raise ValidationError({'lost_reason': 'Required when status is Lost.'})
        super().save(*args, **kwargs)

    def _apply_lifecycle_transition(self, *, from_state, to_state, reason, user):
        """Sync denormalized lifecycle context. Opportunity lifecycle is
        forward-only per the seed (Won and Lost are both final)."""
        from django.utils import timezone
        now = timezone.now()
        if to_state == self.StatusChoices.WON:
            self.won_at = now
            # Default actual_value from estimated if caller didn't set it.
            if self.actual_value is None:
                self.actual_value = self.estimated_value
        elif to_state == self.StatusChoices.LOST:
            self.lost_at = now
            self.lost_reason = reason or ''


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
