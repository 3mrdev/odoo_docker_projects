from odoo import models,fields,api,_

class AccountMove(models.Model):
    _inherit = 'account.move'

    approval_request_id = fields.Many2one('approval.request', string='Approval Request')