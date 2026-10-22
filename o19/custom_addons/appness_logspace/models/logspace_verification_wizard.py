# -*- coding: utf-8 -*-

from odoo import fields, models


class LogspaceVerificationWizard(models.TransientModel):
    """Provider must enter the customer's verification code before the
    pickup / drop-off status can be reached. The code itself is only known
    to the customer (shown on their portal tracking page).

    The comparison lives in sale.order._verify_logspace_code so the driver
    portal and this backend wizard cannot drift apart.
    """
    _name = 'logspace.verification.wizard'
    _description = 'Logspace Customer Verification Wizard'

    order_id = fields.Many2one(
        'sale.order',
        string='Order',
        required=True,
        readonly=True,
    )
    code_type = fields.Selection(
        [('pickup', 'Pickup'), ('dropoff', 'Drop-off')],
        string='Verification Type',
        required=True,
        readonly=True,
    )
    entered_code = fields.Char(
        string='Verification Code',
        required=True,
        help='Enter the 4-digit code provided by the customer.',
    )

    def action_verify(self):
        """Validate the entered code and apply the status transition."""
        self.ensure_one()
        order = self.order_id
        # Raises UserError on a mismatch or once the attempt limit is reached.
        order._verify_logspace_code(self.code_type, self.entered_code)
        if self.code_type == 'pickup':
            order._apply_pickup_completed()
        else:
            order._apply_dropoff_completed()
        return {'type': 'ir.actions.act_window_close'}
