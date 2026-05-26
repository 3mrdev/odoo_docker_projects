from odoo import models, fields, api, _


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    approval_type = fields.Selection(selection_add=[('stock_material', 'Stock Material Transfer')])

    # Available warehouses - if empty, user can choose any warehouse
    source_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'approval_category_src_wh_rel',
        'category_id', 'warehouse_id',
        string='Available Source Warehouses',
        help="If set, users can only select from these source warehouses. If empty, any warehouse is allowed.")

    dest_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        'approval_category_dest_wh_rel',
        'category_id', 'warehouse_id',
        string='Available Destination Warehouses',
        help="If set, users can only select from these destination warehouses. If empty, any warehouse is allowed.")

    # Available locations - subset of selected warehouses
    # If warehouses are set, locations must be from those warehouses
    # If locations are also set, must be subset of warehouses
    source_location_ids = fields.Many2many(
        'stock.location',
        'approval_category_src_loc_rel',
        'category_id', 'location_id',
        string='Available Source Locations',
        domain="[('usage', '=', 'internal'), '|', ('warehouse_id', '=', False), ('warehouse_id', 'in', source_warehouse_ids)]",
        help="If set, users can only select from these source locations. If empty, any internal location is allowed. "
             "If warehouses are specified, locations should be from those warehouses.")

    dest_location_ids = fields.Many2many(
        'stock.location',
        'approval_category_dest_loc_rel',
        'category_id', 'location_id',
        string='Available Destination Locations',
        domain="[('usage', '=', 'internal'), '|', ('warehouse_id', '=', False), ('warehouse_id', 'in', dest_warehouse_ids)]",
        help="If set, users can only select from these destination locations. If empty, any internal location is allowed. "
             "If warehouses are specified, locations should be from those warehouses.")

    @api.onchange('approval_type')
    def _onchange_approval_type(self):
        super()._onchange_approval_type()
        if self.approval_type == 'stock_material':
            self.has_product = 'required'
            self.has_quantity = 'required'
