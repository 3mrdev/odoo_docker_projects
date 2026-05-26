from odoo import models,fields,api,_

class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    expense_ids = fields.One2many("hr.expense","vehicle_id")
    expense_count = fields.Integer(compute="_compute_expense_count")

    def _compute_expense_count(self):
        for record in self:
            record.expense_count = len(record.expense_ids)
    
    def action_view_expenses(self):
        self.ensure_one()
        
        if not self.env.user.employee_id:
            raise UserError(_("You must have an employee profile to create an expense"))

        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.expense",
            "domain": [("vehicle_id", "=", self.id)],
            "name": _("Expenses"),
            "view_mode": "list,form",
            "context": {"create": True,"default_vehicle_id": self.id,"default_employee_id": self.env.user.employee_id.id},
        }