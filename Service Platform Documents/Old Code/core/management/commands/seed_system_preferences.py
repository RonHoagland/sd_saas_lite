from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings
import os
from core.models import Preference

class Command(BaseCommand):
    help = 'Seeds essential system preferences with default values.'

    def handle(self, *args, **options):
        User = get_user_model()
        # Ensure we have a system user for 'created_by'
        system_user, _ = User.objects.get_or_create(username='system')
        
        # Calculate dynamic paths
        backup_path = os.path.join(settings.BASE_DIR, 'backups')
        docs_path = os.path.join(settings.BASE_DIR, 'docs')
        logos_path = os.path.join(settings.MEDIA_ROOT, 'logos')
        
        defaults = [
            # General
            ('general_site_name', 'BrixaWares Platform', 'string', 'Site Name', 'The name of the application displayed in the header.', 'General', False, False, ''),
            ('general_admin_email', 'admin@example.com', 'string', 'Admin Email', 'Primary contact email for system notifications.', 'General', False, False, 'email'),
            
            # Localization
            ('l10n_timezone', 'America/Chicago', 'string', 'System Timezone', 'Timezone for displayed dates and times.', 'Localization', False, False, 'timezone'),
            ('l10n_date_format', 'YYYY-MM-DD', 'string', 'Date Format', 'Display format for dates.', 'Localization', False, False, 'date_format'),
            ('l10n_time_format', 'HH:MM:SS', 'string', 'Time Format', 'Display format for times.', 'Localization', False, False, 'time_format'),
            ('l10n_currency', 'USD', 'string', 'Currency', 'Default currency code (ISO 4217).', 'Localization', False, False, 'currency'),
            
            # Branding / UI
            ('ui_theme_color', '#2563eb', 'string', 'Primary Theme Color', 'Main color used for buttons and highlights.', 'Branding', False, False, 'color'),
            ('ui_logo_url', '/static/img/logo.png', 'text', 'Logo URL', 'Path to the organization logo.', 'Branding', False, False, 'file_upload'),
            
            # Company Information
            ('company_name', 'BrixaWares Inc.', 'string', 'Company Name', 'Legal name of the organization.', 'Company Information', False, False, ''),
            ('company_address', '123 Tech Blvd, Innovation City', 'string', 'Company Address', 'Physical address displayed on reports/invoices.', 'Company Information', False, False, 'textarea'),
            ('company_phone', '+1-555-0100', 'string', 'Company Phone', 'Primary contact number.', 'Company Information', False, False, ''),
            ('company_email', 'contact@brixawares.com', 'string', 'Company Email', 'Public contact email.', 'Company Information', False, False, 'email'),
            ('company_website', 'https://www.brixawares.com', 'string', 'Company Website', 'Official website URL.', 'Company Information', False, False, 'url'),

            # Security
            ('security_session_timeout', '60', 'integer', 'Session Timeout', 'User session timeout in minutes.', 'Security', False, False, ''),
            ('security_password_min_length', '8', 'integer', 'Min Password Length', 'Minimum required characters for user passwords.', 'Security', False, False, ''),
            
            # Email Configuration
            ('email_host', 'smtp.example.com', 'string', 'SMTP Host', 'Mail server address.', 'Email Configuration', False, False, ''),
            ('email_port', '587', 'integer', 'SMTP Port', 'Mail server port (e.g., 587, 465).', 'Email Configuration', False, False, ''),
            ('email_host_user', 'apikey', 'string', 'SMTP User', 'Username for SMTP authentication.', 'Email Configuration', False, False, ''),
            ('security_smtp_password', '', 'password', 'SMTP Password', 'Password for email server.', 'Email Configuration', True, False, ''),
            ('email_use_tls', 'true', 'boolean', 'Use TLS', 'Enable Transport Layer Security.', 'Email Configuration', False, False, ''),
            ('email_from_address', 'system@brixawares.com', 'string', 'Default From Address', 'Default sender address for system emails.', 'Email Configuration', False, False, 'email'),
            
            # System paths (LOCKED per User Requirement)
            ('system_backup_path', backup_path, 'path', 'Backup Directory', 'Local filesystem path for storing backups.', 'System', False, True, ''),
            ('system_upload_path', docs_path, 'path', 'Documents Directory', 'Root path for document storage (docs/<table_name>/<id>/<filename>).', 'System', False, True, ''),
            ('system_logos_path', logos_path, 'path', 'Logos Directory', 'Storage path for system logos.', 'System', False, True, ''),
        ]
        
        created_count = 0
        updated_count = 0
        
        for key, val, dtype, name, desc, group, secret, locked, ui_hint in defaults:
            # We want to UPDATE existing ones too if they were missing new fields
            pref, created = Preference.objects.update_or_create(
                key=key,
                defaults={
                    'value': val,
                    'default_value': val,
                    'data_type': dtype,
                    'name': name,
                    'description': desc,
                    'preference_group': group,
                    'is_secret': secret,
                    'is_locked': locked,
                    'input_type': ui_hint,
                    'created_by': system_user,
                    'updated_by': system_user,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created: {name} ({key})"))
                created_count += 1
            else:
                self.stdout.write(f"Updated: {name} ({key})")
                updated_count += 1
                
        self.stdout.write(self.style.SUCCESS(f"Preference seeding complete. Created: {created_count}, Updated: {updated_count}"))
