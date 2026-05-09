# crm/api.py
# REST API serializers and viewsets for CRM models.
# Source: Data Models V6, Sections 1.2, 2.1.

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter
from api.base import (
    TenantModelSerializer,
    TenantModelViewSet,
    ReadOnlyTenantViewSet,
    TenantNoDeleteViewSet,
)
from .models import (
    Person,
    Customer,
    Account,
    Contact,
    Address,
    Phone,
    Social,
    Lead,
    Opportunity,
    OpportunityContacts,
)


# ---------------------------------------------------------------------------
# Person Serializers & ViewSets
# ---------------------------------------------------------------------------

class PersonSerializer(TenantModelSerializer):
    """Serializer for Person model."""

    full_legal_name = serializers.CharField(read_only=True)

    class Meta:
        model = Person
        fields = TenantModelSerializer.Meta.fields + [
            'prefix',
            'first_name',
            'middle_name',
            'last_name',
            'suffix',
            'preferred_name',
            'date_of_birth',
            'full_legal_name',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'full_legal_name',
        ]


class PersonViewSet(TenantModelViewSet):
    """ViewSet for Person CRUD operations."""

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filterset_fields = ['first_name', 'last_name', 'prefix', 'suffix']
    search_fields = ['first_name', 'middle_name', 'last_name', 'preferred_name']
    ordering_fields = ['created_on', 'last_name', 'first_name']


# ---------------------------------------------------------------------------
# Customer Serializers & ViewSets
# ---------------------------------------------------------------------------

class AccountSerializer(TenantModelSerializer):
    """Serializer for Account model (1:1 with Customer)."""

    class Meta:
        model = Account
        fields = TenantModelSerializer.Meta.fields + [
            'customer',
            'account_terms',
            'credit_limit',
            'credit_status',
            'tax_rate',
            'tax_exempt',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'customer',
        ]


class AccountViewSet(TenantNoDeleteViewSet):
    """ViewSet for Account. Read/update only — Accounts are auto-created with the
    Customer and deleted only via Customer cascade."""

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    filterset_fields = ['customer_id', 'credit_status', 'tax_exempt']
    search_fields = ['customer__company_name', 'customer__customer_number',
                     'customer__account_number']
    ordering_fields = ['created_on', 'credit_status']


class CustomerSerializer(TenantModelSerializer):
    """Serializer for Customer model."""

    assigned_to_id = serializers.IntegerField(
        source='assigned_to.id',
        read_only=True,
        allow_null=True,
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True,
    )
    account = AccountSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = TenantModelSerializer.Meta.fields + [
            'customer_number',
            'status',
            'account_type',
            'company_name',
            'display_name',
            'dba',
            'legal_entity_type',
            'tax_id',
            'ein',
            'vat_number',
            'industry',
            'employee_count',
            'annual_revenue',
            'primary_person',
            'assigned_to',
            'assigned_to_id',
            'assigned_to_username',
            'lead_source',
            'customer_since',
            'hold_date',
            'hold_reason',
            'closed_at',
            'closed_reason',
            'inactive_at',
            'inactive_reason',
            'account_number',
            'tags',
            'preferred_contact_method',
            'do_not_contact',
            'do_not_email',
            'do_not_call',
            'do_not_sms',
            'marketing_opt_in',
            'preferred_language',
            'service_route',
            'service_zone',
            'access_instructions',
            'preferred_technician',
            'preferred_service_window',
            'requires_appointment',
            'portal_user',
            'external_id',
            'source_system',
            'account',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'customer_number',
            'assigned_to_id',
            'assigned_to_username',
            # Lifecycle-managed denormalized state-context fields. Only the
            # lifecycle service writes these (via _apply_lifecycle_transition);
            # editing them through the API would drift them from the audit log.
            'hold_date', 'hold_reason',
            'closed_at', 'closed_reason',
            'inactive_at', 'inactive_reason',
            'account',
        ]

    def validate_customer_since(self, value):
        """Once set, ``customer_since`` is editable only by Tenant Admins
        (per Ron, Apr 2026). First-time set is always allowed."""
        request = self.context.get('request')
        if request is None or self.instance is None:
            return value  # create flow or no request context
        existing = self.instance.customer_since
        if existing is None or existing == value:
            return value
        if not getattr(request.user, 'is_tenant_admin', False):
            raise serializers.ValidationError(
                "customer_since can only be changed by a Tenant Admin once set."
            )
        return value

    def validate(self, attrs):
        """Mirror Customer.clean(): Residential customers require primary_person.
        Resolves account_type and primary_person from incoming attrs first,
        falling back to the existing instance for partial updates."""
        attrs = super().validate(attrs)
        account_type = attrs.get(
            'account_type',
            self.instance.account_type if self.instance else None,
        )
        primary_person = attrs.get(
            'primary_person',
            self.instance.primary_person if self.instance else None,
        )
        if account_type == 'Residential' and not primary_person:
            raise serializers.ValidationError({
                'primary_person': 'Required for Residential customers.',
            })
        return attrs


