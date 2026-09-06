from odoo import api, fields, models


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    project_id = fields.Many2one('project.project', string='Project')

    @api.depends('project_id')
    def _compute_warehouse_id(self):
        for rec in self:
            rec.warehouse_id = rec.project_id.warehouse_id if rec.project_id else False

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Project Warehouse',
        compute='_compute_warehouse_id',
        store=True,
    )

    @api.onchange('category_id')
    def _onchange_category_set_warehouse(self):
        """When category is selected, auto-fill destination warehouse from project if approval type is stock_material."""
        if self.category_id and self.category_id.approval_type == 'stock_material':
            if self.project_id and self.project_id.warehouse_id:
                self.dest_warehouse_id = self.project_id.warehouse_id

    def _get_custom_values(self):
        res = super()._get_custom_values()
        if self.project_id:
            res['project_id'] = self.project_id.id
            if self.project_id.warehouse_id and self.project_id.warehouse_id.out_type_id:
                res['picking_type_id'] = self.project_id.warehouse_id.out_type_id.id
        return res
