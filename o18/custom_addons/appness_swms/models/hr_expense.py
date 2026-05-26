from odoo import models,fields,api,_


class HrExpense(models.Model):
    _inherit = "hr.expense"

    vehicle_id = fields.Many2one("fleet.vehicle")