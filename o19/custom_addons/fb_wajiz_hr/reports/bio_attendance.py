from odoo import fields,models,api, _
from odoo.exceptions import UserError
import logging
from datetime import date,datetime
from datetime import timedelta
import calendar

_logger = logging.getLogger(__name__)

class BioAttendanceReportWizard(models.TransientModel):
    _name = 'fb.bio.attendance.report.wizard'
    _description = 'Wizard to Print Employee Bio Attendance Report'

    def _get_default_from_date(self):
        #first day of the current month
        first_day = date.today().replace(day=1)
        return first_day

    def _get_default_to_date(self):
        #last day of the current moth
        year = date.today().year
        month = date.today().month
        last_day = calendar.monthrange(year, month)[1]
        return date(year, month, last_day)

    from_date = fields.Date(default=_get_default_from_date, required=True)
    to_date = fields.Date(default=_get_default_to_date, required=True)
    departments = fields.Many2many("hr.department")
        
    # def print_report(self):
    #     """Call when the button 'Get Report' is clicked."""
        
    #     docs = []

    #     allowed_time = 30

    #     for department in self.departments:
    #         employees_docs = []
    #         employees = self.env['hr.employee'].search([('department_id', '=', department.id)])

    #         for employee in employees:
    #             diff_days = (self.to_date - self.from_date).days

    #             absence_details = []
    #             late_details = []
    #             leaves_details = []
    #             absence_notes = ""
    #             total_absent_days = 0
    #             total_absent_minutes = 0
    #             for day in range(diff_days + 1):
    #                 current_day = self.from_date + timedelta(days=day)
    #                 c_day_of_week = current_day.strftime("%A")
    #                 employee_hours_per_day = employee.resource_calendar_id.hours_per_day
    #                 day_txt = f"{current_day} {c_day_of_week} :"
                    
    #                 timeoff_records = self.env["hr.leave"].search([
    #                     ('employee_id', '=', employee.id), 
    #                     ('request_date_from', '<=', current_day), 
    #                     ('request_date_to', '>=', current_day),
    #                     ('state', '=', 'validate')
    #                 ])
                    
    #                 attendance_records = self.env['hr.attendance'].search([('employee_id', '=', employee.id), ('check_in', '>=', current_day), ('check_out', '<=', current_day)])
                    
    #                 if not attendance_records:
    #                     flag_found = False

    #                     for time in employee.resource_calendar_id.attendance_ids:
    #                         if current_day.weekday() == int(time.dayofweek):
    #                             flag_found = True
    #                             break

    #                     if flag_found:
                            
    #                         if timeoff_records:
    #                             flag_unpaid = False
    #                             for record in timeoff_records:
    #                                 if record.holiday_status_id.work_entry_type_id.is_unforeseen:
    #                                     flag_unpaid = True

    #                             if flag_unpaid:
    #                                 absence_details.append(day_txt + " Absent \n")
    #                                 leaves_details.append(day_txt + f" Absent {record.holiday_status_id.name}\n")
    #                                 total_absent_days += 1
    #                             else:
    #                                 leaves_details.append(day_txt + f"{record.holiday_status_id.name}\n")
    #                         else:
    #                             absence_details.append(day_txt + " Absent \n")
    #                             total_absent_days += 1
                            
    #                 for record in attendance_records:
    #                     absence_hours = employee_hours_per_day - record.worked_hours
    #                     absence_minutes = (absence_hours * 60) % 60
    #                     if absence_minutes > allowed_time:
    #                         late_details.append(day_txt + f" Worked: {record.worked_hours:.2f} Hours, Late: {absence_minutes:.2f} Minutes \n")
    #                         total_absent_minutes += absence_minutes

    #             absence_notes += f" Absent {total_absent_days} Days, Late Minutes: {total_absent_minutes:.2f} Minutes\n\n"

    #             employees_docs.append({
    #                 'job_uid' : employee.job_uid or "N/A",
    #                 'job_title': employee.job_id.name or "N/A",
    #                 'employee_id': employee.identification_id or "N/A",
    #                 'employee_name': employee.name or "N/A",
    #                 'absence_notes': absence_notes,
    #                 'late_details': late_details,
    #                 'approval_notes': "",
    #                 'absence_details': absence_details,
    #                 'leaves_details': leaves_details,
    #                 'leave_text': "",
    #             })
    #         docs.append({
    #             'department_name': department.name,
    #             'employees_docs': employees_docs,
    #         })

    #     data = {
    #         'doc_ids': self.ids,
    #         'doc_model': self._name,
    #         'from_date': self.from_date,
    #         'to_date': self.to_date,
    #         'print_date': datetime.now(),
    #         'print_user': self.env.user.name,
    #         'docs': docs,
    #     }

    #     # Use `module_name.report_id` as reference.
    #     return self.env.ref('fb_wajiz_hr.bio_attendance_report_action').report_action(self, data=data)

    def print_report(self):
        """Call when the button 'Get Report' is clicked."""
        docs = []
        allowed_time = 30

        t_from = _("From")
        t_to = _("to")
        t_hrs = _("hrs")
        t_min = _("min")
        t_minutes = _("Minutes")
        t_days = _("days")
        t_days_capital = _("Days")
        t_absent = _("Absent")
        t_absent_without_reason = _("Absent without reason")
        t_absent_with_reason = _("Absent with reason")
        t_late = _("Late")
        t_approved = _("Approved")
        t_unpaid = _("Unpaid")
        t_worked = _("Worked")
        t_notes = _("Notes")
        t_at = _("At")
        t_absent_1_day_at = _("Absent 1 day At")
        t_absent_days = _("Absent")

        for department in self.departments:
            employees_docs = []
            employees = self.env['hr.employee'].search([('department_id', '=', department.id)])

            for employee in employees:
                diff_days = (self.to_date - self.from_date).days
                absence_days = []
                leaves_days = []
                late_details = []
                leaves_details = []
                total_absent_days = 0
                total_leave_days = 0
                total_leave_absent_days = 0
                total_absent_minutes = 0
                timeoff_records_checked = []

                for day in range(diff_days + 1):
                    current_day = self.from_date + timedelta(days=day)
                    c_day_of_week = current_day.strftime("%A")
                    employee_hours_per_day = employee.resource_calendar_id.hours_per_day

                    # Leaves
                    timeoff_records = self.env["hr.leave"].search([
                        ('employee_id', '=', employee.id),
                        ('request_date_from', '<=', current_day),
                        ('request_date_to', '>=', current_day),
                        ('state', '=', 'validate')
                    ])

                    # Attendance
                    attendance_records = self.env['hr.attendance'].search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '>=', current_day),
                        ('check_out', '<=', current_day)
                    ])
                    
                    if not attendance_records:
                        # Check if employee is supposed to work that day
                        is_workday = any(current_day.weekday() == int(t.dayofweek)
                                        for t in employee.resource_calendar_id.attendance_ids)
                        if is_workday:
                            if timeoff_records:
                                leaves_days.append(current_day)
                                flag_unpaid = any(r.holiday_status_id.work_entry_type_id.is_unforeseen for r in timeoff_records)
                                for record in timeoff_records:
                                    gap_days = record.number_of_days

                                    if record.id not in timeoff_records_checked:
                                        timeoff_records_checked.append(record.id)
                                        if flag_unpaid:
                                            leaves_details.append(t_from+f" {record.request_date_from.strftime('%Y-%m-%d')}" + t_to+ f" {record.request_date_to.strftime('%Y-%m-%d')} ({record.holiday_status_id.name})")
                                        else:
                                            leaves_details.append(t_from+f" {record.request_date_from.strftime('%Y-%m-%d')}" + t_to+ f" {record.request_date_to.strftime('%Y-%m-%d')} ({record.holiday_status_id.name})")

                                    if flag_unpaid:
                                        #leaves_details.append(f"Absent without reason at {current_day.strftime('%Y-%m-%d')} {c_day_of_week} ({record.holiday_status_id.name})")
                                        #total_absent_days += 1
                                        total_leave_absent_days += 1
                                    else:
                                        #leaves_details.append(f"Absent with reason at {current_day.strftime('%Y-%m-%d')} {c_day_of_week} because of ({record.holiday_status_id.name})")
                                        total_leave_days += 1 
                            else:
                                # Mark as absent
                                absence_days.append(current_day)
                                total_absent_days += 1

                    # if not attendance_records:
                    #     # Check if employee is supposed to work that day
                    #     is_workday = any(current_day.weekday() == int(t.dayofweek)
                    #                     for t in employee.resource_calendar_id.attendance_ids)
                    #     if is_workday:
                    #         if timeoff_records:
                    #             flag_unpaid = any(r.holiday_status_id.work_entry_type_id.is_unforeseen for r in timeoff_records)
                    #             for record in timeoff_records:
                    #                 gap_days = record.number_of_days
                                    
                    #                 if record.id not in timeoff_records_checked:
                    #                     timeoff_records_checked.append(record.id)
                    #                     if flag_unpaid:
                    #                         #leaves_details.append(f"Absent without reason at {current_day.strftime('%Y-%m-%d')} {c_day_of_week} ({record.holiday_status_id.name})")
                    #                         leaves_details.append(f"Absent {gap_days} days without reason from {record.request_date_from.strftime('%Y-%m-%d')} to {record.request_date_to.strftime('%Y-%m-%d')} ({record.holiday_status_id.name})")
                    #                         total_absent_days += gap_days
                    #                     else:
                    #                         #leaves_details.append(f"Absent with reason at {current_day.strftime('%Y-%m-%d')} {c_day_of_week} because of ({record.holiday_status_id.name})")
                    #                         leaves_details.append(f"Absent {gap_days} days with reason from {record.request_date_from.strftime('%Y-%m-%d')} to {record.request_date_to.strftime('%Y-%m-%d')} ({record.holiday_status_id.name})")
                    #         else:
                    #             # Mark as absent
                    #             absence_days.append(current_day)
                    #             total_absent_days += 1

                    # Late logic
                    for record in attendance_records:
                        absence_hours = employee_hours_per_day - record.worked_hours
                        absence_minutes = (absence_hours * 60)
                        if absence_minutes > allowed_time:
                            late_details.append(
                                f"{current_day.strftime('%Y-%m-%d')} {c_day_of_week}: " + t_worked + f" {record.worked_hours:.2f}"+ t_hrs+", " + t_late + f" {absence_minutes:.2f}"+ t_min
                            )
                            total_absent_minutes += absence_minutes

                # ✅ Group consecutive absences
                grouped_absences = []
                if absence_days:
                    absence_days.sort()
                    start_date = absence_days[0]
                    prev_date = absence_days[0]

                    for current_day in absence_days[1:]:
                        if current_day == prev_date + timedelta(days=1):
                            # consecutive
                            prev_date = current_day
                        else:
                            # gap found → finalize previous range
                            if start_date == prev_date:
                                c_day_of_week = start_date.strftime("%A")
                                grouped_absences.append(t_absent_1_day_at + f" \n {start_date.strftime('%Y-%m-%d')} {c_day_of_week}")
                            else:
                                gap_days = (prev_date - start_date).days
                                grouped_absences.append(t_absent + f" {gap_days + 1} "+ t_days +" "+t_from + f" \n {start_date.strftime('%Y-%m-%d')} \n"+t_to+ f" \n {prev_date.strftime('%Y-%m-%d')}")
                            start_date = current_day
                            prev_date = current_day
                    
                    # Finalize last group
                    if start_date == prev_date:
                        c_day_of_week = start_date.strftime("%A")
                        grouped_absences.append(t_absent_1_day_at +f"\n {start_date.strftime('%Y-%m-%d')} {c_day_of_week}")
                    else:
                        gap_days = (prev_date - start_date).days
                        grouped_absences.append(t_absent+f" {gap_days + 1}"+" "+t_days+" "+t_from+f"\n {start_date.strftime('%Y-%m-%d')} \n"+t_to+f"\n {prev_date.strftime('%Y-%m-%d')}")

                # ✅ Group consecutive absences
                grouped_leaves = []
                if leaves_days:
                    leaves_days.sort()
                    start_date = leaves_days[0]
                    prev_date = leaves_days[0]

                    for current_day in leaves_days[1:]:
                        if current_day == prev_date + timedelta(days=1):
                            # consecutive
                            prev_date = current_day
                        else:
                            # gap found → finalize previous range
                            if start_date == prev_date:
                                c_day_of_week = start_date.strftime("%A")
                                grouped_leaves.append(t_absent_1_day_at + f"\n {start_date.strftime('%Y-%m-%d')} {c_day_of_week}")
                            else:
                                gap_days = (prev_date - start_date).days
                                grouped_leaves.append(t_absent+f" {gap_days + 1}"+" "+t_days+" "+t_from+f"\n {start_date.strftime('%Y-%m-%d')} \n"+t_to+f"\n {prev_date.strftime('%Y-%m-%d')}")
                            start_date = current_day
                            prev_date = current_day
                    
                    # Finalize last group
                    if start_date == prev_date:
                        c_day_of_week = start_date.strftime("%A")
                        grouped_leaves.append(t_absent_1_day_at + f"\n {start_date.strftime('%Y-%m-%d')} {c_day_of_week}")
                    else:
                        gap_days = (prev_date - start_date).days
                        grouped_leaves.append(t_absent+f" {gap_days + 1}"+" "+t_days+" "+t_from+f"\n {start_date.strftime('%Y-%m-%d')} \n"+t_to+f"\n {prev_date.strftime('%Y-%m-%d')}")

                absence_notes = t_absent_without_reason + f" {total_absent_days} " + t_days
                late_notes = t_late + f" {total_absent_minutes:.2f}" + t_minutes 
                
                leave_notes = ""
                if total_leave_days > 0:
                    leave_notes = t_absent_with_reason + f" {total_leave_days} " + t_days 
                    
                if total_leave_absent_days > 0:
                    leave_notes += t_absent_without_reason + f" {total_leave_absent_days} " + t_days_capital

                if leaves_details:
                    leave_notes += t_notes +"\n".join(leaves_details)
                    
                absence_count = len(grouped_absences)
                late_count = len(late_details)
                leaves_count = len(grouped_leaves)
                rows_count = absence_count + late_count + leaves_count + 1

                if grouped_absences or grouped_leaves or late_details:
                    employees_docs.append({
                        'job_uid': employee.job_uid or "N/A",
                        'job_title': employee.job_id.name or "N/A",
                        'employee_id': employee.identification_id or "N/A",
                        'employee_name': employee.name or "N/A",
                        'absence_notes': absence_notes,
                        'late_details': late_details,
                        'late_notes': late_notes,
                        'approval_notes': t_approved,
                        'absence_details': grouped_absences,  # ✅ Use grouped version
                        'leaves_details': grouped_leaves,
                        'leave_text': leave_notes,
                        'absence_count': absence_count,
                        'late_count': late_count,
                        'leaves_count': leaves_count,
                        'rows_count': rows_count,
                    })

            docs.append({
                'department_name': department.name,
                'employees_docs': employees_docs,
            })

        data = {
            'doc_ids': self.ids,
            'doc_model': self._name,
            'from_date': self.from_date,
            'to_date': self.to_date,
            'print_date': datetime.now(),
            'print_user': self.env.user.name,
            'docs': docs,
        }

        return self.env.ref('fb_wajiz_hr.bio_attendance_report_action').report_action(self, data=data)

class BioAttendanceReportTemplate(models.AbstractModel):
    """Abstract Model for attendance report template."""

    _name = 'report.fb_wajiz_hr.bio_attendance_report_view'
    _description = 'Bio Attendance Report Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        return data