from odoo import fields, models


class MaintenanceRequestCategory(models.Model):
    _name = 'maintenance.request.category'
    _description = 'Maintenance Request Category'
    _order = 'sequence, id'

    name = fields.Char(string='Category Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    request_ids = fields.One2many('maintenance.request', 'maintenance_category_id', string='Maintenance Requests')