class CustomerViewSet(TenantModelViewSet):
    """ViewSet for Customer CRUD operations."""

    queryset = Customer.objects.select_related('account').all()
    serializer_class = CustomerSerializer
    filterset_fields = ['status', 'account_type', 'assigned_to_id', 'industry',
                        'do_not_contact']
    search_fields = ['company_name', 'display_name', 'customer_number',
                     'account_number', 'external_id']
    ordering_fields = ['created_on', 'company_name', 'status', 'customer_since']


# ---------------------------------------------------------------------------
# Contact Serializers & ViewSets
# ---------------------------------------------------------------------------

class ContactSerializer(TenantModelSerializer):
    """Serializer for Contact model."""

    person_name = serializers.CharField(
        source='person.__str__',
        read_only=True,
    )
    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Contact
        fields = TenantModelSerializer.Meta.fields + [
            'person',
            'person_name',
            'customer',
            'customer_name',
            'vendor',
            'bank',
            'role_title',
            'department',
            'is_primary',
            'status',
            'start_date',
            'left_date',
            'reports_to',
            'is_decision_maker',
            'is_billing_contact',
            'is_technical_contact',
            'is_emergency_contact',
            'notes',
            'last_contacted_at',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'person_name',
            'customer_name',
        ]

    def validate_reports_to(self, value):
        """A Contact cannot report to itself."""
        if value is not None and self.instance is not None and value.id == self.instance.id:
            raise serializers.ValidationError(
                "A contact cannot report to itself."
            )
        return value


class ContactViewSet(TenantModelViewSet):
    """ViewSet for Contact CRUD operations."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_fields = ['status', 'is_primary', 'customer_id', 'person_id',
                        'is_decision_maker', 'is_billing_contact',
                        'is_technical_contact', 'is_emergency_contact']
    search_fields = ['person__first_name', 'person__last_name', 'role_title',
                     'department']
    ordering_fields = ['created_on', 'person__last_name', 'is_primary',
                       'last_contacted_at']


# ---------------------------------------------------------------------------
# Address Serializers & ViewSets
# ---------------------------------------------------------------------------

class AddressSerializer(TenantModelSerializer):
    """Serializer for Address model."""

    full_address = serializers.SerializerMethodField(read_only=True)

    def get_full_address(self, obj):
        line1 = obj.street
        if obj.street_2:
            line1 = f'{line1} {obj.street_2}'.strip()
        parts = [line1, obj.city, obj.state_code or obj.state, obj.zip, obj.country]
        return ', '.join([p for p in parts if p])

    class Meta:
        model = Address
        fields = TenantModelSerializer.Meta.fields + [
            'customer',
            'contact',
            'vendor',
            'bank',
            'asset',
            'user',
            'warehouse',
            'work_group',
            'address_type',
            'is_primary',
            'street',
            'street_2',
            'city',
            'state',
            'state_code',
            'zip',
            'country',
            'country_code',
            'latitude',
            'longitude',
            'geocoded_at',
            'is_verified',
            'verified_at',
            'full_address',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'full_address',
        ]


class AddressViewSet(TenantModelViewSet):
    """ViewSet for Address CRUD operations."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filterset_fields = ['address_type', 'is_primary', 'customer_id', 'contact_id',
                        'is_verified', 'country_code']
    search_fields = ['street', 'street_2', 'city', 'state', 'zip']
    ordering_fields = ['created_on', 'city', 'address_type']


# ---------------------------------------------------------------------------
# Phone Serializers & ViewSets
# ---------------------------------------------------------------------------

class PhoneSerializer(TenantModelSerializer):
    """Serializer for Phone model."""

    full_number = serializers.SerializerMethodField(read_only=True)

    def get_full_number(self, obj):
        base = f'{obj.country_code} {obj.number}'.strip() if obj.country_code else obj.number
        if obj.extension:
            return f'{base} x{obj.extension}'
        return base

    class Meta:
        model = Phone
        fields = TenantModelSerializer.Meta.fields + [
            'customer',
            'contact',
            'vendor',
            'bank',
            'user',
            'warehouse',
            'phone_type',
            'country_code',
            'number',
            'is_primary',
            'extension',
            'sms_capable',
            'is_verified',
            'verified_at',
            'full_number',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'full_number',
        ]


class PhoneViewSet(TenantModelViewSet):
    """ViewSet for Phone CRUD operations."""

    queryset = Phone.objects.all()
    serializer_class = PhoneSerializer
    filterset_fields = ['phone_type', 'is_primary', 'customer_id', 'contact_id',
                        'sms_capable', 'is_verified']
    search_fields = ['number']
    ordering_fields = ['created_on', 'phone_type', 'is_primary']


# ---------------------------------------------------------------------------
# Social Serializers & ViewSets
# ---------------------------------------------------------------------------

