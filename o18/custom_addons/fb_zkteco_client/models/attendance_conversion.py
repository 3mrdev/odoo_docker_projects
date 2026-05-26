from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime
import logging

_logger = logging.getLogger(__name__)

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
    sync_error = fields.Text(string="Sync Error")
    
    # Configuration fields (can be set via system parameters)
    @api.model
    def _get_multiple_sessions_enabled(self):
        """Check if multiple sessions per day are enabled"""
        return self.env['ir.config_parameter'].sudo().get_param(
            'zkteco.multiple_sessions_enabled', default='False'
        ).lower() == 'false'

    def convert_to_hr_attendance(self,default_end_time="16:00"):
        """
        Enhanced conversion of ZKTeco attendance records into Odoo's hr.attendance model.
        
        Features:
        - Processes only unsynced records
        - Handles Odoo 18 constraint for multiple check-ins per day
        - Prevents blocking of other records due to individual errors
        - Comprehensive error handling and logging
        - Smart duplicate detection and handling
        - Validation of attendance logic
        - Bulk processing for better performance
        """
        try:
            # Get unsynced attendance records, sorted by Employee ID and timestamp
            unsynced_records = self.env["fb.zkteco.attendance"].sudo().search([
                ('sync', '=', False)
            ]).sorted(lambda r: (r.name, r.timestamp))
            
            if not unsynced_records:
                _logger.info("No unsynced ZKTeco attendance records found.")
                return
            
            _logger.info(f"Processing {len(unsynced_records)} unsynced ZKTeco attendance records.")
            
            hr_employee_model = self.env['hr.employee'].sudo()
            hr_attendance_model = self.env['hr.attendance'].sudo()
            
            # Track processing results
            successfully_synced = self.env['fb.zkteco.attendance'].sudo()
            failed_records = []
            
            # Group records by employee and date for better processing
            grouped_records = self._group_records_by_employee_date(unsynced_records, hr_employee_model)
            
            # Process each employee's daily attendance
            for (employee_id, date_str), daily_records in grouped_records.items():
                try:
                    synced_for_day = self._process_daily_attendance(
                        employee_id, date_str, daily_records, hr_attendance_model,default_end_time
                    )
                    successfully_synced |= synced_for_day
                    
                except Exception as e:
                    error_msg = f"Failed to process attendance for employee {employee_id} on {date_str}: {str(e)}"
                    _logger.error(error_msg)
                    
                    # Mark records with error but don't stop processing
                    for record in daily_records:
                        record.sync_error = error_msg
                        failed_records.append(record)
            
            # Mark successfully synced records
            if successfully_synced:
                successfully_synced.write({
                    'sync': True,
                    'sync_timestamp': fields.Datetime.now(),
                    'sync_error': False,
                })
                _logger.info(f"Successfully synced {len(successfully_synced)} ZKTeco attendance records.")
            
            # Log failed records summary
            if failed_records:
                _logger.warning(f"Failed to sync {len(failed_records)} ZKTeco attendance records. Check individual record errors.")
            
        except Exception as e:
            _logger.error(f"Critical error in convert_to_hr_attendance: {str(e)}")
            raise

    def _group_records_by_employee_date(self, records, hr_employee_model):
        """
        Group attendance records by employee and date.
        Returns: dict with key (employee_id, date_string) and value list of records
        """
        grouped = {}
        employee_cache = {}  # Cache employee lookups
        
        for record in records:
            try:
                # Use cached employee lookup
                if record.name not in employee_cache:
                    employee = hr_employee_model.search([
                        ('identification_id', '=', record.name)
                    ], limit=1)
                    
                    if not employee:
                        # record.message_post(
                        #     body=f"Employee with ID '{record.name}' not found in the system.",
                        #     message_type='notification'
                        # )
                        record.sync_error = f"Employee with ID '{record.name}' not found"
                        continue
                    
                    employee_cache[record.name] = employee
                
                employee = employee_cache[record.name]
                date_str = record.timestamp.date().strftime('%Y-%m-%d')
                key = (employee.id, date_str)
                
                if key not in grouped:
                    grouped[key] = []
                grouped[key].append(record)
                
            except Exception as e:
                error_msg = f"Error grouping record {record.id}: {str(e)}"
                _logger.error(error_msg)
                record.sync_error = error_msg
                
        return grouped

    def _process_daily_attendance(self, employee_id, date_str, daily_records, hr_attendance_model,default_end_time):
        """
        Process attendance records for a single employee on a single day.
        Handles multiple check-ins/check-outs (breaks, customer visits, etc.)
        Creates multiple attendance sessions when appropriate.
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        # Sort all records by timestamp to process chronologically
        daily_records.sort(key=lambda r: r.timestamp)
        
        # # Handle previous day's open attendance (missing check-out)
        # check_ins = [r for r in daily_records if r.check_type == 'in']
        # if check_ins:
        #     self._handle_previous_open_attendance(employee_id, check_ins[0], hr_attendance_model,default_end_time)
        
        # Check if we should use single session or multiple sessions approach
        # if self._get_multiple_sessions_enabled() and self._should_use_multiple_sessions(daily_records):
        #     synced_records += self._process_multiple_sessions(employee_id, date_str, daily_records, hr_attendance_model)
        # else:
        synced_records += self._process_single_session(employee_id, date_str, daily_records, hr_attendance_model)
        
        return synced_records

    def _should_use_multiple_sessions(self, daily_records):
        """
        Determine if we should create multiple attendance sessions or consolidate into one.
        
        Multiple sessions are created when:
        1. There are alternating check-ins and check-outs (indicating breaks/trips)
        2. There are gaps longer than a threshold between check-out and next check-in
        """
        if len(daily_records) < 3:  # Need at least 3 records for multiple sessions
            return False
        
        # Look for pattern: IN -> OUT -> IN (-> OUT optional)
        check_sequence = [r.check_type for r in daily_records]
        
        # Check for alternating pattern starting with 'in'
        if len(check_sequence) >= 3:
            for i in range(len(check_sequence) - 2):
                if (check_sequence[i] == 'in' and 
                    check_sequence[i + 1] == 'out' and 
                    check_sequence[i + 2] == 'in'):
                    return True
        
        return False

    def _process_multiple_sessions(self, employee_id, date_str, daily_records, hr_attendance_model):
        """
        Process multiple attendance sessions for the same day (breaks, customer visits, etc.)
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        sessions = []
        current_session = None
        
        try:
            # Build sessions from the records
            for record in daily_records:
                if record.check_type == 'in':
                    # Start new session
                    if current_session and 'check_out' not in current_session:
                        # Previous session has no check-out, close it
                        sessions.append(current_session)
                    current_session = {'check_in': record, 'check_in_record': record}
                
                elif record.check_type == 'out' and current_session:
                    # Close current session
                    current_session['check_out'] = record.timestamp
                    current_session['check_out_record'] = record
                    sessions.append(current_session)
                    current_session = None
                
                elif record.check_type == 'out' and not current_session:
                    # Check-out without check-in
                    record.message_post(
                        body=f"Check-out at {record.timestamp} without corresponding check-in for this session.",
                        message_type='notification'
                    )
                    record.sync_error = "Check-out without matching check-in"
                    synced_records |= record
            
            # Handle unclosed session
            if current_session:
                sessions.append(current_session)
            
            # Create attendance records for each session
            session_count = 0
            for i, session in enumerate(sessions):
                if self._validate_session(session):
                    # Check for existing attendance that might conflict
                    existing = self._find_conflicting_attendance(employee_id, session, hr_attendance_model)
                    
                    if existing:
                        synced_records += self._merge_with_existing_session(existing, session)
                    else:
                        synced_records += self._create_session_attendance(employee_id, session, i + 1)
                        session_count += 1
                else:
                    # Invalid session, mark records as synced with error
                    synced_records |= session['check_in_record']
                    if 'check_out_record' in session:
                        synced_records |= session['check_out_record']
            
            if session_count > 0:
                _logger.info(f"Created {session_count} attendance sessions for employee {employee_id} on {date_str}")
                
        except Exception as e:
            error_msg = f"Error processing multiple sessions: {str(e)}"
            _logger.error(error_msg)
            for record in daily_records:
                record.sync_error = error_msg
        
        return synced_records

    def _process_single_session(self, employee_id, date_str, daily_records, hr_attendance_model):
        """
        Process as a single consolidated session (original logic)
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        # Separate check-ins and check-outs
        check_ins = [r for r in daily_records if r.check_type == 'in']
        check_outs = [r for r in daily_records if r.check_type == 'out']
        
        # Get existing attendance for this employee on this date
        date_start = datetime.strptime(date_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        date_end = date_start + timedelta(days=1)
        
        existing_attendance = hr_attendance_model.search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_start),
            ('check_in', '<', date_end)
        ], limit=1)
        _logger.error(f"_process_single_session check_ins {check_ins}")
        if check_ins:
            first_check_in = check_ins[0]
            if existing_attendance:
                synced_records += self._handle_existing_attendance(
                    existing_attendance, first_check_in, check_outs, daily_records
                )
            else:
                synced_records += self._create_new_attendance(
                    employee_id, first_check_in, check_outs, daily_records
                )
        elif check_outs and existing_attendance:
            synced_records += self._handle_existing_attendance(
                existing_attendance, False, check_outs, daily_records
            )
        elif check_outs and not existing_attendance:
            # Check-out without check-in - mark all as synced with error
            for checkout in check_outs:
                checkout.message_post(
                    body=f"Check-out at {checkout.timestamp} without corresponding check-in. Skipped.",
                    message_type='notification'
                )
                checkout.sync_error = "Check-out without check-in"
                synced_records |= checkout
        
        return synced_records

    def _validate_session(self, session):
        """
        Validate if a session is valid for creating attendance record
        """
        if 'check_in' not in session:
            return False
        
        # If there's a check_out, ensure it's after check_in
        if 'check_out' in session:
            if session['check_out'] <= session['check_in_record'].timestamp:
                session['check_out_record'].message_post(
                    body=f"Invalid session: check-out {session['check_out']} is not after check-in {session['check_in_record'].timestamp}",
                    message_type='notification'
                )
                return False
        
        return True

    def _find_conflicting_attendance(self, employee_id, session, hr_attendance_model):
        """
        Find existing attendance that might conflict with the new session
        """
        check_in_time = session['check_in_record'].timestamp
        
        # Look for attendance on the same day
        date_start = check_in_time.replace(hour=0, minute=0, second=0)
        date_end = date_start + timedelta(days=1)
        
        existing = hr_attendance_model.search([
            ('employee_id', '=', employee_id),
            ('check_in', '>=', date_start),
            ('check_in', '<', date_end)
        ], limit=1)
        
        return existing

    def _merge_with_existing_session(self, existing_attendance, session):
        """
        Merge new session with existing attendance record if appropriate
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        try:
            check_in_record = session['check_in_record']
            
            # Use earliest check-in time
            if check_in_record.timestamp < existing_attendance.check_in:
                existing_attendance.check_in = check_in_record.timestamp
                check_in_record.message_post(
                    body=f"Updated existing session check-in time to {check_in_record.timestamp}",
                    message_type='notification'
                )
            else:
                check_in_record.message_post(
                    body=f"Check-in at {check_in_record.timestamp} merged with existing session (earlier check-in exists)",
                    message_type='notification'
                )
            
            synced_records |= check_in_record
            
            # Handle check-out if present
            if 'check_out' in session:
                check_out_record = session['check_out_record']
                if not existing_attendance.check_out or session['check_out'] > existing_attendance.check_out:
                    existing_attendance.check_out = session['check_out']
                    check_out_record.message_post(
                        body=f"Updated existing session check-out time to {session['check_out']}",
                        message_type='notification'
                    )
                else:
                    check_out_record.message_post(
                        body=f"Check-out at {session['check_out']} merged with existing session",
                        message_type='notification'
                    )
                synced_records |= check_out_record
                
        except Exception as e:
            error_msg = f"Error merging sessions: {str(e)}"
            _logger.error(error_msg)
            for key in ['check_in_record', 'check_out_record']:
                if key in session:
                    session[key].sync_error = error_msg
        
        return synced_records

    def _create_session_attendance(self, employee_id, session, session_number):
        """
        Create attendance record for a single session
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        try:
            attendance_data = {
                'employee_id': employee_id,
                'check_in': session['check_in_record'].timestamp,
            }
            
            if 'check_out' in session:
                attendance_data['check_out'] = session['check_out']
            
            # Create the attendance record
            hr_attendance = self.env['hr.attendance'].sudo().create(attendance_data)
            
            # Log success
            session_info = f"Session {session_number}"
            if 'check_out' in session:
                session_info += f" (Complete: {attendance_data['check_in']} to {attendance_data['check_out']})"
            else:
                session_info += f" (Open: {attendance_data['check_in']} - no check-out)"
            
            session['check_in_record'].message_post(
                body=f"Multiple sessions detected. {session_info} created successfully.",
                message_type='notification'
            )
            
            synced_records |= session['check_in_record']
            if 'check_out_record' in session:
                synced_records |= session['check_out_record']
                
        except Exception as e:
            error_msg = f"Error creating session attendance: {str(e)}"
            _logger.error(error_msg)
            session['check_in_record'].sync_error = error_msg
            if 'check_out_record' in session:
                session['check_out_record'].sync_error = error_msg
        
        return synced_records

    def _handle_previous_open_attendance(self, employee_id, current_check_in, hr_attendance_model,default_end_time):
        """
        Handle cases where employee forgot to check out on previous day.
        Automatically closes the previous open attendance session.
        """
        try:
            # Look for open attendance (no check_out) for this employee
            open_attendance = hr_attendance_model.search([
                ('employee_id', '=', employee_id),
                ('check_out', '=', False),
                ('check_in', '<', current_check_in.timestamp)
            ], limit=1)
            
            if open_attendance:
                previous_day_check_in = open_attendance.check_in
                # Calculate automatic check-out time (end of working day or before new check-in)
                # Use the day's end (e.g., 6 PM) or 1 minute before new check-in, whichever is earlier
                # previous_day_end = open_attendance.check_in.replace(hour=12, minute=0, second=0)
                # one_minute_before_new_checkin = current_check_in.timestamp - timedelta(minutes=1)
                
                # auto_checkout_time = min(previous_day_end, one_minute_before_new_checkin)

                default_hour, default_minute = map(int, default_end_time.split(':'))

                # Set check-out to the default end time on the same day as check-in
                auto_checkout_time = previous_day_check_in.replace(
                    hour=default_hour, 
                    minute=default_minute, 
                    second=0, 
                    microsecond=0
                )
                
                # Only auto-close if the calculated time is after the original check-in
                if auto_checkout_time > open_attendance.check_in:
                    open_attendance.check_out = auto_checkout_time
                    
                    # Log the automatic closure
                    current_check_in.message_post(
                        body=f"Automatically closed previous day's attendance. "
                             f"Missing check-out added at {auto_checkout_time} "
                             f"(Original check-in: {open_attendance.check_in})",
                        message_type='notification'
                    )
                    _logger.info(f"Auto-closed open attendance for employee {employee_id}. "
                               f"Check-in: {open_attendance.check_in}, Auto check-out: {auto_checkout_time}")
                else:
                    # If we can't determine a valid auto-checkout time, log as warning
                    current_check_in.message_post(
                        body=f"Found open attendance from {open_attendance.check_in} but couldn't determine valid auto-checkout time. "
                             f"Manual review required.",
                        message_type='notification'
                    )
                    _logger.warning(f"Could not auto-close attendance for employee {employee_id}. Manual review needed.")
                    
        except Exception as e:
            _logger.error(f"Error handling previous open attendance for employee {employee_id}: {str(e)}")

    def _handle_existing_attendance(self, existing_attendance, check_in_record, check_outs, daily_records):
        """
        Handle cases where attendance already exists for the day.
        Updates the existing record if the new data is more accurate.
        """
        _logger.error("_handle_existing_attendance")
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        try:
            # Compare timestamps - use the earliest check-in
            if check_in_record.timestamp < existing_attendance.check_in:
                existing_attendance.check_in = check_in_record.timestamp
                check_in_record.message_post(
                    body=f"Updated existing check-in time from {existing_attendance.check_in} to {check_in_record.timestamp}",
                    message_type='notification'
                )
                synced_records |= check_in_record
            else:
                # Mark as synced even if not used (to avoid reprocessing)
                check_in_record.message_post(
                    body=f"Check-in at {check_in_record.timestamp} ignored - earlier check-in exists at {existing_attendance.check_in}",
                    message_type='notification'
                )
                synced_records |= check_in_record
            
            # Handle check-out
            if check_outs:
                latest_checkout = max(check_outs, key=lambda r: r.timestamp)
                
                if not existing_attendance.check_out or latest_checkout.timestamp > existing_attendance.check_out:
                    # Validate check-out is after check-in
                    _logger.error("_handle_existing_attendance 2")
                    if latest_checkout.timestamp > existing_attendance.check_in:
                        existing_attendance.check_out = latest_checkout.timestamp
                        latest_checkout.message_post(
                            body=f"Updated check-out time to {latest_checkout.timestamp}",
                            message_type='notification'
                        )
                        synced_records |= latest_checkout
                    else:
                        latest_checkout.message_post(
                            body=f"Invalid check-out time {latest_checkout.timestamp} is before check-in {existing_attendance.check_in}",
                            message_type='notification'
                        )
                        latest_checkout.sync_error = "Check-out before check-in"
                
                # Mark other check-outs as synced
                for checkout in check_outs:
                    if checkout != latest_checkout:
                        checkout.message_post(
                            body=f"Additional check-out at {checkout.timestamp} ignored - using latest check-out",
                            message_type='notification'
                        )
                        synced_records |= checkout
            
        except Exception as e:
            error_msg = f"Error updating existing attendance: {str(e)}"
            _logger.error(error_msg)
            for record in daily_records:
                record.sync_error = error_msg
            
        return synced_records

    def _create_new_attendance(self, employee_id, check_in_record, check_outs, daily_records):
        """
        Create a new hr.attendance record.
        """
        synced_records = self.env['fb.zkteco.attendance'].sudo()
        
        try:
            # Prepare attendance data
            attendance_data = {
                'employee_id': employee_id,
                'check_in': check_in_record.timestamp,
            }
            
            # Add check-out if available and valid
            if check_outs:
                # Use the latest check-out
                latest_checkout = max(check_outs, key=lambda r: r.timestamp)
                
                if latest_checkout.timestamp > check_in_record.timestamp:
                    attendance_data['check_out'] = latest_checkout.timestamp
                    synced_records |= latest_checkout
                    
                    # Mark other check-outs as synced but not used
                    for checkout in check_outs:
                        if checkout != latest_checkout:
                            checkout.message_post(
                                body=f"Additional check-out at {checkout.timestamp} ignored - using latest check-out",
                                message_type='notification'
                            )
                            synced_records |= checkout
                else:
                    latest_checkout.message_post(
                        body=f"Invalid check-out time {latest_checkout.timestamp} is before check-in {check_in_record.timestamp}",
                        message_type='notification'
                    )
                    latest_checkout.sync_error = "Check-out before check-in"
            
            # Create the attendance record (may have only check_in if no valid check_out)
            hr_attendance = self.env['hr.attendance'].sudo().create(attendance_data)
            
            # Log success with appropriate message
            if 'check_out' in attendance_data:
                check_in_record.message_post(
                    body=f"Complete attendance record created for {check_in_record.timestamp.date()} "
                         f"(Check-in: {attendance_data['check_in']}, Check-out: {attendance_data['check_out']})",
                    message_type='notification'
                )
            else:
                check_in_record.message_post(
                    body=f"Attendance record created for {check_in_record.timestamp.date()} "
                         f"(Check-in: {attendance_data['check_in']}) - No check-out recorded. "
                         f"Employee may still be at work or forgot to check out.",
                    message_type='notification'
                )
            
            synced_records |= check_in_record
            
            # Handle multiple check-ins on the same day
            for record in daily_records:
                if record.check_type == 'in' and record != check_in_record:
                    record.message_post(
                        body=f"Additional check-in at {record.timestamp} ignored - using first check-in of the day",
                        message_type='notification'
                    )
                    synced_records |= record
            
        except Exception as e:
            error_msg = f"Error creating attendance record: {str(e)}"
            _logger.error(error_msg)
            for record in daily_records:
                record.sync_error = error_msg
            
        return synced_records

    @api.model
    def auto_close_open_attendances(self, days_back=1, default_end_time="18:00"):
        """
        Utility method to automatically close open attendance records (missing check-outs).
        
        Args:
            days_back (int): How many days back to check for open attendances
            default_end_time (str): Default end time in HH:MM format (24-hour)
        
        This can be run as a separate daily cron job to handle forgotten check-outs.
        """
        try:
            cutoff_date = fields.Datetime.now() - timedelta(days=days_back)
            hr_attendance_model = self.env['hr.attendance'].sudo()
            
            # Find open attendance records older than cutoff
            open_attendances = hr_attendance_model.search([
                ('check_out', '=', False),
                ('check_in', '<', cutoff_date)
            ])
            
            if not open_attendances:
                _logger.info("No old open attendance records found.")
                return
            
            default_hour, default_minute = map(int, default_end_time.split(':'))
            closed_count = 0
            
            for attendance in open_attendances:
                try:
                    # Set check-out to the default end time on the same day as check-in
                    auto_checkout = attendance.check_in.replace(
                        hour=default_hour, 
                        minute=default_minute, 
                        second=0, 
                        microsecond=0
                    )
                    
                    # Ensure check-out is after check-in
                    if auto_checkout > attendance.check_in:
                        attendance.check_out = auto_checkout
                        closed_count += 1
                        _logger.info(f"Auto-closed attendance for employee {attendance.employee_id.name}. "
                                   f"Check-in: {attendance.check_in}, Auto check-out: {auto_checkout}")
                    else:
                        # If default time is before check-in, add 8 hours to check-in time
                        auto_checkout = attendance.check_in + timedelta(hours=8)
                        attendance.check_out = auto_checkout
                        closed_count += 1
                        _logger.info(f"Auto-closed attendance for employee {attendance.employee_id.name} "
                                   f"using 8-hour duration. Check-in: {attendance.check_in}, "
                                   f"Auto check-out: {auto_checkout}")
                        
                except Exception as e:
                    _logger.error(f"Error auto-closing attendance {attendance.id}: {str(e)}")
            
            _logger.info(f"Successfully auto-closed {closed_count} open attendance records.")
            
        except Exception as e:
            _logger.error(f"Error in auto_close_open_attendances: {str(e)}")

    @api.model
    def cleanup_old_synced_records(self, days_to_keep=30):
        """
        Utility method to clean up old synced records to prevent database bloat.
        Can be called from a separate cron job.
        """
        cutoff_date = fields.Datetime.now() - timedelta(days=days_to_keep)
        old_records = self.search([
            ('sync', '=', True),
            ('sync_timestamp', '<', cutoff_date)
        ])
        
        if old_records:
            _logger.info(f"Cleaning up {len(old_records)} old synced ZKTeco attendance records.")
            old_records.unlink()

    @api.model
    def retry_failed_sync(self):
        """
        Utility method to retry failed synchronizations.
        Can be called from a separate cron job.
        """
        failed_records = self.search([
            ('sync', '=', False),
            ('sync_error', '!=', False)
        ])
        
        if failed_records:
            _logger.info(f"Retrying sync for {len(failed_records)} failed records.")
            # Clear previous errors and retry
            failed_records.write({'sync_error': False})
            failed_records.convert_to_hr_attendance()