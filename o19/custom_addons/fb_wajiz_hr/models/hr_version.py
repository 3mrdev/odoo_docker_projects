from odoo import models, fields, api

class HRVersion(models.Model):
    _inherit = "hr.version"

    # _identification_id_uniq = models.Constraint(
    #     'unique (identification_id)',
    #     'The Identification ID must be unique !',
    # )

    have_ins = fields.Boolean(string="Does he/she have insurance ?", default=False, groups="hr.group_hr_manager", tracking=True)
    fixed_allowance = fields.Monetary(string="Fixed Allowance", default=0.0, groups="hr.group_hr_manager", tracking=True)
    dynamic_allowance = fields.Monetary(string="Dynamic Allowance", default=0.0, groups="hr.group_hr_manager", tracking=True)
    insurance_type_id = fields.Many2one('hr.insurance.type', string="Insurance Type", groups="hr.group_hr_manager", tracking=True)
    insurance_percentage = fields.Float(string="Insurance Percentage",related='insurance_type_id.percentage', store=True)

class InusranceType(models.Model):
    _name = 'hr.insurance.type'
    _description = 'Insurance Type'
    
    name = fields.Char(string="Name", required=True)
    percentage = fields.Float(string="Percentage", required=True)