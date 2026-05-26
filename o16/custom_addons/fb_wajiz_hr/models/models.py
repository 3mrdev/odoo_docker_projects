from odoo import fields,models,_,api,exceptions
from odoo.exceptions import UserError
from datetime import date,datetime
from datetime import timedelta

 
class Employee(models.Model):
	_inherit = "hr.employee"
	# _rec_name = "job_uid"

	def name_get(self):
		return [(i.id, "[" + str(i.job_uid) +"] " + i.name) for i in self]

	_sql_constraints = [
	    ('job_uid_uniq', 'unique (job_uid)', _('The Job Uid must be unique !')),
		('identification_id_uniq', 'unique (identification_id)', _('The Identification ID must be unique !')),
		('visa_no_uniq', 'unique (visa_no)', _('The Visa No. must be unique !')),
	]

	job_uid = fields.Char(required=True)
	department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",tracking=True)
	documents = fields.One2many("hr.document","employee_id",groups="hr.group_hr_user")
	job_residency = fields.Char(string="Job (Residency)",groups="hr.group_hr_user")
	related_documents_count = fields.Integer(compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document1 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document2 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document3 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document4 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document5 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	related_document6 = fields.Boolean(default=False,compute="_documents_count",store=True,groups="hr.group_hr_user")
	contract_id = fields.Many2one('hr.contract', string='Contract', readonly=True, help="Contract",groups="hr.group_hr_user")
	# personal_mobile = fields.Char(string='Mobile',related='address_home_id.mobile', store=True,help="Personal mobile number of the employee",groups="hr.group_hr_user")
	joining_date = fields.Date(string='Joining Date',help="Employee joining date computed from the contract start date",
		compute='_compute_joining_date', store=True,groups="hr.group_hr_user")
	id_expiry_date = fields.Date(
		string='Expiry Date',
		help='Expiry date of Identification ID',groups="hr.group_hr_user")
	passport_expiry_date = fields.Date(
		string='Expiry Date',
		help='Expiry date of Passport ID',groups="hr.group_hr_user")
	iban_number = fields.Char(string="IBAN Number",groups="hr.group_hr_user")
	id_attachment_id = fields.Many2many(
		'ir.attachment', 'id_attachment_rel',
		'id_ref', 'attach_ref',
		string="Attachment",
		help='You can attach the copy of your Id',groups="hr.group_hr_user")
	passport_attachment_id = fields.Many2many(
		'ir.attachment',
		'passport_attachment_rel',
		'passport_ref', 'attach_ref1',
		string="Attachment",
		help='You can attach the copy of Passport',groups="hr.group_hr_user")
	fam_ids = fields.One2many(
		'hr.employee.family', 'employee_id',
		string='Family', help='Family Information',groups="hr.group_hr_user")

	@api.depends("documents")
	def _documents_count(self):
		for rec in self:
			rec.related_documents_count = len(rec.documents)

			for doc in rec.documents:
				if doc.doc_type.id == 1:
					rec.related_document1 = True
				if doc.doc_type.id == 2:
					rec.related_document2 = True
				if doc.doc_type.id == 3:
					rec.related_document3 = True
				if doc.doc_type.id == 4:
					rec.related_document4 = True
				if doc.doc_type.id == 5:
					rec.related_document5 = True
				if doc.doc_type.id == 6:
					rec.related_document6 = True

	def action_related_documents(self):
		return {
			'name': 'Legal Documents',
			'type': 'ir.actions.act_window',
			'domain': [('employee_id', '=', self.id)],
			# 'context': {'search_default_group_doc_type': 1},
			'view_type': 'form',
			'view_mode': 'kanban,tree,form',
			'res_model': 'hr.document',
			'context': {'default_employee_id': self.id},
			'view_id': False,
			'views': [(self.env.ref('fb_wajiz_hr.document_kanban').id, 'kanban'),
						(self.env.ref('fb_wajiz_hr.document_tree').id, 'tree'),
						(self.env.ref('fb_wajiz_hr.document_form').id, 'form')],
			'target': 'current',
		}

	total_hours_not_attended = fields.One2many(
		'employee.attendance.report', 
		'employee_id', 
		string="Attendance Report",
		store=True
	)
                

class EmployeeAttendanceReport(models.Model):
    _name = 'employee.attendance.report'
    
    employee_id = fields.Many2one('hr.employee', string="Employee")
    date = fields.Date(string="Date")
    day = fields.Char(string="Day")
    absence_hours = fields.Float(string="Absence Hours")
    worked_hours = fields.Float(string="Worked Hours")
    identification_no = fields.Char(string="Identification No", related='employee_id.identification_id', readonly=True)
    notes_id = fields.Many2one('attendance.notes', string="Notes", store=True)
    approval = fields.Char(string="Approval", store=True)
    department_id = fields.Many2one('hr.department', string="Department", compute='_compute_department_id', store=True)

    @api.depends('employee_id.department_id')
    def _compute_department_id(self):
        for record in self:
            record.department_id = record.employee_id.department_id
            
class AttendanceNotes(models.Model):
    _name = 'attendance.notes'
    _description = 'Attendance Notes'

    name = fields.Char(string="Note", required=True)  # Title of the note
    description = fields.Text(string="Description")  # Details of the note
    employee_id = fields.Many2one('hr.employee', string="Employee")  # Employee related to the note
    date = fields.Date(string="Date", default=fields.Date.context_today)  # Date of the note
    
class AttendanceReportWizard(models.TransientModel):
    _name = 'attendance.report.wizard'
    _description = 'Attendance Report Wizard'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)

    def print_report(self):
        records = self.env['employee.attendance.report'].search([
            ('employee_id', '=', self.employee_id),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)
        ])
        return self.employee_id.ref('fb_wajiz_hr.action_employee_attendance_report').report_action(records, data={'date_from': self.date_from, 'date_to': self.date_to})
  
