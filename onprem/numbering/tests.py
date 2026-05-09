# numbering/tests.py
# Comprehensive tests for the numbering service.
# Source: Numbering Service Specification V1.

import uuid
from datetime import date
from django.core.exceptions import ValidationError
from django.utils import timezone
from tests.base import SDTATestCase
from .models import NumberingRule, NumberSequence, AssignedNumber
from .services import (
    generate_number,
    get_next_sequence_value,
    check_reset_needed,
    format_number,
    assign_number,
    get_assigned_number,
    has_assigned_number,
    compute_inventory_item_prefix,
)
from .exceptions import (
    NoRuleDefinedError,
    NumberingDisabledError,
    DuplicateAssignmentError,
)


class NumberingRuleTests(SDTATestCase):
    """Test NumberingRule model and creation."""

    def test_create_numbering_rule(self):
        """Test basic rule creation."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            is_enabled=True,
            prefix='C',
            include_year=True,
            year_format='YY',
            include_month=False,
            sequence_length=4,
            delimiter='-',
            reset_behavior='yearly',
        )
        self.assertEqual(rule.entity_type, 'customer')
        self.assertEqual(rule.prefix, 'C')
        self.assertTrue(rule.is_enabled)

    def test_unique_constraint_entity_type_per_tenant(self):
        """Test that entity_type must be unique per tenant."""
        NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        with self.assertRaises(Exception):  # IntegrityError
            NumberingRule.objects.create(
                tenant_id=self.tenant_id,
                entity_type='customer',
                prefix='C2',
            )

    def test_rule_str(self):
        """Test string representation of rule."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='work_order',
            prefix='WO',
        )
        self.assertEqual(str(rule), 'work_order (WO)')


class NumberSequenceTests(SDTATestCase):
    """Test NumberSequence model and get_or_create logic."""

    def test_create_sequence(self):
        """Test creating a NumberSequence."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        sequence = NumberSequence.objects.create(rule=rule)
        self.assertEqual(sequence.current_value, 0)
        self.assertIsNone(sequence.last_reset_date)

    def test_get_or_create_sequence(self):
        """Test get_or_create for sequence."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        seq1, created1 = NumberSequence.objects.get_or_create(rule=rule)
        self.assertTrue(created1)
        seq2, created2 = NumberSequence.objects.get_or_create(rule=rule)
        self.assertFalse(created2)
        self.assertEqual(seq1.id, seq2.id)


class FormatNumberTests(SDTATestCase):
    """Test format_number function with various configurations."""

    def test_format_prefix_only(self):
        """Test formatting with prefix only."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
            include_month=False,
        )
        formatted = format_number(rule, 1)
        self.assertEqual(formatted, 'C-0001')

    def test_format_prefix_with_year_yy(self):
        """Test formatting with prefix and year (YY)."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=True,
            year_format='YY',
            include_month=False,
        )
        formatted = format_number(rule, 42)
        # Year will be current year in YY format
        year_str = timezone.now().strftime('%y')
        self.assertEqual(formatted, f'C-{year_str}-0042')

    def test_format_prefix_with_year_yyyy(self):
        """Test formatting with prefix and year (YYYY)."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=True,
            year_format='YYYY',
            include_month=False,
        )
        formatted = format_number(rule, 123)
        year_str = timezone.now().strftime('%Y')
        self.assertEqual(formatted, f'C-{year_str}-0123')

    def test_format_prefix_with_year_and_month(self):
        """Test formatting with prefix, year, and month."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=True,
            year_format='YY',
            include_month=True,
        )
        formatted = format_number(rule, 7)
        year_str = timezone.now().strftime('%y')
        month_str = timezone.now().strftime('%m')
        self.assertEqual(formatted, f'C-{year_str}-{month_str}-0007')

    def test_format_custom_delimiter(self):
        """Test formatting with custom delimiter."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='SR',
            include_year=True,
            year_format='YY',
            delimiter='_',
        )
        formatted = format_number(rule, 99)
        year_str = timezone.now().strftime('%y')
        self.assertEqual(formatted, f'SR_{year_str}_0099')

    def test_format_custom_sequence_length(self):
        """Test formatting with different sequence length."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
            sequence_length=6,
        )
        formatted = format_number(rule, 42)
        self.assertEqual(formatted, 'C-000042')


