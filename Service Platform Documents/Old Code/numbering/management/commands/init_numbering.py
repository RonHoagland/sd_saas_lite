"""
Management command to initialize default numbering rules for all business entities.

Per Platform Core Numbering specification: Rules define format, prefix, and reset behavior.

Usage:
    python manage.py init_numbering
"""

from django.core.management.base import BaseCommand
from numbering.models import NumberingRule


class Command(BaseCommand):
    help = 'Initialize default numbering rules for all business entities'

    def handle(self, *args, **options):
        """Create default numbering rules for all entity types."""
        
        # Get a system user for audit fields
        from django.contrib.auth import get_user_model
        User = get_user_model()
        system_user = User.objects.filter(is_superuser=True).first()
        
        if not system_user:
            self.stdout.write(
                self.style.ERROR(
                    '❌ No superuser found. Please create a superuser first:\n'
                    '   python manage.py createsuperuser'
                )
            )
            return
        
        # Define default rules per entity type
        rules = [
            # Base Models
            {
                'entity_type': 'client',
                'prefix': 'CLI',
                'sequence_length': 4,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Client numbering (CLI260001)',
            },
            {
                'entity_type': 'product',
                'prefix': '', # No prefix, uses Alpha Year
                'sequence_length': 4,
                'include_year': False, # Handled by custom format
                'include_month': False,
                'year_format': 'YY', # Placeholder, not used but required by loop
                'reset_behavior': 'yearly',
                'custom_format': 'alpha_year',
                'description': 'Product numbering (BF0001)',
            },
            
            # Projects Module
            {
                'entity_type': 'project',
                'prefix': 'PRJ',
                'sequence_length': 5,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Project numbering (PRJ2600001)',
            },
            {
                'entity_type': 'task',
                'prefix': 'TSK',
                'sequence_length': 5,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Task numbering (TSK2600001)',
            },
            
            # Invoicing Module
            {
                'entity_type': 'invoice',
                'prefix': 'INV',
                'sequence_length': 6,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Invoice numbering (INV26000001)',
            },
            
            # Service Module
            {
                'entity_type': 'serviceitem',
                'prefix': 'SRV',
                'sequence_length': 4,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Service item numbering (SRV260001)',
            },
            {
                'entity_type': 'workorder',
                'prefix': 'WOR',
                'sequence_length': 6,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Work order numbering (WOR26000001)',
            },
            
            # Sales Module
            {
                'entity_type': 'lead',
                'prefix': 'LED',
                'sequence_length': 5,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Lead numbering (LED2600001)',
            },
            {
                'entity_type': 'quote',
                'prefix': 'QOT',
                'sequence_length': 5,
                'include_year': True,
                'include_month': False,
                'year_format': 'YY',  # Last 2 digits
                'reset_behavior': 'yearly',
                'description': 'Quote numbering (QOT2600001)',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for rule_data in rules:
            # Prepare defaults with audit fields
            defaults = {
                'prefix': rule_data['prefix'],
                'sequence_length': rule_data['sequence_length'],
                'include_year': rule_data['include_year'],
                'include_month': rule_data['include_month'],
                'year_format': rule_data['year_format'],
                'reset_behavior': rule_data['reset_behavior'],
                'description': rule_data['description'],
                'is_enabled': True,
                'delimiter': '',
                'created_by': system_user,
                'updated_by': system_user,
                'custom_format': rule_data.get('custom_format'),
            }
            
            rule, created = NumberingRule.objects.update_or_create(
                entity_type=rule_data['entity_type'],
                defaults=defaults
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {rule.entity_type} → {rule.prefix}-...')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'• Updated: {rule.entity_type}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Numbering initialization complete: '
                f'{created_count} created, {updated_count} updated'
            )
        )
