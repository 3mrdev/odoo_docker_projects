from odoo import models


class ApprovalProductLine(models.Model):
    _name = 'approval.product.line'
    _inherit = ['approval.product.line', 'analytic.mixin']
