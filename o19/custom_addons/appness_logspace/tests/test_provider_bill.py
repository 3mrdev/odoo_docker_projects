# -*- coding: utf-8 -*-

import ast

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import LogspacePaymentCommon


@tagged('post_install', '-at_install')
class TestLogspaceProviderBill(LogspacePaymentCommon):

    def _make_provider_user(self, provider, login):
        """Internal provider user bound to the provider partner."""
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': provider.name + ' User',
            'login': login,
            'email': login,
            'partner_id': provider.id,
            'company_id': self.env.company.id,
            'company_ids': [Command.set(self.env.company.ids)],
            'group_ids': [Command.set([
                self.env.ref('appness_logspace.group_logspace_provider').id,
            ])],
        })

    def _complete_order(self, provider):
        """Drive an order to order_completed so the bill is created."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'is_logspace_order': True,
            'require_payment': True,
            'prepayment_percent': 1.0,
            'logspace_provider_id': provider.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [Command.clear()],
            })],
        })
        order.action_confirm()
        order.logspace_state = 'dropoff_completed'
        order.action_complete_order()
        return order

    # ---------------------------------------------------------------------
    # Snapshot fields on the order
    # ---------------------------------------------------------------------

    def test_bill_snapshots_follow_the_bill(self):
        """Payout + commission are stored computes keyed on the bill.

        Order total is 100, fee 10% -> payout 90, rate 0.1. Editing the draft
        bill afterwards re-runs the compute, so the order never goes stale.
        """
        provider = self.env['res.partner'].create({
            'name': 'Bill Snapshot Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        order = self._complete_order(provider)

        bill = order.logspace_provider_bill_id
        self.assertTrue(bill)
        # B5: bills are posted on creation.
        self.assertEqual(bill.state, 'posted')
        # amount_untaxed, not amount_total: the test company's default 15%
        # purchase tax lands on the bill but is not part of the payout.
        self.assertAlmostEqual(order.logspace_provider_bill_amount, bill.amount_untaxed)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 90.0)
        self.assertAlmostEqual(order.logspace_provider_commission_rate, 0.1)

        bill.button_draft()
        bill.invoice_line_ids[0].price_unit = 80.0
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 80.0)
        self.assertAlmostEqual(order.logspace_provider_commission_rate, 0.2)

    def test_tax_and_addons_do_not_inflate_the_commission(self):
        """B3: the fee is a percentage of the UNTAXED subtotal, while the
        payout is anchored on what the customer actually paid (amount_total).

        100 service + 20 add-on, 15% sale tax on both: amount_total = 138,
        subtotal = 120, fee 10% -> commission 12, payout 126. Charging the fee
        on amount_total instead would pay 124.20.
        """
        provider = self.env['res.partner'].create({
            'name': 'Tax Split Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        sale_tax = self.env['account.tax'].create({
            'name': 'Sale 15%',
            'amount_type': 'percent',
            'amount': 15.0,
            'type_tax_use': 'sale',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'is_logspace_order': True,
            'require_payment': True,
            'prepayment_percent': 1.0,
            'logspace_provider_id': provider.id,
            'order_line': [
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 100.0,
                    'tax_ids': [Command.set(sale_tax.ids)],
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 20.0,
                    'tax_ids': [Command.set(sale_tax.ids)],
                }),
            ],
        })
        order.action_confirm()
        order.logspace_state = 'dropoff_completed'
        order.action_complete_order()

        bill = order.logspace_provider_bill_id
        self.assertTrue(bill)
        self.assertAlmostEqual(order.amount_total, 138.0)
        self.assertAlmostEqual(bill.amount_untaxed, 126.0)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 126.0)

    def _service_product(self):
        """The real Logspace service product: the quoted bill branch identifies
        the service line by it to split add-ons out of the subtotal."""
        return self.env.ref(
            'appness_logspace.product_logspace_service_product_template'
        ).product_variant_id

    def test_bill_pays_the_quoted_provider_price(self):
        """C: the matrix quotes customer = provider + fee, so the bill takes
        the quoted fee FLAT instead of a percentage of the customer subtotal,
        which would charge the platform's own fee on the fee.

        Customer charged 99, quote 90 provider / 9 fee at 10%: the legacy
        formula would take 10% x 99 = 9.9 and pay 89.1; the quote wins and
        pays 90.
        """
        provider = self.env['res.partner'].create({
            'name': 'Quoted Payout Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'is_logspace_order': True,
            'require_payment': True,
            'prepayment_percent': 1.0,
            'logspace_provider_id': provider.id,
            'order_line': [Command.create({
                'product_id': self._service_product().id,
                'product_uom_qty': 1.0,
                'price_unit': 99.0,
                'tax_ids': [Command.clear()],
            })],
        })
        order.action_confirm()
        order.write({
            'logspace_quoted_provider_price': 90.0,
            'logspace_quoted_platform_fee': 9.0,
        })
        order.logspace_state = 'dropoff_completed'
        order.action_complete_order()

        bill = order.logspace_provider_bill_id
        self.assertTrue(bill)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, bill.amount_untaxed)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 90.0)
        self.assertAlmostEqual(order.logspace_provider_commission_rate, 9.0 / 99.0)

    def test_quote_keeps_addons_commissionable(self):
        """With a quote, the service fee is flat and add-ons stay commissionable.

        Service 99 + add-on 20 (15% sale tax on both): amount_total 136.85,
        add-on untaxed 20 -> commission 9 + 10% x 20 = 11 -> payout 125.85.
        """
        provider = self.env['res.partner'].create({
            'name': 'Quoted Addon Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        sale_tax = self.env['account.tax'].create({
            'name': 'Quote Sale 15%',
            'amount_type': 'percent',
            'amount': 15.0,
            'type_tax_use': 'sale',
        })
        order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'is_logspace_order': True,
            'require_payment': True,
            'prepayment_percent': 1.0,
            'logspace_provider_id': provider.id,
            'order_line': [
                Command.create({
                    'product_id': self._service_product().id,
                    'product_uom_qty': 1.0,
                    'price_unit': 99.0,
                    'tax_ids': [Command.set(sale_tax.ids)],
                }),
                Command.create({
                    'product_id': self.product.id,
                    'product_uom_qty': 1.0,
                    'price_unit': 20.0,
                    'tax_ids': [Command.set(sale_tax.ids)],
                }),
            ],
        })
        order.action_confirm()
        order.write({
            'logspace_quoted_provider_price': 90.0,
            'logspace_quoted_platform_fee': 9.0,
        })
        order.logspace_state = 'dropoff_completed'
        order.action_complete_order()

        bill = order.logspace_provider_bill_id
        self.assertTrue(bill)
        self.assertAlmostEqual(order.amount_total, 136.85)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 125.85)

    def test_full_commission_fee_skips_the_bill_loudly(self):
        """B4: platform_fee_percentage 1.0 reads as 100% commission - payout 0,
        no bill. The skip must log a warning, not pass silently."""
        provider = self.env['res.partner'].create({
            'name': 'Full Fee Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 1.0,
        })
        with self.assertLogs(
            'odoo.addons.appness_logspace.models.sale_order', level='WARNING',
        ) as logs:
            order = self._complete_order(provider)

        self.assertFalse(order.logspace_provider_bill_id)
        self.assertAlmostEqual(order.logspace_provider_bill_amount, 0.0)
        self.assertAlmostEqual(order.logspace_provider_commission_rate, 0.0)
        self.assertTrue(any('skipped' in line for line in logs.output), logs.output)

    def test_provider_reads_order_payout_without_bill_access(self):
        """The order columns are readable by a provider who cannot read bills.

        The compute runs under sudo, so rendering the Logspace order list for
        a provider never needs the account.move ACL.
        """
        provider = self.env['res.partner'].create({
            'name': 'Payout Read Provider',
            'is_provider': True,
            'state': 'approved',
            'platform_fee_percentage': 0.1,
        })
        order = self._complete_order(provider)
        user = self._make_provider_user(provider, 'payout.read.provider@example.com')

        self.assertAlmostEqual(
            order.with_user(user).logspace_provider_bill_amount, 90.0)

    # ---------------------------------------------------------------------
    # ACL + record rule on account.move
    # ---------------------------------------------------------------------

    def test_provider_can_read_only_his_own_bills(self):
        provider_a = self.env['res.partner'].create({
            'name': 'Own Bill Provider',
            'is_provider': True,
            'state': 'approved',
        })
        provider_b = self.env['res.partner'].create({
            'name': 'Other Bill Provider',
            'is_provider': True,
            'state': 'approved',
        })
        order_a = self._complete_order(provider_a)
        order_b = self._complete_order(provider_b)
        bill_a = order_a.logspace_provider_bill_id
        bill_b = order_b.logspace_provider_bill_id

        user_a = self._make_provider_user(provider_a, 'own.bill.provider@example.com')

        self.assertAlmostEqual(bill_a.with_user(user_a).amount_untaxed, 90.0)
        with self.assertRaises(AccessError):
            bill_b.with_user(user_a).read(['amount_untaxed'])

    def test_bills_action_scopes_to_logspace_bills(self):
        """The action domain returns only bills the module created."""
        provider = self.env['res.partner'].create({
            'name': 'Action Domain Provider',
            'is_provider': True,
            'state': 'approved',
        })
        order = self._complete_order(provider)
        plain_bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': provider.id,
            'invoice_line_ids': [Command.create({
                'name': 'Plain vendor bill',
                'quantity': 1,
                'price_unit': 5.0,
            })],
        })

        action = self.env.ref('appness_logspace.action_logspace_provider_bills')
        results = self.env[action.res_model].search(ast.literal_eval(action.domain))
        self.assertIn(order.logspace_provider_bill_id, results)
        self.assertNotIn(plain_bill, results)

    # ---------------------------------------------------------------------
    # Views + menu
    # ---------------------------------------------------------------------

    def test_logspace_order_views_hide_the_order_total(self):
        """The two Logspace views show the payout, not the customer total."""
        tree = self.env.ref('appness_logspace.provider_order_tree')
        self.assertIn('logspace_provider_bill_amount', tree.arch)
        self.assertIn('logspace_provider_commission_rate', tree.arch)
        self.assertNotIn('name="amount_total"', tree.arch)

        form = self.env.ref('appness_logspace.provider_order')
        self.assertIn('logspace_provider_bill_amount', form.arch)
        self.assertIn('logspace_provider_commission_rate', form.arch)
        self.assertNotIn('name="tax_totals"', form.arch)

    def test_provider_bills_menu_survives_menu_filter(self):
        """Level-3 menus reach providers after the deterministic whitelist.

        filter_logspace_menus receives a Python SET; sorting by id is what
        guarantees the Sales parent is whitelisted before this child.
        """
        provider = self.env['res.partner'].create({
            'name': 'Menu Filter Provider',
            'is_provider': True,
            'state': 'approved',
        })
        user = self._make_provider_user(provider, 'menu.filter.provider@example.com')

        menu_xmlids = (
            'appness_logspace.menu_logspace_root',
            'appness_logspace.menu_logspace_sales',
            'appness_logspace.menu_logspace_orders',
            'appness_logspace.menu_logspace_provider_bills',
            'appness_logspace.menu_logspace_configuration',
            'appness_logspace.menu_logspace_vehicle_categories',
        )
        menu_ids = {self.env.ref(xmlid).id for xmlid in menu_xmlids}
        visible = self.env['ir.ui.menu'].with_user(user).filter_logspace_menus(menu_ids)

        self.assertIn(self.env.ref('appness_logspace.menu_logspace_provider_bills').id, visible)
        self.assertNotIn(self.env.ref('appness_logspace.menu_logspace_configuration').id, visible)
        self.assertNotIn(self.env.ref('appness_logspace.menu_logspace_vehicle_categories').id, visible)
