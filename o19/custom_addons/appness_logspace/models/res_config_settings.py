# -*- coding: utf-8 -*-
from odoo import api, fields, models

# Defaults shown before the admin saves the settings for the first time.
# They reproduce the hard-coded texts that used to live in
# logspace_vendor_templates.xml so the pages render identically out of the box.
# Plain literals: module-level _() runs at import where no language context
# exists (it only logged a WARNING and translated nothing), and these are
# stored config-parameter values, not translatable UI labels.
DEFAULT_CANCEL_REFUND_POLICY = (
    'Free cancellation up to 24 hours before booking date\n'
    '50% refund after Pickup Started\n'
    '0% refund after Pickup Completed')
DEFAULT_ESTIMATED_TIME_POLICY = 'Estimated time after pickup is 2 days.'


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    logspace_cancel_refund_policy = fields.Text(
        string='Cancel / Refund Policy',
        help='Displayed under the Book Now button on the vehicle info page. '
             'One policy point per line.')
    logspace_estimated_time_policy = fields.Text(
        string='Estimated Time Policy',
        help='Displayed above the Book Now button on the vehicle info page.')

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res['logspace_cancel_refund_policy'] = params.get_param(
            'appness_logspace.cancel_refund_policy',
            DEFAULT_CANCEL_REFUND_POLICY)
        res['logspace_estimated_time_policy'] = params.get_param(
            'appness_logspace.estimated_time_policy',
            DEFAULT_ESTIMATED_TIME_POLICY)
        return res

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param(
            'appness_logspace.cancel_refund_policy',
            self.logspace_cancel_refund_policy or '')
        params.set_param(
            'appness_logspace.estimated_time_policy',
            self.logspace_estimated_time_policy or '')
