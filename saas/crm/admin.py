# crm/admin.py
from django.contrib import admin
from staff.admin import TenantModelAdmin
from crm.models import (
    Person, Customer, Account, Contact, Address, Phone, Social,
    Lead, Opportunity, OpportunityContacts,
)


@admin.register(Person)
class PersonAdmin(TenantModelAdmin):
    list_display = ('first_name', 'last_name', 'preferred_name', 'prefix',
                    'suffix', 'tenant_id')
    list_filter = ('tenant_id', 'prefix', 'suffix')
    search_fields = ('first_name', 'middle_name', 'last_name', 'preferred_name')


@admin.register(Customer)
class CustomerAdmin(TenantModelAdmin):
    list_display = ('customer_number', 'company_name', 'account_type',
                    'status', 'industry', 'tenant_id', 'created_on')
    list_filter = ('tenant_id', 'status', 'account_type', 'industry',
                   'do_not_contact')
    search_fields = ('customer_number', 'company_name', 'display_name',
                     'account_number', 'external_id')
    raw_id_fields = ('primary_person', 'preferred_technician', 'portal_user',
                     'assigned_to')


@admin.register(Account)
class AccountAdmin(TenantModelAdmin):
    list_display = ('customer', 'account_terms', 'credit_limit', 'credit_status',
                    'pricing_tier', 'discount_percentage', 'po_required',
                    'tax_exempt', 'tenant_id')
    list_filter = ('tenant_id', 'credit_status', 'tax_exempt', 'po_required')
    search_fields = ('customer__customer_number', 'customer__company_name',
                     'customer__account_number')
    raw_id_fields = ('customer',)


@admin.register(Contact)
class ContactAdmin(TenantModelAdmin):
    list_display = ('person', 'customer', 'role_title', 'is_primary',
                    'is_decision_maker', 'is_billing_contact', 'status',
                    'tenant_id')
    list_filter = ('tenant_id', 'status', 'is_primary', 'is_decision_maker',
                   'is_billing_contact', 'is_technical_contact',
                   'is_emergency_contact')
    search_fields = ('person__first_name', 'person__last_name',
                     'role_title', 'department')
    raw_id_fields = ('person', 'customer', 'vendor', 'bank', 'reports_to')


@admin.register(Address)
class AddressAdmin(TenantModelAdmin):
    list_display = ('street', 'city', 'state_code', 'country_code',
                    'address_type', 'is_primary', 'is_verified', 'tenant_id')
    list_filter = ('tenant_id', 'address_type', 'is_verified', 'country_code')
    search_fields = ('street', 'street_2', 'city', 'zip')


@admin.register(Phone)
class PhoneAdmin(TenantModelAdmin):
    list_display = ('country_code', 'number', 'phone_type', 'is_primary',
                    'sms_capable', 'is_verified', 'tenant_id')
    list_filter = ('tenant_id', 'phone_type', 'sms_capable', 'is_verified')
    search_fields = ('number',)


@admin.register(Social)
class SocialAdmin(TenantModelAdmin):
    list_display = ('type', 'value', 'tenant_id')
    list_filter = ('tenant_id', 'type')


@admin.register(Lead)
class LeadAdmin(TenantModelAdmin):
    list_display = ('lead_number', 'person', 'customer', 'status',
                    'source', 'assigned_to', 'lead_score', 'tenant_id')
    list_filter = ('tenant_id', 'status', 'source')
    search_fields = ('lead_number', 'person__first_name', 'person__last_name',
                     'customer__company_name')
    raw_id_fields = ('customer', 'person', 'assigned_to')


@admin.register(Opportunity)
class OpportunityAdmin(TenantModelAdmin):
    list_display = ('opportunity_number', 'name', 'status', 'estimated_value',
                    'actual_value', 'probability', 'assigned_to', 'tenant_id')
    list_filter = ('tenant_id', 'status')
    search_fields = ('opportunity_number', 'name', 'competitor')
    raw_id_fields = ('customer', 'lead', 'assigned_to')


@admin.register(OpportunityContacts)
class OpportunityContactsAdmin(TenantModelAdmin):
    list_display = ('opportunity', 'contact', 'role_in_opportunity', 'tenant_id')
