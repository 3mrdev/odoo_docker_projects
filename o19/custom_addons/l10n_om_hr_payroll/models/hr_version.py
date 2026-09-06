from odoo import models, fields, api

class HRVersion(models.Model):
    _inherit = "hr.version"

    housing_allowance = fields.Monetary(string="Housing Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    transportation_allowance = fields.Monetary(string="Transportation Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    telephone_allowance = fields.Monetary(string="Telephone Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    communication_allowance = fields.Monetary(string="Communication Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    utility_allowance = fields.Monetary(string="Utility Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    electricity_allowance = fields.Monetary(string="Electricity Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    meals_allowance = fields.Monetary(string="Meals Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    overtime_allowance = fields.Monetary(string="Overtime Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    overtime_by_hour = fields.Monetary(string="Overtime by hour", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    medical_allowance = fields.Monetary(string="Medical Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    nature_of_work_allowance = fields.Monetary(string="Nature of Work Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    technician_allowance = fields.Monetary(string="Technician Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    high_cost_of_living_allowance = fields.Monetary(string="High Cost of Living Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    shift_allowance = fields.Monetary(string="Shift Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    motivational_allowance = fields.Monetary(string="Motivational Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    water_allowance = fields.Monetary(string="Water Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    air_fare_allowance = fields.Monetary(string="Air Fare Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    other_allowance = fields.Monetary(string="Other Allowance", groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user", tracking=True)
    total_payroll_amount = fields.Monetary(string="Total Amount", compute='_compute_total_payroll_amount',store=True,groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")

    @api.depends('wage','housing_allowance', 'transportation_allowance', 'telephone_allowance', 'communication_allowance', 'utility_allowance', 'electricity_allowance', 'meals_allowance', 'overtime_allowance', 'medical_allowance', 'nature_of_work_allowance', 'technician_allowance', 'high_cost_of_living_allowance', 'shift_allowance', 'motivational_allowance', 'water_allowance', 'other_allowance')
    def _compute_total_payroll_amount(self):
        for record in self:
            record.total_payroll_amount = record.wage + record.housing_allowance + record.transportation_allowance + record.telephone_allowance + record.communication_allowance + record.utility_allowance + record.electricity_allowance + record.meals_allowance + record.overtime_allowance + record.medical_allowance + record.nature_of_work_allowance + record.technician_allowance + record.high_cost_of_living_allowance + record.shift_allowance + record.motivational_allowance + record.water_allowance + record.other_allowance