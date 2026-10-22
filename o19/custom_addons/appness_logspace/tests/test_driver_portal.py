# -*- coding: utf-8 -*-

import re
from contextlib import contextmanager
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.addons.mail.models.mail_template import MailTemplate
from odoo.tests import HttpCase, TransactionCase, tagged

DRIVER_PASSWORD = 'DriverTest!2026'


def _code_pattern(code):
    """Match a verification code only as a standalone 4-digit run.

    Track pages and emails legitimately contain other numbers (prices, dates),
    and the web client's session_info embeds a 64-char hex registry_hash that
    can start with any 4 digits, so a digit-only guard would match inside it
    (e.g. code 6450 vs registry_hash "6450df..."). The code must also not be
    part of a longer word/hex token.
    """
    return re.compile(r'(?<![\w])%s(?![\w])' % re.escape(code))


class LogspaceDriverCommon(TransactionCase):
    """Shared fixtures: an approved provider, two flagged drivers and a
    confirmed Logspace order assigned to driver A."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver_group = cls.env.ref('appness_logspace.group_logspace_driver')
        cls.portal_group = cls.env.ref('base.group_portal')
        cls.internal_group = cls.env.ref('base.group_user')

        cls.provider = cls.env['res.partner'].create({
            'name': 'Driver Test Provider',
            'is_provider': True,
            'is_approved_provider': True,
            'state': 'approved',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Driver Test Customer',
            'email': 'driver.test.customer@example.com',
        })
        cls.driver_a = cls._make_driver('Driver A', 'driver.a@example.com')
        cls.driver_b = cls._make_driver('Driver B', 'driver.b@example.com')

        cls.driver_a_user = cls.driver_a.driver_portal_user_id
        cls.driver_b_user = cls.driver_b.driver_portal_user_id
        cls.customer_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Driver Test Customer User',
            'login': 'driver.test.customer.user@example.com',
            'email': 'driver.test.customer.user@example.com',
            'partner_id': cls.customer.id,
            'group_ids': [Command.set([cls.portal_group.id])],
        })

        cls.product = cls.env['product.product'].create({
            'name': 'Driver Test Transport',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.order = cls._make_order(cls.driver_a)

    @classmethod
    def _make_driver(cls, name, email):
        return cls.env['res.partner'].create({
            'name': name,
            'parent_id': cls.provider.id,
            'type': 'contact',
            'is_company': False,
            'is_driver': True,
            'email': email,
        })

    @classmethod
    def _make_order(cls, driver):
        order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'is_logspace_order': True,
            'logspace_provider_id': cls.provider.id,
            'logspace_driver_id': driver.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        order.action_confirm()
        return order

    def _as_driver_a(self):
        return self.order.with_user(self.driver_a_user)

    def _wrong_code(self, real_code):
        return '0000' if real_code != '0000' else '0001'

    def _flush(self):
        """Flush every env on this cursor, then drop the test env's cache."""
        self.env.flush_all()
        self.order.invalidate_recordset()

    @contextmanager
    def _raised(self, exception=UserError):
        """Like assertRaises, but WITHOUT Odoo's savepoint rollback.

        TransactionCase.assertRaises runs the body inside a savepoint that is
        rolled back when the exception fires (odoo/tests/common.py:_assertRaises).
        That discards the failed-attempt counter written immediately before the
        raise - which is exactly what the throttling tests need to inspect.
        A UserError raised from Python leaves the SQL transaction usable, so
        catching it manually is safe.

        In production the controller catches these errors and the request
        commits, so the counter does persist; see TestLogspaceDriverHttp for the
        cross-request proof.
        """
        try:
            yield
        except exception:
            pass
        else:
            self.fail('%s was not raised' % exception.__name__)

    # The single linear path a driver walks, in order. Each entry is
    # (state_reached, action_key, code_type); code_type is None for the steps
    # that need no verification code.
    WORKFLOW_PATH = [
        ('pickup_started', 'start_pickup', None),
        ('vendor_arrived_pickup', 'vendor_arrived_pickup', None),
        ('pickup_addons', 'pickup_addons', None),
        ('pickup_completed', 'pickup_completed', 'pickup'),
        ('pre_dropoff_addons', 'pre_dropoff_addons', None),
        ('arrived_destination', 'arrived_destination', None),
        ('dropoff_completed', 'dropoff_completed', 'dropoff'),
    ]

    def _advance_to(self, state):
        """Walk the order forward to `state` as driver A, supplying real codes.

        Incremental on purpose: tests may call this repeatedly on the same
        order (the availability table iterates every state), and replaying the
        path from order_received would raise on the already-applied steps.
        """
        targets = [entry[0] for entry in self.WORKFLOW_PATH]
        self.assertIn(
            state, ('order_received',) + tuple(targets),
            '%s is not a state a driver can reach' % state,
        )
        self.order.invalidate_recordset()
        current = self.order.logspace_state
        if current == state:
            return
        start = 0 if current == 'order_received' else targets.index(current) + 1
        end = targets.index(state) + 1
        self.assertLess(
            start, end, 'cannot walk backwards from %s to %s' % (current, state),
        )
        order = self._as_driver_a()
        for _, action, code_type in self.WORKFLOW_PATH[start:end]:
            code = None
            if code_type == 'pickup':
                code = self.order.verification_code_pickup
            elif code_type == 'dropoff':
                code = self.order.verification_code_dropoff
            order.action_driver_transition(action, code=code)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, state)


