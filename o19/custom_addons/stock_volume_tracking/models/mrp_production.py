from odoo import models,fields,api,_
from odoo.exceptions import UserError,ValidationError
from .utils import cal_volume_total

class MRPProduction(models.Model):
    _inherit = "mrp.production"

    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
        # readonly=False,
        store=True,
    )
    volume_length = fields.Float(
        string='Length (cm)',
        digits='Volume',
        help="Length dimension from purchase order",
    )
    volume_width = fields.Float(
        string='Width ',
        digits='Volume',
        help="Width dimension from purchase order",
    )
    volume_height = fields.Float(
        string='Height ',
        digits='Volume',
        help="Height dimension from purchase order",
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
    product_yield = fields.Float(string="Total Expected Yield",compute="_cal_product_yeild",store=True)

    @api.depends("move_raw_ids")
    def _cal_product_yeild(self):
        for rec in self:
            product_yield = 0

            for move in rec.move_raw_ids:
                product_yield += move.product_yield

            rec.product_yield = product_yield

    @api.depends('volume_length', 'volume_width', 'volume_height','product_qty')
    def _compute_volume_total(self):
        for line in self:
            cal_volume_total(self,line,line.product_qty)

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

    def _prepare_stock_lot_values(self):
        """Override to include dimensions when creating new lot."""
        vals = super()._prepare_stock_lot_values()
        if self.is_volume_tracked:
            vals.update({
                'volume_length': self.volume_length,
                'volume_width': self.volume_width,
                'volume_height': self.volume_height,
            })
        return vals

    # def _get_bom_values(self, ratio=1):
    #     bom_lines_values, byproduct_values, operations_values = super()._get_bom_values(ratio)
    #     # By-Product lines values.
    #     byproduct_values = []
    #     for move_byproduct in self.move_byproduct_ids:
    #         uom, qty = super().get_uom_and_quantity(move_byproduct)
    #         bom_byproduct_vals = {
    #             'cost_share': move_byproduct.cost_share,
    #             'product_id': move_byproduct.product_id.id,
    #             'product_qty': qty,
    #             'product_uom_id': uom.id,
    #             'volume_length': self.volume_length,
    #             'volume_width': self.volume_width,
    #             'volume_height': self.volume_height,
    #         }
    #         byproduct_values.append(fields.Command.create(bom_byproduct_vals))

    #     return (bom_lines_values, byproduct_values, operations_values)

    # def button_mark_done(self):
    #     res = super().button_mark_done()
    #     error_messages = ""
    #     for production in self:
    #         if production.is_volume_tracked:
    #             if production.lot_producing_ids:
    #                 lot_producing_id = production.lot_producing_ids[0]
    #                 for move in production.move_raw_ids:
    #                     for move_line in move.move_line_ids:
    #                         if move_line.lot_id:
    #                             if move_line.lot_id.volume_length != lot_producing_id.volume_length or move_line.lot_id.volume_width != lot_producing_id.volume_width or move_line.lot_id.volume_height != lot_producing_id.volume_height:
    #                                 error_messages += f"Lot {move_line.lot_id.display_name} dimensions do not match {production.product_id.name} dimensions {lot_producing_id.display_name}\n"
    #     if error_messages:
    #         raise UserError(error_messages)
    #     return res