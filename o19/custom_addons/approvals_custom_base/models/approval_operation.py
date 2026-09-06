from odoo import models, fields


class ApprovalOperation(models.Model):
    _name = 'approval.operation'
    _description = 'Approval Operation Status'
    _order = 'sequence, id'

    name = fields.Char(string='Operation Status', required=True)
    sequence = fields.Integer(default=10)
