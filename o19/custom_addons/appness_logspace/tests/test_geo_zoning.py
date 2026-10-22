# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged('-at_install', 'post_install')
class TestZoneHierarchy(TransactionCase):
    """Test zone parent-child relationships."""

    def setUp(self):
        super().setUp()
        self.gov = self.env['logspace.zone'].create({
            'name': 'Test Governorate',
            'code': 'TEST-GOV',
            'zone_type': 'governorate',
        })
        self.city_a = self.env['logspace.zone'].create({
            'name': 'Test City A',
            'code': 'TEST-A',
            'zone_type': 'city',
            'parent_id': self.gov.id,
        })
        self.city_b = self.env['logspace.zone'].create({
            'name': 'Test City B',
            'code': 'TEST-B',
            'zone_type': 'city',
            'parent_id': self.gov.id,
        })

    def test_parent_child_relationship(self):
        """Child zones should appear in parent's child_ids."""
        self.assertIn(self.city_a, self.gov.child_ids)
        self.assertIn(self.city_b, self.gov.child_ids)
        self.assertEqual(self.city_a.parent_id, self.gov)

    def test_code_uppercase(self):
        """Zone codes should be auto-uppercased."""
        zone = self.env['logspace.zone'].create({
            'name': 'Lower Code',
            'code': 'lower-code',
        })
        self.assertEqual(zone.code, 'LOWER-CODE')

    def test_code_unique(self):
        """Duplicate zone codes should raise."""
        with self.assertRaises(Exception):
            self.env['logspace.zone'].create({
                'name': 'Duplicate Code',
                'code': 'TEST-GOV',
            })


