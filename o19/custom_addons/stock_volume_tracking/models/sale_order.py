# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_mrp_bom_lines_count = fields.Integer(string='BOM Lines Count', compute='_compute_bom_lines_count')
    sale_mrp_production_count = fields.Integer(string='Manufacturing Order Count', compute='_compute_mrp_production_count',store=True)
    show_volume_tracked = fields.Boolean(string='Show Volume Tracked', compute='_compute_show_volume_tracked')
    show_mrp_production_button = fields.Boolean(string='Show MRP Production Button', compute='_compute_show_volume_tracked')
    show_mrp_production_alert = fields.Boolean(string='Show MRP Production Alert', compute='_compute_show_volume_tracked')
    mrp_production_created = fields.Boolean(string='Manufacturing Order Created')

    @api.depends('order_line.is_volume_tracked')
    def _compute_show_volume_tracked(self):
        for order in self:
            show_volume_tracked = False
            show_mrp_production_button = False
            show_mrp_production_alert = False
            for line in order.order_line:
                if line.is_volume_tracked:
                    show_volume_tracked = True
                    flag_has_bom_lines = len(line.sale_mrp_bom_lines) > 0
                    flag_has_demand = line.product_uom_qty > line.get_available_product_qty()
                    if flag_has_bom_lines:
                        show_mrp_production_button = True
                    if flag_has_demand:
                        show_mrp_production_alert = True

            order.show_volume_tracked = show_volume_tracked
            order.show_mrp_production_button = show_mrp_production_button
            order.show_mrp_production_alert = show_mrp_production_alert

    @api.depends('order_line.sale_mrp_bom_lines')
    def _compute_bom_lines_count(self):
        for order in self:
            bom_lines_count = 0
            for line in order.order_line:
                bom_lines_count += len(line.sale_mrp_bom_lines)
            order.sale_mrp_bom_lines_count = bom_lines_count

    @api.depends('order_line','mrp_production_created')
    def _compute_mrp_production_count(self):
        for order in self:
            mos = self.env['mrp.production'].search([('sale_line_id.order_id', '=', order.id)])
            mrp_production_count = len(mos)
            order.sale_mrp_production_count = mrp_production_count

    def action_view_bom_lines(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.mrp.bom.line',
            'name': 'BOM Lines',
            'domain': [('order_id', '=', self.id)],
            'context': {'default_order_id_domain': self.id},
            'view_mode': 'list',
            'target': 'current',
        }
    
    def action_view_mrp_production(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'name': 'Manufacturing Orders',
            'domain': [('sale_line_id.order_id', '=', self.id)],
            'view_mode': 'list',
            'target': 'current',
        }

    def action_generate_mrp_production(self):
        for order in self:
            for line in order.order_line:
                if line.is_volume_tracked:
                    production = line.generate_mrp_production()
                    if production:
                        for move in line.move_ids:
                            if move.location_dest_id.usage == 'customer':
                                move.created_production_id = production.id
            order.mrp_production_created = True
                        