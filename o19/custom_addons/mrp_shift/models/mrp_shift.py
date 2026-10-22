from odoo import fields, models


class MrpShift(models.Model):
    _name = 'mrp.shift'
    _description = 'Production Shift'
    _order = 'sequence, id'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
