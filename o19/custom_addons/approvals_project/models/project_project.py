from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = 'project.project'

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    def _get_picking_action(self, action_name, picking_type=None):
        """Override to set picking type from project warehouse for From WH / To WH."""
        res = super()._get_picking_action(action_name, picking_type)
        if self.warehouse_id and picking_type:
            if picking_type == 'outgoing' and self.warehouse_id.out_type_id:
                res['context']['default_picking_type_id'] = self.warehouse_id.out_type_id.id
            elif picking_type == 'incoming' and self.warehouse_id.in_type_id:
                res['context']['default_picking_type_id'] = self.warehouse_id.in_type_id.id
            res['context']['default_project_warehouse_id'] = self.warehouse_id.id
        return res

    def action_open_project_approvals(self):
        self.ensure_one()
        context = {'default_project_id': self.id}
        if self.warehouse_id:
            context['default_project_warehouse_id'] = self.warehouse_id.id
            context['default_dest_warehouse_id'] = self.warehouse_id.id
        return {
            'name': 'Approvals',
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': context,
        }
