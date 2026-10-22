# -*- coding: utf-8 -*-
"""Every logspace_state change must email customer, provider and driver -
one SEPARATE email per party - and only the customer's email carries the
verification codes (the driver collects them from the customer in person)."""

import re
from unittest.mock import patch

from odoo import Command
from odoo.addons.mail.models.mail_template import MailTemplate
from odoo.tests import tagged

from .common import LogspacePaymentCommon


def _code_pattern(code):
    return r'\b%s\b' % (re.escape(code or '____'),)


@tagged('post_install', '-at_install')
class TestLogspaceStatusEmails(LogspacePaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.StatusTemplate = cls.env['mail.template']
        cls.customer_template = cls.env.ref(
            'appness_logspace.email_template_logspace_status_customer')
        cls.provider_template = cls.env.ref(
            'appness_logspace.email_template_logspace_status_provider')
        cls.driver_template = cls.env.ref(
            'appness_logspace.email_template_logspace_status_driver')
        cls.status_template_ids = [
            cls.customer_template.id, cls.provider_template.id, cls.driver_template.id]

        cls.provider = cls.env['res.partner'].create({
            'name': 'Status Test Provider',
            'is_provider': True,
            'state': 'approved',
            'email': 'status.provider@example.com',
        })
        cls.driver = cls.env['res.partner'].create({
            'name': 'Status Test Driver',
            'parent_id': cls.provider.id,
            'is_driver': True,
            'email': 'status.driver@example.com',
        })
        cls.order.write({
            'logspace_provider_id': cls.provider.id,
            'logspace_driver_id': cls.driver.id,
        })
        cls.order.write({'verification_code_pickup': '1234'})

    def _status_sends(self, mock_send):
        """Return the status templates used by send_mail calls in this test."""
        used = []
        for call in mock_send.call_args_list:
            template = call.args[0] if call.args else call.kwargs.get('template')
            if template is not None and template.id in self.status_template_ids:
                used.append(template.id)
        return used

    # ------------------------------------------------------------------
    # Recipients are distinct and private (one party per email)
    # ------------------------------------------------------------------

    def test_each_template_targets_its_own_party(self):
        # partner_to stores the raw template literal "{{ object.partner_id.id }}"
        self.assertIn('partner_id', self.customer_template.partner_to)
        self.assertIn('logspace_provider_id', self.provider_template.partner_to)
        self.assertIn('logspace_driver_id', self.driver_template.partner_to)

    # ------------------------------------------------------------------
    # The write() hook
    # ------------------------------------------------------------------

    def test_transition_emails_all_three_parties(self):
        self.order.action_confirm()
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.write({'logspace_state': 'pickup_started'})
        self.assertEqual(len(self._status_sends(mock_send)), 3)

    def test_same_state_write_sends_nothing(self):
        self.order.action_confirm()
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.write({'logspace_state': 'order_received'})
        self.assertEqual(self._status_sends(mock_send), [])

    def test_draft_order_sends_nothing(self):
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.write({'logspace_state': 'order_received'})
        self.assertEqual(self._status_sends(mock_send), [])

    def test_skip_flag_suppresses_all_emails(self):
        self.order.action_confirm()
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.with_context(
                logspace_skip_status_emails=True,
            ).write({'logspace_state': 'pickup_started'})
        self.assertEqual(self._status_sends(mock_send), [])

    def test_order_completed_skips_customer_only(self):
        """The delivered email is already sent to the customer on completion;
        provider and driver still get their status update."""
        self.order.action_confirm()
        self.order.write({'logspace_state': 'dropoff_completed'})
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            self.order.write({'logspace_state': 'order_completed'})
        used = self._status_sends(mock_send)
        self.assertNotIn(self.customer_template.id, used)
        self.assertIn(self.provider_template.id, used)
        self.assertIn(self.driver_template.id, used)

    def test_non_logspace_order_sends_nothing(self):
        plain_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'pricelist_id': self.pricelist.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })],
        })
        plain_order.action_confirm()
        with patch.object(MailTemplate, 'send_mail', autospec=True) as mock_send:
            plain_order.write({'logspace_state': 'pickup_started'})
        self.assertEqual(self._status_sends(mock_send), [])

    # ------------------------------------------------------------------
    # Content: codes in the customer email ONLY
    # ------------------------------------------------------------------

    def test_customer_email_renders_both_codes(self):
        self.order.write({'verification_code_dropoff': '5678'})
        rendered = self.customer_template.sudo()._render_field(
            'body_html', [self.order.id])[self.order.id]
        rendered = str(rendered)
        self.assertRegex(rendered, _code_pattern('1234'))
        self.assertRegex(rendered, _code_pattern('5678'))

    def test_customer_email_omits_missing_dropoff_code(self):
        self.assertFalse(self.order.verification_code_dropoff)
        rendered = self.customer_template.sudo()._render_field(
            'body_html', [self.order.id])[self.order.id]
        self.assertNotRegex(str(rendered), _code_pattern('5678'))
        self.assertRegex(str(rendered), _code_pattern('1234'))

    def test_provider_email_has_no_codes(self):
        rendered = str(self.provider_template.sudo()._render_field(
            'body_html', [self.order.id])[self.order.id])
        self.assertNotRegex(rendered, _code_pattern('1234'))
        self.assertIn(self.order.name, rendered)

    def test_driver_email_has_no_codes(self):
        rendered = str(self.driver_template.sudo()._render_field(
            'body_html', [self.order.id])[self.order.id])
        self.assertNotRegex(rendered, _code_pattern('1234'))
        self.assertIn(self.order.name, rendered)

    def test_all_emails_carry_the_no_reply_notice(self):
        for template in (self.customer_template, self.provider_template,
                         self.driver_template):
            rendered = str(template.sudo()._render_field(
                'body_html', [self.order.id])[self.order.id]).lower()
            self.assertIn('automated message', rendered)
            self.assertIn('do not reply', rendered)

    def test_subject_carries_the_status_label(self):
        self.order.write({'logspace_state': 'pickup_started'})
        rendered = self.customer_template.sudo()._render_field(
            'subject', [self.order.id])[self.order.id]
        self.assertIn('Pickup Started', str(rendered))

    def test_use_default_to_is_off_so_partner_to_is_honoured(self):
        """With Odoo 19's default use_default_to=True the template's
        partner_to is ignored and every email goes to the order's default
        recipient (the customer). Regression guard: each template must
        resolve to its OWN partner."""
        self.order.write({'logspace_state': 'pickup_started'})
        for template, wanted_partner in (
            (self.customer_template, self.order.partner_id),
            (self.provider_template, self.provider),
            (self.driver_template, self.driver),
        ):
            self.assertFalse(template.use_default_to, template.name)
            mail_values = template.sudo()._generate_template(
                [self.order.id],
                render_fields=['subject', 'body_html', 'email_from',
                               'partner_to', 'email_to'],
            )[self.order.id]
            self.assertEqual(mail_values.get('partner_ids'), [wanted_partner.id])