@tagged('-at_install', 'post_install')
class TestZoneDistance(TransactionCase):
    """Test zone distance matrix and lookup logic."""

    def setUp(self):
        super().setUp()
        self.ZoneDist = self.env['logspace.zone.distance']

        # Create zone hierarchy: gov → city_a, city_b; gov2 → city_c
        self.gov = self.env['logspace.zone'].create({
            'name': 'Gov Alpha',
            'code': 'GOV-ALPHA',
            'zone_type': 'governorate',
        })
        self.gov2 = self.env['logspace.zone'].create({
            'name': 'Gov Beta',
            'code': 'GOV-BETA',
            'zone_type': 'governorate',
        })
        self.city_a = self.env['logspace.zone'].create({
            'name': 'City A',
            'code': 'CITY-A',
            'zone_type': 'city',
            'parent_id': self.gov.id,
        })
        self.city_b = self.env['logspace.zone'].create({
            'name': 'City B',
            'code': 'CITY-B',
            'zone_type': 'city',
            'parent_id': self.gov.id,
        })
        self.city_c = self.env['logspace.zone'].create({
            'name': 'City C',
            'code': 'CITY-C',
            'zone_type': 'city',
            'parent_id': self.gov2.id,
        })

    def test_exact_distance_lookup(self):
        """Direct zone pair should return stored distance."""
        self.ZoneDist.create({
            'zone_from_id': self.city_a.id,
            'zone_to_id': self.city_b.id,
            'estimated_km': 50.0,
        })
        result = self.ZoneDist.get_distance(self.city_a, self.city_b)
        self.assertAlmostEqual(result, 50.0)

    def test_symmetric_auto_create(self):
        """Creating A→B should auto-create B→A with same distance."""
        self.ZoneDist.create({
            'zone_from_id': self.city_a.id,
            'zone_to_id': self.city_b.id,
            'estimated_km': 75.0,
            'estimated_minutes': 60,
        })
        reverse = self.ZoneDist.search([
            ('zone_from_id', '=', self.city_b.id),
            ('zone_to_id', '=', self.city_a.id),
        ], limit=1)
        self.assertTrue(reverse, 'Reverse distance should be auto-created')
        self.assertAlmostEqual(reverse.estimated_km, 75.0)
        self.assertEqual(reverse.estimated_minutes, 60)

    def test_reverse_lookup(self):
        """Looking up B→A when only A→B exists should still return the distance."""
        self.ZoneDist.create({
            'zone_from_id': self.city_a.id,
            'zone_to_id': self.city_b.id,
            'estimated_km': 120.0,
        })
        result = self.ZoneDist.get_distance(self.city_b, self.city_a)
        self.assertAlmostEqual(result, 120.0)

    def test_same_zone_default(self):
        """Same zone lookup should return default 5.0 km."""
        result = self.ZoneDist.get_distance(self.city_a, self.city_a)
        self.assertAlmostEqual(result, 5.0)

    def test_no_match_returns_zero(self):
        """Completely unrelated zones with no path should return 0.0."""
        result = self.ZoneDist.get_distance(self.city_a, self.city_c)
        self.assertAlmostEqual(result, 0.0)

    def test_parent_fallback(self):
        """
        When child zones have no direct distance, the lookup should fall
        back to the parent zone's distance.

        Setup: only gov → gov2 has a distance.
        Lookup: city_a (child of gov) → city_c (child of gov2)
        Expected: should return gov→gov2 distance via parent walk.
        """
        self.ZoneDist.create({
            'zone_from_id': self.gov.id,
            'zone_to_id': self.gov2.id,
            'estimated_km': 500.0,
        })
        result = self.ZoneDist.get_distance(self.city_a, self.city_c)
        self.assertAlmostEqual(result, 500.0)

    def test_parent_fallback_one_side(self):
        """
        Fallback when only one zone has a parent.

        Setup: gov → city_c has distance.
        Lookup: city_a (child of gov) → city_c
        Expected: should find gov → city_c via parent of city_a.
        """
        self.ZoneDist.create({
            'zone_from_id': self.gov.id,
            'zone_to_id': self.city_c.id,
            'estimated_km': 350.0,
        })
        result = self.ZoneDist.get_distance(self.city_a, self.city_c)
        self.assertAlmostEqual(result, 350.0)

    def test_none_zone_returns_zero(self):
        """Passing None should return 0.0."""
        result = self.ZoneDist.get_distance(self.city_a, None)
        self.assertAlmostEqual(result, 0.0)

    def test_same_zone_distance_allowed(self):
        """Explicit same-zone rows are allowed (local moves): zones are areas,
        not points, so Muscat -> Muscat is a real ~25 km intra-zone distance.
        The mirror of A -> A is itself: exactly one row must exist."""
        self.ZoneDist.create({
            'zone_from_id': self.city_a.id,
            'zone_to_id': self.city_a.id,
            'estimated_km': 25.0,
        })
        self.assertAlmostEqual(
            self.ZoneDist.get_distance(self.city_a, self.city_a), 25.0)
        same = self.ZoneDist.search([
            ('zone_from_id', '=', self.city_a.id),
            ('zone_to_id', '=', self.city_a.id),
        ])
        self.assertEqual(len(same), 1)

    def test_same_zone_parent_fallback(self):
        """A child zone with no same-zone row resolves to the parent's
        same-zone row through the hierarchy walk (Ruwi -> Ruwi uses
        Muscat -> Muscat)."""
        self.ZoneDist.create({
            'zone_from_id': self.gov.id,
            'zone_to_id': self.gov.id,
            'estimated_km': 500.0,
        })
        self.assertAlmostEqual(
            self.ZoneDist.get_distance(self.city_a, self.city_a), 500.0)


