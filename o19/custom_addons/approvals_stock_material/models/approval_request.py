from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # Computed available warehouses for domain
    available_source_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        compute='_compute_available_warehouses',
        string='Available Source Warehouses')

    available_dest_warehouse_ids = fields.Many2many(
        'stock.warehouse',
        compute='_compute_available_warehouses',
        string='Available Destination Warehouses')

    # Warehouse selection with dynamic domain
    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Source Warehouse',
        readonly=False,
        domain="[('id', 'in', available_source_warehouse_ids)]")

    dest_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Destination Warehouse',
        readonly=False,
        domain="[('id', 'in', available_dest_warehouse_ids)]")

    # Computed available locations for domain (Odoo 19 pattern)
    available_source_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_available_source_locations',
        string='Available Source Locations')

    available_dest_location_ids = fields.Many2many(
        'stock.location',
        compute='_compute_available_dest_locations',
        string='Available Destination Locations')

    # Location selection with dynamic domain
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        domain="[('id', 'in', available_source_location_ids)]")

    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        domain="[('id', 'in', available_dest_location_ids)]")

    # Stock pickings created from this request
    stock_picking_ids = fields.One2many('stock.picking', 'approval_request_id', string='Stock Transfers')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count')

    @api.depends('stock_picking_ids')
    def _compute_stock_picking_count(self):
        for request in self:
            request.stock_picking_count = len(request.stock_picking_ids)

    @api.depends('category_id', 'category_id.source_warehouse_ids', 'category_id.dest_warehouse_ids')
    def _compute_available_warehouses(self):
        """Compute available warehouses based on category restrictions."""
        for request in self:
            # If category has available warehouses, use those; otherwise all warehouses
            if request.category_id and request.category_id.source_warehouse_ids:
                request.available_source_warehouse_ids = request.category_id.source_warehouse_ids.ids
            else:
                request.available_source_warehouse_ids = self.env['stock.warehouse'].search([]).ids

            if request.category_id and request.category_id.dest_warehouse_ids:
                request.available_dest_warehouse_ids = request.category_id.dest_warehouse_ids.ids
            else:
                request.available_dest_warehouse_ids = self.env['stock.warehouse'].search([]).ids

    @api.depends('source_warehouse_id', 'category_id', 'category_id.source_location_ids')
    def _compute_available_source_locations(self):
        """Compute available source locations based on warehouse and category restrictions."""
        Location = self.env['stock.location']
        for request in self:
            # Start with all internal locations
            domain = [('usage', '=', 'internal')]

            # Layer 1: Filter by selected warehouse (if any)
            if request.source_warehouse_id:
                domain.extend(['|', ('warehouse_id', '=', request.source_warehouse_id.id), ('warehouse_id', '=', False)])

            location_ids = Location.search(domain).ids

            # Layer 2: Filter by category's available locations (if set)
            if request.category_id and request.category_id.source_location_ids:
                category_location_ids = request.category_id.source_location_ids.ids
                location_ids = list(set(location_ids) & set(category_location_ids))

            request.available_source_location_ids = location_ids

    @api.depends('dest_warehouse_id', 'category_id', 'category_id.dest_location_ids')
    def _compute_available_dest_locations(self):
        """Compute available destination locations based on warehouse and category restrictions."""
        Location = self.env['stock.location']
        for request in self:
            # Start with all internal locations
            domain = [('usage', '=', 'internal')]

            # Layer 1: Filter by selected warehouse (if any)
            if request.dest_warehouse_id:
                domain.extend(['|', ('warehouse_id', '=', request.dest_warehouse_id.id), ('warehouse_id', '=', False)])

            location_ids = Location.search(domain).ids

            # Layer 2: Filter by category's available locations (if set)
            if request.category_id and request.category_id.dest_location_ids:
                category_location_ids = request.category_id.dest_location_ids.ids
                location_ids = list(set(location_ids) & set(category_location_ids))

            request.available_dest_location_ids = location_ids

    @api.onchange('approval_type')
    def _onchange_approval_type_stock(self):
        """Reset warehouse and location selections when approval type changes."""
        super()._onchange_approval_type()
        if self.approval_type == 'stock_material':
            self.source_warehouse_id = False
            self.dest_warehouse_id = False
            self.source_location_id = False
            self.dest_location_id = False

    @api.onchange('source_warehouse_id')
    def _onchange_source_warehouse(self):
        """Reset source location when warehouse changes."""
        self.source_location_id = False

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse(self):
        """Reset destination location when warehouse changes."""
        self.dest_location_id = False

    def _get_source_warehouse_domain(self):
        """Return domain for source warehouse based on category."""
        if self.category_id and self.category_id.source_warehouse_ids:
            return [('id', 'in', self.category_id.source_warehouse_ids.ids)]
        return []

    def _get_dest_warehouse_domain(self):
        """Return domain for destination warehouse based on category."""
        if self.category_id and self.category_id.dest_warehouse_ids:
            return [('id', 'in', self.category_id.dest_warehouse_ids.ids)]
        return []

    def action_approve(self, approver=None):
        if self.approval_type == 'stock_material':
            if not self.source_warehouse_id or not self.dest_warehouse_id:
                raise UserError(_("Source and Destination warehouses are required for stock material transfer."))
            if not self.source_location_id or not self.dest_location_id:
                raise UserError(_("Source and Destination locations are required for stock material transfer."))

            # Validate warehouses are valid based on category restrictions
            source_wh_domain = self._get_source_warehouse_domain()
            dest_wh_domain = self._get_dest_warehouse_domain()

            if source_wh_domain:
                valid_source_wh = self.env['stock.warehouse'].search_count([('id', '=', self.source_warehouse_id.id)] + source_wh_domain)
                if not valid_source_wh:
                    raise UserError(_("Selected source warehouse is not valid for this approval category."))

            if dest_wh_domain:
                valid_dest_wh = self.env['stock.warehouse'].search_count([('id', '=', self.dest_warehouse_id.id)] + dest_wh_domain)
                if not valid_dest_wh:
                    raise UserError(_("Selected destination warehouse is not valid for this approval category."))

            # Validate locations are in the computed available locations
            if self.source_location_id not in self.available_source_location_ids:
                raise UserError(_("Selected source location is not valid for this approval category."))
            if self.dest_location_id not in self.available_dest_location_ids:
                raise UserError(_("Selected destination location is not valid for this approval category."))

        return super().action_approve(approver)

    def action_create_custom_by_type(self):
        if self.approval_type == 'stock_material':
            return self._action_create_stock_transfers()
        return super().action_create_custom_by_type()

    def _action_create_stock_transfers(self):
        """Create 2 pickings with dependency: Source→Transit, Transit→Destination."""
        self.ensure_one()

        if not self.source_warehouse_id or not self.dest_warehouse_id:
            raise UserError(_("Source and Destination warehouses are required."))
        if not self.source_location_id or not self.dest_location_id:
            raise UserError(_("Source and Destination locations are required."))
        if not self.product_line_ids:
            raise UserError(_("At least one product line is required."))

        # Get transit location from company
        transit_location = self.company_id.internal_transit_location_id
        if not transit_location:
            raise UserError(_("Company '%s' does not have an internal transit location configured.", self.company_id.name))

        # Validate product lines
        for line in self.product_line_ids:
            if not line.product_id:
                raise UserError(_("Please select a product for all lines."))
            if line.quantity <= 0:
                raise UserError(_("Quantity must be greater than 0 for product '%s'.", line.product_id.name))

        # Get picking types
        source_picking_type = self._get_internal_picking_type(self.source_warehouse_id)
        dest_picking_type = self._get_internal_picking_type(self.dest_warehouse_id)

        # Create first picking: Source Location → Transit
        picking_1_vals = {
            'approval_request_id': self.id,
            'picking_type_id': source_picking_type.id,
            'location_id': self.source_location_id.id,
            'location_dest_id': transit_location.id,
            'origin': self.name,
            'move_ids': [],
        }

        picking_1_vals_custom_values = super()._get_custom_values()
        if picking_1_vals_custom_values:
            picking_1_vals.update(picking_1_vals_custom_values)

        move_vals_list = []
        for line in self.product_line_ids:
            move_vals_list.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
                'location_id': self.source_location_id.id,
                'location_dest_id': transit_location.id,
                'description_picking': line.description or line.product_id.display_name,
            }))
        picking_1_vals['move_ids'] = move_vals_list

        picking_1 = self.env['stock.picking'].create(picking_1_vals)

        # Create second picking: Transit → Destination (with dependency on first)
        picking_2_vals = {
            'approval_request_id': self.id,
            'picking_type_id': dest_picking_type.id,
            'location_id': transit_location.id,
            'location_dest_id': self.dest_location_id.id,
            'origin': self.name,
            'move_ids': [],
        }

        picking_2_vals_custom_values = super()._get_custom_values()
        if picking_2_vals_custom_values:
            picking_2_vals.update(picking_2_vals_custom_values)

        move_vals_list_2 = []
        for i, line in enumerate(self.product_line_ids):
            # Link to the corresponding move from picking_1
            origin_move = picking_1.move_ids[i] if i < len(picking_1.move_ids) else False
            move_vals_list_2.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
                'location_id': transit_location.id,
                'location_dest_id': self.dest_location_id.id,
                'description_picking': line.description or line.product_id.display_name,
                'move_orig_ids': [(6, 0, [origin_move.id])] if origin_move else False,
            }))
        picking_2_vals['move_ids'] = move_vals_list_2

        picking_2 = self.env['stock.picking'].create(picking_2_vals)

        # Confirm pickings (reserve them)
        picking_1.action_confirm()
        picking_2.action_confirm()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Transfers'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', [picking_1.id, picking_2.id])],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def _get_internal_picking_type(self, warehouse):
        """Get internal transfer picking type for warehouse."""
        picking_type = warehouse.int_type_id
        if not picking_type:
            raise UserError(_("Warehouse '%s' does not have an internal transfer picking type.", warehouse.name))
        return picking_type

    def action_open_stock_transfers(self):
        """Return the list of stock transfers created from this approval request."""
        self.ensure_one()
        return {
            'name': _('Stock Transfers'),
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.stock_picking_ids.ids)],
        }
