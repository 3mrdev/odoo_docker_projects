from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    approval_request_id = fields.Many2one('approval.request', string='Approval Request')
