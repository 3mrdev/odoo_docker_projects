from odoo import fields,models,api,_
from odoo.exceptions import UserError

class GLNCert(models.Model):
    _name = "gln.cert"
    _description = "GLN Certificate"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string='GLN',required=True,tracking=True)
    latitude = fields.Char(string='Latitude',required=True,tracking=True)
    longitude = fields.Char(string='Longitude',required=True,tracking=True)
    location_name = fields.Char(string='Location Name',required=True,tracking=True)
    sale_order_line_id = fields.Many2one('sale.order.line',string="Sale Order Line",required=True,tracking=True)
    order_id = fields.Many2one('sale.order',string="Order",related='sale_order_line_id.order_id',store=True)
    order_id_domain = fields.Many2one('sale.order',string="Order")

    @api.constrains('sale_order_line_id')
    def _check_sale_order_line_id(self):
        for record in self:
            gln_certs_count = len(record.sale_order_line_id.gln_certs)
            if gln_certs_count > record.sale_order_line_id.max_gln_certs:
                raise UserError(_(f"You have exceeded the maximum allowed GLN Certificates for this order line ({record.sale_order_line_id.display_name})"))