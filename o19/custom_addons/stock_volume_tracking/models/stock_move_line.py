from odoo import models, fields, api
from .utils import cal_volume_total

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    sale_mrp_lot_id = fields.Many2one('stock.lot',related='move_id.sale_mrp_lot_id',store=True)
    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
    )
    volume_length_move = fields.Float(
        string='MLength (cm)',
        related='move_id.volume_length',
        # readonly=False,
        store=True,
    )
    volume_width_move = fields.Float(
        string='MWidth (cm)',
        related='move_id.volume_width',
        # readonly=False,
        store=True,
    )
    volume_height_move = fields.Float(
        string='MHeight (cm)',
        related='move_id.volume_height',
        # readonly=False,
        store=True,
    )
    volume_length = fields.Float(
        string='Length (cm)',
        related='lot_id.volume_length',
        # readonly=False,
        store=True,
    )
    volume_width = fields.Float(
        string='Width (cm)',
        related='lot_id.volume_width',
        # readonly=False,
        store=True,
    )
    volume_height = fields.Float(
        string='Height (cm)',
        related='lot_id.volume_height',
        # readonly=False,
        store=True,
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

    def _get_aggregated_properties(self, move_line=False, move=False):
        """Override to inject volume tracking data into the aggregated line dict
        so that the delivery report template can display dimensions."""
        properties = super()._get_aggregated_properties(move_line=move_line, move=move)
        move = move or (move_line and move_line.move_id)
        if move:
            properties['is_volume_tracked'] = move.is_volume_tracked
            if move.is_volume_tracked:
                properties['volume_length'] = move.volume_length
                properties['volume_width'] = move.volume_width
                properties['volume_height'] = move.volume_height
        return properties

    @api.depends('volume_length', 'volume_width', 'volume_height','quantity')
    def _compute_volume_total(self):
        for line in self:
            cal_volume_total(self,line,line.quantity)

    # @api.onchange('volume_length', 'volume_width', 'volume_height')
    # def _onchange_volume(self):
    #     for line in self:
    #         if line.product_id.is_volume_tracked:
    #             matching_lot = line._find_matching_lot()
    #             if matching_lot:
    #                 line.lot_name = matching_lot.name
    #             else:
    #                 volume_total = (line.volume_length or 0) * (line.volume_width or 0) * (line.volume_height or 0)
    #                 line.lot_name = 'VOL'+str(volume_total)

    def _prepare_new_lot_vals(self):
        """Override to include dimensions when creating new lot."""
        vals = super()._prepare_new_lot_vals()
        if self.is_volume_tracked:
            vals.update({
                'volume_length': self.volume_length_move,
                'volume_width': self.volume_width_move,
                'volume_height': self.volume_height_move,
            })
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        """Override to auto-find matching lot based on dimensions."""
        for vals in vals_list:
            product_id = vals.get('product_id')
            if product_id:
                product = self.env['product.product'].browse(product_id)
                if product.is_volume_tracked:
                    move_id = vals.get('move_id')
                    sale_mrp_lot_id = vals.get('sale_mrp_lot_id', 0)
                    
                    if move_id:
                        move = self.env['stock.move'].browse(move_id)
                        
                        matching_lot = False
                        if move.sale_mrp_lot_id:
                            matching_lot = move.sale_mrp_lot_id
                        else:
                            if sale_mrp_lot_id:
                                matching_lot = self.env['stock.lot'].browse(sale_mrp_lot_id)

                        if matching_lot:
                            quant = self.env['stock.quant'].search(
                                [('lot_id', '=', matching_lot.id), ('quantity', '>', '0.0'), ('location_id', 'child_of', move.location_id.id)],
                                order='id desc',
                                limit=1
                            )
                            if quant:
                                vals.update({
                                    'quant_id': quant.id,
                                })
                            # else:
                            #     vals.update({
                            #         'lot_name': matching_lot.name,
                            #     })
        
        return super().create(vals_list)

    # def _find_matching_lot(self):
    #     """Find existing lot with matching product and dimensions."""
    #     self.ensure_one()
    #     if not self.is_volume_tracked:
    #         return self.env['stock.lot']
        
    #     domain = [
    #         ('product_id', '=', self.product_id.id),
    #         ('volume_length', '=', self.volume_length),
    #         ('volume_width', '=', self.volume_width),
    #         ('volume_height', '=', self.volume_height),
    #     ]
    #     # Add company filter if applicable
    #     if self.company_id:
    #         domain.append(('company_id', 'in', [self.company_id.id, False]))
        
    #     return self.env['stock.lot'].search(domain, limit=1)

    # @api.model_create_multi
    # def create(self, vals_list):
    #     """Override to auto-find matching lot based on dimensions."""
    #     for vals in vals_list:
    #         # Only process if we have dimensions and a lot_name but no lot_id
    #         product_id = vals.get('product_id')
    #         if product_id:
    #             product = self.env['product.product'].browse(product_id)
    #             if product.is_volume_tracked:
    #                 # Get dimensions from vals or from related move
    #                 move_id = vals.get('move_id')
    #                 volume_length = vals.get('volume_length', 0)
    #                 volume_width = vals.get('volume_width', 0)
    #                 volume_height = vals.get('volume_height', 0)
                    
    #                 # If dimensions are in move but not in vals, get them from move
    #                 if move_id and not (volume_length and volume_width and volume_height):
    #                     move = self.env['stock.move'].browse(move_id)
    #                     volume_length = volume_length or move.volume_length
    #                     volume_width = volume_width or move.volume_width
    #                     volume_height = volume_height or move.volume_height
                    
    #                 # Search for matching lot
    #                 # if volume_length and volume_width and volume_height:
    #                 domain = [
    #                     ('product_id', '=', product_id),
    #                     ('volume_length', '=', volume_length),
    #                     ('volume_width', '=', volume_width),
    #                     ('volume_height', '=', volume_height),
    #                 ]
    #                 matching_lot = self.env['stock.lot'].search(domain, limit=1)
    #                 if matching_lot:
    #                     vals['lot_name'] = matching_lot.name
    #                 else:
    #                     volume_total = (volume_length or 0) * (volume_width or 0) * (volume_height or 0)
    #                     vals['lot_name'] = 'VOL'+str(volume_total)
        
    #     return super().create(vals_list)

    # def _create_and_assign_production_lot(self):
    #     """Override to find matching lots or create new ones with dimensions."""
    #     # Separate volume-tracked move lines for special handling
    #     volume_tracked_lines = self.filtered(
    #         lambda ml: ml.is_volume_tracked and 
    #         ml.volume_length and ml.volume_width and ml.volume_height
    #     )
    #     other_lines = self - volume_tracked_lines
        
    #     # Handle volume-tracked lines: find or create lots
    #     for ml in volume_tracked_lines:
    #         if ml.lot_id:
    #             continue  # Already has a lot
            
    #         # Try to find matching lot
    #         matching_lot = ml._find_matching_lot()
    #         if matching_lot:
    #             ml.lot_id = matching_lot
    #         else:
    #             # Create new lot with dimensions
    #             lot_vals = ml._prepare_new_lot_vals()
    #             new_lot = self.env['stock.lot'].create(lot_vals)
    #             ml.lot_id = new_lot
        
    #     # Let standard logic handle other lines
    #     if other_lines:
    #         super(StockMoveLine, other_lines)._create_and_assign_production_lot()
