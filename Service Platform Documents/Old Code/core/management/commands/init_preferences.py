from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Preference

class Command(BaseCommand):
    help = 'Initializes the standard set of system preferences.'

    def handle(self, *args, **options):
        self.stdout.write('Initializing system preferences...')
        
        system_user, _ = User.objects.get_or_create(username='system', defaults={'is_active': False})
        
        # Define standard preferences based on preferences_functionality.md
        # (key, value, type, name, description)
        defaults = [
            # General / Company
            ('company_name', 'BrixaWares', 'string', 'Company Name', 'Name of the organization using the platform'),
            ('company_address_1', '', 'string', 'Address Line 1', 'Primary address line'),
            ('company_address_2', '', 'string', 'Address Line 2', 'Secondary address line (Suite, Floor, etc.)'),
            ('company_city', '', 'string', 'City', 'City'),
            ('company_state', '', 'string', 'State/Province', 'State or Province'),
            ('company_postalcode', '', 'string', 'Postal Code', 'ZIP or Postal Code'),
            ('company_country', '', 'string', 'Country', 'Country Name'),
            ('company_phone', '', 'string', 'Company Phone', 'Contact number for reports'),
            ('company_website', '', 'string', 'Company Website', 'Main website URL'),
            ('company_logo_print', '', 'path', 'Print Logo', 'Path/URL to high-res logo for printed documents (300x100px)'),
            ('company_logo_digital', '', 'path', 'Digital Logo', 'Path/URL to screen logo (150x75px)'),
            ('default_logo_height', '50', 'integer', 'Default Logo Height', 'Logo height in pixels for layout'),

            # Financial & Localization
            ('finance_default_currency', 'USD', 'string', 'Default Currency', 'Default currency code (e.g. USD, EUR)'),
            ('finance_currency_symbol', '$', 'string', 'Currency Symbol', 'Symbol for currency display (e.g. $)'),
            ('finance_tax_rate', '0.00', 'decimal', 'Global Tax Rate', 'Default system tax rate percentage'),
            ('finance_tax_label', 'Tax', 'string', 'Tax Label', 'Label for tax on invoices (e.g. VAT, Sales Tax)'),
            ('finance_decimal_precision', '2', 'integer', 'Decimal Precision', 'Number of decimal places for currency'),
            ('loc_default_country', 'US', 'string', 'Default Country', 'ISO code for default country selection'),
            ('loc_default_phone_code', '1', 'string', 'Default Phone Code', 'Country calling code (e.g. 1, 63)'),
            ('loc_default_phone_format', '+1 (XXX) XXX-XXXX', 'string', 'Phone Format', 'Display format mask for phone numbers'),
            ('loc_date_format', 'MM/DD/YYYY', 'string', 'Date Format', 'System-wide date display format'),
            ('loc_timezone', 'America/Chicago', 'string', 'Time Zone', 'System default time zone'),
            ('site_title', 'BrixaWares Platform', 'string', 'Site Title', 'Browser tab title'), # Kept as it is standard

            # Brand Colors
            ('ui_theme_color', '#1e3a8a', 'string', 'Theme Color', 'Primary color for sidebar and headers'),

            # Email Configuration
            ('email_from_address', 'noreply@brixawares.com', 'string', 'From Email Address', 'Default sender address for system emails'),
            ('email_smtp_host', 'smtp.example.com', 'string', 'SMTP Host', 'Mail server hostname'),
            ('email_smtp_port', '587', 'integer', 'SMTP Port', 'Mail server port'),
            ('email_smtp_user', '', 'string', 'SMTP Username', 'Username for SMTP authentication'),
            ('email_smtp_password', '', 'password', 'SMTP Password', 'Password for SMTP authentication'),
            ('email_use_tls', 'true', 'boolean', 'Use TLS', 'Enable Transport Layer Security'),
            ('email_use_ssl', 'false', 'boolean', 'Use SSL', 'Enable Secure Sockets Layer'),

            # Backup & Retention (Updated Spec - Managed in Backup App)
             # REMOVED: backup_retention_days, backup_storage_path, backup_schedule_time, backup_scope, audit_log_retention_days
        ]

        # 1. UPSERT (Create or Update)
        created_count = 0
        updated_count = 0
        current_keys = set()

        for config in defaults:
            # Unpack with flexibility for optional is_editable
            if len(config) == 6:
                key, val, dtype, name, desc, editable = config
            else:
                key, val, dtype, name, desc = config
                editable = True # Default
                
            current_keys.add(key)
            obj, created = Preference.objects.get_or_create(
                key=key,
                defaults={
                    'value': val,
                    'default_value': val,
                    'data_type': dtype,
                    'name': name,
                    'description': desc,
                    'created_by': system_user,
                    'updated_by': system_user,
                    'is_editable': editable
                }
            )
            
            if created:
                created_count += 1
            else:
                # Update metadata if it changed (name, desc, type, is_editable)
                updated = False
                if obj.name != name: obj.name = name; updated = True
                if obj.description != desc: obj.description = desc; updated = True
                if obj.data_type != dtype: obj.data_type = dtype; updated = True
                if obj.is_editable != editable: obj.is_editable = editable; updated = True
                
                if updated:
                    obj.save()
                    updated_count += 1
        
        # 2. CLEANUP (Remove obsolete keys)
        # Find all keys in DB that are NOT in our defaults list
        obsolete_prefs = Preference.objects.exclude(key__in=current_keys)
        deleted_count = obsolete_prefs.count()
        if deleted_count > 0:
            self.stdout.write(f"Removing {deleted_count} obsolete preferences...")
            obsolete_prefs.delete()

        self.stdout.write(self.style.SUCCESS(f'Successfully processed preferences. Created: {created_count}, Updated: {updated_count}, Deleted: {deleted_count}'))
