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

    class Meta:
        model = Person
        fields = TenantModelSerializer.Meta.fields + [
            'first_name',
            'last_name',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields


class PersonViewSet(TenantModelViewSet):
    """ViewSet for Person CRUD operations."""

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    filterset_fields = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']
    ordering_fields = ['created_on', 'last_name', 'first_name']


# ---------------------------------------------------------------------------
# Customer Serializers & ViewSets
# ---------------------------------------------------------------------------

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

    class Meta:
        model = Customer
        fields = TenantModelSerializer.Meta.fields + [
            'customer_number',
            'status',
            'account_type',
            'company_name',
            'assigned_to',
            'assigned_to_id',
            'assigned_to_username',
            'lead_source',
            'tax_exempt',
            'customer_since',
            'hold_date',
            'hold_reason',
            'closed_at',
            'closed_reason',
            'account_number',
            'account_terms',
            'credit_limit',
            'credit_status',
            'tax_rate',
            'tags',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'customer_number',
            'assigned_to_id',
            'assigned_to_username',
        ]


class CustomerViewSet(TenantModelViewSet):
    """ViewSet for Customer CRUD operations."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ['status', 'account_type', 'credit_status', 'assigned_to_id']
    search_fields = ['company_name', 'customer_number', 'account_number']
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
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'person_name',
            'customer_name',
        ]


class ContactViewSet(TenantModelViewSet):
    """ViewSet for Contact CRUD operations."""

    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    filterset_fields = ['status', 'is_primary', 'customer_id', 'person_id']
    search_fields = ['person__first_name', 'person__last_name', 'role_title']
    ordering_fields = ['created_on', 'person__last_name', 'is_primary']


# ---------------------------------------------------------------------------
# Address Serializers & ViewSets
# ---------------------------------------------------------------------------

class AddressSerializer(TenantModelSerializer):
    """Serializer for Address model."""

    full_address = serializers.SerializerMethodField(read_only=True)

    def get_full_address(self, obj):
        parts = [obj.street, obj.city, obj.state, obj.zip, obj.country]
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
            'city',
            'state',
            'zip',
            'country',
            'full_address',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'full_address',
        ]


class AddressViewSet(TenantModelViewSet):
    """ViewSet for Address CRUD operations."""

    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    filterset_fields = ['address_type', 'is_primary', 'customer_id', 'contact_id']
    search_fields = ['street', 'city', 'state', 'zip']
    ordering_fields = ['created_on', 'city', 'address_type']


# ---------------------------------------------------------------------------
# Phone Serializers & ViewSets
# ---------------------------------------------------------------------------

class PhoneSerializer(TenantModelSerializer):
    """Serializer for Phone model."""

    full_number = serializers.SerializerMethodField(read_only=True)

    def get_full_number(self, obj):
        if obj.extension:
            return f'{obj.number} x{obj.extension}'
        return obj.number

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
            'number',
            'is_primary',
            'extension',
            'full_number',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'full_number',
        ]


class PhoneViewSet(TenantModelViewSet):
    """ViewSet for Phone CRUD operations."""

    queryset = Phone.objects.all()
    serializer_class = PhoneSerializer
    filterset_fields = ['phone_type', 'is_primary', 'customer_id', 'contact_id']
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
    """Serializer for Lead model."""

    customer_name = serializers.CharField(
        source='customer.company_name',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = Lead
        fields = TenantModelSerializer.Meta.fields + [
            'lead_number',
            'customer',
            'customer_name',
            'first_name',
            'last_name',
            'phone',
            'email',
            'source',
            'status',
            'notes',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'lead_number',
            'customer_name',
        ]


class LeadViewSet(TenantModelViewSet):
    """ViewSet for Lead CRUD operations."""

    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filterset_fields = ['status', 'source', 'customer_id']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'lead_number']
    ordering_fields = ['created_on', 'last_name', 'status', 'first_name']


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
            'expected_close_date',
            'assigned_to',
            'assigned_to_username',
            'notes',
            'opportunity_contacts',
        ]
        read_only_fields = TenantModelSerializer.Meta.read_only_fields + [
            'opportunity_number',
            'customer_name',
            'lead_name',
            'assigned_to_username',
            'opportunity_contacts',
        ]


class OpportunityViewSet(TenantModelViewSet):
    """ViewSet for Opportunity CRUD operations."""

    queryset = Opportunity.objects.all()
    serializer_class = OpportunitySerializer
    filterset_fields = ['status', 'customer_id', 'lead_id', 'assigned_to_id']
    search_fields = ['name', 'opportunity_number', 'customer__company_name']
    ordering_fields = ['created_on', 'name', 'status', 'estimated_value', 'expected_close_date']


# ---------------------------------------------------------------------------
# Router Setup
# ---------------------------------------------------------------------------

router = DefaultRouter()
router.register(r'persons', PersonViewSet, basename='person')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'phones', PhoneViewSet, basename='phone')
router.register(r'socials', SocialViewSet, basename='social')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'opportunities', OpportunityViewSet, basename='opportunity')
router.register(r'opportunity-contacts', OpportunityContactsViewSet, basename='opportunity-contacts')
