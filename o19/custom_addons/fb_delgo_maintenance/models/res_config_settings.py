from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    maintenance_loss_location_id = fields.Many2one(
        related='company_id.maintenance_loss_location_id', readonly=False)
