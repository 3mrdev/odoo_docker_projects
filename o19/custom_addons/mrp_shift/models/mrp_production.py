from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

CONFIRMED_STATES = ('done', 'progress', 'to_close')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    shift_id = fields.Many2one(
        'mrp.shift',
        string='Shift',
        index=True,
    )

    def write(self, vals):
        res = super().write(vals)
        if 'shift_id' in vals:
            # Keep all work orders in sync with the MO shift.
            self.workorder_ids.write({'shift_id': vals['shift_id']})
        return res

    @api.constrains('state', 'shift_id')
    def _check_shift_id_confirmed(self):
        for production in self:
            if production.state in CONFIRMED_STATES and not production.shift_id:
                raise ValidationError(_(
                    "You must define a shift on the manufacturing order %s "
                    "before confirming it.",
                    production.display_name,
                ))