@tagged('post_install', '-at_install')
class TestLogspaceDriverIdentity(LogspaceDriverCommon):
    """Task 1/3: the driver flag provisions a portal-only login."""

    def test_driver_group_implies_portal_not_internal(self):
        self.assertIn(self.portal_group, self.driver_group.implied_ids)
        self.assertNotIn(self.internal_group, self.driver_group.implied_ids)

    def test_flagging_contact_autocreates_portal_user(self):
        self.assertTrue(self.driver_a_user, 'no portal user was created for the driver contact')
        self.assertIn(self.driver_group, self.driver_a_user.group_ids)
        self.assertIn(self.portal_group, self.driver_a_user.group_ids)
        # The load-bearing assertion: a driver must stay a portal (share) user,
        # otherwise they land in the backend instead of the website portal.
        self.assertTrue(self.driver_a_user.share)
        self.assertFalse(self.driver_a_user._is_internal())

    def test_driver_flag_rejects_company_and_non_provider_parent(self):
        with self.assertRaises(UserError):
            self.env['res.partner'].create({
                'name': 'Driver Test Company',
                'is_company': True,
                'is_driver': True,
            })
        with self.assertRaises(UserError):
            self.env['res.partner'].create({
                'name': 'Driver Test Orphan',
                'is_company': False,
                'is_driver': True,
            })

    def test_portal_access_button_requires_driver_flag_and_email(self):
        plain_contact = self.env['res.partner'].create({
            'name': 'Driver Test Plain Contact',
            'parent_id': self.provider.id,
            'is_company': False,
        })
        with self.assertRaises(UserError):
            plain_contact.action_create_driver_portal_user()

        plain_contact.write({'is_driver': True})
        with self.assertRaises(UserError):
            plain_contact.action_create_driver_portal_user()

        plain_contact.write({'email': 'driver.plain@example.com'})
        plain_contact.action_create_driver_portal_user()
        self.assertTrue(plain_contact.driver_portal_user_id)


@tagged('post_install', '-at_install')
class TestLogspacePortalNavigation(LogspaceDriverCommon):
    """The website navbar's "My Orders" item is this module's own website.menu
    record (data/website_menu.xml). It carries no group_ids, so the core ir.rule
    lets everyone see it - guests and drivers included."""

    def test_my_orders_navbar_item_is_hidden_from_drivers_and_guests(self):
        """group_ids cannot express this rule: it is an allowlist, and "not a
        driver" is not a group - a driver holds base.group_portal exactly like a
        customer does. Visibility is therefore computed in
        models/website_menu.py::_compute_visible.
        """
        menus = self.env['website.menu'].search([('url', '=', '/logspace/my/orders')])
        self.assertTrue(menus, 'data/website_menu.xml should have created the item')

        # website.menu.create() copies a parent-less main-menu child once per
        # website and binds the xmlid to a website_id=False row that never
        # renders, which is why the override matches on url rather than resolving
        # env.ref(). Assert that shape so this test fails loudly if it changes.
        self.assertGreaterEqual(
            len(menus), 1,
            'expected the per-website duplicate(s) plus the website_id=False '
            'template row that holds the xmlid',
        )

        expectations = (
            ('admin', self.env.user, True),
            ('customer', self.customer_user, True),
            ('driver', self.driver_a_user, False),
            ('public', self.env.ref('base.public_user'), False),
        )
        for label, user, expected in expectations:
            scoped = menus.with_user(user)
            # is_visible is a NON-STORED computed field, and Odoo caches computed
            # values per transaction keyed by (record, field) - NOT per user. Read
            # it for one user and every later user in the same transaction gets the
            # cached value, so this test would pass whatever the first row said.
            # Invalidate before each read. (This silently produced contradictory
            # results while the behaviour was first being pinned down.)
            scoped.invalidate_recordset(['is_visible'])
            with self.subTest(user=label):
                self.assertEqual(
                    set(scoped.mapped('is_visible')), {expected},
                    '%s should%s see the My Orders navbar item'
                    % (label, '' if expected else ' not'),
                )


