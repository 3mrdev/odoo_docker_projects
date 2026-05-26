from odoo import models, fields, api

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    analytic_both = fields.Boolean(string='Analytic Both', default=False)
    analytic_distribution_debit = fields.Json(string='Analytic Distribution Debit', default={})
    analytic_distribution_credit = fields.Json(string='Analytic Distribution Credit', default={})