class GenerateNumberTests(SDTATestCase):
    """Test generate_number service function."""

    def test_generate_number_success(self):
        """Test successful number generation."""
        NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
        )
        number = generate_number(self.tenant_id, 'customer')
        self.assertEqual(number, 'C-0001')

    def test_generate_number_no_rule(self):
        """Test that NoRuleDefinedError is raised when rule doesn't exist."""
        with self.assertRaises(NoRuleDefinedError):
            generate_number(self.tenant_id, 'nonexistent')

    def test_generate_number_disabled_rule(self):
        """Test that NumberingDisabledError is raised when rule is disabled."""
        NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            is_enabled=False,
        )
        with self.assertRaises(NumberingDisabledError):
            generate_number(self.tenant_id, 'customer')

    def test_generate_multiple_numbers_increments(self):
        """Test that multiple calls increment the sequence."""
        NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
        )
        num1 = generate_number(self.tenant_id, 'customer')
        num2 = generate_number(self.tenant_id, 'customer')
        num3 = generate_number(self.tenant_id, 'customer')

        self.assertEqual(num1, 'C-0001')
        self.assertEqual(num2, 'C-0002')
        self.assertEqual(num3, 'C-0003')


class CheckResetNeededTests(SDTATestCase):
    """Test check_reset_needed logic."""

    def test_reset_behavior_none(self):
        """Test that 'none' behavior never resets."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='none',
        )
        sequence = NumberSequence.objects.create(rule=rule, current_value=99)
        sequence.last_reset_date = date(2020, 1, 1)
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 99)
        self.assertEqual(sequence.last_reset_date, date(2020, 1, 1))

    def test_reset_behavior_yearly_first_time(self):
        """Test yearly reset on first call (no last_reset_date)."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='yearly',
        )
        sequence = NumberSequence.objects.create(rule=rule, current_value=50)
        sequence.last_reset_date = None
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 0)
        self.assertEqual(sequence.last_reset_date, timezone.now().date())

    def test_reset_behavior_yearly_same_year(self):
        """Test yearly reset does not trigger if still in same year."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='yearly',
        )
        today = timezone.now().date()
        sequence = NumberSequence.objects.create(
            rule=rule, current_value=50, last_reset_date=today
        )
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 50)
        self.assertEqual(sequence.last_reset_date, today)

    def test_reset_behavior_yearly_different_year(self):
        """Test yearly reset triggers when year changes."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='yearly',
        )
        sequence = NumberSequence.objects.create(
            rule=rule, current_value=50, last_reset_date=date(2020, 6, 15)
        )
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 0)
        self.assertEqual(sequence.last_reset_date, timezone.now().date())

    def test_reset_behavior_monthly_first_time(self):
        """Test monthly reset on first call."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='monthly',
        )
        sequence = NumberSequence.objects.create(rule=rule, current_value=50)
        sequence.last_reset_date = None
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 0)
        self.assertEqual(sequence.last_reset_date, timezone.now().date())

    def test_reset_behavior_monthly_same_month(self):
        """Test monthly reset does not trigger if still in same month/year."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='monthly',
        )
        today = timezone.now().date()
        sequence = NumberSequence.objects.create(
            rule=rule, current_value=50, last_reset_date=today
        )
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 50)
        self.assertEqual(sequence.last_reset_date, today)

    def test_reset_behavior_monthly_different_month(self):
        """Test monthly reset triggers when month changes."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            reset_behavior='monthly',
        )
        sequence = NumberSequence.objects.create(
            rule=rule, current_value=50, last_reset_date=date(2026, 1, 15)
        )
        # Assuming current month is not January 2026
        check_reset_needed(sequence, rule)
        self.assertEqual(sequence.current_value, 0)
        self.assertEqual(sequence.last_reset_date, timezone.now().date())


class AssignNumberTests(SDTATestCase):
    """Test assign_number service function."""

    def test_assign_number_creates_record(self):
        """Test that assign_number creates an AssignedNumber record."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
        )
        entity_id = uuid.uuid4()
        assigned = assign_number(self.tenant_id, 'customer', entity_id, 'user@test.com')

        self.assertIsNotNone(assigned)
        self.assertEqual(assigned.number, 'C-0001')
        self.assertEqual(assigned.entity_id, entity_id)
        self.assertEqual(assigned.assigned_by, 'user@test.com')

    def test_assign_number_duplicate_error(self):
        """Test that assigning twice raises DuplicateAssignmentError."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
        )
        entity_id = uuid.uuid4()
        assign_number(self.tenant_id, 'customer', entity_id)

        with self.assertRaises(DuplicateAssignmentError):
            assign_number(self.tenant_id, 'customer', entity_id)

    def test_assign_number_no_rule(self):
        """Test that assigning without rule raises NoRuleDefinedError."""
        entity_id = uuid.uuid4()
        with self.assertRaises(NoRuleDefinedError):
            assign_number(self.tenant_id, 'nonexistent', entity_id)


class AssignedNumberImmutabilityTests(SDTATestCase):
    """Test immutability of AssignedNumber records."""

    def test_assigned_number_cannot_be_saved_after_creation(self):
        """Test that save() raises ValidationError on existing records."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        assigned = AssignedNumber.objects.create(
            tenant_id=self.tenant_id,
            rule=rule,
            entity_type='customer',
            entity_id=uuid.uuid4(),
            number='C-0001',
            assigned_by='System',
        )
        # Try to modify
        assigned.assigned_by = 'Someone Else'
        with self.assertRaises(ValidationError):
            assigned.save()

    def test_assigned_number_cannot_be_deleted(self):
        """Test that delete() always raises ValidationError."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        assigned = AssignedNumber.objects.create(
            tenant_id=self.tenant_id,
            rule=rule,
            entity_type='customer',
            entity_id=uuid.uuid4(),
            number='C-0001',
            assigned_by='System',
        )
        with self.assertRaises(ValidationError):
            assigned.delete()


class GetAssignedNumberTests(SDTATestCase):
    """Test get_assigned_number and has_assigned_number."""

    def test_get_assigned_number_returns_number(self):
        """Test retrieving an assigned number."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            include_year=False,
        )
        entity_id = uuid.uuid4()
        assign_number(self.tenant_id, 'customer', entity_id)

        number = get_assigned_number(self.tenant_id, 'customer', entity_id)
        self.assertEqual(number, 'C-0001')

    def test_get_assigned_number_returns_none(self):
        """Test retrieving when no number assigned."""
        entity_id = uuid.uuid4()
        number = get_assigned_number(self.tenant_id, 'customer', entity_id)
        self.assertIsNone(number)

    def test_has_assigned_number_returns_true(self):
        """Test has_assigned_number when assigned."""
        rule = NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
        )
        entity_id = uuid.uuid4()
        assign_number(self.tenant_id, 'customer', entity_id)

        has_it = has_assigned_number(self.tenant_id, 'customer', entity_id)
        self.assertTrue(has_it)

    def test_has_assigned_number_returns_false(self):
        """Test has_assigned_number when not assigned."""
        entity_id = uuid.uuid4()
        has_it = has_assigned_number(self.tenant_id, 'customer', entity_id)
        self.assertFalse(has_it)