@tagged('-at_install', 'post_install')
class TestPriceMatrixDistanceAutoPopulate(TransactionCase):
    """Test that the price matrix auto-populates distance_km from zone distance."""

    def setUp(self):
        super().setUp()
        self.ZoneDist = self.env['logspace.zone.distance']
        self.PriceMatrix = self.env['logspace.price.matrix']

        self.zone_a = self.env['logspace.zone'].create({
            'name': 'PM Zone A',
            'code': 'PM-ZONE-A',
            'zone_type': 'city',
        })
        self.zone_b = self.env['logspace.zone'].create({
            'name': 'PM Zone B',
            'code': 'PM-ZONE-B',
            'zone_type': 'city',
        })
        self.provider = self.env['res.partner'].create({
            'name': 'Test Provider PM',
            'is_provider': True,
            'is_company': True,
            'email': 'pm-test@example.com',
        })
        self.vtype = self.env['logspace.vehicle.type'].create({
            'name': 'Test VType PM',
            'code': 'VTYPE-PM',
            'category_id': self.env.ref('appness_logspace.vehicle_category_light').id,
        })

    def test_onchange_populates_distance(self):
        """_onchange_zones should fill distance_km from zone distance matrix."""
        self.ZoneDist.create({
            'zone_from_id': self.zone_a.id,
            'zone_to_id': self.zone_b.id,
            'estimated_km': 200.0,
        })
        pm = self.PriceMatrix.new({
            'provider_id': self.provider.id,
            'vehicle_type_id': self.vtype.id,
            'zone_from_id': self.zone_a.id,
            'zone_to_id': self.zone_b.id,
            'provider_price': 0.0,
        })
        pm._onchange_zones()
        self.assertAlmostEqual(pm.distance_km, 200.0)


