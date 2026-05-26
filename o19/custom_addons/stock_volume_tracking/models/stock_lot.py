from odoo import models, fields, api
from .utils import cal_volume_total

class StockLot(models.Model):
    _inherit = "stock.lot"

    image = fields.Binary()
    is_volume_tracked = fields.Boolean(
        related='product_id.is_volume_tracked',
        string="Volume Tracked",
    )
    is_cost_tracked = fields.Boolean(
        related='product_id.is_cost_tracked',
        string="Cost Tracked",
    )
    volume_length = fields.Float('Length (cm)', help="Length dimension", digits='Volume')
    volume_width = fields.Float('Width (cm)', help="Width dimension", digits='Volume')
    volume_height = fields.Float('Height (cm)', help="Height dimension", digits='Volume')
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

    cost_per_volume = fields.Float(
        string='Cost per Volume',
        compute='_compute_cost_per_volume',
        store=True,
        help="Calculated cost per volume: Total Cost / Total Volume",
    )

    is_equal_volume_cost = fields.Boolean(
        compute='_compute_is_equal_volume_cost',
        store=True,
        string="Cost Status",
        help="Indicates if the cost per volume is equal to the standard price of the product."
    )

    @api.depends('cost_per_volume','standard_price')
    def _compute_is_equal_volume_cost(self):
        for line in self:
            line.is_equal_volume_cost = line.cost_per_volume == line.standard_price

    @api.depends('volume','product_id.standard_price')
    def _compute_cost_per_volume(self):
        for line in self:
            volume = line.volume
            if volume > 0:
                cubic_volume = volume/1000000
                line.cost_per_volume = line.product_id.standard_price * cubic_volume
            else:
                line.cost_per_volume = 0
    
    def set_cost_per_volume(self):
        for line in self:
            if line.is_cost_tracked:
                if not line.is_equal_volume_cost:
                    line.standard_price = line.cost_per_volume

    #Override to update lot standard price to work with cost_per_volume
    #instead of product_id.standard_price in the standard flow of stock.lot
    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)
        for product, lots_by_product in lots.grouped('product_id').items():
            if product.lot_valuated and product.is_cost_tracked: #NEW
                for lot in lots_by_product: #NEW
                    volume = lot.volume #NEW
                    if volume > 0: #NEW
                        cubic_volume = volume/1000000 #NEW
                        cost_per_cubic_volume = lot.product_id.standard_price * cubic_volume #NEW
                        # Standard Odoo sets standard_price to product.standard_price, override it
                        if not lot.standard_price or lot.standard_price == lot.product_id.standard_price: #NEW
                            lot.with_context(disable_auto_revaluation=True).write({
                                'standard_price': cost_per_cubic_volume,
                            }) #NEW
        return lots

    #Override to update lot standard price to work with cost_per_volume
    #instead of product_id.standard_price in the standard flow of stock.lot
    def _update_standard_price(self):
        for lot in self:
            lot = lot.with_context(disable_auto_revaluation=True)
            if not lot.product_id.lot_valuated:
                continue
            if lot.product_id.cost_method == 'standard':
                if lot.product_id.is_cost_tracked: #NEW
                    volume = lot.volume #NEW
                    if volume > 0: #NEW
                        cubic_volume = volume/1000000 #NEW
                        cost_per_cubic_volume = lot.product_id.standard_price * cubic_volume #NEW
                        if not lot.standard_price or lot.standard_price == lot.product_id.standard_price:
                            lot.standard_price = cost_per_cubic_volume#NEW
                else:#NEW
                    if not lot.standard_price:
                        lot.standard_price = lot.product_id.standard_price#NOT NEW
                continue
            lot.standard_price = lot.product_id._run_avco(lot=lot)[0]

    @api.depends('volume_length', 'volume_width', 'volume_height','product_qty')
    def _compute_volume_total(self):
        for line in self:
            cal_volume_total(self,line,line.product_qty)
    
    @api.depends('name', 'volume_length', 'volume_width', 'volume_height')
    def _compute_display_name(self):
        """Always show dimensions in display name when available."""
        lots_without_volume = self.env['stock.lot']
        for lot in self:
            if lot.is_volume_tracked:
                lot.display_name = f"{lot.name}-{lot.volume_length}×{lot.volume_width}×{lot.volume_height}"
            else:
                lots_without_volume |= lot
        
        if lots_without_volume:
            super(StockLot, lots_without_volume)._compute_display_name()