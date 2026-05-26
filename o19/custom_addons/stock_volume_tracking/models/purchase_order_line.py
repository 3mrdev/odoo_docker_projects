from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from .utils import cal_volume_total

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
        store=False,
        readonly=True,
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

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        """Override to pass dimensions from PO line to stock move."""
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.is_volume_tracked:
            vals.update({
                'volume_length': self.volume_length,
                'volume_width': self.volume_width,
                'volume_height': self.volume_height,
            })
        return vals
