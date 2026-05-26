from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class Attendance(models.Model):
    _name = "fb.zkteco.attendance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "ZKTeco Attendance Records"
    _rec_name = "name"

    name = fields.Char(string="Employee ID", required=True)
    device = fields.Many2one("fb.zkteco.device", string="Device", required=True)
    timestamp = fields.Datetime(string="Timestamp", required=True)
    check_type = fields.Selection([
        ("in", "Check In"),
        ("out", "Check Out"),
    ], required=True)
    sync = fields.Boolean(string="Synced", default=False)
    sync_timestamp = fields.Datetime(string="Synced At")

    # def convert_to_hr_attendance(self):
    #     """
    #     Converts ZKTeco attendance records into Odoo's hr.attendance records.
    #     This method ensures:
    #     - No duplicate attendance records are created
    #     - Only the first check-in and the last check-out are recorded
    #     """
    #     # Get all unsynced attendance records grouped by Employee ID
    #     unsynced_records = self.env["fb.zkteco.attendance"].sudo().search([('sync', '=', False)])
    #     hr_employee_model = self.env['hr.employee'].sudo()
    #     hr_attendance_model = self.env['hr.attendance'].sudo()
    #     synced_records = self.env['fb.zkteco.attendance'].sudo()

    #     # processed_employees = {}
    #     # Group records by Employee ID and Date
    #     daily_attendance = {}
    #     for rec in unsynced_records.sorted(lambda r: (r.name, r.timestamp)):
    #         employee = hr_employee_model.search([('barcode', '=', rec.name)], limit=1)
    #         if not employee:
    #             continue  # Skip if no matching employee is found

    #         # if employee.id not in processed_employees:
    #         #     processed_employees[employee.id] = {'check_in': False, 'check_out': False}

    #         date_key = (employee.id, rec.timestamp.date())
    #         if date_key not in daily_attendance:
    #             daily_attendance[date_key] = {'check_in': False, 'check_out': False}

    #         # if rec.check_type == 'in':
    #         #     if not processed_employees[employee.id]['check_in']:
    #         #         processed_employees[employee.id]['check_in'] = rec.timestamp
    #         # elif rec.check_type == 'out':
    #         #     processed_employees[employee.id]['check_out'] = rec.timestamp

    #         if rec.check_type == 'in' and not daily_attendance[date_key]['check_in']:
    #             daily_attendance[date_key]['check_in'] = rec
    #         elif rec.check_type == 'out':
    #             daily_attendance[date_key]['check_out'] = rec

    #     # for emp_id, times in processed_employees.items():
    #     #     check_in = times['check_in']
    #     #     check_out = times['check_out']

    #     #     if check_in and check_out:
    #     #         existing_attendance = hr_attendance_model.search([
    #     #             ('employee_id', '=', emp_id),
    #     #             ('check_in', '=', check_in),
    #     #             ('check_out', '=', check_out)
    #     #         ])
    #     #         if not existing_attendance:
    #     #             hr_attendance_model.create({
    #     #                 'employee_id': emp_id,
    #     #                 'check_in': check_in,
    #     #                 'check_out': check_out,
    #     #             })

    #     # Create hr.attendance records
    #     for (employee_id, date), times in daily_attendance.items():
    #         check_in_record = times['check_in']
    #         check_out_record = times['check_out']

    #         if check_in_record and check_out_record:
    #             # Avoid duplicates
    #             existing_attendance = hr_attendance_model.search([
    #                 ('employee_id', '=', employee_id),
    #                 ('check_in', '=', check_in_record.timestamp),
    #                 ('check_out', '=', check_out_record.timestamp)
    #             ])
    #             if not existing_attendance:
    #                 hr_attendance_model.create({
    #                     'employee_id': employee_id,
    #                     'check_in': check_in_record.timestamp,
    #                     'check_out': check_out_record.timestamp,
    #                 })
    #             # Mark records as synced
    #             synced_records |= check_in_record | check_out_record

    #     # Mark all records as synced
    #     synced_records.write({
    #         'sync': True,
    #         'sync_timestamp': fields.Datetime.now(),
    #     })

    def convert_to_hr_attendance(self):
        """
        Converts ZKTeco attendance records into Odoo's hr.attendance model.
        - Processes only unsynced records.
        - Ensures no duplicates are created.
        - Handles separate attendance records for each day.
        - Validates that check-out is after check-in.
        - Logs errors in the chatter of the attendance record.
        """
        # Get unsynced attendance records, sorted by Employee ID and timestamp
        unsynced_records = self.env["fb.zkteco.attendance"].sudo().search([('sync', '=', False)]).sorted(lambda r: (r.name, r.timestamp))
        hr_employee_model = self.env['hr.employee'].sudo()
        hr_attendance_model = self.env['hr.attendance'].sudo()
        synced_records = self.env['fb.zkteco.attendance'].sudo()

        # Group records by Employee ID and Date
        daily_attendance = {}
        for rec in unsynced_records:
            employee = hr_employee_model.search([('identification_id', '=', rec.name)], limit=1)
            if not employee:
                rec.message_post(
                    body=f"Employee with ID '{rec.name}' not found in the system.",
                    message_type='notification'
                )
                continue  # Skip if no matching employee is found

            date_key = (employee.id, rec.timestamp.date())
            if date_key not in daily_attendance:
                daily_attendance[date_key] = {'check_in': False, 'check_out': False}

            if rec.check_type == 'in' and not daily_attendance[date_key]['check_in']:
                daily_attendance[date_key]['check_in'] = rec
            elif rec.check_type == 'out':
                daily_attendance[date_key]['check_out'] = rec

        # Create hr.attendance records
        for (employee_id, date), times in daily_attendance.items():
            check_in_record = times['check_in']
            check_out_record = times['check_out']

            if check_in_record and check_out_record:
                # Validate that check-out is after check-in
                if check_out_record.timestamp <= check_in_record.timestamp:
                    check_out_record.message_post(
                        body=(
                            f"Invalid check-out time ({check_out_record.timestamp}) is earlier than check-in time "
                            f"({check_in_record.timestamp}). Please verify the device data."
                        ),
                        message_type='notification'
                    )
                    continue

                # Avoid duplicates
                existing_attendance = hr_attendance_model.search([
                    ('employee_id', '=', employee_id),
                    ('check_in', '=', check_in_record.timestamp),
                    ('check_out', '=', check_out_record.timestamp)
                ])
                if not existing_attendance:
                    hr_attendance_model.create({
                        'employee_id': employee_id,
                        'check_in': check_in_record.timestamp,
                        'check_out': check_out_record.timestamp,
                    })
                    check_in_record.message_post(
                        body=f"Attendance created for Employee {employee_id} on {date}.",
                        message_type='notification'
                    )
                    check_out_record.message_post(
                        body=f"Attendance created for Employee {employee_id} on {date}.",
                        message_type='notification'
                    )
                # Mark records as synced
                synced_records |= check_in_record | check_out_record

            elif check_in_record and not check_out_record:
                check_in_record.message_post(
                    body=f"Check-in recorded at {check_in_record.timestamp}, waiting for check-out.",
                    message_type='notification'
                )

        # Mark synced records
        synced_records.write({
            'sync': True,
            'sync_timestamp': fields.Datetime.now(),
        })