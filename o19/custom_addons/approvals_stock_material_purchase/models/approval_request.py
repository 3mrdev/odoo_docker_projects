import logging

from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import clean_context

_logger = logging.getLogger(__name__)


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # ==========================================================================
    # TRACKING FIELDS FOR SEQUENTIAL MODE
    # ==========================================================================
    pending_receipt_ids = fields.Many2many(
        'stock.picking',
        'approval_request_pending_receipt_rel',
        'approval_request_id', 'picking_id',
        string='Pending Receipts',
        help="Receipts that need transfers to be created (auto mode tracking)"
    )

    has_pending_receipts = fields.Boolean(
        compute='_compute_has_pending_receipts',
        string='Has Pending Receipts'
    )

    # Related field for easy access in views
    transfer_creation_mode = fields.Selection(
        related='category_id.transfer_creation_mode',
        string='Transfer Creation Mode',
        readonly=True,
        store=False
    )

    @api.depends('pending_receipt_ids')
    def _compute_has_pending_receipts(self):
        for request in self:
            request.has_pending_receipts = bool(request.pending_receipt_ids)

    # ==========================================================================
    # COMPUTE METHODS FOR DESTINATION WAREHOUSE/LOCATION DOMAINS
    # ==========================================================================
    @api.depends('category_id', 'category_id.dest_warehouse_ids')
    def _compute_available_warehouses(self):
        """Override to compute available destination warehouses for combined type."""
        # Call super to handle stock_material type
        super()._compute_available_warehouses()

        # For stock_material_purchase type, only dest warehouses are used (source comes from PO receipt)
        for request in self:
            if request.approval_type == 'stock_material_purchase':
                if request.category_id and request.category_id.dest_warehouse_ids:
                    request.available_dest_warehouse_ids = request.category_id.dest_warehouse_ids.ids
                else:
                    request.available_dest_warehouse_ids = self.env['stock.warehouse'].search([]).ids

    @api.depends('dest_warehouse_id', 'category_id', 'category_id.dest_location_ids')
    def _compute_available_dest_locations(self):
        """Override to compute available destination locations for combined type."""
        # Call super to handle stock_material type
        super()._compute_available_dest_locations()

        # For stock_material_purchase type
        Location = self.env['stock.location']
        for request in self:
            if request.approval_type == 'stock_material_purchase':
                domain = [('usage', '=', 'internal')]
                if request.dest_warehouse_id:
                    domain.extend(['|', ('warehouse_id', '=', request.dest_warehouse_id.id), ('warehouse_id', '=', False)])
                location_ids = Location.search(domain).ids
                if request.category_id and request.category_id.dest_location_ids:
                    category_location_ids = request.category_id.dest_location_ids.ids
                    location_ids = list(set(location_ids) & set(category_location_ids))
                request.available_dest_location_ids = location_ids

    # ==========================================================================
    # ONCHANGE AND VALIDATION
    # ==========================================================================
    @api.onchange('approval_type')
    def _onchange_approval_type_combined(self):
        """Reset fields when switching to/from combined type."""
        if self.approval_type == 'stock_material_purchase':
            self.dest_warehouse_id = False
            self.dest_location_id = False
            self.source_warehouse_id = False
            self.source_location_id = False

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_combined(self):
        """Reset destination location when warehouse changes."""
        self.dest_location_id = False

    def action_approve(self, approver=None):
        """Override to add validation for stock_material_purchase type."""
        # Only validate for combined type - let super handle stock_material
        if self.approval_type == 'stock_material_purchase':
            # Destination is required (source comes from PO receipt)
            if not self.dest_warehouse_id or not self.dest_location_id:
                raise UserError(_(
                    "Destination warehouse and location are required for stock + purchase workflow. "
                    "Source will be determined automatically from the Purchase Order receipt."
                ))

            # Validate warehouses are valid based on category restrictions
            if self.category_id and self.category_id.dest_warehouse_ids:
                valid_dest_wh = self.env['stock.warehouse'].search_count([
                    ('id', '=', self.dest_warehouse_id.id),
                    ('id', 'in', self.category_id.dest_warehouse_ids.ids)
                ])
                if not valid_dest_wh:
                    raise UserError(_("Selected destination warehouse is not valid for this approval category."))

            # Validate locations
            if self.dest_location_id not in self.available_dest_location_ids:
                raise UserError(_("Selected destination location is not valid for this approval category."))

        return super().action_approve(approver)

    # ==========================================================================
    # BUTTON: Create RFQ's (for stock_material_purchase type only)
    # ==========================================================================
    def action_create_rfq_combined(self):
        """Create Purchase Orders from approval request.

        VALIDATION:
        - Must have product lines
        - Each line must have a vendor (seller_id) configured

        Creates: One PO per vendor (grouped by vendor)
        """
        self.ensure_one()
        if self.approval_type != 'stock_material_purchase':
            return

        # Validation: Must have product lines
        if not self.product_line_ids:
            raise UserError(_("You must add at least one product line."))

        # Validation: Each product must have a vendor
        lines_without_vendor = self.product_line_ids.filtered(lambda l: not l.seller_id)
        if lines_without_vendor:
            product_names = ', '.join(lines_without_vendor.mapped('product_id.name'))
            raise UserError(_(
                "Please configure vendors for the following products: %s",
                product_names
            ))

        # Create purchase orders (grouped by vendor)
        self._create_purchase_orders_combined()

        # Log creation to chatter
        self._log_po_creation_to_chatter()

        # For auto mode, notify that we're waiting for receipts
        if self.category_id.transfer_creation_mode == 'auto_on_validate':
            self.message_post(
                body=_("<b>Auto-transfer mode enabled</b>. Transfers will be automatically created when PO receipts are validated."),
                subtype_xmlid='mail.mt_note'
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Orders'),
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'context': clean_context(self.env.context),
            'domain': [('id', 'in', self.product_line_ids.purchase_order_line_id.order_id.ids)],
        }

    def _create_purchase_orders_combined(self):
        """Create purchase orders from approval product lines, grouped by vendor."""
        self.product_line_ids._check_products_vendor()

        for line in self.product_line_ids:
            seller = line.seller_id or line.product_id.with_company(line.company_id)._select_seller(
                quantity=line.po_uom_qty,
                uom_id=line.product_id.uom_id,
            )
            vendor = seller.partner_id
            po_domain = line._get_purchase_orders_domain(vendor)
            purchase_orders = self.env['purchase.order'].search(po_domain)

            if purchase_orders:
                # Existing RFQ found - add to it
                purchase_line = self.env['purchase.order.line'].search([
                    ('order_id', 'in', purchase_orders.ids),
                    ('product_id', '=', line.product_id.id),
                    ('product_uom_id', '=', line.seller_id.product_uom_id.id or line.product_id.uom_id.id),
                ], limit=1)
                if purchase_line:
                    line.purchase_order_line_id = purchase_line.id
                    purchase_line.product_qty += line.po_uom_qty
                    purchase_order = purchase_line.order_id
                else:
                    purchase_order = purchase_orders[0]
                    seller_uom_qty = line.product_uom_id._compute_quantity(line.quantity, seller.product_uom_id)
                    po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                        line.product_id,
                        seller_uom_qty,
                        seller.product_uom_id,
                        line.company_id,
                        vendor,
                        purchase_order,
                    )
                    new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                    line.purchase_order_line_id = new_po_line.id
                    purchase_order.order_line = [(4, new_po_line.id)]

                # Update origin
                new_origin = set([self.name])
                if purchase_order.origin:
                    missing_origin = new_origin - set(purchase_order.origin.split(', '))
                    if missing_origin:
                        purchase_order.write({'origin': purchase_order.origin + ', ' + ', '.join(missing_origin)})
                else:
                    purchase_order.write({'origin': ', '.join(new_origin)})
            else:
                # No RFQ found: create a new one
                po_vals = line._get_purchase_order_values(vendor)
                new_purchase_order = self.env['purchase.order'].create(po_vals)
                seller_uom_qty = line.product_uom_id._compute_quantity(line.quantity, seller.product_uom_id)
                po_line_vals = self.env['purchase.order.line']._prepare_purchase_order_line(
                    line.product_id,
                    seller_uom_qty,
                    seller.product_uom_id,
                    line.company_id,
                    vendor,
                    new_purchase_order,
                )
                new_po_line = self.env['purchase.order.line'].create(po_line_vals)
                line.purchase_order_line_id = new_po_line.id
                new_purchase_order.order_line = [(4, new_po_line.id)]

    # ==========================================================================
    # BUTTON: Transfer Material (for manual mode only)
    # ==========================================================================
    def action_create_transfer_combined(self):
        """Create stock transfers for all validated PO receipts.

        VALIDATION:
        - Must have destination warehouse/location selected
        - Must have at least one validated PO receipt

        Creates: 2 transfers per receipt (Receipt→Transit, Transit→Dest)
        """
        self.ensure_one()
        if self.approval_type != 'stock_material_purchase':
            return

        # Validation: Destination required (source comes from receipt)
        if not self.dest_warehouse_id or not self.dest_location_id:
            raise UserError(_("Destination warehouse and location are required."))

        # Find all done receipts from related POs
        purchase_orders = self.product_line_ids.purchase_order_line_id.order_id
        if not purchase_orders:
            raise UserError(_("No Purchase Orders found. Please create RFQ's first."))

        # Find receipts through stock moves (purchase_id on picking is not stored, can't search directly)
        # Look for pickings that have moves linked to our purchase order lines
        po_line_ids = self.product_line_ids.purchase_order_line_id.ids
        moves = self.env['stock.move'].search([
            ('purchase_line_id', 'in', po_line_ids),
            ('state', '=', 'done'),
        ])
        receipt_ids = moves.mapped('picking_id').ids
        receipts = self.env['stock.picking'].browse(receipt_ids).filtered(
            lambda p: p.picking_type_id.code == 'incoming' and p.state == 'done'
        )

        if not receipts:
            raise UserError(_(
                "No validated receipts found. Please confirm and receive the Purchase Orders first."
            ))

        # Create transfers for each receipt
        created_transfers = self.env['stock.picking']
        processed_receipts = []
        skipped_receipts = []

        for receipt in receipts:
            # Check if transfers already created for this receipt (only count our custom transfers)
            existing = self.env['stock.picking'].search_count([
                ('origin_receipt_picking_id', '=', receipt.id),
                ('approval_request_id', '=', self.id),
                ('is_from_approval_receipt', '=', True),
            ])
            if existing:
                skipped_receipts.append(receipt.name)
                continue

            try:
                transfers = self._create_transfers_from_receipt(receipt)
                created_transfers |= transfers
                processed_receipts.append(receipt.name)
            except Exception as e:
                _logger.error("Transfer creation failed for receipt %s: %s", receipt.name, str(e), exc_info=True)
                # Log error to chatter but continue with other receipts
                self.message_post(
                    body=_("❌ <b>Transfer creation failed</b> for receipt %s: %s", receipt.name, str(e)),
                    subtype_xmlid='mail.mt_note'
                )

        if processed_receipts:
            self.message_post(
                body=_("✅ <b>Transfers created</b> for receipt(s): %s", ', '.join(processed_receipts)),
                subtype_xmlid='mail.mt_note'
            )

        if skipped_receipts:
            self.message_post(
                body=_("ℹ️ <b>Skipped</b> (already processed): %s", ', '.join(skipped_receipts)),
                subtype_xmlid='mail.mt_note'
            )

        if not created_transfers:
            raise UserError(_("All receipts have already been processed. No new transfers created."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Transfers'),
            'res_model': 'stock.picking',
            'domain': [('id', 'in', created_transfers.ids)],
            'view_mode': 'list,form',
            'target': 'current',
        }

    def _create_transfers_from_receipt(self, receipt_picking):
        """Create 2 linked transfers from a PO receipt.

        FLOW:
            Receipt Location (PO destination) → Transit → Final Destination

        Args:
            receipt_picking: A validated stock.picking (PO receipt)

        Returns:
            Recordset of 2 created stock.pickings
        """
        self.ensure_one()

        # Get warehouse from receipt destination
        receipt_dest_location = receipt_picking.location_dest_id
        source_warehouse = receipt_dest_location.warehouse_id

        if not source_warehouse:
            raise UserError(_(
                "Receipt destination location '%s' is not associated with a warehouse.",
                receipt_dest_location.name
            ))

        transit_location = self.company_id.internal_transit_location_id
        if not transit_location:
            raise UserError(_(
                "Company '%s' does not have an internal transit location configured.",
                self.company_id.name
            ))

        # Get picking types
        source_int_type = source_warehouse.int_type_id
        dest_int_type = self.dest_warehouse_id.int_type_id

        if not source_int_type:
            raise UserError(_(
                "Warehouse '%s' does not have an internal transfer picking type.",
                source_warehouse.name
            ))
        if not dest_int_type:
            raise UserError(_(
                "Warehouse '%s' does not have an internal transfer picking type.",
                self.dest_warehouse_id.name
            ))

        # Prepare move lines for all products in the receipt
        move_vals_list_1 = []  # Receipt Dest → Transit
        move_vals_list_2 = []  # Transit → Final Dest

        for receipt_move in receipt_picking.move_ids:
            if receipt_move.quantity <= 0:
                continue  # Skip moves with no quantity done

            # Transfer 1 move: Receipt Destination → Transit
            move_vals_list_1.append((0, 0, {
                'product_id': receipt_move.product_id.id,
                'product_uom_qty': receipt_move.quantity,
                'product_uom': receipt_move.product_uom.id,
                'location_id': receipt_dest_location.id,
                'location_dest_id': transit_location.id,
                'description_picking': receipt_move.description_picking or receipt_move.product_id.display_name,
            }))

        if not move_vals_list_1:
            raise UserError(_("Receipt %s has no products with quantity done.", receipt_picking.name))

        # Get PO name from receipt moves (all moves should have same PO)
        po_name = receipt_picking.move_ids.purchase_line_id.order_id.name
        if po_name:
            origin_str = f"{self.name} ← PO:{po_name} ← Receipt:{receipt_picking.name}"
        else:
            origin_str = f"{self.name} ← Receipt:{receipt_picking.name}"

        # Create Transfer 1: Receipt Destination → Transit
        # Let Odoo generate the name from picking type sequence
        picking_1_vals = {
            'approval_request_id': self.id,
            'origin_receipt_picking_id': receipt_picking.id,
            'is_from_approval_receipt': True,
            'company_id': self.company_id.id,
            'picking_type_id': source_int_type.id,
            'location_id': receipt_dest_location.id,
            'location_dest_id': transit_location.id,
            'origin': origin_str,
            'move_ids': move_vals_list_1,
        }
        picking_1 = self.env['stock.picking'].create(picking_1_vals)
        picking_1.action_confirm()

        # Now prepare Transfer 2 moves with links to Transfer 1
        for i, receipt_move in enumerate(receipt_picking.move_ids):
            if receipt_move.quantity <= 0:
                continue

            origin_move = picking_1.move_ids[i] if i < len(picking_1.move_ids) else False

            move_vals_list_2.append((0, 0, {
                'product_id': receipt_move.product_id.id,
                'product_uom_qty': receipt_move.quantity,
                'product_uom': receipt_move.product_uom.id,
                'location_id': transit_location.id,
                'location_dest_id': self.dest_location_id.id,
                'description_picking': receipt_move.description_picking or receipt_move.product_id.display_name,
                'move_orig_ids': [(6, 0, [origin_move.id])] if origin_move else False,
            }))

        # Create Transfer 2: Transit → Final Destination
        # Let Odoo generate the name from picking type sequence
        picking_2_vals = {
            'approval_request_id': self.id,
            'origin_receipt_picking_id': receipt_picking.id,
            'is_from_approval_receipt': True,
            'company_id': self.company_id.id,
            'picking_type_id': dest_int_type.id,
            'location_id': transit_location.id,
            'location_dest_id': self.dest_location_id.id,
            'origin': origin_str,
            'move_ids': move_vals_list_2,
        }
        picking_2 = self.env['stock.picking'].create(picking_2_vals)
        picking_2.action_confirm()

        return picking_1 | picking_2

    # ==========================================================================
    # SMART BUTTON ACTIONS
    # ==========================================================================
    def action_open_purchase_orders_combined(self):
        """Return the list of purchase orders."""
        self.ensure_one()
        purchase_ids = self.product_line_ids.purchase_order_line_id.order_id.ids
        return {
            'name': _('Purchase Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'context': clean_context(self.env.context),
            'domain': [('id', 'in', purchase_ids)],
        }

    def action_open_stock_transfers_combined(self):
        """Return the list of stock transfers."""
        self.ensure_one()
        return {
            'name': _('Stock Transfers'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.stock_picking_ids.ids)],
        }

    def action_view_pending_receipts(self):
        """Open view of pending receipts that need transfer creation."""
        self.ensure_one()
        return {
            'name': _('Pending Receipts'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.pending_receipt_ids.ids)],
        }

    # ==========================================================================
    # CHATTER LOGGING METHODS
    # ==========================================================================
    def _log_po_creation_to_chatter(self):
        """Log PO creation to approval chatter."""
        purchase_orders_data = self._get_order_data_from_product_lines(self.product_line_ids)
        if purchase_orders_data:
            po_creation_chatter_msg = self._generate_po_log_message("created", purchase_orders_data)
            self.message_post(body=po_creation_chatter_msg, subtype_xmlid='mail.mt_note')

    def _get_order_data_from_product_lines(self, product_lines, include_raw_data=False):
        """Get order data for chatter logging."""
        orders_data = []
        grouped_product_lines = product_lines.grouped(lambda line: line.purchase_order_line_id.order_id)
        for order_id, lines in grouped_product_lines.items():
            if not order_id:
                continue
            order_data = {}
            if include_raw_data:
                order_data["order"] = order_id
                order_data["product_lines"] = lines
            order_data["order_name"] = order_id.name
            order_data["products"] = [(line.product_id.name, line.quantity) for line in lines]
            orders_data.append(order_data)
        return orders_data

    def _generate_po_log_message(self, po_state, purchase_orders_data):
        """Generate PO log message for chatter."""
        log_msg_header_by_state = {
            'created': _("<b>The following products have been added to the RFQs:</b>"),
            'removed': _("<b>The following products have been removed from the RFQs:</b>"),
            'require_manual_action': _("<b>The following products couldn't be removed because the RFQs are not in draft state:</b>"),
        }

        return Markup("%(log_msg_header)s<br><br>%(purchase_log)s<hr>") % {
            'log_msg_header': Markup(log_msg_header_by_state.get(po_state, "")),
            'purchase_log': Markup().join(
                Markup("RFQ <b>%(po_name)s</b>:<br><ul>%(products_lines)s</ul>") % {
                    'po_name': purchase_order['order_name'],
                    'products_lines': Markup().join(
                        Markup("<li>%(quantity)s %(name)s</li>") % {
                            'name': product_line[0],
                            'quantity': product_line[1]
                        } for product_line in purchase_order["products"]
                    )
                } for purchase_order in purchase_orders_data
            )
        }

    # ==========================================================================
    # CANCEL OVERRIDE
    # ==========================================================================
    def action_cancel(self):
        """Override to handle cancellation of combined type."""
        res = super().action_cancel()

        # Handle PO cancellation (from approvals_purchase logic)
        if self.approval_type == 'stock_material_purchase' and self.purchase_order_count:
            purchase_orders_data_per_state = self._cancel_approval_request()
            self._log_po_cancellation_to_chatter(purchase_orders_data_per_state)

        # Handle transfer cancellation
        if self.approval_type == 'stock_material_purchase' and self.stock_picking_count:
            for picking in self.stock_picking_ids:
                if picking.state not in ('done', 'cancel'):
                    picking.action_cancel()

        return res

    def _cancel_approval_request(self):
        """Cancel related purchase orders (adapted from approvals_purchase)."""
        purchase_orders = self.sudo().product_line_ids.purchase_order_line_id.order_id
        purchase_orders_data_per_state = {"removed": [], "require_manual_action": []}

        for purchase_order in purchase_orders:
            product_lines = self.sudo().product_line_ids.filtered(
                lambda line: line.purchase_order_line_id.order_id.id == purchase_order.id
            )

            if purchase_order.state == 'draft':
                purchase_orders_data_per_state["removed"].extend(
                    self._get_order_data_from_product_lines(product_lines)
                )
                removed_lines = self.sudo().env['purchase.order.line']
                for product_line in product_lines:
                    purchase_order_line = product_line.purchase_order_line_id
                    if purchase_order_line.product_qty == product_line.quantity:
                        removed_lines |= purchase_order_line
                    else:
                        purchase_order_line.product_qty -= product_line.quantity
                if len(purchase_order.order_line) == len(removed_lines):
                    purchase_order.write({'state': 'cancel'})
                    purchase_order.unlink()
                elif removed_lines:
                    removed_lines.unlink()
            else:
                purchase_orders_data_per_state["require_manual_action"].extend(
                    self._get_order_data_from_product_lines(product_lines, include_raw_data=True)
                )

            product_lines.purchase_order_line_id = False

        return purchase_orders_data_per_state

    def _log_po_cancellation_to_chatter(self, purchase_orders_data_per_state):
        """Log PO cancellation to chatter."""
        po_cancellation_states = ["removed", "require_manual_action"]
        cancellation_log_msg = ""
        for po_state in po_cancellation_states:
            purchase_orders_data = purchase_orders_data_per_state[po_state]
            if purchase_orders_data:
                cancellation_log_msg += self._generate_po_log_message(po_state, purchase_orders_data)
            if po_state == "require_manual_action":
                self._log_cancellation_exception_to_po_chatter(purchase_orders_data)

        if cancellation_log_msg:
            self.message_post(body=cancellation_log_msg, subtype_xmlid='mail.mt_note')

    def _log_cancellation_exception_to_po_chatter(self, purchase_orders_data):
        """Log cancellation exception to PO chatter."""
        for purchase_order_data in purchase_orders_data:
            purchase_order_data["order"]._activity_schedule_with_view(
                'mail.mail_activity_data_warning',
                views_or_xmlid='approvals_purchase.exception_approval_request_canceled',
                user_id=self.env.user.id,
                render_context={
                    'approval_requests': self,
                    'product_lines': purchase_order_data["product_lines"],
                }
            )
