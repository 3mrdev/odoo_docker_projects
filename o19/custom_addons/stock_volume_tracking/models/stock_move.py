from odoo import models, fields,api,_
from odoo.exceptions import ValidationError
from .utils import cal_volume_total

class StockMove(models.Model):
    _inherit = "stock.move"

    sale_mrp_lot_id = fields.Many2one('stock.lot')
    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
        readonly=False,
        store=True,
    )
    volume_length = fields.Float(
        string='Length (cm)',
        digits='Volume',
        help="Length dimension from purchase order",
    )
    volume_width = fields.Float(
        string='Width (cm)',
        digits='Volume',
        help="Width dimension from purchase order",
    )
    volume_height = fields.Float(
        string='Height (cm)',
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
    product_yield = fields.Float(string="Expected Yield",compute="_cal_product_yeild",store=True)

    @api.depends("production_id","lot_ids","product_uom_qty","move_line_ids")
    def _cal_product_yeild(self):
        for rec in self:
            product_yield = 0
            lots_volume = 0

            if rec.raw_material_production_id:
                for mline in rec.move_line_ids:
                    lots_volume += mline.lot_id.volume * mline.quantity
                
                if rec.raw_material_production_id.volume > 0:
                    product_yield = lots_volume/rec.raw_material_production_id.volume

            rec.product_yield = product_yield

    @api.depends('volume_length', 'volume_width', 'volume_height','quantity',"product_uom_qty")
    def _compute_volume_total(self):
        for line in self:
            cal_volume_total(self,line,line.product_uom_qty)

    @api.constrains('volume_length', 'volume_width', 'volume_height','product_id.max_volume_length','product_id.max_volume_width','product_id.max_volume_height','product_id.min_volume_length','product_id.min_volume_width','product_id.min_volume_height')
    def _check_min_max_volume_dimensions(self):
        for line in self:
            if line.product_id and line.is_volume_tracked and line.picking_type_id.code == 'incoming':
                minimum_dimensions = f"{line.product_id.min_volume_length}x{line.product_id.min_volume_width}x{line.product_id.min_volume_height}"
                maximum_dimensions = f"{line.product_id.max_volume_length}x{line.product_id.max_volume_width}x{line.product_id.max_volume_height}"
                current_dimensions = f"{line.volume_length}x{line.volume_width}x{line.volume_height}"
                if line.volume_length > line.product_id.max_volume_length or line.volume_width > line.product_id.max_volume_width or line.volume_height > line.product_id.max_volume_height:
                    raise ValidationError(_(f"For product {line.product_id.display_name}, Volume dimensions (LxWxH) {current_dimensions} must be between the minimum {minimum_dimensions} and maximum {maximum_dimensions} volume dimensions."))
                if line.volume_length < line.product_id.min_volume_length or line.volume_width < line.product_id.min_volume_width or line.volume_height < line.product_id.min_volume_height:
                    raise ValidationError(_(f"For product {line.product_id.display_name}, Volume dimensions (LxWxH) {current_dimensions} must be between the minimum {minimum_dimensions} and maximum {maximum_dimensions} volume dimensions."))

    def _prepare_merge_moves_distinct_fields(self):
        """
        Override to prevent merging volume-tracked moves with different dimensions.
        When stock_volume_tracking.merge_by_dimensions is enabled, volume-tracked
        products will only merge if they have identical Length × Width × Height.
        This ensures different physical items (cylinders/batches) remain separate.
        """
        fields = super()._prepare_merge_moves_distinct_fields()

        # Check if dimension-based merge is enabled in settings
        merge_by_dimensions = self.env['ir.config_parameter'].sudo().get_param(
            'stock_volume_tracking.merge_by_dimensions', 'False'
        )

        if merge_by_dimensions == 'True':
            # For volume-tracked products, add dimensions to merge criteria
            # This means moves will only merge if they have the same L×W×H
            volume_tracked_moves = self.filtered(lambda m: m.product_id.is_volume_tracked)
            if volume_tracked_moves:
                # Add volume dimensions to distinct fields
                fields.extend(['volume_length', 'volume_width', 'volume_height'])

        return fields

    #Override Original Odoo Standard Method
    def _create_lot_ids_from_move_line_vals(self, vals_list, product_id, company_id=False):
        """ This method will search or create the lot_id from the lot_name and set it in the vals_list
        """
        lot_names = [vals['lot_name'] for vals in vals_list if vals.get('lot_name')]
        lot_ids = self.env['stock.lot'].search([
            ('product_id', '=', product_id),
            '|', ('company_id', '=', company_id), ('company_id', '=', False),
            ('name', 'in', lot_names),
        ])
        lot_id_names = set(lot_ids.mapped('name'))
        lot_names = [lot_name for lot_name in lot_names if lot_name not in lot_id_names]  # lot_names not found to create
        
        volume_length = 0
        volume_width = 0
        volume_height = 0
        if 'production_id' in vals_list[0]:
            if vals_list:
                production_id = self.env["mrp.production"].browse(vals_list[0]['production_id'])
                for by_product_move in production_id.move_byproduct_ids:
                    if int(vals_list[0]['product_id']) == by_product_move.product_id.id:
                        volume_length = by_product_move.volume_length
                        volume_width = by_product_move.volume_width
                        volume_height = by_product_move.volume_height

            # raise ValidationError(f"{vals_list} LxWxH = {self.volume_length}x{self.volume_width}x{self.volume_height}={self.volume_display}")
        
        lots_to_create_vals = [
            {
                'product_id': product_id, 
                'name': lot_name,
                'volume_length': volume_length, #New line add
                'volume_width': volume_width, #New line add
                'volume_height': volume_height, #New line add
            } for lot_name in lot_names
        ]
        lot_ids |= self.env['stock.lot'].create(lots_to_create_vals)

        lot_id_by_name = {lot.name: lot.id for lot in lot_ids}
        for vals in vals_list:
            lot_name = vals.get('lot_name', None)
            if not lot_name:
                continue
            vals['lot_id'] = lot_id_by_name[lot_name]
            vals['lot_name'] = False

    def _action_assign(self, force_qty=False):
        """Override to assign reserved lots from sale order lines."""
        super()._action_assign(force_qty=force_qty)
        
        for move in self:
            # Check if this move comes from a sale order line with a reserved lot
            if (move.sale_line_id and 
                hasattr(move.sale_line_id, 'reserved_lot_id') and 
                move.sale_line_id.reserved_lot_id):
                reserved_lot = move.sale_line_id.reserved_lot_id
                # Assign the reserved lot to move lines that don't have a lot yet
                for move_line in move.move_line_ids.filtered(lambda ml: not ml.lot_id):
                    move_line.lot_id = reserved_lot
