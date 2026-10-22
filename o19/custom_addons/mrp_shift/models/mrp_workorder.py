from odoo import api, fields, models


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    shift_id = fields.Many2one(
        'mrp.shift',
        string='Shift',
        index=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        to_fetch = {
            vals['production_id']
            for vals in vals_list
            if not vals.get('shift_id') and vals.get('production_id')
        }
        shifts = {
            production.id: production.shift_id.id
            for production in self.env['mrp.production'].browse(to_fetch)
        } if to_fetch else {}
        for vals in vals_list:
            if not vals.get('shift_id') and vals.get('production_id'):
                vals['shift_id'] = shifts[vals['production_id']]
        return super().create(vals_list)
