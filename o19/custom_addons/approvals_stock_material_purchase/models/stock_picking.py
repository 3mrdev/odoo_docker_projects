from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ==========================================================================
    # LINKING FIELDS
    # ==========================================================================
    origin_receipt_picking_id = fields.Many2one(
        'stock.picking',
        string='Origin PO Receipt',
        index=True,
        help="The PO receipt that this transfer was created from (for sequential workflow)"
    )

    is_from_approval_receipt = fields.Boolean(
        string='From Approval Receipt',
        default=False,
        index=True,
        help="True if this picking was created from a PO receipt in approval workflow"
    )

    # ==========================================================================
    # AUTO-TRANSFER TRIGGER
    # ==========================================================================
    def button_validate(self):
        """Override to trigger auto-transfer creation for approval workflow."""
        res = super().button_validate()

        # Only process if this is a PO receipt (incoming picking with purchase_id)
        if self.picking_type_id.code == 'incoming' and self.purchase_id:
            self._trigger_approval_auto_transfers()

        return res

    def _trigger_approval_auto_transfers(self):
        """Check if this receipt should trigger auto-transfers in any approval request."""
        self.ensure_one()

        # Find the purchase order from this receipt's moves
        purchase_ids = self.move_ids.filtered(
            lambda m: m.purchase_line_id
        ).mapped('purchase_line_id.order_id').ids

        if not purchase_ids:
            return

        purchase_id = purchase_ids[0]

        # Find related approval requests with auto mode enabled
        # Search through: purchase order → product lines → approval request
        self.env.cr.execute("""
            SELECT DISTINCT ar.id
            FROM approval_request ar
            JOIN approval_category ac ON ac.id = ar.category_id
            JOIN approval_product_line apl ON apl.approval_request_id = ar.id
            JOIN purchase_order_line pol ON pol.id = apl.purchase_order_line_id
            WHERE pol.order_id = %s
            AND ac.approval_type = 'stock_material_purchase'
            AND ac.transfer_creation_mode = 'auto_on_validate'
        """, (purchase_id,))

        approval_ids = [row[0] for row in self.env.cr.fetchall()]

        for approval_id in approval_ids:
            approval = self.env['approval.request'].browse(approval_id)

            # Check if destination is configured
            if not approval.dest_warehouse_id or not approval.dest_location_id:
                approval.message_post(
                    body=_("⚠️ <b>Auto-transfer skipped</b> for receipt %s: Destination warehouse/location not configured in approval request.", self.name),
                    subtype_xmlid='mail.mt_note'
                )
                continue

            # Check if transfers already exist for this receipt (only count our custom transfers)
            existing = self.env['stock.picking'].search_count([
                ('origin_receipt_picking_id', '=', self.id),
                ('approval_request_id', '=', approval.id),
                ('is_from_approval_receipt', '=', True),
            ])

            if existing:
                # Already processed, skip silently
                continue

            try:
                # Auto-create transfers
                transfers = approval._create_transfers_from_receipt(self)

                # Log success to approval chatter
                approval.message_post(
                    body=_("✅ <b>Auto-transfers created</b> from receipt %s: %d transfer(s) generated",
                           self.name, len(transfers)),
                    subtype_xmlid='mail.mt_note'
                )

            except Exception as e:
                # Log error but don't block - receipt is already validated
                approval.message_post(
                    body=_("❌ <b>Auto-transfer failed</b> for receipt %s: %s", self.name, str(e)),
                    subtype_xmlid='mail.mt_note'
                )
