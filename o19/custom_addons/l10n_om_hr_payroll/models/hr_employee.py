from odoo import models, fields, api

class HREmployee(models.Model):
    _inherit = "hr.employee"
    # _sql_constraints = [
    #     ('job_number_unique', 'unique(job_number)', 'Job Number must be unique!')
    # ]

    _job_number_unique = models.Constraint(
        'unique (job_number)',
        'The Job Number must be unique !',
    )

    housing_allowance = fields.Monetary(string="Housing Allowance", readonly=False, related="version_id.housing_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    transportation_allowance = fields.Monetary(string="Transportation Allowance", readonly=False, related="version_id.transportation_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    telephone_allowance = fields.Monetary(string="Telephone Allowance", readonly=False, related="version_id.telephone_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    communication_allowance = fields.Monetary(string="Communication Allowance", readonly=False, related="version_id.communication_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    utility_allowance = fields.Monetary(string="Utility Allowance", readonly=False, related="version_id.utility_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    electricity_allowance = fields.Monetary(string="Electricity Allowance", readonly=False, related="version_id.electricity_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    meals_allowance = fields.Monetary(string="Meals Allowance", readonly=False, related="version_id.meals_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    overtime_allowance = fields.Monetary(string="Overtime Allowance", readonly=False, related="version_id.overtime_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    overtime_by_hour = fields.Monetary(string="Overtime by hour", readonly=False, related="version_id.overtime_by_hour", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    medical_allowance = fields.Monetary(string="Medical Allowance", readonly=False, related="version_id.medical_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    nature_of_work_allowance = fields.Monetary(string="Nature of Work Allowance", readonly=False, related="version_id.nature_of_work_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    technician_allowance = fields.Monetary(string="Technician Allowance", readonly=False, related="version_id.technician_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    high_cost_of_living_allowance = fields.Monetary(string="High Cost of Living Allowance", readonly=False, related="version_id.high_cost_of_living_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    shift_allowance = fields.Monetary(string="Shift Allowance", readonly=False, related="version_id.shift_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    motivational_allowance = fields.Monetary(string="Motivational Allowance", readonly=False, related="version_id.motivational_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    water_allowance = fields.Monetary(string="Water Allowance", readonly=False, related="version_id.water_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    air_fare_allowance = fields.Monetary(string="Air Fare Allowance", readonly=False, related="version_id.air_fare_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    other_allowance = fields.Monetary(string="Other Allowance", readonly=False, related="version_id.other_allowance", inherited=True, groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    total_payroll_amount = fields.Monetary(string="Total Amount", compute='_compute_total_payroll_amount',store=True,groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    
    has_pasi = fields.Boolean(string="Has Pasi",groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    is_omani = fields.Boolean(string="Is Ommani",compute='_compute_is_omani',groups="hr.group_hr_manager,hr_payroll.group_hr_payroll_user")
    job_number = fields.Char(string="Job Number", groups="hr.group_hr_user,hr_payroll.group_hr_payroll_user")
    l10n_om_civil_id = fields.Char(string="Civil ID / National Number", groups="hr.group_hr_user,hr_payroll.group_hr_payroll_user")
    l10n_om_pasi_number = fields.Char(string="PASI Subscriber Number", groups="hr.group_hr_user,hr_payroll.group_hr_payroll_user")

    def get_next_job_number(self):
        for rec in self:
            if not rec.job_number:
                rec.job_number = self.env['ir.sequence'].next_by_code('hr.job.number')

    @api.depends('country_id')
    def _compute_is_omani(self):
        for record in self:
            record.is_omani = record.country_id.code == 'OM'

    @api.depends('wage','housing_allowance', 'transportation_allowance','communication_allowance', 'telephone_allowance', 'utility_allowance', 'electricity_allowance', 'meals_allowance', 'overtime_allowance', 'medical_allowance', 'nature_of_work_allowance', 'technician_allowance', 'high_cost_of_living_allowance', 'shift_allowance', 'motivational_allowance', 'water_allowance', 'other_allowance')
    def _compute_total_payroll_amount(self):
        for record in self:
            record.total_payroll_amount = record.wage + record.housing_allowance + record.transportation_allowance + record.communication_allowance + record.telephone_allowance + record.utility_allowance + record.electricity_allowance + record.meals_allowance + record.overtime_allowance + record.medical_allowance + record.nature_of_work_allowance + record.technician_allowance + record.high_cost_of_living_allowance + record.shift_allowance + record.motivational_allowance + record.water_allowance + record.other_allowance