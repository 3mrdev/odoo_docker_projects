from odoo import fields,models,_,api,exceptions
from odoo.exceptions import UserError
from datetime import date,datetime
from datetime import timedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    bio_absence_days = fields.Float(string='Absence Days', compute='_compute_absence_hours', store=True, help="Total absence days for the payslip period.")
    bio_late_minutes = fields.Float(string='Late Hours', compute='_compute_absence_hours', store=True, help="Total late hours for the payslip period.")
    bio_early_minutes = fields.Float(string='Early Hours', compute='_compute_absence_hours', store=True, help="Total early hours for the payslip period.")
    bio_diff_minutes = fields.Float(string='Diff Hours', compute='_compute_absence_hours', store=True, help="Total diff hours for the payslip period.")

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_absence_hours(self):
        for payslip in self:
            
            if payslip.date_to and payslip.date_from:
                diff_days = (payslip.date_to - payslip.date_from).days
            else:
                diff_days = 30

            allowed_time = 30
            total_absent_days = 0
            total_absent_minutes = 0
            for day in range(diff_days + 1):
                current_day = payslip.date_from + timedelta(days=day)
                c_day_of_week = current_day.strftime("%A")
                employee_hours_per_day = payslip.employee_id.resource_calendar_id.hours_per_day
                day_txt = f"{current_day} {c_day_of_week} :"
                
                timeoff_records = self.env["hr.leave"].search([
                    ('employee_id', '=', payslip.employee_id.id), 
                    ('request_date_from', '<=', current_day), 
                    ('request_date_to', '>=', current_day),
                    ('state', '=', 'validate')
                ])
                
                attendance_records = self.env['hr.attendance'].search([('employee_id', '=', payslip.employee_id.id), ('check_in', '>=', current_day), ('check_out', '<=', current_day)])
                
                if not attendance_records:
                    flag_found = False

                    for time in payslip.employee_id.resource_calendar_id.attendance_ids:
                        if current_day.weekday() == int(time.dayofweek):
                            flag_found = True
                            break

                    if flag_found:
                        
                        if timeoff_records:
                            flag_unpaid = False
                            for record in timeoff_records:
                                if record.holiday_status_id.work_entry_type_id.is_unforeseen:
                                    flag_unpaid = True

                            if flag_unpaid:
                                total_absent_days += 1
                        else:
                            total_absent_days += 1
                        
                for record in attendance_records:
                    absence_hours = employee_hours_per_day - record.worked_hours
                    absence_minutes = (absence_hours * 60)
                    if absence_minutes > allowed_time:
                        total_absent_minutes += absence_minutes

            payslip.bio_absence_days = total_absent_days
            payslip.bio_diff_minutes = total_absent_minutes
            payslip.bio_early_minutes = total_absent_minutes
            payslip.bio_late_minutes = total_absent_minutes