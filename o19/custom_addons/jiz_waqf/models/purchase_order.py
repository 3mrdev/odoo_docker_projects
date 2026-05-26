from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    waqf_id = fields.Many2one('jiz.waqf', string='Waqf')