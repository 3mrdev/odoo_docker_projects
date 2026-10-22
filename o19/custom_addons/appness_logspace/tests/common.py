# -*- coding: utf-8 -*-

from odoo import Command

from odoo.addons.payment.tests.common import PaymentCommon


class LogspacePaymentCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pricelist = cls.env['product.pricelist'].create({
            'name': 'Logspace Test Pricelist',
            'currency_id': cls.currency.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Logspace Test Transport',
            'type': 'service',
            'list_price': 100.0,
        })
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'pricelist_id': cls.pricelist.id,
            'is_logspace_order': True,
            'require_payment': True,
            'prepayment_percent': 1.0,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
                'tax_ids': [Command.clear()],
            })],
        })

    def _create_logspace_transaction(
        self, *, amount=None, legacy_link=False, reference=None,
    ):
        values = {
            'amount': amount if amount is not None else self.order.amount_total,
            'currency_id': self.order.currency_id.id,
            'partner_id': self.order.partner_id.id,
            'reference': reference or self.reference,
        }
        if legacy_link:
            values['logspace_order_id'] = self.order.id
        else:
            values['sale_order_ids'] = [Command.set([self.order.id])]
            values['logspace_order_id'] = self.order.id
        return self._create_transaction('redirect', **values)
