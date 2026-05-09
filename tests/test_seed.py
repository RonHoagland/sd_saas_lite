# tests/test_seed.py
# Tests for the tenant provisioning seed data (config/seed.py).

from django.db import IntegrityError

from tests.base import SDTATestCase
from config.seed import (
    seed_tenant, seed_numbering, seed_lifecycle, seed_value_lists,
    NUMBERING_RULES, LIFECYCLE_STATES, LIFECYCLE_TRANSITIONS, VALUE_LISTS,
)
from numbering.models import NumberingRule, NumberSequence
from lifecycle.models import LifecycleStateDef, LifecycleTransitionRule
from value_lists.models import ValueList, ValueListItem


# ═══════════════════════════════════════════════════════════════════════════════
# Data integrity tests — validate the seed definition dicts themselves
# ═══════════════════════════════════════════════════════════════════════════════

class SeedDataIntegrityTest(SDTATestCase):
    """Validate seed data definitions for completeness and consistency."""

    def test_numbering_rules_count(self):
        """23 entity types should have numbering rules."""
        self.assertEqual(len(NUMBERING_RULES), 23)

    def test_numbering_unique_entity_types(self):
        """No duplicate entity_type in NUMBERING_RULES."""
        types = [r['entity_type'] for r in NUMBERING_RULES]
        self.assertEqual(len(types), len(set(types)))

    def test_numbering_unique_prefixes(self):
        """No duplicate prefix in NUMBERING_RULES."""
        prefixes = [r['prefix'] for r in NUMBERING_RULES]
        self.assertEqual(len(prefixes), len(set(prefixes)))

    def test_lifecycle_states_count(self):
        """29 entity types should have lifecycle state definitions."""
        self.assertEqual(len(LIFECYCLE_STATES), 29)

    def test_lifecycle_transitions_count(self):
        """29 entity types should have lifecycle transition definitions."""
        self.assertEqual(len(LIFECYCLE_TRANSITIONS), 29)

    def test_lifecycle_entity_types_match(self):
        """LIFECYCLE_STATES and LIFECYCLE_TRANSITIONS should cover the same entity types."""
        self.assertEqual(set(LIFECYCLE_STATES.keys()), set(LIFECYCLE_TRANSITIONS.keys()))

    def test_lifecycle_each_entity_has_one_default(self):
        """Each entity type should have exactly one is_default=True state."""
        for entity_type, states in LIFECYCLE_STATES.items():
            defaults = [s for s in states if s['is_default']]
            self.assertEqual(
                len(defaults), 1,
                f"Entity '{entity_type}' has {len(defaults)} default states, expected 1"
            )

    def test_lifecycle_no_self_transitions(self):
        """No transition should have from_state == to_state."""
        for entity_type, transitions in LIFECYCLE_TRANSITIONS.items():
            for trans in transitions:
                self.assertNotEqual(
                    trans['from_state'], trans['to_state'],
                    f"Entity '{entity_type}': self-transition {trans['from_state']}→{trans['to_state']}"
                )

    def test_lifecycle_transitions_reference_valid_states(self):
        """All from_state and to_state values must exist in LIFECYCLE_STATES."""
        for entity_type, transitions in LIFECYCLE_TRANSITIONS.items():
            state_names = {s['state_name'] for s in LIFECYCLE_STATES[entity_type]}
            for trans in transitions:
                self.assertIn(
                    trans['from_state'], state_names,
                    f"Entity '{entity_type}': from_state '{trans['from_state']}' not in states"
                )
                self.assertIn(
                    trans['to_state'], state_names,
                    f"Entity '{entity_type}': to_state '{trans['to_state']}' not in states"
                )

    def test_lifecycle_no_transitions_from_final_states(self):
        """No transition should originate from a final state."""
        for entity_type, transitions in LIFECYCLE_TRANSITIONS.items():
            final_states = {
                s['state_name'] for s in LIFECYCLE_STATES[entity_type]
                if s['state_type'] == 'final'
            }
            for trans in transitions:
                self.assertNotIn(
                    trans['from_state'], final_states,
                    f"Entity '{entity_type}': transition from final state '{trans['from_state']}'"
                )

    def test_lifecycle_no_duplicate_transitions(self):
        """No duplicate (from_state, to_state) per entity type."""
        for entity_type, transitions in LIFECYCLE_TRANSITIONS.items():
            pairs = [(t['from_state'], t['to_state']) for t in transitions]
            self.assertEqual(
                len(pairs), len(set(pairs)),
                f"Entity '{entity_type}' has duplicate transitions"
            )

    def test_value_lists_count(self):
        """12 value lists should be defined."""
        self.assertEqual(len(VALUE_LISTS), 12)

    def test_value_lists_unique_slugs(self):
        """No duplicate slug in VALUE_LISTS."""
        slugs = [vl['slug'] for vl in VALUE_LISTS]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_value_lists_each_has_items(self):
        """Each value list should have at least one item."""
        for vl in VALUE_LISTS:
            self.assertGreater(
                len(vl['items']), 0,
                f"Value list '{vl['slug']}' has no items"
            )

    def test_value_lists_at_most_one_default_per_list(self):
        """Each value list should have at most one is_default=True item."""
        for vl in VALUE_LISTS:
            defaults = [i for i in vl['items'] if i.get('is_default')]
            self.assertLessEqual(
                len(defaults), 1,
                f"Value list '{vl['slug']}' has {len(defaults)} defaults"
            )

    def test_value_lists_unique_values_per_list(self):
        """No duplicate value within a single value list."""
        for vl in VALUE_LISTS:
            values = [i['value'] for i in vl['items']]
            self.assertEqual(
                len(values), len(set(values)),
                f"Value list '{vl['slug']}' has duplicate item values"
            )

    def test_numbering_all_entity_types_are_lifecycle_subset(self):
        """All numbered entity types should also be lifecycle-managed (or at least defined)."""
        lifecycle_types = set(LIFECYCLE_STATES.keys())
        for rule in NUMBERING_RULES:
            self.assertIn(
                rule['entity_type'], lifecycle_types,
                f"Numbered entity '{rule['entity_type']}' has no lifecycle states"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Seed function execution tests
# ═══════════════════════════════════════════════════════════════════════════════

class SeedNumberingTest(SDTATestCase):
    """Test that seed_numbering creates the right records."""

    def test_creates_rules(self):
        count = seed_numbering(self.tenant_id)
        self.assertEqual(count, 23)
        self.assertEqual(
            NumberingRule.all_objects.filter(tenant_id=self.tenant_id).count(), 23
        )

    def test_creates_sequences(self):
        seed_numbering(self.tenant_id)
        self.assertEqual(
            NumberSequence.objects.filter(rule__tenant_id=self.tenant_id).count(), 23
        )

    def test_sequences_start_at_zero(self):
        seed_numbering(self.tenant_id)
        for seq in NumberSequence.objects.filter(rule__tenant_id=self.tenant_id):
            self.assertEqual(seq.current_value, 0)

    def test_rule_defaults(self):
        seed_numbering(self.tenant_id)
        rule = NumberingRule.all_objects.get(
            tenant_id=self.tenant_id, entity_type='customer'
        )
        self.assertEqual(rule.prefix, 'C')
        self.assertTrue(rule.is_enabled)
        self.assertTrue(rule.include_year)
        self.assertEqual(rule.year_format, 'YY')
        self.assertFalse(rule.include_month)
        self.assertEqual(rule.sequence_length, 4)
        self.assertEqual(rule.delimiter, '-')
        self.assertEqual(rule.reset_behavior, 'yearly')

    def test_idempotency_raises_on_duplicate(self):
        seed_numbering(self.tenant_id)
        with self.assertRaises(IntegrityError):
            seed_numbering(self.tenant_id)


class SeedLifecycleTest(SDTATestCase):
    """Test that seed_lifecycle creates the right records."""

    def test_creates_states(self):
        result = seed_lifecycle(self.tenant_id)
        total_expected = sum(len(s) for s in LIFECYCLE_STATES.values())
        self.assertEqual(result['states'], total_expected)
        self.assertEqual(
            LifecycleStateDef.all_objects.filter(tenant_id=self.tenant_id).count(),
            total_expected,
        )

    def test_creates_transitions(self):
        result = seed_lifecycle(self.tenant_id)
        total_expected = sum(len(t) for t in LIFECYCLE_TRANSITIONS.values())
        self.assertEqual(result['transitions'], total_expected)
        self.assertEqual(
            LifecycleTransitionRule.all_objects.filter(tenant_id=self.tenant_id).count(),
            total_expected,
        )

    def test_customer_states(self):
        seed_lifecycle(self.tenant_id)
        states = LifecycleStateDef.all_objects.filter(
            tenant_id=self.tenant_id, entity_type='customer'
        ).order_by('sort_order')
        self.assertEqual(states.count(), 4)
        names = list(states.values_list('state_name', flat=True))
        self.assertEqual(names, ['Active', 'Inactive', 'Hold', 'Closed'])

    def test_customer_default_state(self):
        seed_lifecycle(self.tenant_id)
        default = LifecycleStateDef.all_objects.get(
            tenant_id=self.tenant_id, entity_type='customer', is_default=True
        )
        self.assertEqual(default.state_name, 'Active')

    def test_customer_final_state(self):
        seed_lifecycle(self.tenant_id)
        finals = LifecycleStateDef.all_objects.filter(
            tenant_id=self.tenant_id, entity_type='customer', state_type='final'
        )
        self.assertEqual(finals.count(), 1)
        self.assertEqual(finals.first().state_name, 'Closed')

    def test_work_order_transitions(self):
        seed_lifecycle(self.tenant_id)
        transitions = LifecycleTransitionRule.all_objects.filter(
            tenant_id=self.tenant_id, entity_type='work_order'
        )
        self.assertEqual(transitions.count(), 9)

    def test_transition_requires_reason(self):
        seed_lifecycle(self.tenant_id)
        cancel_rule = LifecycleTransitionRule.all_objects.get(
            tenant_id=self.tenant_id,
            entity_type='work_order',
            from_state='Draft',
            to_state='Cancelled',
        )
        self.assertTrue(cancel_rule.requires_reason)


class SeedValueListsTest(SDTATestCase):
    """Test that seed_value_lists creates the right records."""

    def test_creates_lists(self):
        result = seed_value_lists(self.tenant_id)
        self.assertEqual(result['lists'], 12)
        self.assertEqual(
            ValueList.all_objects.filter(tenant_id=self.tenant_id).count(), 12
        )

    def test_creates_items(self):
        result = seed_value_lists(self.tenant_id)
        total_expected = sum(len(vl['items']) for vl in VALUE_LISTS)
        self.assertEqual(result['items'], total_expected)

    def test_lists_are_system(self):
        seed_value_lists(self.tenant_id)
        non_system = ValueList.all_objects.filter(
            tenant_id=self.tenant_id, is_system=False
        ).count()
        self.assertEqual(non_system, 0)

    def test_lead_source_items(self):
        seed_value_lists(self.tenant_id)
        vl = ValueList.all_objects.get(tenant_id=self.tenant_id, slug='lead_source')
        items = ValueListItem.all_objects.filter(
            tenant_id=self.tenant_id, value_list=vl
        ).order_by('sort_order')
        self.assertEqual(items.count(), 8)
        self.assertEqual(items.first().label, 'Referral')
        self.assertTrue(items.first().is_default)

    def test_payment_method_default(self):
        seed_value_lists(self.tenant_id)
        vl = ValueList.all_objects.get(tenant_id=self.tenant_id, slug='payment_method')
        default_item = ValueListItem.all_objects.get(
            tenant_id=self.tenant_id, value_list=vl, is_default=True
        )
        self.assertEqual(default_item.value, 'credit_card')


class SeedTenantIntegrationTest(SDTATestCase):
    """Test the full seed_tenant function."""

    def test_seed_tenant_returns_counts(self):
        counts = seed_tenant(self.tenant_id)
        self.assertEqual(counts['numbering'], 23)
        self.assertIn('states', counts['lifecycle'])
        self.assertIn('transitions', counts['lifecycle'])
        self.assertEqual(counts['value_lists']['lists'], 12)

    def test_seed_tenant_atomic(self):
        """Full seed is wrapped in a transaction — partial failure rolls back all."""
        # Create one numbering rule to cause IntegrityError on re-seed
        from numbering.models import NumberingRule
        NumberingRule.objects.create(
            tenant_id=self.tenant_id,
            entity_type='customer',
            prefix='C',
            created_by='System',
            updated_by='System',
        )
        with self.assertRaises(IntegrityError):
            seed_tenant(self.tenant_id)
        # Verify nothing was partially created (lifecycle and value_lists
        # should not exist since the transaction rolled back).
        self.assertEqual(
            LifecycleStateDef.all_objects.filter(tenant_id=self.tenant_id).count(), 0
        )
        self.assertEqual(
            ValueList.all_objects.filter(tenant_id=self.tenant_id).count(), 0
        )
