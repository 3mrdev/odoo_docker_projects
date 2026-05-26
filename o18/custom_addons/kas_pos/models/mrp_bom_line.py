from odoo import fields,models,api

class MRPBomLine(models.Model):
    _inherit = "mrp.bom.line"

    product_qty = fields.Float('Quantity', default=1.0,digits='BOM Product Unit of Measure', required=True)