class SocialSerializer(TenantModelSerializer):
    """Serializer for Social model (emails and social links)."""

    class Meta:
        model = Social
        fields = TenantModelSerializer.Meta.fields + [
            'customer',
            'contact',
            'vendor',
            'person',
            'user',
            'type',
            'value',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class SocialViewSet(TenantModelViewSet):
    """ViewSet for Social CRUD operations."""

    queryset = Social.objects.all()
    serializer_class = SocialSerializer
    filterset_fields = ['type', 'customer_id', 'contact_id', 'person_id']
    search_fields = ['value']
    ordering_fields = ['created_on', 'type']


# ---------------------------------------------------------------------------
# Lead Serializers & ViewSets
# ---------------------------------------------------------------------------

class LeadSerializer(TenantModelSerializer):
    """Serializer for Lead model.

    Lead is the sales-tracking shell around a Customer + Person pair.
    All operational data (phones, addresses, emails, notes) lives on the
    Customer or via the Note system — the serializer surfaces convenience
    read-only display fields but does not duplicate them.
    """

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    customer_account_type = serializers.CharField(
        source='customer.account_type',
        read_only=True,
    )
    person_name = serializers.CharField(source='person.__str__', read_only=True)

    class Meta:
        model = Lead
        fields = TenantModelSerializer.Meta.fields + [
            'lead_number',
            'customer',
            'customer_name',
            'customer_account_type',
            'person',
            'person_name',
            'source',
            'status',
            'tags',
            'assigned_to',
            'lead_score',
            'last_contacted_at',
            'next_followup_at',
            'qualified_at',
            'converted_at',
            'lost_at',
            'lost_reason',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'lead_number',
            'customer_name',
            'customer_account_type',
            'person_name',
            # Lifecycle-managed denormalized fields — only the lifecycle service
            # writes these via _apply_lifecycle_transition.
            'qualified_at', 'converted_at', 'lost_at', 'lost_reason',
        ]


class LeadViewSet(TenantModelViewSet):
    """ViewSet for Lead CRUD operations."""

    queryset = Lead.objects.select_related('customer', 'person').all()
    serializer_class = LeadSerializer
    filterset_fields = ['status', 'source', 'customer_id', 'person_id',
                        'assigned_to_id']
    search_fields = ['lead_number',
                     'person__first_name', 'person__last_name',
                     'customer__company_name']
    ordering_fields = ['created_on', 'status', 'lead_score',
                       'next_followup_at']


# ---------------------------------------------------------------------------
# Opportunity Serializers & ViewSets
# ---------------------------------------------------------------------------

class OpportunityContactsSerializer(TenantModelSerializer):
    """Nested serializer for OpportunityContacts."""

    contact_person = serializers.CharField(
        source='contact.person.__str__',
        read_only=True,
    )
    contact_role = serializers.CharField(
        source='contact.role_title',
        read_only=True,
    )

    class Meta:
        model = OpportunityContacts
        fields = TenantModelSerializer.Meta.fields + [
            'opportunity',
            'contact',
            'contact_person',
            'contact_role',
            'customer',
            'role_in_opportunity',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'contact_person',
            'contact_role',
        ]


class OpportunityContactsViewSet(TenantModelViewSet):
    """ViewSet for OpportunityContacts (M2M junction)."""

    queryset = OpportunityContacts.objects.all()
    serializer_class = OpportunityContactsSerializer
    filterset_fields = ['opportunity_id', 'contact_id', 'customer_id']
    search_fields = ['role_in_opportunity', 'contact__person__first_name', 'contact__person__last_name']
    ordering_fields = ['created_on', 'role_in_opportunity']


class OpportunitySerializer(TenantModelSerializer):
    """Serializer for Opportunity model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
    )
    lead_name = serializers.CharField(
        source='lead.__str__',
        read_only=True,
        allow_null=True,
    )
    assigned_to_username = serializers.CharField(
        source='assigned_to.username',
        read_only=True,
        allow_null=True,
    )
    # Nested contacts for read operations
    opportunity_contacts = OpportunityContactsSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Opportunity
        fields = TenantModelSerializer.Meta.fields + [
            'opportunity_number',
            'customer',
            'customer_name',
            'lead',
            'lead_name',
            'name',
            'status',
            'estimated_value',
            'actual_value',
            'probability',
            'expected_close_date',
            'assigned_to',
            'assigned_to_username',
            'next_step',
            'competitor',
            'notes',
            'tags',
            'won_at',
            'lost_at',
            'lost_reason',
            'opportunity_contacts',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'opportunity_number',
            'customer_name',
            'lead_name',
            'assigned_to_username',
            'opportunity_contacts',
            # Lifecycle-managed denormalized fields.
            'won_at', 'lost_at', 'lost_reason',
        ]


class OpportunityViewSet(TenantModelViewSet):
    """ViewSet for Opportunity CRUD operations."""

    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    filterset_fields = ['status', 'customer_id', 'lead_id', 'assigned_to_id']
    search_fields = ['name', 'opportunity_number', 'customer__company_name']
    ordering_fields = ['created_on', 'name', 'status', 'estimated_value',
                       'actual_value', 'probability', 'expected_close_date']


# ---------------------------------------------------------------------------
# Router Setup
# ---------------------------------------------------------------------------

router = DefaultRouter()
router.register(r'persons', PersonViewSet, basename='person')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'phones', PhoneViewSet, basename='phone')
router.register(r'socials', SocialViewSet, basename='social')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'opportunity-contacts', OpportunityContactsViewSet, basename='opportunity-contacts')
