from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class MaintenanceSparePartsWizard(models.TransientModel):
    _name = 'maintenance.spare.parts.wizard'
    _description = 'Request Spare Parts from a Maintenance Request'

    maintenance_request_id = fields.Many2one(
        'maintenance.request', string='Maintenance Request',
        required=True, ondelete='cascade')
    company_id = fields.Many2one(
        related='maintenance_request_id.company_id')
    category_id = fields.Many2one(
        'approval.category', string='Approval Category', required=True,
        domain="[('approval_type', 'in', ['stock_material', 'stock_material_purchase']),"
               " '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The category drives the approval workflow. Stock Material "
             "consumes from a warehouse, Stock Transfer + Purchase buys the "
             "parts through purchase orders. Create categories in Approvals "
             "> Configuration.")
    category_approval_type = fields.Selection(
        related='category_id.approval_type')
    dest_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Destination Warehouse')
    dest_location_id = fields.Many2one(
        'stock.location', string='Destination (Loss) Location',
        domain="[('usage', '=', 'inventory'),"
               " '|', ('warehouse_id', '=', dest_warehouse_id), ('warehouse_id', '=', False),"
               " '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="The stock moves reaching this location are accounted as "
             "consumption on the equipment's maintenance expense account.")
    source_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Source Warehouse',
        invisible="category_approval_type != 'stock_material'")
    source_location_id = fields.Many2one(
        'stock.location', string='Source Location',
        domain="[('usage', '=', 'internal'),"
               " '|', ('warehouse_id', '=', source_warehouse_id), ('warehouse_id', '=', False),"
               " '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        invisible="category_approval_type != 'stock_material'")

    # -------------------------------------------------------------
    # Defaults
    # -------------------------------------------------------------
    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        request = self.env['maintenance.request'].browse(
            defaults.get('maintenance_request_id'))
        if not request:
            return defaults
        company = request.company_id or self.env.company
        loss = company.maintenance_loss_location_id
        if not loss:
            return defaults
        if 'dest_location_id' in fields_list:
            defaults.setdefault('dest_location_id', loss.id)
        if loss.warehouse_id and 'dest_warehouse_id' in fields_list:
            defaults.setdefault('dest_warehouse_id', loss.warehouse_id.id)
        return defaults

    @api.model_create_multi
    def create(self, vals_list):
        wizards = super().create(vals_list)
        # Safety net when the destination defaults were not applied through
        # default_get (no context defaults available).
        wizards.filtered(
            lambda w: w.maintenance_request_id and not w.dest_location_id
        )._apply_loss_location_defaults()
        return wizards

    def _apply_loss_location_defaults(self):
        for wizard in self:
            company = (
                wizard.maintenance_request_id.company_id or self.env.company)
            loss = company.maintenance_loss_location_id
            if not loss:
                continue
            wizard.dest_location_id = loss
            if loss.warehouse_id:
                wizard.dest_warehouse_id = loss.warehouse_id

    # -------------------------------------------------------------
    # Onchanges
    # -------------------------------------------------------------
    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse(self):
        if (
            self.dest_location_id
            and self.dest_location_id.warehouse_id != self.dest_warehouse_id
        ):
            self.dest_location_id = False

    @api.onchange('source_warehouse_id')
    def _onchange_source_warehouse(self):
        if self.source_warehouse_id:
            self.source_location_id = self.source_warehouse_id.lot_stock_id

    # -------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------
    def action_open_approval_request(self):
        self.ensure_one()
        if not self.env.user.has_group(
            'fb_delgo_maintenance.group_maintenance_spare_parts'
        ):
            raise AccessError(_(
                "You need the \"Request Spare Parts\" access right to "
                "request spare parts."))

        self._check_values()

        # Create the request directly: the stock_material modules' onchanges
        # clear the source/destination locations when a warehouse changes,
        # which also fires when the form opens from context defaults, so
        # passing defaults through is not reliable.
        vals = {
            'category_id': self.category_id.id,
            'maintenance_request_id': self.maintenance_request_id.id,
            'request_owner_id': self.env.uid,
            'dest_warehouse_id': self.dest_warehouse_id.id,
            'dest_location_id': self.dest_location_id.id,
        }
        if self.category_id.approval_type == 'stock_material':
            vals.update({
                'source_warehouse_id': self.source_warehouse_id.id,
                'source_location_id': self.source_location_id.id,
            })
        approval = self.env['approval.request'].create(vals)
        return {
            'name': _('Spare Parts Approval'),
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval.id,
            'view_mode': 'form',
        }

    def _check_values(self):
        """Server-side validation of the selections fed to the approval."""
        approval_type = self.category_id.approval_type
        if approval_type not in ('stock_material', 'stock_material_purchase'):
            raise UserError(_(
                "Select a spare-parts approval category (Stock Material "
                "Transfer or Stock Transfer + Purchase)."))
        if not self.dest_warehouse_id or not self.dest_location_id:
            raise UserError(_("Destination warehouse and location are required."))
        if self.dest_location_id.usage != 'inventory':
            raise UserError(_(
                "The destination location must be a loss location "
                "(Inventory Loss usage) so the consumption is accounted."))
        if self.dest_location_id.company_id not in (False, self.company_id):
            raise UserError(_(
                "The destination location belongs to another company."))
        if approval_type == 'stock_material':
            if not self.source_warehouse_id or not self.source_location_id:
                raise UserError(_(
                    "Source warehouse and location are required to consume "
                    "from stock."))
            if self.source_location_id.usage != 'internal':
                raise UserError(_("The source location must be an internal location."))
            if self.source_location_id.company_id not in (False, self.company_id):
                raise UserError(_(
                    "The source location belongs to another company."))
