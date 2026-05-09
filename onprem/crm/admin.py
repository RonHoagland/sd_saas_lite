# crm/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from crm.models import (
    Person, Customer, Contact, Address, Phone, Social,
    Lead, Opportunity, OpportunityContacts,
)


@admin.register(Person)
class PersonAdmin(TenantModelAdmin):
    list_display = ('first_name', 'last_name', 'tenant_id')
    search_fields = ('first_name', 'last_name')


@admin.register(Customer)
class CustomerAdmin(TenantModelAdmin):
    list_display = ('customer_number', 'company_name', 'account_type',
                    'status', 'tenant_id', 'created_on')
    list_filter = ('tenant_id', 'status', 'account_type', 'credit_status')
    search_fields = ('customer_number', 'company_name', 'account_number')


@admin.register(Contact)
class ContactAdmin(TenantModelAdmin):
    list_display = ('person', 'customer', 'is_primary', 'status', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'is_primary')


@admin.register(Address)
class AddressAdmin(TenantModelAdmin):
    list_display = ('street', 'city', 'state', 'address_type', 'is_primary',
                    'tenant_id')
    list_filter = ('tenant_id', 'address_type')
    search_fields = ('street', 'city', 'zip')


@admin.register(Phone)
class PhoneAdmin(TenantModelAdmin):
    list_display = ('number', 'phone_type', 'is_primary', 'tenant_id')
    list_filter = ('tenant_id', 'phone_type')
    search_fields = ('number',)


@admin.register(Social)
class SocialAdmin(TenantModelAdmin):
    list_display = ('type', 'value', 'tenant_id')
    list_filter = ('tenant_id', 'type')


@admin.register(Lead)
class LeadAdmin(TenantModelAdmin):
    list_display = ('lead_number', 'first_name', 'last_name', 'status',
                    'source', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'source')
    search_fields = ('lead_number', 'first_name', 'last_name', 'email')


@admin.register(Opportunity)
class OpportunityAdmin(TenantModelAdmin):
    list_display = ('opportunity_number', 'name', 'status', 'estimated_value',
                    'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('opportunity_number', 'name')


@admin.register(OpportunityContacts)
class OpportunityContactsAdmin(TenantModelAdmin):
    list_display = ('opportunity', 'contact', 'role_in_opportunity', 'tenant_id')
