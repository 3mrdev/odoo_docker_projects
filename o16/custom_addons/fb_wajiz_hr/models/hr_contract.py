from odoo import models, fields, api
from datetime import datetime, time

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    have_ins = fields.Boolean(string="Does he\she have insurance ?", default=False)
    fixed_allowance = fields.Monetary(string="Fixed Allowance", default=0.0)
    dynamic_allowance = fields.Monetary(string="Dynamic Allowance", default=0.0)
    insurance_type_id = fields.Many2one('hr.insurance.type', string="Insurance Type")
    insurance_percentage = fields.Float(string="Insurance Percentage",related='insurance_type_id.percentage', store=True)
    
    # def _generate_work_entries(self, date_start, date_stop, **kwargs):
    #     """
    #     Override to ensure date objects are converted to datetime objects.
    #     The core Odoo method requires datetime objects but sometimes receives date objects.
    #     """
    #     # Convert date to datetime if necessary
    #     if date_start and not isinstance(date_start, datetime):
    #         date_start = datetime.combine(date_start, time.min)
    #     if date_stop and not isinstance(date_stop, datetime):
    #         date_stop = datetime.combine(date_stop, time.max)
        
    #     return super(HrContract, self)._generate_work_entries(date_start, date_stop, **kwargs)

class InusranceType(models.Model):
    _name = 'hr.insurance.type'
    _description = 'Insurance Type'
    
    name = fields.Char(string="Name", required=True)
    percentage = fields.Float(string="Percentage", required=True)