class ApprovalCategoryApprover(models.Model):
    _inherit = 'approval.category.approver'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Select the department associated with this approver.'
    )

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    absence_hours = fields.Float(string='Absence Hours', compute='_compute_absence_hours', store=True, help="Total absence hours for the payslip period.")

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_absence_hours(self):
        for payslip in self:
            total_absent_hours = 0.0
            employee = payslip.employee_id

            if employee:
                # Fetch attendance records for the employee within the payslip date range
                attendance_records = self.env['hr.attendance'].search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', payslip.date_from),
                    ('check_out', '<=', payslip.date_to)
                ])

                # Fetch validated leave records within the payslip date range
                leaves = self.env['hr.leave'].search([
                    ('employee_id', '=', employee.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', payslip.date_to),
                    ('request_date_to', '>=', payslip.date_from)
                ])

                worked_days = {(record.check_in.date(), record.check_out) for record in attendance_records if record.check_in and record.check_out}
                
                # Calculate total days in the payslip period
                total_days = (payslip.date_to - payslip.date_from).days + 1

                # Calculate absence hours from attendance records
                for day in range(total_days):
                    current_date = payslip.date_from + timedelta(days=day)
                    c_day_of_week = current_date.strftime("%A")

                    # Check if the current day is not Friday
                    if (c_day_of_week != 'Friday' and current_date not in [wd[0] for wd in worked_days]):
                        total_absent_hours += 8.0  # 8 hours for each absent day

                # Add absence hours for validated leave days (excluding Fridays)
                for leave in leaves:
                    # leave_days = (leave.request_date_to - leave.request_date_from).days + 1
                    # for day in range(leave_days):
                    #     leave_date = leave.request_date_from + timedelta(days=day)
                    #     if leave_date.strftime("%A") != 'Friday':

                    total_absent_hours -= leave.number_of_days_display * 8.0  # 8 hours for each leave day

                # Calculate absence hours for worked days (if hours worked are less than 8)
                for record in attendance_records:
                    if record.check_in and record.check_out:
                        worked_hours = (record.check_out - record.check_in).total_seconds() / 3600
                        if worked_hours < 8.0:
                            absence_hours = 8.0 - worked_hours
                            total_absent_hours += absence_hours

            payslip.absence_hours = total_absent_hours

# class HrPayslipWorkedDays(models.Model):
#     _inherit = 'hr.payslip.worked_days'

#     def _get_worked_day_lines(self, contracts, date_from, date_to):
#         res = super()._get_worked_day_lines(contracts, date_from, date_to)
#         for contract in contracts:
#             unapproved_absence_hours = self.env['hr.attendance'].search_count([
#                 ('employee_id', '=', contract.employee_id.id),
#                 ('check_in', '>=', date_from),
#                 ('check_out', '<=', date_to),
#                 ('leave_id', '=', False)  # No approved leave
#             ])
#             if unapproved_absence_hours:
#                 res.append({
#                     'name': 'Unapproved Absence',
#                     'sequence': 99,
#                     'code': 'UnapprovedAbsence',
#                     'number_of_hours': unapproved_absence_hours,
#                     'contract_id': contract.id,
#                 })
#         return res


class ApprovalApprover(models.Model):
    _inherit = 'approval.approver'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        help='Department associated with this approver.',
        compute='_compute_department_id',
        store=True
    )

    def write(self, vals):
        # Call super to ensure standard write behavior
        res = super(ApprovalApprover, self).write(vals)

        # Check if the status is being changed to 'approved'
        if 'status' in vals and vals['status'] == 'approved':
            for record in self:
                # Find all approvers in the same request with status 'pending'
                pending_records = self.env['approval.approver'].search([
                    ('request_id', '=', record.request_id.id),
                    ('status', '=', 'pending'),
                    ('department_id', '=', record.department_id.id)  # Ensure the same department
                ])
                # Remove all pending records
                pending_records.unlink()

        return res

    @api.depends('user_id', 'request_id.category_id.approver_ids')
    def _compute_department_id(self):
        for record in self:
            if record.request_id and record.user_id:
                # Find the approver in the category with the same user_id
                approver = record.request_id.category_id.approver_ids.filtered(lambda a: a.user_id == record.user_id)
                record.department_id = approver.department_id if approver else False
            else:
                record.department_id = False 

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    have_tracking_device = fields.Boolean(string="Have Tracking Device?")
    have_chip_number = fields.Boolean(string="WAIE Chip?")
    device_number = fields.Char(string="Device Number", required=False)
    related_documents_count = fields.Integer(compute="_documents_count", store=True, groups="hr.group_hr_user")
    documents = fields.One2many("hr.document", "vehicle_id", groups="hr.group_hr_user")
       
    @api.depends("documents")
    def _documents_count(self):
        for rec in self:
            rec.related_documents_count = len(rec.documents)

    def action_related_documents_for_vehicle(self):
        return {
            'name': 'Legal Documents',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)],
            # 'context': {'search_default_group_doc_type': 1},
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'hr.document',
            'context': {'default_vehicle_id': self.id},
            'view_id': False,
            'views': [
                (self.env.ref('fb_wajiz_hr.document_kanban').id, 'kanban'),
                (self.env.ref('fb_wajiz_hr.document_tree').id, 'tree'),
                (self.env.ref('fb_wajiz_hr.document_form').id, 'form')
            ],
            'target': 'current',
        }
	

