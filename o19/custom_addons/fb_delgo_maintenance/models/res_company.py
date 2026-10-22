from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    maintenance_loss_location_id = fields.Many2one(
        'stock.location',
        string='Maintenance Loss Location',
        domain=[('usage', '=', 'inventory')],
        check_company=True,
        help="Default destination of the spare parts consumed by maintenance. "
             "Stock moves reaching it generate a journal entry debiting the "
             "equipment's maintenance expense account.")
