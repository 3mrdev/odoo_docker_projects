from odoo import api, fields, models


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    # Approval types whose destination can be the maintenance loss location.
    MAINTENANCE_TYPES = ('stock_material', 'stock_material_purchase')

    maintenance_request_id = fields.Many2one(
        'maintenance.request', string='Maintenance Request', index='btree_not_null',
        help="Maintenance request for which the material of this approval "
             "request will be consumed.")

    def _is_maintenance_consumption(self):
        """Whether this request consumes material for a maintenance request."""
        self.ensure_one()
        return bool(
            self.maintenance_request_id
            and self.approval_type in self.MAINTENANCE_TYPES
        )

    def _get_maintenance_consumption_company(self):
        """Company driving the loss location of a maintenance consumption.

        The request company comes from the approval category and can be
        empty on shared categories; the maintenance request's company is
        then the fallback.
        """
        self.ensure_one()
        return self.company_id or self.maintenance_request_id.company_id

    # -------------------------------------------------------------
    # Destination availability: let maintenance consumptions reach the
    # inventory-loss locations, which the stock_material modules exclude
    # (they restrict destinations to internal locations).
    # -------------------------------------------------------------
    @api.depends(
        'category_id', 'category_id.dest_warehouse_ids',
        'maintenance_request_id', 'company_id.maintenance_loss_location_id')
    def _compute_available_warehouses(self):
        super()._compute_available_warehouses()
        for request in self:
            if not request._is_maintenance_consumption():
                continue
            company = request._get_maintenance_consumption_company()
            loss = company.maintenance_loss_location_id
            if loss and loss.warehouse_id:
                request.available_dest_warehouse_ids |= loss.warehouse_id

    @api.depends(
        'dest_warehouse_id', 'category_id', 'category_id.dest_location_ids',
        'maintenance_request_id', 'company_id.maintenance_loss_location_id')
    def _compute_available_dest_locations(self):
        super()._compute_available_dest_locations()
        for request in self:
            if not request._is_maintenance_consumption():
                continue
            company = request._get_maintenance_consumption_company()
            # Union instead of intersection: the maintenance flow may always
            # consume to a loss location of the selected warehouse.
            domain = [('usage', '=', 'inventory')]
            if request.dest_warehouse_id:
                domain.extend([
                    '|',
                    ('warehouse_id', '=', request.dest_warehouse_id.id),
                    ('warehouse_id', '=', False),
                ])
            domain.extend([
                '|',
                ('company_id', '=', company.id),
                ('company_id', '=', False),
            ])
            request.available_dest_location_ids |= self.env['stock.location'].search(domain)

    # -------------------------------------------------------------
    # Analytic prefill: new product lines get the equipment's analytic
    # distribution so the purchase orders inherit it.
    # -------------------------------------------------------------
    @api.onchange('product_line_ids')
    def _onchange_product_line_ids_analytic_prefill(self):
        if not self._is_maintenance_consumption():
            return
        equipment = self.maintenance_request_id.equipment_id
        if not equipment or not equipment.analytic_distribution:
            return
        for line in self.product_line_ids:
            if not line.analytic_distribution:
                line.analytic_distribution = equipment.analytic_distribution