class ComputeInventoryItemPrefixTests(SDTATestCase):
    """Test compute_inventory_item_prefix function."""

    def test_inventory_prefix_2026(self):
        """Test 2026 → YU (2→Y, 6→U)."""
        prefix = compute_inventory_item_prefix(year=2026)
        self.assertEqual(prefix, 'YU')

    def test_inventory_prefix_2027(self):
        """Test 2027 → YT (2→Y, 7→T)."""
        prefix = compute_inventory_item_prefix(year=2027)
        self.assertEqual(prefix, 'YT')

    def test_inventory_prefix_2030(self):
        """Test 2030 → XQ (3→X, 0→Q)."""
        prefix = compute_inventory_item_prefix(year=2030)
        self.assertEqual(prefix, 'XQ')

    def test_inventory_prefix_2020(self):
        """Test 2020 → YQ (2→Y, 0→Q)."""
        prefix = compute_inventory_item_prefix(year=2020)
        self.assertEqual(prefix, 'YQ')

    def test_inventory_prefix_2019(self):
        """Test 2019 → YZ (1→Z, 9→R) — wait, "19" → "ZR"."""
        prefix = compute_inventory_item_prefix(year=2019)
        self.assertEqual(prefix, 'ZR')

    def test_inventory_prefix_current_year(self):
        """Test with no year argument (uses current)."""
        prefix = compute_inventory_item_prefix()
        # Should be a 2-letter string
        self.assertEqual(len(prefix), 2)
        # All letters should be in the mapping
        valid_letters = set('QZYX WVUTSR')
        self.assertTrue(all(c in valid_letters for c in prefix))

    def test_inventory_prefix_all_digits(self):
        """Test each digit maps correctly."""
        mapping = {
            '0': 'Q', '1': 'Z', '2': 'Y', '3': 'X', '4': 'W',
            '5': 'V', '6': 'U', '7': 'T', '8': 'S', '9': 'R',
        }
        # Test year 2000
        prefix = compute_inventory_item_prefix(year=2000)
        self.assertEqual(prefix, 'QQ')  # 0→Q, 0→Q

        # Test year 2001
        prefix = compute_inventory_item_prefix(year=2001)
        self.assertEqual(prefix, 'QZ')  # 0→Q, 1→Z

        # Test year 2010
        prefix = compute_inventory_item_prefix(year=2010)
        self.assertEqual(prefix, 'ZQ')  # 1→Z, 0→Q