@tagged('post_install', '-at_install')
class TestLogspaceDriverTransitions(LogspaceDriverCommon):
    """Task 2/4/5: the driver dispatcher, its authorization and the code gate."""

    def test_full_delivery_walk(self):
        self._advance_to('dropoff_completed')
        self.assertTrue(self.order.delivery_date)

    def test_each_transition_rejects_wrong_prior_state(self):
        # From order_received only start_pickup is legal.
        for action in self.order._LOGSPACE_DRIVER_ACTIONS:
            if action == 'start_pickup':
                continue
            with self.subTest(action=action), self.assertRaises(UserError):
                self._as_driver_a().action_driver_transition(action, code='0000')
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_action_availability_per_state(self):
        """Exactly one action is offered per state, so a driver always sees a
        single button and advances one step at a time.

        The table is spelled out rather than derived from _LOGSPACE_DRIVER_ACTIONS
        so a spec typo cannot hide behind a tautological comparison against the
        spec itself. Note the driver spec is deliberately STRICTER than the model:
        _apply_pickup_completed still accepts pickup_started / vendor_arrived_pickup
        / pickup_addons and action_arrived_destination still accepts
        pickup_completed / pre_dropoff_addons, because admins and providers need
        that latitude to rescue an order. Only the driver-facing list is linear.
        """
        expected = {
            'order_received': {'start_pickup'},
            'pickup_started': {'vendor_arrived_pickup'},
            'vendor_arrived_pickup': {'pickup_addons'},
            'pickup_addons': {'pickup_completed'},
            'pickup_completed': {'pre_dropoff_addons'},
            'pre_dropoff_addons': {'arrived_destination'},
            'arrived_destination': {'dropoff_completed'},
            # Terminal states for a driver: the provider/admin finish the rest.
            'dropoff_completed': set(),
        }
        for state, expected_keys in expected.items():
            if state != 'order_received':
                self._advance_to(state)
            with self.subTest(state=state):
                available = {
                    a['key'] for a in self.order._get_logspace_driver_actions() if a['available']
                }
                self.assertEqual(available, expected_keys)

    def test_every_spec_entry_names_exactly_one_from_state(self):
        """Guard the invariant the one-button rule rests on.

        A second state in any from_states tuple immediately reintroduces a
        two-button screen, and nothing else in the suite would catch it: the
        availability table above only checks the states it walks, and it walks a
        single linear path.
        """
        for key, spec in self.order._LOGSPACE_DRIVER_ACTIONS.items():
            with self.subTest(action=key):
                self.assertEqual(
                    len(spec['from_states']), 1,
                    '%s offers itself from %s; a driver must see one button at a '
                    'time, so this must name exactly one state' % (key, list(spec['from_states'])),
                )

    def test_no_two_actions_share_a_from_state(self):
        """The other half of the one-button rule: no state may claim two actions.

        Single-element from_states is not sufficient on its own - two entries
        could each name one state and still name the SAME one.
        """
        seen = {}
        for key, spec in self.order._LOGSPACE_DRIVER_ACTIONS.items():
            for state in spec['from_states']:
                seen.setdefault(state, []).append(key)
        duplicated = {s: ks for s, ks in seen.items() if len(ks) > 1}
        self.assertEqual(
            duplicated, {},
            'these states would render more than one button: %s' % duplicated,
        )

    def test_driver_cannot_skip_a_step_over_http(self):
        """Hiding the extra button is cosmetic unless the model enforces it too.

        /logspace/driver/orders/action is reachable with a hand-built request, and
        the underlying methods accept a wider set of states than the driver spec
        does (on purpose, for admin/provider rescue). Without the check in
        action_driver_transition a driver could jump straight from pickup_started
        to pickup_completed and never visit the add-on step.
        """
        self._advance_to('pickup_started')
        self.assertEqual(self.order.logspace_state, 'pickup_started')

        # The CORRECT code, deliberately. Passing a wrong one would raise from
        # _verify_logspace_code and the test would pass without the availability
        # guard ever being reached - which is exactly how it was first written, and
        # reverting the guard left it green. Supplying the right code means the
        # only thing that can stop this transition is the guard.
        #
        # The model would happily accept it: _apply_pickup_completed's
        # expected_states still includes pickup_started, so admins and providers
        # keep their rescue path. Only the driver spec is strict.
        with self.assertRaises(UserError):
            self._as_driver_a().action_driver_transition(
                'pickup_completed', code=self.order.verification_code_pickup,
            )
        self._flush()
        self.assertEqual(
            self.order.logspace_state, 'pickup_started',
            'a rejected transition must not move the order',
        )

        # The legitimate next step still works, so the guard is not over-broad.
        self._as_driver_a().action_driver_transition('vendor_arrived_pickup')
        self._flush()
        self.assertEqual(self.order.logspace_state, 'vendor_arrived_pickup')

    def test_a_rejected_step_does_not_burn_a_code_attempt(self):
        """Ordering matters: the availability check runs BEFORE code verification.

        A driver who fires a stale request (page open across a state change) must
        not spend one of their five attempts on a step that was never available -
        especially since exhausting them locks the pickup code.
        """
        self._advance_to('pickup_started')
        for _attempt in range(3):
            with self.assertRaises(UserError):
                self._as_driver_a().action_driver_transition(
                    'pickup_completed', code=self.order.verification_code_pickup,
                )
        self._flush()
        self.assertEqual(
            self.order.verification_attempts_pickup, 0,
            'an unavailable action must be rejected before the code is compared',
        )

    def test_no_action_available_on_unconfirmed_order(self):
        draft = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_logspace_order': True,
            'logspace_provider_id': self.provider.id,
            'logspace_driver_id': self.driver_a.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        self.assertFalse([a for a in draft._get_logspace_driver_actions() if a['available']])

    def test_actions_never_expose_expected_codes(self):
        for action in self.order._get_logspace_driver_actions():
            self.assertEqual(
                set(action), {'key', 'label', 'needs_code', 'code_type', 'highlight', 'available'},
            )

    def test_unknown_action_rejected(self):
        with self.assertRaises(UserError):
            self._as_driver_a().action_driver_transition('complete_order')
        with self.assertRaises(UserError):
            self._as_driver_a().action_driver_transition('action_confirm')

    def test_code_steps_reject_missing_and_empty_code(self):
        """Regression: portal users used to bypass verification entirely."""
        self._advance_to('pickup_addons')
        for code in (None, '', '   '):
            with self.subTest(code=code), self.assertRaises(UserError):
                self._as_driver_a().action_driver_transition('pickup_completed', code=code)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'pickup_addons')

    def test_empty_code_rejected_when_no_code_generated(self):
        """Regression for the wizard bug: '' compared against an unset code
        used to pass verification."""
        self.order.sudo().verification_code_pickup = False
        with self.assertRaises(UserError):
            self._as_driver_a()._verify_logspace_code('pickup', '')

    def test_wrong_code_rejected_then_correct_code_accepted(self):
        self._advance_to('pickup_addons')
        with self._raised():
            self._as_driver_a().action_driver_transition(
                'pickup_completed', code=self._wrong_code(self.order.verification_code_pickup),
            )
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_addons')
        self.assertEqual(self.order.verification_attempts_pickup, 1)

        self._as_driver_a().action_driver_transition(
            'pickup_completed', code=self.order.verification_code_pickup,
        )
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_completed')
        self.assertEqual(self.order.verification_attempts_pickup, 0)

    def test_dropoff_step_uses_dropoff_code_not_pickup_code(self):
        self._advance_to('arrived_destination')
        self.assertTrue(self.order.verification_code_dropoff)
        with self.assertRaises(UserError):
            self._as_driver_a().action_driver_transition(
                'dropoff_completed', code=self.order.verification_code_pickup,
            )
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'arrived_destination')

        self._as_driver_a().action_driver_transition(
            'dropoff_completed', code=self.order.verification_code_dropoff,
        )
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'dropoff_completed')

    def test_five_wrong_codes_lock_the_order(self):
        self._advance_to('pickup_addons')
        wrong = self._wrong_code(self.order.verification_code_pickup)
        for attempt in range(self.order.MAX_VERIFICATION_ATTEMPTS):
            with self.subTest(attempt=attempt), self._raised():
                self._as_driver_a().action_driver_transition('pickup_completed', code=wrong)
        self._flush()
        self.assertEqual(
            self.order.verification_attempts_pickup, self.order.MAX_VERIFICATION_ATTEMPTS,
        )

        # Locked: even the correct code is refused from the portal.
        with self.assertRaises(UserError):
            self._as_driver_a().action_driver_transition(
                'pickup_completed', code=self.order.verification_code_pickup,
            )
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'pickup_addons')

        # The lock must not strand the delivery - an admin can still finish it.
        self.order.action_pickup_completed()
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'pickup_completed')

    def _make_provider_user(self, login='driver.test.rescue.provider@example.com'):
        """An internal provider user - the backend-wizard actor, not a portal driver."""
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Driver Test Rescue Provider',
            'login': login,
            'email': login,
            'partner_id': self.provider.id,
            'group_ids': [Command.set([
                self.env.ref('appness_logspace.group_logspace_provider').id,
            ])],
        })

    def test_provider_can_rescue_an_order_a_driver_locked(self):
        """The throttle must not strand the delivery.

        A driver who burns all five attempts leaves the order locked, and the
        error tells them to contact their provider - so the provider has to
        actually be able to finish it. Providers are internal users on the
        backend wizard, not the HTTP surface the counter exists to protect.
        """
        self._advance_to('pickup_addons')
        wrong = self._wrong_code(self.order.verification_code_pickup)
        for _attempt in range(self.order.MAX_VERIFICATION_ATTEMPTS):
            with self._raised():
                self._as_driver_a().action_driver_transition('pickup_completed', code=wrong)
        self._flush()
        self.assertEqual(
            self.order.verification_attempts_pickup, self.order.MAX_VERIFICATION_ATTEMPTS,
        )

        provider_user = self._make_provider_user()
        wizard = self.env['logspace.verification.wizard'].with_user(provider_user).create({
            'order_id': self.order.id,
            'code_type': 'pickup',
            'entered_code': self.order.verification_code_pickup,
        })
        wizard.action_verify()
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_completed')
        self.assertEqual(self.order.verification_attempts_pickup, 0)

    def test_lock_still_holds_on_the_sudoed_portal_path(self):
        """Security guard for the provider exemption.

        controllers/driver.py loads orders with .sudo() before calling
        action_driver_transition, and sudo() flips env.su while KEEPING env.user
        - so env.su is True for every driver request. Widening the exemption to
        a bare `not env.su` test would silently let a locked-out driver through.
        This reproduces the controller's exact recordset and pins the behaviour.
        """
        self._advance_to('pickup_addons')
        self.order.write({
            'verification_attempts_pickup': self.order.MAX_VERIFICATION_ATTEMPTS,
        })
        self._flush()

        order = self.order.with_user(self.driver_a_user).sudo()
        self.assertTrue(order.env.su)
        self.assertEqual(order.env.user, self.driver_a_user)
        # The exemption is keyed on the provider group, which a sudo'd driver
        # does not have - so the cap still applies to them.
        self.assertFalse(order._is_logspace_provider_user())

        with self._raised():
            order.action_driver_transition(
                'pickup_completed', code=self.order.verification_code_pickup,
            )
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_addons')

    def test_driver_cannot_write_state_directly(self):
        with self.assertRaises(UserError):
            self.order.with_user(self.driver_a_user).write({'logspace_state': 'dropoff_completed'})
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_other_driver_cannot_act(self):
        order_b = self._make_order(self.driver_b)
        with self.assertRaises(AccessError):
            order_b.with_user(self.driver_a_user).action_driver_transition('start_pickup')
        order_b.invalidate_recordset()
        self.assertEqual(order_b.logspace_state, 'order_received')

    def test_customer_portal_user_cannot_act(self):
        with self.assertRaises(AccessError):
            self.order.with_user(self.customer_user).action_driver_transition('start_pickup')
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_superuser_is_not_treated_as_driver(self):
        # The controller loads orders with sudo(); authorization must still be
        # checked against the real session user, not the superuser flag.
        self.assertFalse(self.order._is_logspace_driver_user())

    def test_sudo_keeps_driver_authorization_scoped_to_session_user(self):
        order_as_driver_sudo = self.order.with_user(self.driver_a_user).sudo()
        self.assertTrue(order_as_driver_sudo._is_logspace_driver_user())
        # sudo() widens rights but not identity: driver B's order stays closed.
        order_b = self._make_order(self.driver_b)
        with self.assertRaises(AccessError):
            order_b.with_user(self.driver_a_user).sudo().action_driver_transition('start_pickup')
        order_b.invalidate_recordset()
        self.assertEqual(order_b.logspace_state, 'order_received')

    def test_non_logspace_order_rejected(self):
        plain = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_logspace_order': False,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        plain.action_confirm()
        plain.sudo().logspace_driver_id = self.driver_a
        with self.assertRaises(UserError):
            plain.with_user(self.driver_a_user).action_driver_transition('start_pickup')

    def test_backend_wizard_still_verifies_after_refactor(self):
        group_provider = self.env.ref('appness_logspace.group_logspace_provider')
        provider_user = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Driver Test Provider User',
            'login': 'driver.test.provider@example.com',
            'email': 'driver.test.provider@example.com',
            'partner_id': self.provider.id,
            'group_ids': [Command.set([group_provider.id])],
        })
        self.order.with_user(provider_user).action_start_pickup()

        wizard = self.env['logspace.verification.wizard'].with_user(provider_user).create({
            'order_id': self.order.id,
            'code_type': 'pickup',
            'entered_code': self._wrong_code(self.order.verification_code_pickup),
        })
        with self._raised():
            wizard.action_verify()
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_started')
        self.assertEqual(self.order.verification_attempts_pickup, 1)

        wizard.entered_code = self.order.verification_code_pickup
        wizard.action_verify()
        self._flush()
        self.assertEqual(self.order.logspace_state, 'pickup_completed')
        self.assertEqual(self.order.verification_attempts_pickup, 0)


