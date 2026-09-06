from odoo import fields, models
from odoo.exceptions import UserError
from odoo.addons.sttl_warehouse_access_control.models.res_users import ResUsers as SttlResUsers

# There's no actual need for cache invalidation in this method at all 
# — the validation loop only reads fields that were just written in the same call, 
# so cache is already consistent. 
# Just remove these both calls from the original method 
# self.env.cache.clear()
# self.env.invalidate_all()

def _fixed_write(self, values):
    res = super(SttlResUsers, self).write(values)

    if self.env.user.has_group('base.group_system'):
        return res

    for location in self.allowed_location_ids:
        if location.warehouse_id and location.warehouse_id not in self.allowed_warehouse_ids:
            raise UserError(
                f"You need warehouse access to view/manage stock in location '{location.name}'"
            )
    return res

SttlResUsers.write = _fixed_write

class ResUsers(models.Model):
    _inherit = 'res.users'

    # Manual route selection - admin decides which routes user sees
    allowed_route_ids = fields.Many2many(
        'stock.route',
        string='Available Routes'
    )