class EmployeeBase(models.AbstractModel):
	_inherit = "hr.employee.base"

	job_uid = fields.Char(required=True)
	job_residency = fields.Char(string="Job (Residency)",groups="hr.group_hr_user")
	address_home_id = fields.Many2one(
        'res.partner', 'Address', help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	personal_mobile = fields.Char(string='Mobile',related='address_home_id.mobile', store=True,help="Personal mobile number of the employee",groups="hr.group_hr_user")
	last_attendance_id = fields.Many2one('hr.attendance', compute='_compute_last_attendance_id', store=True,
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	last_check_in = fields.Datetime(related='last_attendance_id.check_in', store=True,
	groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	last_check_out = fields.Datetime(related='last_attendance_id.check_out', store=True,
	groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	attendance_state = fields.Selection(string="Attendance Status", compute='_compute_attendance_state',
	selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")],
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	hours_last_month = fields.Float(
	compute='_compute_hours_last_month', groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	hours_today = fields.Float(compute='_compute_hours_today',
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	hours_last_month_display = fields.Char(compute='_compute_hours_last_month', groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	total_overtime = fields.Float(compute='_compute_total_overtime', compute_sudo=True,
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")

class EmployeePublic(models.Model):
	_inherit = "hr.employee.public"

	job_uid = fields.Char(readonly=True)
	job_residency = fields.Char(string="Job (Residency)",groups="hr.group_hr_user")
	address_home_id = fields.Many2one(
        'res.partner', 'Address', help='Enter here the private address of the employee, not the one linked to your company.',
        groups="hr.group_hr_user", tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	personal_mobile = fields.Char(string='Mobile',related='address_home_id.mobile', store=True,help="Personal mobile number of the employee",groups="hr.group_hr_user")
	last_attendance_id = fields.Many2one('hr.attendance', compute='_compute_last_attendance_id', store=True,
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	last_check_in = fields.Datetime(related='last_attendance_id.check_in', store=True,
	groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	last_check_out = fields.Datetime(related='last_attendance_id.check_out', store=True,
	groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	attendance_state = fields.Selection(string="Attendance Status", compute='_compute_attendance_state',
	selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")],
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	hours_last_month = fields.Float(
	compute='_compute_hours_last_month', groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	hours_today = fields.Float(compute='_compute_hours_today',
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	hours_last_month_display = fields.Char(compute='_compute_hours_last_month', groups="hr_attendance.group_hr_attendance_user,hr.group_hr_user")
	total_overtime = fields.Float(compute='_compute_total_overtime', compute_sudo=True,
	groups="hr_attendance.group_hr_attendance_kiosk,hr_attendance.group_hr_attendance,hr.group_hr_user")
	related_documents_count = fields.Integer(compute="_documents_count",store=True,groups="hr.group_hr_user")
	documents = fields.One2many(
    related='employee_id.documents',  
    comodel_name="hr.document",
    inverse_name="public_employee_id",
    groups="hr.group_hr_user",
    readonly=True  
	)
	@api.depends("documents")
	def _documents_count(self):
		for rec in self:
			rec.related_documents_count = len(rec.documents)

			for doc in rec.documents:
				if doc.doc_type.id == 1:
					rec.related_document1 = True
				if doc.doc_type.id == 2:
					rec.related_document2 = True
				if doc.doc_type.id == 3:
					rec.related_document3 = True
				if doc.doc_type.id == 4:
					rec.related_document4 = True
				if doc.doc_type.id == 5:
					rec.related_document5 = True
				if doc.doc_type.id == 6:
					rec.related_document6 = True

	def action_related_documents(self):
		return {
			'name': 'Legal Documents',
			'type': 'ir.actions.act_window',
			'domain': [('employee_id', '=', self.employee_id.id)],
			# 'context': {'search_default_group_doc_type': 1},
			'view_type': 'form',
			'view_mode': 'kanban,tree,form',
			'res_model': 'hr.document',
			'context': {'default_employee_id': self.employee_id.id},
			'view_id': False,
			'views': [(self.env.ref('fb_wajiz_hr.document_kanban').id, 'kanban'),
						(self.env.ref('fb_wajiz_hr.document_tree').id, 'tree'),
						(self.env.ref('fb_wajiz_hr.document_form').id, 'form')],
			'target': 'current',
		}

class Documents(models.Model):
	_name = "hr.document"
	_inherit = ['mail.thread', 'mail.activity.mixin'] 

	employee_id = fields.Many2one("hr.employee",tracking=2)
	public_employee_id = fields.Many2one("hr.employee.public", string="Public Employee", tracking=2)
	vehicle_id = fields.Many2one("fleet.vehicle",string="Vehicle",tracking=2)
	name = fields.Char(required=True)
	number = fields.Char(string="Document Number",required=False)
	document = fields.Binary(required=False)
	begin_date = fields.Date()
	begin_date_hijri = fields.Char()
	finish_date = fields.Date(required=True,tracking=5)
	finish_date_hijri = fields.Char(required=False,tracking=5)
	doc_type = fields.Many2one("hr.document.type",required=True,tracking=3)
	state = fields.Selection([
		('draft','Draft'),
		('valid','Valid'),
		('renew','Renew'),
		('expired','Expired'),
		('canceled','Canceled'),
	],default="draft",tracking=1)

	active = fields.Boolean(default=True,tracking=4)
	company_id = fields.Many2one('res.company', 'Company', readonly=True, help="Company",
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})


	def draft(self):
		for rec in self:
			rec.state = "draft"

	def valid(self):
		for rec in self:
			rec.state = "valid"

	def cancel(self):
		for rec in self:
			rec.state = "canceled"

	def reminders(self):
		today = date.today()
		flag = False
		documents = self.env["hr.document"].sudo().search([])
		# message_partner_ids
		hr_officers = self.env.ref('hr.group_hr_user').users
		hr_managers = self.env.ref('hr.group_hr_manager').users
		hr_users = hr_officers + hr_managers
		
		notification_ids = []
		list_inp = [] 
		for user in hr_users:
			list_inp.append(user.partner_id.id)

		res_list = []
		for item in list_inp: 
			if item not in res_list: 
				res_list.append(item) 
		
		for document in documents:
			if document.state == "valid":
				diff = document.finish_date - today

				if diff.days < document.doc_type.days:
					document.state = "renew"
					flag = True
					for user in res_list:
						notification_ids = [(0, 0, {
							'res_partner_id': user,
							'notification_type': 'inbox'
						})]
						document.message_post(
							message_type="notification",
							body='One of your employees has to renew his documents!', 
							notification_ids=notification_ids,
							author_id=2)
						
				if diff.days < 1:
					document.state = "expired"
					flag = True
					for user in res_list:
						notification_ids = [(0, 0, {
							'res_partner_id': user,
							'notification_type': 'inbox'
						})]
						document.message_post(
							message_type='notification',
							body='One of your employees document has expired!', 
							notification_ids=notification_ids,
							author_id=2)
				
				
		if flag:

			notification = {
				'type': 'ir.actions.client',
				'tag': 'display_notification',
				'params': {
					'title': _('Employees Documents'),
					'message': 'One of your employees has to renew his documents',
					'sticky': True,
				}
			}
			return notification

	@api.constrains('document')
	def _check_document_size(self):
		max_size = self.doc_type.max_size * 1024 * 1024 
		for record in self:
			if record.document and len(record.document) > max_size:
				raise exceptions.ValidationError(_("The document size should not exceed %s MB." % (max_size / (1024 * 1024))))


class DocumentTypes(models.Model):
    _name = "hr.document.type"

    name = fields.Char()
    days = fields.Integer()
    max_size = fields.Float("Max Document Size (MB)")
    
    DOCUMENT_CATEGORY_SELECTION = [
        ('employee', 'Employee'),
        ('vehicle', 'Vehicle'),
    ]

    document_category = fields.Selection(
        selection=DOCUMENT_CATEGORY_SELECTION,
        string="Document Category",
        required=True,
        default='employee',
        help="Select whether the document is for an Employee or a Vehicle."
    )

class HrCustody(models.Model):
	_inherit = 'hr.custody'

	active = fields.Boolean(default=True)
	attachment = fields.Binary()
	cost = fields.Float()
	date_request = fields.Date(string='Requested Date', required=False, track_visibility='always', readonly=True,
                               help="Requested date",
                               states={'draft': [('readonly', False)]}, default=datetime.now().strftime('%Y-%m-%d'))
	purpose = fields.Char(string='Reason', track_visibility='always', required=False, readonly=True, help="Reason",states={'draft': [('readonly', False)]})

	# return date validation
	@api.constrains('return_date')
	def validate_return_date(self):
		pass
		# if self.return_date < self.date_request:
		#     raise ValidationError(_('Please Give Valid Return Date'))

class HrCustodyPro(models.Model):
	_inherit = "custody.property"

	active = fields.Boolean(default=True)