@tagged('post_install', '-at_install')
class TestLogspaceDriverNotification(LogspaceDriverCommon):
    """Task 7: the assignment email fires once and never carries a code."""

    def _assignment_messages(self, order):
        return order.message_ids.filtered(
            lambda m: 'Delivery assignment emailed' in (m.body or '')
        )

    def _sent_templates(self, mock_send):
        """Template ids used by the patched send_mail calls in this test."""
        return [
            call.args[0].id for call in mock_send.call_args_list if call.args
        ]

    def test_confirmation_emails_driver_exactly_once(self):
        self.assertEqual(len(self._assignment_messages(self.order)), 1)
        # Re-writing the same driver must not re-notify.
        self.order.write({'logspace_driver_id': self.driver_a.id})
        self.assertEqual(len(self._assignment_messages(self.order)), 1)

    def test_reassigning_to_another_driver_notifies_once(self):
        self.order.write({'logspace_driver_id': self.driver_b.id})
        self.assertEqual(len(self._assignment_messages(self.order)), 2)
        self.assertIn('Driver B', self._assignment_messages(self.order).sorted('id')[-1].body)

    def test_customer_gets_his_own_driver_assigned_email(self):
        """Assignment notifies the driver AND the customer, one email each.

        The customer email carries the driver's identity and the pickup code;
        the driver's own notice never carries a code (see the structural test
        below and TestLogspaceDriverHttp).
        """
        customer_template = self.env.ref('appness_logspace.email_template_driver_assigned')
        driver_template = self.env.ref(
            'appness_logspace.email_template_driver_assignment_notice')
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.write({'logspace_driver_id': self.driver_b.id})
        sent = self._sent_templates(mock_send)
        self.assertEqual(sent.count(customer_template.id), 1)
        self.assertEqual(sent.count(driver_template.id), 1)

    def test_draft_order_sends_no_assignment_email(self):
        draft = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_logspace_order': True,
            'logspace_provider_id': self.provider.id,
            'logspace_driver_id': self.driver_a.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            draft.write({'logspace_driver_id': self.driver_b.id})
        self.assertEqual(self._sent_templates(mock_send), [])

    def test_skip_flag_suppresses_assignment_emails(self):
        """Upgrade backfills confirm historical orders with this flag set;
        the assignment notices (driver and customer) stay silent too."""
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.with_context(logspace_skip_status_emails=True).write(
                {'logspace_driver_id': self.driver_b.id})
        self.assertEqual(self._sent_templates(mock_send), [])

    def test_customer_email_targets_the_customer_and_carries_a_token(self):
        self.order.write({'logspace_driver_id': self.driver_b.id})
        # Tokenized before rendering so a GUEST can open the track link.
        self.assertTrue(self.order.access_token)
        template = self.env.ref('appness_logspace.email_template_driver_assigned')
        self.assertFalse(template.use_default_to, template.name)
        mail_values = template.sudo()._generate_template(
            [self.order.id],
            render_fields=['subject', 'body_html', 'partner_to'],
        )[self.order.id]
        self.assertEqual(mail_values.get('partner_ids'), [self.customer.id])
        self.assertIn('access_token', str(mail_values.get('body_html')))

    def test_booking_confirmation_template_is_gone(self):
        """Deleted as redundant: the confirmation write already emails all
        three parties the 'Order Received' status email."""
        self.assertFalse(self.env.ref(
            'appness_logspace.email_template_booking_confirmation',
            raise_if_not_found=False,
        ))

    def test_draft_order_does_not_notify(self):
        draft = self.env['sale.order'].create({
            'partner_id': self.customer.id,
            'is_logspace_order': True,
            'logspace_provider_id': self.provider.id,
            'logspace_driver_id': self.driver_a.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        self.assertFalse(self._assignment_messages(draft))
        draft.action_confirm()
        self.assertEqual(len(self._assignment_messages(draft)), 1)

    def test_email_recipient_is_the_driver(self):
        template = self.env.ref('appness_logspace.email_template_driver_assignment_notice')
        self.assertIn('logspace_driver_id', template.partner_to)

    def test_email_contains_no_verification_codes(self):
        template = self.env.ref('appness_logspace.email_template_driver_assignment_notice')
        # Structural guarantee: the template cannot render what it never names.
        source = (template.subject or '') + (template.body_html or '')
        self.assertNotIn('verification_code_pickup', source)
        self.assertNotIn('verification_code_dropoff', source)

        rendered = template.sudo()._render_field('body_html', [self.order.id])[self.order.id]
        rendered = str(rendered)
        self.assertNotRegex(rendered, _code_pattern(self.order.verification_code_pickup))
        self.assertIn(self.order.name, rendered)
        self.assertIn('/logspace/driver/orders/track/', rendered)


@tagged('post_install', '-at_install')
class TestLogspaceDriverHttp(LogspaceDriverCommon, HttpCase):
    """Task 6/9: the portal routes and, above all, that the driver track page
    never renders either verification code."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for user in (cls.driver_a_user, cls.driver_b_user, cls.customer_user):
            user.password = DRIVER_PASSWORD
        cls.env.flush_all()

    def test_non_driver_is_redirected_away_from_driver_pages(self):
        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        for path in ('/logspace/driver/orders', '/logspace/driver/orders/active'):
            with self.subTest(path=path):
                response = self.url_open(path, allow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertIn('/logspace/my', response.headers.get('Location', ''))

        result = self.make_jsonrpc_request(
            '/logspace/driver/orders/action',
            {'order_name': self.order.name, 'action': 'start_pickup'},
        )
        self.assertIn('error', result)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_driver_cannot_see_or_act_on_another_drivers_order(self):
        self.authenticate('driver.b@example.com', DRIVER_PASSWORD)
        response = self.url_open(
            '/logspace/driver/orders/track/%s' % self.order.name, allow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)

        result = self.make_jsonrpc_request(
            '/logspace/driver/orders/action',
            {'order_name': self.order.name, 'action': 'start_pickup'},
        )
        self.assertIn('error', result)
        self.order.invalidate_recordset()
        self.assertEqual(self.order.logspace_state, 'order_received')

    def test_driver_track_page_exposes_no_verification_codes(self):
        """Regression for the OTP-leak risk: the customer track page renders both
        codes in plaintext; the driver page must render neither."""
        self.order.sudo().verification_code_dropoff = self.order._generate_verification_code()
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)

        # The first QWeb render can exceed the default HTTP timeout after upgrade.
        response = self.url_open(
            '/logspace/driver/orders/track/%s' % self.order.name, timeout=60,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')

        html = response.text
        self.assertIn(self.order.name, html)
        self.assertIn('logspace-driver-page', html)
        self.assertIn('data-action="start_pickup"', html)
        self.assertNotRegex(html, _code_pattern(self.order.verification_code_pickup))
        self.assertNotRegex(html, _code_pattern(self.order.verification_code_dropoff))

        # The button must carry BOTH the data-action and the hook class, on the
        # same element. logspace_driver.js binds `click .logspace-driver-action`,
        # so a button that only has data-action renders fine and does nothing.
        # This regressed once already: a static class= next to t-attf-class= on
        # the same tag is silently replaced by qweb, not merged.
        # The class is matched as a whole space-delimited token so that the
        # inner label span's `logspace-driver-action-label` cannot satisfy it.
        self.assertRegex(
            html,
            r'<button[^>]*class="(?:[^"]*\s)?logspace-driver-action(?:\s[^"]*)?"'
            r'[^>]*data-action="start_pickup"',
        )

        list_response = self.url_open('/logspace/driver/orders')
        self.assertEqual(list_response.status_code, 200)
        self.assertNotRegex(list_response.text, _code_pattern(self.order.verification_code_pickup))

    def _post_action(self, order, action, code=None):
        params = {'order_name': order.name, 'action': action}
        if code is not None:
            params['code'] = code
        return self.make_jsonrpc_request('/logspace/driver/orders/action', params)

    def test_driver_action_route_walks_the_whole_delivery(self):
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        order = self.order

        # Non-code steps advance the real order, one request at a time.
        for action, expected_state in (
            ('start_pickup', 'pickup_started'),
            ('vendor_arrived_pickup', 'vendor_arrived_pickup'),
            ('pickup_addons', 'pickup_addons'),
        ):
            with self.subTest(action=action):
                result = self._post_action(order, action)
                self.assertTrue(result.get('ok'), result)
                self.assertEqual(result['state'], expected_state)
                order.invalidate_recordset()
                self.assertEqual(order.logspace_state, expected_state)

        # The code-gated step refuses a missing code with an inline error (not a
        # 500), and the error text must never echo the expected code back.
        result = self._post_action(order, 'pickup_completed')
        self.assertIn('error', result)
        self.assertNotIn('ok', result)
        order.invalidate_recordset()
        self.assertEqual(order.logspace_state, 'pickup_addons')

        wrong = self._wrong_code(order.verification_code_pickup)
        result = self._post_action(order, 'pickup_completed', code=wrong)
        self.assertIn('error', result)
        self.assertNotIn(order.verification_code_pickup, result['error'])

        result = self._post_action(order, 'pickup_completed',
                                   code=order.verification_code_pickup)
        self.assertTrue(result.get('ok'), result)
        self.assertEqual(result['state'], 'pickup_completed')

        # An unknown order name is reported, not raised.
        result = self.make_jsonrpc_request(
            '/logspace/driver/orders/action',
            {'order_name': 'S99999', 'action': 'start_pickup'},
        )
        self.assertIn('error', result)

    def test_track_page_renders_exactly_one_button_per_state(self):
        """The reported symptom: two buttons on screen at once confuses the driver.

        Walk the whole delivery over HTTP and assert the rendered page offers
        exactly one action at every step. The availability table tests the model;
        only the rendered HTML proves what the driver actually sees - and a page
        that renders the right model data can still be dead (the t-attf-class
        regression that dropped the JS hook class did exactly that).

        Counting `data-action` is exact: that attribute appears on one element in
        the whole template (views/logspace_driver_templates.xml:146).
        """
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        order = self.order
        url = '/logspace/driver/orders/track/%s' % order.name

        def rendered_actions():
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200)
            return re.findall(r'<button[^>]*data-action="([^"]+)"', response.text)

        def step(expected_state, expected_action, code=None):
            order.invalidate_recordset()
            self.assertEqual(order.logspace_state, expected_state)
            with self.subTest(state=expected_state):
                self.assertEqual(
                    rendered_actions(), [expected_action],
                    'the driver must see exactly one button at %s' % expected_state,
                )
            result = self._post_action(order, expected_action, code=code)
            self.assertTrue(result.get('ok'), result)

        step('order_received', 'start_pickup')
        step('pickup_started', 'vendor_arrived_pickup')
        step('vendor_arrived_pickup', 'pickup_addons')
        step('pickup_addons', 'pickup_completed', code=order.verification_code_pickup)
        step('pickup_completed', 'pre_dropoff_addons')
        step('pre_dropoff_addons', 'arrived_destination')

        # Arriving mints the drop-off code, so it cannot be read before this point.
        order.invalidate_recordset()
        self.assertTrue(
            order.verification_code_dropoff,
            'arriving at the destination must mint the drop-off code',
        )
        step('arrived_destination', 'dropoff_completed', code=order.verification_code_dropoff)

        # Terminal: no buttons at all, and the empty-state message in their place.
        order.invalidate_recordset()
        self.assertEqual(order.logspace_state, 'dropoff_completed')
        self.assertEqual(rendered_actions(), [])
        self.assertIn('No action is available at this stage', self.url_open(url).text)

    def test_wrong_codes_lock_the_order_across_requests(self):
        """The throttle has to survive separate HTTP requests - that is the whole
        point, since a brute-force attacker makes one request per guess.

        Unlike the TransactionCase version, nothing here is rolled back: the
        controller catches the UserError and the request commits, so the counter
        really does accumulate in the database.
        """
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        order = self._make_order(self.driver_a)
        self._post_action(order, 'start_pickup')
        self._post_action(order, 'vendor_arrived_pickup')
        self._post_action(order, 'pickup_addons')

        wrong = self._wrong_code(order.verification_code_pickup)
        for attempt in range(self.order.MAX_VERIFICATION_ATTEMPTS):
            with self.subTest(attempt=attempt):
                result = self._post_action(order, 'pickup_completed', code=wrong)
                self.assertIn('error', result)
                order.invalidate_recordset()
                self.assertEqual(order.verification_attempts_pickup, attempt + 1)

        order.invalidate_recordset()
        self.assertEqual(
            order.verification_attempts_pickup, order.MAX_VERIFICATION_ATTEMPTS,
        )

        # Locked out - even the correct code is now refused over the portal.
        result = self._post_action(
            order, 'pickup_completed', code=order.verification_code_pickup,
        )
        self.assertIn('error', result)
        order.invalidate_recordset()
        self.assertEqual(order.logspace_state, 'pickup_addons')

        # The lock must not strand the delivery: an admin can still complete it.
        order.action_pickup_completed()
        order.invalidate_recordset()
        self.assertEqual(order.logspace_state, 'pickup_completed')

    # -------------------------------------------------------------------------
    # Shared account page: the "My Deliveries" card is gated on the driver flag,
    # but it lives in logspace_my_account, which every customer also renders.
    # -------------------------------------------------------------------------

    def test_driver_sees_my_deliveries_card_on_account_page(self):
        """A driver gets deliveries, and never the customer's orders.

        Asserted on the whole page rather than one card on purpose: "My Orders"
        reaches a driver from TWO places - the card in logspace_my_account and the
        website navbar entry from data/website_menu.xml - so a whole-page check
        covers both, and would fail if either gate were removed.
        """
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my')
        self.assertEqual(response.status_code, 200)
        self.assertIn('My Deliveries', response.text)
        self.assertIn('/logspace/driver/orders', response.text)
        self.assertNotIn('My Orders', response.text)
        self.assertNotIn('/logspace/my/orders', response.text)

    def test_customer_account_page_renders_without_the_driver_card(self):
        """Regression: logspace_my_account is shared with customers, so the
        driver-only card must not leak to them - and the t-if must not break
        the page for them either. The customer keeps My Orders, in both the card
        and the navbar."""
        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('My Deliveries', response.text)
        self.assertNotIn('/logspace/driver/orders', response.text)
        self.assertIn('My Orders', response.text)
        self.assertIn('/logspace/my/orders', response.text)

    def test_my_account_dropdown_points_at_the_logspace_account_page(self):
        """Core hardcodes href="/my/home" in portal.my_account_link; the module's
        own account page is /logspace/my.

        Scoped to role="menuitem" so the assertion cannot be satisfied by an
        unrelated /logspace/my link (the breadcrumb and the Back button both point
        there) or broken by one (portal.portal_breadcrumbs also hardcodes
        /my/home).
        """
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my')
        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.text, r'href="/logspace/my"[^>]*role="menuitem"',
            'the My Account dropdown item must point at /logspace/my',
        )
        self.assertNotRegex(
            response.text, r'href="/my/home"[^>]*role="menuitem"',
            'no dropdown item may still point at /my/home',
        )

    def test_driver_is_redirected_off_the_customer_orders_page(self):
        """Hiding the card would be cosmetic if the URL behind it stayed open."""
        self.authenticate('driver.a@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my/orders', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/logspace/driver/orders', response.headers.get('Location', ''))

    def test_customer_orders_page_still_renders_for_a_customer(self):
        """The driver guard must not take the customer's own orders page with it."""
        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my/orders')
        self.assertEqual(response.status_code, 200)

    # -------------------------------------------------------------------------
    # Core portal landing routes are redirected to the Logspace pages.
    #
    # These are not cosmetic: before LogspacePortalHome existed, /my/account
    # answered 500 for EVERY portal user. This module's controllers are merged
    # into one dynamic class (all descend from LogspaceController) whose rules are
    # inserted into the werkzeug map before portal's, and LogspacePaymentController
    # inherits payment's PaymentPortal - which pulls in portal.CustomerPortal's
    # routes WITHOUT account.PortalAccount in the MRO. So the inherited core
    # account() won /my/account and rendered portal.portal_my_details with no
    # `invoice_sending_methods`, dying on len(None).
    # -------------------------------------------------------------------------

    def test_my_account_does_not_500_and_reaches_the_logspace_profile(self):
        """Regression for the /my/account 500 described above."""
        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        response = self.url_open('/my/account', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/logspace/my/profile', response.headers.get('Location', ''))

        # And the page it points at must actually render.
        followed = self.url_open('/my/account')
        self.assertEqual(followed.status_code, 200)
        self.assertNotIn('Internal Server Error', followed.text)

    def test_core_portal_home_routes_reach_the_logspace_account_page(self):
        """Every portal user lands on /logspace/my, not the core dashboard."""
        for login in ('driver.test.customer.user@example.com', 'driver.a@example.com'):
            with self.subTest(login=login):
                self.authenticate(login, DRIVER_PASSWORD)
                for path in ('/my', '/my/home'):
                    response = self.url_open(path, allow_redirects=False)
                    self.assertEqual(response.status_code, 303, path)
                    self.assertIn('/logspace/my', response.headers.get('Location', ''))

    def test_redirect_target_renders_for_both_roles(self):
        """A redirect is worthless if the destination 500s - follow it."""
        for login, expected in (
            ('driver.test.customer.user@example.com', 'My Orders'),
            ('driver.a@example.com', 'My Deliveries'),
        ):
            with self.subTest(login=login):
                self.authenticate(login, DRIVER_PASSWORD)
                response = self.url_open('/my')
                self.assertEqual(response.status_code, 200)
                self.assertIn('/logspace/my', response.url)
                self.assertIn(expected, response.text)

    def test_track_cancel_get_falls_through_to_the_orders_list(self):
        """/logspace/my/orders/track/cancel is POST-only, but a GET on it has no
        method match on the static rule and lands in logspace_track with
        order_id='cancel'. Pinned so the redirect stays deliberate - and so that
        "fixing" the track route cannot silently break cancellation."""
        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        response = self.url_open('/logspace/my/orders/track/cancel', allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertIn('/logspace/my/orders', response.headers.get('Location', ''))

    def test_track_cancel_post_still_routes_to_the_cancel_handler(self):
        """The other half: POST must still reach logspace_cancel_order.

        Asserted against the routing map rather than by posting, so the test
        cannot cancel a real order.
        """
        adapter = self.env['ir.http'].routing_map().bind('localhost')
        for method, expected in (('POST', 'logspace_cancel_order'),
                                 ('GET', 'logspace_track')):
            rule, args = adapter.match(
                '/logspace/my/orders/track/cancel', method=method, return_rule=True,
            )
            endpoint = getattr(rule.endpoint, 'func', rule.endpoint)
            with self.subTest(method=method):
                self.assertEqual(getattr(endpoint, '__name__', None), expected)
                self.assertEqual(rule.rule == '/logspace/my/orders/track/cancel', method == 'POST')

    def test_customer_track_page_survives_a_provider_without_a_phone(self):
        """Regression for the removed res.partner.mobile field.

        vendor_phone used to read `phone or mobile or ''`. Because `or`
        short-circuits, that only raised once a provider had no phone - which is
        exactly the case nobody tests, so the customer track page 500'd in
        production-shaped data. Same for the booking page's `data-phone`, which
        reads the logged-in partner's phone.
        """
        self.provider.phone = False
        self.customer_user.partner_id.phone = False
        self.env.flush_all()

        self.authenticate('driver.test.customer.user@example.com', DRIVER_PASSWORD)
        response = self.url_open(
            '/logspace/my/orders/track/%s' % self.order.name, timeout=60,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.order.name, response.text)
