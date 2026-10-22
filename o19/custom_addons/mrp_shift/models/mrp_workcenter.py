from odoo import fields, models


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    shift_id = fields.Many2one(
        related='workorder_id.shift_id',
        string='Shift',
        readonly=True,
    )
