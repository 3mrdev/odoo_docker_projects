# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.

from odoo.addons.payment.tests.common import PaymentCommon


class OMPayCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ompay = cls._prepare_provider('ompay', update_values={
            'ompay_api_key': 'ompay-test-api-key',
            'ompay_api_secret': 'ompay-test-api-secret',
        })
        cls.provider = cls.ompay
        cls.currency = cls.env.ref('base.OMR')
        cls.amount = 12.5
        cls.payment_method = cls.env['payment.method']._get_from_code('card')
        cls.reference = 'OMPay-TEST-001'

    def _create_ompay_transaction(self, **values):
        transaction_values = {
            'provider_id': self.provider.id,
            'payment_method_id': self.payment_method.id,
            'reference': self.reference,
            'amount': self.amount,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'operation': 'online_redirect',
            **values,
        }
        return self.env['payment.transaction'].create(transaction_values)

    @staticmethod
    def _response(data):
        return {'success': True, 'data': data}

    def _inquiry_data(self, status='PROCESSING', **values):
        return {
            'transaction_id': '11111111-1111-1111-1111-111111111111',
            'reference_number': self.reference,
            'status': status,
            'amount': '12.500',
            'currency': 'OMR',
            **values,
        }
