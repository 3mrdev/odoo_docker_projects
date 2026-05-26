from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from odoo.fields import Domain
from .utils import cal_volume_total

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
    )
    volume_length = fields.Float(
        string='Length (cm)',
        digits='Volume',
        help="Length dimension of the product",
    )
    volume_width = fields.Float(
        string='Width (cm)',
        digits='Volume',
        help="Width dimension of the product",
    )
    volume_height = fields.Float(
        string='Height (cm)',
        digits='Volume',
        help="Height dimension of the product",
    )
    volume_display = fields.Char(
        string='Line/Square/Cubic',
        compute='_compute_volume_total',
        store=True,
    )
    volume = fields.Float(
        string='Volume',
        compute='_compute_volume_total',
        store=True,
        digits='Volume',
        help="Calculated volume: Length×Width×Height",
    )
    volume_total = fields.Float(
        string='Total Volume',
        compute='_compute_volume_total',
        store=True,
        digits='Volume',
        help="Calculated volume: Length×Width×Height",
    )
    reserved_lot_id = fields.Many2one(
        'stock.lot',
        string="Reserved Lot",
        copy=False,
        help="Select a specific lot to reserve for this sale. "
             "The lot dimensions will be shown in the dropdown.",
    )
    available_lot_ids = fields.Many2many(
        'stock.lot',
        string="Available Lots",
        compute='_compute_available_lot_ids',
        help="Lots available for selection (with quantity > 0)",
    )
    lot_volume_display = fields.Char(
        string="Lot Line/Square/Cubic",
        related='reserved_lot_id.volume_display',
        readonly=True,
    )
    lot_volume_total = fields.Float(
        string="Lot Volume",
        related='reserved_lot_id.volume_total',
        readonly=True,
    )
    lot_product_qty = fields.Float(
        string="Lot Qty",
        related='reserved_lot_id.product_qty',
        readonly=True,
    )

    sale_mrp_bom_lines = fields.One2many(
        'sale.mrp.bom.line',
        'sale_order_line_id',
        string='BOM Lines',
        copy=False,
    )

    @api.depends('volume_length', 'volume_width', 'volume_height','product_uom_qty')
    def _compute_volume_total(self):
        for line in self:
            cal_volume_total(self,line,line.product_uom_qty)


    @api.constrains('volume_length', 'volume_width', 'volume_height','product_id.max_volume_length','product_id.max_volume_width','product_id.max_volume_height','product_id.min_volume_length','product_id.min_volume_width','product_id.min_volume_height')
    def _check_min_max_volume_dimensions(self):
        for line in self:
            if line.product_id and line.is_volume_tracked:
                minimum_dimensions = f"{line.product_id.min_volume_length}x{line.product_id.min_volume_width}x{line.product_id.min_volume_height}"
                maximum_dimensions = f"{line.product_id.max_volume_length}x{line.product_id.max_volume_width}x{line.product_id.max_volume_height}"
                current_dimensions = f"{line.volume_length}x{line.volume_width}x{line.volume_height}"
                if line.volume_length > line.product_id.max_volume_length or line.volume_width > line.product_id.max_volume_width or line.volume_height > line.product_id.max_volume_height:
                    raise ValidationError(_(f"For product {line.product_id.display_name}, Volume dimensions (LxWxH) {current_dimensions} must be between the minimum {minimum_dimensions} and maximum {maximum_dimensions} volume dimensions."))
                if line.volume_length < line.product_id.min_volume_length or line.volume_width < line.product_id.min_volume_width or line.volume_height < line.product_id.min_volume_height:
                    raise ValidationError(_(f"For product {line.product_id.display_name}, Volume dimensions (LxWxH) {current_dimensions} must be between the minimum {minimum_dimensions} and maximum {maximum_dimensions} volume dimensions."))

    # def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
    #     """Override to pass dimensions from PO line to stock move."""
    #     vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
    #     if self.is_volume_tracked:
    #         vals.update({
    #             'volume_length': self.volume_length,
    #             'volume_width': self.volume_width,
    #             'volume_height': self.volume_height,
    #         })
    #     return vals

    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_available_lot_ids(self):
        """Compute available lots with stock for the product."""
        for line in self:
            if not line.product_id or not line.is_volume_tracked:
                line.available_lot_ids = False
                continue
            
            # Find lots with available quantity
            domain = Domain([
                ('product_id', '=', line.product_id.id),
                ('product_qty', '>', 0),
            ])
            # Add company filter
            if line.company_id:
                domain &= Domain([('company_id', 'in', [line.company_id.id, False])])
            
            available_lots = self.env['stock.lot'].search(domain)
            line.available_lot_ids = available_lots

    @api.onchange('product_id')
    def _onchange_product_clear_lot(self):
        """Clear reserved lot when product changes."""
        if self.reserved_lot_id and self.reserved_lot_id.product_id != self.product_id:
            self.reserved_lot_id = False

    # @api.onchange('reserved_lot_id')
    # def _onchange_reserved_lot_id(self):
    #     """Update product description with lot dimensions."""
    #     if self.reserved_lot_id and self.reserved_lot_id.volume_display:
    #         # Optionally append dimensions to name
    #         pass  # Keep it simple for now

    def get_available_product_qty(self):
        available_product_qty = 0
        for lot in self.available_lot_ids:
            if self.volume_length == lot.volume_length and \
                self.volume_width == lot.volume_width and \
                self.volume_height == lot.volume_height:
                available_product_qty += lot.product_qty
        return available_product_qty
    
    def generate_mrp_production(self):
        if self.is_volume_tracked:
            move_raw_ids = []
            if self.sale_mrp_bom_lines:
                for bom_line in self.sale_mrp_bom_lines:
                    move_raw_ids.append((0, 0,{
                        'product_id': bom_line.product_id.id,
                        'product_uom_qty': bom_line.quantity,
                        'sale_mrp_lot_id':bom_line.lot_id.id
                    }))

                available_product_qty = self.get_available_product_qty()
                product_qty = self.product_uom_qty - available_product_qty

                mo = {
                    'product_id': self.product_id.id,
                    'product_qty': product_qty,
                    'picking_type_id': picking_type_id,
                    'volume_length': self.volume_length,
                    'volume_width': self.volume_width,
                    'volume_height': self.volume_height,
                    'sale_line_id': self.id,
                    'origin': self.order_id.name,
                    'move_raw_ids': move_raw_ids,
                }
                
                picking_type_id = self.order_id.warehouse_id.manu_type_id or False
                if picking_type_id:
                    mo['picking_type_id'] = picking_type_id.id

                if product_qty > 0:
                    production = self.env['mrp.production'].create(mo)
                    # production.action_confirm()
                    return production
        return False

    def _prepare_procurement_values(self):
        """Pass reserved lot info to procurement."""
        values = super(SaleOrderLine, self)._prepare_procurement_values()
        if self.is_volume_tracked:
            values.update({
                'volume_length': self.volume_length,
                'volume_width': self.volume_width,
                'volume_height': self.volume_height,
            })
            # production = self.generate_mrp_production()
            # if production:
            #     values['created_production_id'] = production.id
        if self.reserved_lot_id:
            values['reserved_lot_id'] = self.reserved_lot_id.id
        return values
