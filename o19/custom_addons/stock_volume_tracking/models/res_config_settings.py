from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Stock Volume Tracking Settings
    stock_volume_tracking_merge_by_dimensions = fields.Boolean(
        string="Prevent Merge of Different Dimensions",
        help="When enabled, volume-tracked products with different Length × Width × Height "
             "will not be merged into a single line during picking confirmation. "
             "Products with identical dimensions can still be merged. "
             "This applies to all stock operations (receipts, deliveries, internal transfers, manufacturing).",
        config_parameter='stock_volume_tracking.merge_by_dimensions',
        default=True,
    )
