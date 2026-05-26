from odoo import models,fields,api,_
from odoo.exceptions import UserError

class ObcChassis(models.Model):
    _name = 'obc.chassis'
    _description = 'OBC Chassis'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(string="Chassis Number",required=True,tracking=True)
    chassis_datamatrix = fields.Char(string="Datamatrix",required=True,tracking=True)
    secret_number_1 = fields.Char(string="Secret Number 1",required=True,tracking=True)
    secret_number_2 = fields.Char(string="Secret Number 2",required=True,tracking=True)
    sale_order_line_id = fields.Many2one('sale.order.line',string="Sale Order Line",required=True,tracking=True)
    order_id = fields.Many2one('sale.order',string="Order",related='sale_order_line_id.order_id',store=True)
    order_id_domain = fields.Many2one('sale.order',string="Order")
    state = fields.Selection([
        ('draft','Draft'),
        ('passed','Passed'),
        ('failed','Failed')
    ],string='State',default='draft',tracking=True)   

    @api.constrains('sale_order_line_id')
    def _check_sale_order_line_id(self):
        for record in self:
            chassis_numbers_count = len(record.sale_order_line_id.chassis_numbers)
            if chassis_numbers_count > record.sale_order_line_id.product_uom_qty:
                raise UserError(_(f"You have exceeded the maximum allowed chassis numbers for this order line ({record.sale_order_line_id.display_name})"))