@tagged('-at_install', 'post_install')
class TestZoneSetupWizard(TransactionCase):
    """Test the provider zone setup wizard."""

    def setUp(self):
        super().setUp()
        self.zone_a = self.env['logspace.zone'].create({
            'name': 'Wiz Zone A',
            'code': 'WIZ-A',
            'zone_type': 'city',
        })
        self.zone_b = self.env['logspace.zone'].create({
            'name': 'Wiz Zone B',
            'code': 'WIZ-B',
            'zone_type': 'city',
        })
        self.provider = self.env['res.partner'].create({
            'name': 'Wizard Provider',
            'is_provider': True,
            'is_company': True,
            'email': 'wiz-test@example.com',
        })
        self.vtype = self.env['logspace.vehicle.type'].create({
            'name': 'Wiz VType',
            'code': 'VTYPE-WIZ',
            'category_id': self.env.ref('appness_logspace.vehicle_category_light').id,
        })

    def test_wizard_generates_same_zone_route(self):
        """A single selected zone must still generate a local self-route,
        priced from the explicit same-zone distance row."""
        self.env['logspace.zone.distance'].create({
            'zone_from_id': self.zone_a.id,
            'zone_to_id': self.zone_a.id,
            'estimated_km': 25.0,
        })
        wizard = self.env['logspace.zone.setup.wizard'].create({
            'provider_id': self.provider.id,
            'zone_ids': [(6, 0, [self.zone_a.id])],
            'vehicle_type_ids': [(6, 0, [self.vtype.id])],
            'base_rate': 10.0,
            'per_km_rate': 1.0,
        })
        self.assertEqual(wizard.estimated_routes, 1)
        wizard.action_confirm()

        entries = self.env['logspace.price.matrix'].search([
            ('provider_id', '=', self.provider.id),
            ('vehicle_type_id', '=', self.vtype.id),
        ])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.zone_from_id, self.zone_a)
        self.assertEqual(entries.zone_to_id, self.zone_a)
        self.assertAlmostEqual(entries.distance_km, 25.0)
        self.assertAlmostEqual(entries.provider_price, 35.0)  # 10 + 25 x 1.0

    def test_wizard_two_zones_generate_self_routes(self):
        """Two zones -> 4 rows (A<->B cross + A->A, B->B local); re-running
        the wizard updates instead of duplicating."""
        wizard = self.env['logspace.zone.setup.wizard'].create({
            'provider_id': self.provider.id,
            'zone_ids': [(6, 0, [self.zone_a.id, self.zone_b.id])],
            'vehicle_type_ids': [(6, 0, [self.vtype.id])],
            'base_rate': 5.0,
            'per_km_rate': 1.0,
        })
        self.assertEqual(wizard.estimated_routes, 4)
        wizard.action_confirm()
        Matrix = self.env['logspace.price.matrix']
        entries = Matrix.search([
            ('provider_id', '=', self.provider.id),
            ('vehicle_type_id', '=', self.vtype.id),
        ])
        self.assertEqual(len(entries), 4)
        self.assertEqual(
            len(entries.filtered(lambda e: e.zone_from_id == e.zone_to_id)), 2)
        wizard.action_confirm()
        self.assertEqual(len(Matrix.search([
            ('provider_id', '=', self.provider.id),
            ('vehicle_type_id', '=', self.vtype.id),
        ])), 4)

    def test_wizard_creates_price_matrix(self):
        """Wizard should create price matrix entries for zone pair permutations."""
        wizard = self.env['logspace.zone.setup.wizard'].create({
            'provider_id': self.provider.id,
            'zone_ids': [(6, 0, [self.zone_a.id, self.zone_b.id])],
            'vehicle_type_ids': [(6, 0, [self.vtype.id])],
            'base_rate': 10.0,
            'per_km_rate': 1.0,
        })
        wizard.action_confirm()

        entries = self.env['logspace.price.matrix'].search([
            ('provider_id', '=', self.provider.id),
            ('vehicle_type_id', '=', self.vtype.id),
        ])
        # 2 zones = A→B, B→A cross + A→A, B→B local self-routes
        self.assertEqual(len(entries), 4)

    def test_wizard_updates_existing(self):
        """With Skip Existing unticked, the wizard updates existing price
        matrix entries with the new rates instead of skipping them."""
        # 50 km between the zones (auto-creates the reverse B→A row too)
        self.env['logspace.zone.distance'].create({
            'zone_from_id': self.zone_a.id,
            'zone_to_id': self.zone_b.id,
            'estimated_km': 50.0,
        })
        # Pre-create one entry at a distinct price
        self.env['logspace.price.matrix'].create({
            'provider_id': self.provider.id,
            'vehicle_type_id': self.vtype.id,
            'zone_from_id': self.zone_a.id,
            'zone_to_id': self.zone_b.id,
            'provider_price': 999.0,
        })
        wizard = self.env['logspace.zone.setup.wizard'].create({
            'provider_id': self.provider.id,
            'zone_ids': [(6, 0, [self.zone_a.id, self.zone_b.id])],
            'vehicle_type_ids': [(6, 0, [self.vtype.id])],
            'base_rate': 10.0,
            'per_km_rate': 1.0,
            'skip_existing': False,
        })
        wizard.action_confirm()

        entries = self.env['logspace.price.matrix'].search([
            ('provider_id', '=', self.provider.id),
            ('vehicle_type_id', '=', self.vtype.id),
        ])
        # A→B and B→A updated to 10.0 + 50.0 x 1.0; the two new self-routes
        # use the 5.0 km same-zone default (no explicit A→A row)
        self.assertEqual(len(entries), 4)
        cross = entries.filtered(lambda e: e.zone_from_id != e.zone_to_id)
        local = entries.filtered(lambda e: e.zone_from_id == e.zone_to_id)
        self.assertEqual(len(cross), 2)
        self.assertEqual(len(local), 2)
        self.assertTrue(all(
            abs(e.provider_price - 60.0) < 0.01 for e in cross
        ), 'Existing entries must be recomputed from the wizard rates')
        self.assertTrue(all(
            abs(e.provider_price - 15.0) < 0.01 for e in local
        ), 'Self-routes fall back to the 5.0 km same-zone default')

    def test_wizard_uses_selected_zones_only(self):
        """The wizard generates routes for explicitly selected zones only -
        child zones are covered by the portal search's hierarchy walk, not
        expanded here (see _get_selected_zones)."""
        gov = self.env['logspace.zone'].create({
            'name': 'Wiz Gov',
            'code': 'WIZ-GOV',
            'zone_type': 'governorate',
        })
        child = self.env['logspace.zone'].create({
            'name': 'Wiz Child',
            'code': 'WIZ-CHILD',
            'zone_type': 'city',
            'parent_id': gov.id,
        })
        wizard = self.env['logspace.zone.setup.wizard'].create({
            'provider_id': self.provider.id,
            'zone_ids': [(6, 0, [gov.id, self.zone_a.id])],
            'vehicle_type_ids': [(6, 0, [self.vtype.id])],
            'base_rate': 5.0,
            'per_km_rate': 0.5,
        })
        selected = wizard._get_selected_zones()
        self.assertIn(gov, selected)
        self.assertIn(self.zone_a, selected)
        self.assertNotIn(child, selected)
