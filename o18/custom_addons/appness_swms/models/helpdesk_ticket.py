from odoo import models,fields,api,_
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import timedelta , datetime ,date
from . import helpers

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    name = fields.Char(string='Subject', required=False, readonly=True,index=True, tracking=True)
    request_seq = fields.Char(default="New")
    is_swms = fields.Boolean(related="team_id.is_swms")
    sequence_id = fields.Many2one("ir.sequence",related="team_id.sequence_id")
    service = fields.Many2one("product.template",related="team_id.service",domain="[('is_swms','=',True),('type','=','service')]",\
        help="SWMS Service that is used in this helpdesk team for all the service requests")
    service_variant_id = fields.Many2one('product.product', 'Product',related="service.product_variant_id")
    is_sponsership = fields.Boolean(related="service.recurring_invoice",
        help='If set, confirming a sale order with this product will create a subscription')
    action_types = fields.Selection(related="service.action_types")
    analytic_account_id = fields.Many2one("account.analytic.account")
    budget_analytic_accounts_ids = fields.Many2many("account.analytic.account",related="service.budget_analytic_accounts_ids")
    budget_line_ids = fields.Many2many("budget.line",compute="_cal_budget_lines",store=True)
    sponsership_lines = fields.One2many("swms.service.line","request",domain="[('product.type','=','service')]")
    material_lines = fields.One2many("swms.service.line","request",domain="[('product.type','=','consu')]")
    next_stage = fields.Many2one("helpdesk.stage",compute="_cal_stage",store=True)
    previous_stage = fields.Many2one("helpdesk.stage",compute="_cal_stage",store=True)
    card_history = fields.One2many("swms.card.spending","request_id")

    vendor_id = fields.Many2one("res.partner",domain="[('is_family','=',False)]")
    vendor_bank = fields.Many2one("res.partner.bank",domain="[('partner_id','=',vendor_id)]")
    vendor_name = fields.Char()
    vendor_phone = fields.Char()
    vendor_address = fields.Char()
    vendor_bank_name = fields.Char()
    vendor_bank_card = fields.Char()

    prepaid_meter_req_no = fields.Char(string="Prepaid meter change request number")

    members_count = fields.Integer(related="partner_id.members_count",store=True)
    total_income = fields.Float(related="partner_id.total_income",store=True)
    total_obligations = fields.Float(related="partner_id.total_obligations",store=True)
    net_worth = fields.Float(related="partner_id.net_worth",store=True)
    member_net_worth = fields.Float(related="partner_id.member_net_worth",store=True)
    accommodation_type = fields.Selection(related="partner_id.accommodation_type",store=True)
    building_type = fields.Selection(related="partner_id.building_type",store=True)
    professional_status = fields.Selection(related="partner_id.professional_status",store=True)

    city_id = fields.Many2one('res.city', string='City',domain="[('country_id', '=?', country_id)]",related="partner_id.city_id")
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]",related="partner_id.state_id")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',related="partner_id.country_id")
    is_address_allowed = fields.Boolean(compute="_cal_address_allow",store=True)

    bills_ids = fields.One2many("account.move","request_id",domain=[('move_type','=','in_invoice')])
    sponserships = fields.One2many("sale.order","request_id")
    projects = fields.One2many("project.project","request_id")
    pickings = fields.One2many("stock.picking","request_id")
    cases = fields.One2many("swms.case","request_id")

    bills_count = fields.Integer(compute="_count_o2m",store=True)
    sponserships_count = fields.Integer(compute="_count_o2m",store=True)
    projects_count = fields.Integer(compute="_count_o2m",store=True)
    pickings_count = fields.Integer(compute="_count_o2m",store=True)
    cases_count = fields.Integer(compute="_count_o2m",store=True)

    plan_id = fields.Many2one('sale.subscription.plan', string='Recurring Plan',related="service.plan_id")
    total_amount = fields.Float()
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string="Report Company Currency",
        readonly=True,
    )
    # user_id ,tracking=True
    payment_status = fields.Selection([
        ('draft', "Draft"),
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('blocked', 'Blocked'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
        ('cancel', "Cancelled"),
    ],compute="cal_payment_status",store=True)

    is_orphan = fields.Boolean(compute="_get_document_types",store=True)
    is_needy_family = fields.Boolean(compute="_get_document_types",store=True)
    is_education = fields.Boolean(compute="_get_document_types",store=True)
    is_material = fields.Boolean(compute="_get_document_types", store=True)
    is_bill = fields.Boolean(compute="_get_document_types", store=True)

    noti_documents = fields.Text()
    documents = fields.Many2many("documents.document",compute='_compute_document_count',store=True)
    document_count = fields.Integer('Document Count', compute='_compute_document_count',store=True)

    #Education
    edu_level = fields.Selection([
        ('basic', 'Basic School'),
        ('middle', 'Middle School'),
        ('high', 'High School'),
        ('university', 'University'),
        ('graduate', 'Graduate'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctor', 'Doctor'),
        ('other', 'Other'),
    ], 'Educational Level',tracking=True)
    edu_major = fields.Char(tracking=True)
    edu_university = fields.Char(tracking=True)
    edu_current_semester = fields.Integer(tracking=True)
    edu_previous_gpa = fields.Float(tracking=True)
    edu_grading_system_type = fields.Selection([
        ('basic', 'Basic School'),
        ('middle', 'Middle School'),
        ('high', 'High School'),
        ('university', 'University'),
    ],'Grading System Type',tracking=True)
    edu_enrollment_date = fields.Date(tracking=True)
    edu_total_fees = fields.Float(tracking=True)
    edu_graduation_date = fields.Date(tracking=True)
    edu_scholarship_status = fields.Selection([
        ('draft', "Draft"),
        ('not_paid', 'Not Paid'),
        ('paid', 'Paid'),
        ('cancel', "Cancelled"),
    ],'Scholarship Status',tracking=True)
    edu_payment_status = fields.Selection([
        ('draft', "Draft"),
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('blocked', 'Blocked'),
        ('invoicing_legacy', 'Invoicing App Legacy'),
        ('cancel', "Cancelled"),
    ], tracking=True)
    
    show_draft_button = fields.Boolean(compute="_cal_stage",store=True)
    show_approve_button = fields.Boolean(compute="_cal_stage",store=True)
    show_cancel_button = fields.Boolean(compute="_cal_stage",store=True)
    show_reject_button = fields.Boolean(compute="_cal_stage", store=True)
    is_done_stage = fields.Boolean(compute="_cal_stage", store=True)

    def _create_activity(self):
        # weeks = 0
        # if rec.service.plan_id:
        #     if rec.service.plan_id.billing_period_unit == 'week':
        #         weeks = 1 * rec.service.plan_id.billing_period_value 
        #     elif rec.service.plan_id.billing_period_unit == 'month':
        #         weeks = 4.34524 * rec.service.plan_id.billing_period_value 
        #     elif rec.service.plan_id.billing_period_unit == 'year':
        #         weeks = 52.1429 * rec.service.plan_id.billing_period_value 
        # 'mail.mail_activity_data_todo'
        # users = self.env.ref('openacademy.group_course_approval').users
        for rec in self:
            activity_type_id = self.env.ref('appness_swms.mail_activity_document_expire').id
            self.env['mail.activity'].search([
                ('res_id', '=', rec.id), 
                ('user_id', '=', self.env.user.id),
                ('activity_type_id', '=',activity_type_id)
            ]).action_feedback(feedback='Approved')
            self.env['mail.activity'].search([
                ('res_id', '=', rec.id), 
                ('activity_type_id', '=', activity_type_id)
            ]).unlink()
            rec.activity_schedule(
                activity_type_id=activity_type_id,
                date_deadline=fields.Date.today()+timedelta(weeks=1),
                summary="Document Expire 1",
                note="Document Expire 2",
                user_id=self.env.user.id
            )
            if rec.user_id:
                rec.activity_schedule(
                    activity_type_id=activity_type_id,
                    date_deadline=fields.Date.today()+timedelta(weeks=1),
                    summary="Document Expire 1",
                    note="Document Expire 2",
                    user_id=rec.user_id.id
                )

    @api.constrains('request_seq','partner_id','service','team_id')
    def seq_gen(self):
        for rec in self:
            if rec.request_seq == "New" and rec.sequence_id != False and rec.service != False:
                rec.request_seq = self.env['ir.sequence'].next_by_code(rec.sequence_id.code) or '/'

            if rec.partner_id and rec.service:
                rec.name = f"{rec.request_seq} - {rec.partner_id.name} - {rec.service.name}"

            if rec.partner_id and rec.team_id.is_family_responsible:
                if rec.partner_id.family_responsible_id:
                    rec.user_id = rec.partner_id.family_responsible_id
                else:
                    #get last user who was responsible for previous tickets of this family
                    last_ticket = self.search([('id','!=',rec.id),('partner_id','=',rec.partner_id.id),('user_id','!=',False)],limit=1,order='create_date desc')
                    if last_ticket:
                        rec.user_id = last_ticket.user_id.id
                        rec.partner_id.family_responsible_id = last_ticket.user_id.id
                    else:
                        user_id = rec.team_id._determine_user_to_assign()[rec.team_id.id]
                        if user_id:
                            rec.user_id = user_id.id
                            rec.partner_id.family_responsible_id = user_id.id

    @api.constrains("sponsership_lines")
    def check_sponsership_lines(self):
        for rec in self:
            family_count = 0
            member_count = 0
            members = []
            # check for duplicate rows
            for line in rec.sponsership_lines:
                if rec.is_needy_family and line.family:
                    family_count += 1
                if not rec.is_needy_family and line.family_member:
                    member_count += 0
                    if line.family_member.id in members:
                        raise ValidationError(_("This family member is already in this waiting list"))
                    else:
                        members.append(line.family_member.id)
            
            if rec.is_needy_family and family_count > 1:
                raise ValidationError(_("This family is already in the waiting list"))
            if not rec.is_needy_family and member_count >= len(rec.partner_id.child_ids)+1:
                raise ValidationError(_("You have reached the family members limit"))

    @api.model_create_multi
    def create(self, vals_list):
        # Prevent "a partner cannot follow twice the same object" error.
        # This happens if the creator is also set to automatically follow via team assignment or UI defaults.
        # Setting mail_create_nosubscribe=True prevents mail.thread from directly executing a blind 
        # INSERT into mail.followers for the creator with check_existing=False.
        tickets = super(HelpdeskTicket, self.with_context(mail_create_nosubscribe=True)).create(vals_list)
        
        # Safely enforce that the creator becomes a follower using properly checked methods 
        for ticket in tickets:
            if ticket.env.user.partner_id:
                ticket.message_subscribe(partner_ids=ticket.env.user.partner_id.ids)
                
        return tickets

    @api.depends(
        "service.document_types.is_orphan",
        "service.document_types.is_needy_family",
        "service.document_types.is_education",
        "service.document_types.is_material",
        "service.document_types.is_bill"
    )
    def _get_document_types(self):
        for rec in self:
            rec.is_orphan = False
            rec.is_needy_family = False
            rec.is_education = False
            rec.is_material = False
            rec.is_bill = False
            if rec.service:
                for doc in rec.service.document_types:
                    if doc.is_orphan:
                        rec.is_orphan = True
                    if doc.is_needy_family:
                        rec.is_needy_family = True
                    if doc.is_education:
                        rec.is_education = True
                    if doc.is_material:
                        rec.is_material = True
                    if doc.is_bill:
                        rec.is_bill = True
    
    @api.depends("bills_ids","sponserships","projects","pickings","cases")
    def _count_o2m(self):
        for rec in self:
            rec.bills_count = len(rec.bills_ids)
            rec.sponserships_count = len(rec.sponserships)
            rec.projects_count = len(rec.projects)
            rec.pickings_count = len(rec.pickings)
            rec.cases_count = len(rec.cases)

    @api.depends("country_id","state_id","city_id","stage_id")
    def _cal_address_allow(self):
        for rec in self:
            if not rec.service.allowed_address:
                continue
            
            service_allowed = False

            for address in rec.service.allowed_address:
                # Check if user's country matches the address country
                if rec.partner_id.country_id.id != address.country_id.id:
                    continue
                
                # Case 1: Service has country, state, and city
                if address.city_ids:
                    if rec.partner_id.city_id.id in address.city_ids.ids:
                        service_allowed = True
                        break
                
                # Case 2: Service has country and state but no city
                elif address.state_ids:
                    if rec.partner_id.state_id.id in address.state_ids.ids:
                        service_allowed = True
                        break
                
                # Case 3: Service has only country (no state and no city)
                elif not address.state_ids and not address.city_ids:
                    service_allowed = True
                    break
            
            if service_allowed:
                rec.is_address_allowed = True
            else:
                rec.is_address_allowed = False

    @api.depends("bills_ids.payment_state")
    def cal_payment_status(self):
        for rec in self:
            for bill in rec.bills_ids: 
                rec.payment_status = bill.payment_state

    @api.depends("budget_analytic_accounts_ids")
    def _cal_budget_lines(self):
        self.calculate_budget_lines()

    def calculate_budget_lines(self):
        for rec in self:
            budget_lines = self.env["budget.line"]
            if rec.budget_analytic_accounts_ids:
                for analytic_account in rec.budget_analytic_accounts_ids:
                    budget_lines |= self.env["budget.line"].sudo().search([(analytic_account.plan_id._column_name(), '=', analytic_account.id)])

            if budget_lines:
                rec.budget_line_ids = budget_lines.ids
            else:
                rec.budget_line_ids = False

    @api.depends("stage_id")
    def _cal_stage(self):
        for rec in self:
            
            if rec.stage_id.id == rec.team_id.is_draft_stage.id:
                rec.show_approve_button = True
                rec.show_reject_button = True

            if rec.stage_id.id == rec.team_id.is_approve_stage.id:
                rec.show_reject_button = True

            if rec.stage_id.id == rec.team_id.is_done_stage.id:
                rec.show_cancel_button = False
                rec.show_reject_button = False
                
                if not rec.is_done_stage:
                    rec.is_done_stage = True
                    self._excute_action_type() #TODO
                
            stages = self.env["helpdesk.stage"].sudo().search([])
            team_stages = stages.filtered(lambda s: rec.team_id.id in s.team_ids.ids).sorted(lambda o: o.sequence)
            sequences = team_stages.mapped("sequence")

            for i in range(0,len(sequences)):
                if rec.stage_id.sequence == sequences[i]:
                    if i - 1 >= 0:
                        for s in team_stages:
                            if s.sequence == sequences[i-1]:
                                rec.previous_stage = s.id
                                if s.id in [ 
                                    rec.team_id.is_done_stage.id,
                                    rec.team_id.is_cancel_stage.id,
                                    rec.team_id.is_reject_stage.id
                                    ]:
                                    rec.previous_stage = False
                                else:
                                    rec.previous_stage = s.id
                    else:
                        rec.previous_stage = False

                    if i + 1 < len(sequences):
                        for s in team_stages:
                            if s.sequence == sequences[i+1]:
                                rec.next_stage = s.id
                                if s.id in [ 
                                    rec.team_id.is_draft_stage.id,
                                    rec.team_id.is_cancel_stage.id,
                                    rec.team_id.is_reject_stage.id
                                    ]:
                                    rec.next_stage = False
                                else:
                                    rec.next_stage = s.id
                    else:
                        rec.next_stage = False

    def button_previous_stage(self):
        for rec in self:
            if rec.previous_stage:
                rec.stage_id = rec.previous_stage.id
                rec.show_cancel_button = True

    def button_next_stage(self):
        for rec in self:
            self._create_activity()
            if rec.next_stage:
                rec.stage_id = rec.next_stage.id

    def button_draft_stage(self):
        for rec in self:
            if rec.team_id.is_draft_stage:
                rec.stage_id = rec.team_id.is_draft_stage.id
                rec.show_draft_button = False
                rec.show_cancel_button = True
                rec.show_approve_button = True
                rec.show_reject_button = True

    def button_approve_stage(self):
        for rec in self:
            if rec.team_id.is_approve_stage:
                rec.stage_id = rec.team_id.is_approve_stage.id
                rec.show_draft_button = False
                rec.show_cancel_button = True
                rec.show_approve_button = False
                rec.show_reject_button = False

    def button_reject_stage(self):
        for rec in self:
            if rec.team_id.is_reject_stage:
                rec.stage_id = rec.team_id.is_reject_stage.id
                rec.show_draft_button = True
                rec.show_cancel_button = False
                rec.show_approve_button = False
                rec.show_reject_button = False

    def button_cancel_stage(self):
        for rec in self:
            if rec.team_id.is_cancel_stage:
                rec.stage_id = rec.team_id.is_cancel_stage.id
                rec.show_draft_button = True
                rec.show_cancel_button = False
                rec.show_approve_button = False
                rec.show_reject_button = False

    def action_see_documents(self):
        self.ensure_one()
        family = []
        if self.partner_id:
            family.append(self.partner_id.id)

            if self.partner_id.child_ids:
                for child in self.partner_id.child_ids:
                    family.append(child.id)
        
            return {
                'name': _('Documents'),
                'domain': [('partner_id', 'in', family)],
                'res_model': 'documents.document',
                'type': 'ir.actions.act_window',
                'views': [(False, 'kanban')],
                'view_mode': 'kanban',
                'context': {
                    "default_partner_id": self.partner_id.id,
                    "searchpanel_default_folder_id": False
                },
            }

    def action_see_projects(self):
        self.ensure_one()
        return {
            'name': _('Projects'),
            'domain': [('request_id', '=', self.id)],
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'views': [(False, 'kanban'),(False, 'form')],
            'view_mode': 'kanban',
            'context': {
                'create':0,
                "default_request_id": self.id,
                'default_is_swms': True,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_see_pickings(self):
        self.ensure_one()
        return {
            'name': _('Delivery'),
            'domain': [('request_id', '=', self.id)],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'),(False, 'form')],
            'view_mode': 'list',
            'context': {
                'create':0,
                "default_request_id": self.id,
                'default_is_swms': True,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_see_bills(self):
        self.ensure_one()
        return {
            'name': _('Vendor Bills'),
            'domain': [
                ('request_id', '=', self.id),
                ('move_type','=','in_invoice')
            ],
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'),(False, 'form')],
            'view_mode': 'list',
            'context': {
                'create':0,
                "default_request_id": self.id,
                'default_move_type': 'in_invoice',
                'default_is_swms': True,
                "default_partner_id": self.partner_id.id,
            },
        }

    def action_see_cases(self):
        self.ensure_one()
        return {
            'name': _('Case Studies'),
            'domain': [
                ('request_id', '=', self.id)
            ],
            'res_model': 'swms.case',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'),(False, 'form')],
            'view_mode': 'list',
            'context': {
                "default_request_id": self.id,
                "default_researcher_id": self.env.user.id,
            },
        }

    def action_see_sponserships(self):
        self.ensure_one()
        return {
            'name': _('Sponserships'),
            'domain': [('request_id', '=', self.id)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'views': [(False, 'list'),(False, 'form')],
            'view_mode': 'list',
            'context': {
                'create':0,
                "default_request_id": self.id,
                'default_is_swms': True,
                "default_family": self.partner_id.id,
            },
        }

    @api.constrains('partner_id','team_id')
    def _check_duplicate_request(self):
        for rec in self:
            if rec.is_swms:
                count = 0
                requests_no = "" 
                if rec.partner_id and rec.team_id.service:
                    requests = self.env["helpdesk.ticket"].sudo().search([
                        ('partner_id','=',rec.partner_id.id),
                        ('service','=',rec.team_id.service.id)
                    ])
                    requests = requests.filtered(lambda re: re.stage_id.id != rec.team_id.is_done_stage.id)
                    for request in requests:
                        if request.stage_id.id not in [rec.team_id.is_done_stage.id,rec.team_id.is_cancel_stage.id]:
                            count += 1
                            requests_no += " - "+request.request_seq

                    if not rec.service.can_be_repeated and count >= 2:
                        raise ValidationError(f"You already have a request for this service before [{requests_no}] and it's not done yet !")

    @api.depends('partner_id.documents','partner_id.child_ids.documents','stage_id')
    def _compute_document_count(self):
        for record in self:
            family = []
            if record.partner_id:
                family.append(record.partner_id.id)
                if record.partner_id.child_ids:
                    for child in record.partner_id.child_ids:
                        family.append(child.id)
                        
                documents = self.env['documents.document'].search(
                    expression.AND([
                        [('partner_id', 'in', family)],
                        [('type', '!=', 'folder')],
                    ])
                )
                record.documents = documents
                record.document_count = len(documents)
            else:
                record.document_count = 0

    @api.constrains('documents','is_orphan','is_needy_family','is_education','stage_id')
    def check_documents(self):
        for rec in self:
            if rec.partner_id:
                if rec.partner_id.is_family:
                    vdoc = helpers.validate_documents(self,rec,True)
                    if vdoc['types'] or vdoc['expired']:
                        rec.noti_documents = _("Missing Documents:")+f""" \n{vdoc['types']}\n{vdoc['expired']}"""
                        if vdoc['issuance'] or vdoc['expire']:
                            rec.noti_documents = rec.noti_documents+"\n"+_("Mandatory fields:")+f""" \n{vdoc['expire']}\n{vdoc['issuance']}"""
                        # raise ValidationError(f"""Missing Documents: \n{vdoc['types']}\nMandatory fields: \n{vdoc['expire']}\n{vdoc['issuance']}""")
                    else:
                        rec.noti_documents = False

    def _excute_action_type(self):
        for rec in self:
            if rec.is_sponsership:
                for line in rec.sponsership_lines:
                    line.submitted() 
                    # salesman_group_id = self.env.ref('sales_team.group_sale_salesman').id
                    # sales_manager_group_id = self.env.ref('sales_team.group_sale_manager').id
                    # sales_team_group_sale_salesman_all_leads = self.env.ref('sales_team.group_sale_salesman_all_leads').id

                    # users = self.env['res.users'].search([('groups_id', 'in', [salesman_group_id,sales_manager_group_id,sales_team_group_sale_salesman_all_leads])])
                    # partner_ids = users.partner_id.ids
                    # body = _('%s has been added to the waiting list') % (rec.family.name)
                    # rec.message_post(body=body, partner_ids=partner_ids)
                    # rec.message_subscribe(partner_ids=partner_ids)
                    # activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
                    # for user in users:
                    #     rec.activity_schedule(
                    #         activity_type_id=activity_type_id,
                    #         date_deadline=fields.Date.today(),
                    #         summary="Assign a sponser",
                    #         note=body,
                    #         user_id=user.id
                    #     )
            else:
                if rec.action_types == 'none':
                    pass
                elif rec.action_types == 'one':
                    if rec.vendor_id:
                        self.env['account.move'].sudo().create({
                            'request_id': rec.id,
                            'family': rec.partner_id.id,
                            'is_swms':True,
                            'partner_id': rec.vendor_id.id,
                            'move_type': 'in_invoice',
                            'invoice_date': fields.Datetime.now(),
                            'invoice_line_ids': [(0, 0, {
                                'product_id': rec.service.product_variant_id.id,
                                'name': rec.service.name,
                                'quantity': 1,
                                'price_unit': rec.total_amount
                            })]
                        })
                    else: #TODO
                        raise ValidationError(_("Please select who to pay"))
                elif rec.action_types == 'recurring':
                    weeks = 0
                    if rec.service.plan_id:
                        if rec.service.plan_id.billing_period_unit == 'week':
                            weeks = 1 * rec.service.plan_id.billing_period_value 
                        elif rec.service.plan_id.billing_period_unit == 'month':
                            weeks = 4.34524 * rec.service.plan_id.billing_period_value 
                        elif rec.service.plan_id.billing_period_unit == 'year':
                            weeks = 52.1429 * rec.service.plan_id.billing_period_value 
                    if rec.vendor_id:
                        self.env['account.move'].sudo().create({
                            'request_id': rec.id,
                            'family': rec.partner_id.id,
                            'is_swms':True,
                            'auto_post':'monthly',
                            'auto_post_until': fields.Date.today()+timedelta(weeks=weeks),
                            'partner_id': rec.vendor_id.id,
                            'move_type': 'in_invoice',
                            'invoice_date': fields.Datetime.now(),
                            'invoice_line_ids': [(0, 0, {
                                'product_id': rec.service.product_variant_id.id,
                                'name': rec.service.name,
                                'quantity': 1,
                                'price_unit': rec.total_amount
                            })]
                        })
                    else: #TODO
                        raise ValidationError(_("Please select who to pay"))
                elif rec.action_types == 'project':
                    if not rec.service.project_template_id:
                        raise ValidationError(_("Please configure a project template in the service."))
                    
                    projects_ids = self.env['project.project'].sudo().search([
                        ('request_id','=', rec.id)
                    ])
                    if not projects_ids:
                        values = {
                            'request_id': rec.id,
                            'is_swms':True,
                            'name':rec.name,
                            'partner_id': rec.partner_id.id,
                        }
                        if rec.service.project_template_id:
                            values['name'] = "%s - %s" % (values['name'], rec.service.project_template_id.name)
                            order_project = rec.service.project_template_id.copy(values)
                            order_project._create_analytic_account()
                        else:
                            order_project = self.env['project.project'].create(values)
                            order_project._create_analytic_account()

                        # Avoid new tasks to go to 'Undefined Stage'
                        if not order_project.type_ids:
                            order_project.type_ids = self.env['project.task.type'].create([{
                                'name': name,
                                'fold': fold,
                                'sequence': sequence,
                            } for name, fold, sequence in [
                                (_('To Do'), False, 5),
                                (_('In Progress'), False, 10),
                                (_('Done'), False, 15),
                                (_('Cancelled'), True, 20),
                            ]])
                elif rec.action_types == 'material':
                    warehouse = self.env["stock.warehouse"].sudo().search([],limit=1)
                    move_ids = []
                    for line in rec.material_lines:
                        if line.product.type == "consu":
                            move_ids.append((0, 0, {
                                'name': line.product.name+" "+line.name,
                                'product_id': line.product.id,
                                'product_uom_qty': line.qty,
                                'product_uom': line.product.uom_id.id,
                                'location_id': warehouse.lot_stock_id.id
                            }))
                            line.state = "submitted"
                    stock_picking = self.env['stock.picking'].sudo().create({
                        'request_id': rec.id,
                        'is_swms':True,
                        'picking_type_id': warehouse.out_type_id.id,
                        'location_id': warehouse.lot_stock_id.id,
                        'partner_id': rec.partner_id.id,
                        'scheduled_date': fields.Datetime.now(),
                        'move_ids': move_ids
                    })
                # else:
                #     raise ValidationError("Other")
            