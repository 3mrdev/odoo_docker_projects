from odoo import fields,models,_,api,exceptions
from odoo.exceptions import UserError
import logging
from datetime import date,datetime
from datetime import timedelta

_logger = logging.getLogger(__name__)

class AttendanceReportWizard(models.TransientModel):
    _name = 'employee.attendance.report.wizard'
    _description = 'Wizard to Print Employee Attendance Report'

    title = fields.Char(string="Report Title")
    year = fields.Integer(string='Year', required=True, default=datetime.now().year)
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', required=True)
        
    def print_report(self):
        """Call when the button 'Get Report' is clicked."""
        
        docs = []
        # Fetch all employees
        departments = self.env['hr.department'].search([])
        employees = self.env['hr.employee'].search([])
        leaves = self.env['hr.leave'].search([])

        for department in departments:
            employees_docs = []
            # Append employee data to docs
            for employee in employees.filtered(lambda emp: emp.department_id == department):
                # Fetch attendance data for the employee
                attendance_records = self.env['hr.attendance'].search([('employee_id', '=', employee.id)])
                employee_leaves = leaves.filtered(lambda leave: leave.employee_id == employee and leave.state == 'validate')
                # Prepare attendance details as a text string
                attendance_details = []
                absence_details = []
                leaves_details = []
                leaves_name = ''
                for record in attendance_records:
                    # Ensure check_in and check_out are valid datetime objects
                    if isinstance(record.check_in, datetime) and isinstance(record.check_out, datetime):
                        worked_hours = (record.check_out - record.check_in).total_seconds() / 3600
                        absence_hours = 8.00 - worked_hours
                        c_day_of_week = record.check_in.strftime("%A")
                        if worked_hours < 8.00 and c_day_of_week != 'Friday' and record.check_in.date() == record.check_out.date():
                            attendance_details.append(f"{record.check_in.date()} , {c_day_of_week} : Worked: {worked_hours:.2f} Hours, Absence: {absence_hours:.2f} Hours")
                    else:
                        # Handle cases where check_in or check_out are not valid
                        c_day_of_week = record.check_in.strftime("%A") if record.check_in else "N/A"
                        attendance_details.append(f"{record.check_in.date() if record.check_in else 'N/A'} , {c_day_of_week} : Missing Attendance Data")

                # Join attendance details into a single string
                if  attendance_details:
                    report_year = self.year #datetime.now().year  # current year
                    report_month = int(self.month) #datetime.now().month  # current month
                    first_day = datetime(report_year, report_month, 1)
                    last_day = datetime(report_year, report_month + 1, 1) - timedelta(days=1)
                    current_day = first_day
                    #attended_dates = {record.check_in.date() for record in attendance_records if record.check_in}
                    if last_day < current_day:
                        raise UserError("Start Date can't be greater then End Date") 
                    total_absent_days = 0
                    total_absent_hours = 0
                    while current_day <= last_day:
                        c_day_of_week = current_day.strftime("%A")
                        #worked_hours = 0
                        for record in attendance_records:
                            if current_day.date() != record.check_in.date() and c_day_of_week != 'Friday':
                                # Employee did not attend this day
                                absence_details.append(f"{current_day.date()} , {c_day_of_week} : Absent")
                                total_absent_days += 1
                                current_day += timedelta(days=1)
                            elif isinstance(record.check_in, datetime) and isinstance(record.check_out, datetime) and current_day.date() == record.check_in.date() and worked_hours < 8.00 and c_day_of_week != 'Friday' and record.check_in.date() == record.check_out.date():
                                worked_hours = (record.check_out - record.check_in).total_seconds() / 3600
                                absence_hours = 8.00 - worked_hours
                                absence_details.append(f"{record.check_in.date()} , {c_day_of_week} : Worked: {worked_hours:.2f} Hours, Absence: {absence_hours:.2f} Hours")
                                total_absent_hours += absence_hours
                                current_day += timedelta(days=1)
                            else:
                                current_day += timedelta(days=1)
                    current_day = first_day
                    while current_day <= last_day:
                        c_day_of_week = current_day.strftime("%A")
                        if employee_leaves:
                            for leave in employee_leaves:
                                if leave.request_date_from <= current_day.date() <= leave.request_date_to:
                                    leaves_details.append(f"{leave.holiday_status_id.name} : {c_day_of_week}, {current_day.date()}")
                                    leaves_name= leave.name
                                    current_day += timedelta(days=1)
                                else:
                                    current_day += timedelta(days=1)
                        else:
                            current_day += timedelta(days=1)
    
                    absence_details.sort()
                    attendance_details_text = "\n".join(absence_details) or "No attendance records found."
                    absent_text = f"غياب {total_absent_days} أيام بدون عذر وغياب {total_absent_hours} ساعات بدون عذر"
                    absent_text_2 = f"خصم {total_absent_days} أيام و{total_absent_hours} ساعات."
                    employees_docs.append({
                        'employee_department': department.name,
                        'job_uid' : employee.job_uid or "N/A",
                        'job_title': employee.job_id.name or "N/A",
                        'employee_id': employee.identification_id or "N/A",
                        'employee_name': employee.name or "N/A",
                        'absence_notes': absent_text,
                        'approval_notes': absent_text_2,
                        'absence_details': absence_details,
                        'attendance_details': attendance_details_text,
                        'leaves_details': leaves_details,
                        'leave_text': leaves_name,
                    })
            docs.append({
                'department_name': department.name,
                'employees_docs': employees_docs,
            })

        data = {
            'doc_ids': self.ids,
            'doc_model': self._name,
            'title': self.title,
            'docs': docs,
        }

        # Use `module_name.report_id` as reference.
        return self.env.ref('fb_wajiz_hr.biometric_report_action').report_action(self, data=data)

class AttendanceReportTemplate(models.AbstractModel):
    """Abstract Model for attendance report template."""

    _name = 'report.fb_wajiz_hr.attendance_report_view'
    _description = 'Attendance Report Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        return data