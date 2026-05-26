from odoo import models,fields,api,_
import datetime

class DocumentType(models.Model):
    _name = "swms.document.type"
    _description = "Document Type"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    choose_activity_type_id = fields.Many2one("mail.activity.type", required=True,
        default=lambda self: self.env.ref('appness_swms.mail_activity_document_expire', raise_if_not_found=False))
    type = fields.Selection([
        ("family","Family"),
        ("income","Income"),
        ("obligation","Obligation"),
        ("property","Property"),
        ("service","Service"),
    ],required=True)
    family_type = fields.Selection([
        ("member","Members"),
        ("family","Family"),
    ],default="family",string="Applicable for?")
    is_mandatory = fields.Boolean()
    active = fields.Boolean(default=True)

    document_domain = fields.Char()
    document_domain_model_name = fields.Char(compute="_document_domain_model_name",store=True)

    #Family
    is_marriage = fields.Boolean(string="Is Married?",help="If the family member is married he/she should upload this document")
    is_birth = fields.Boolean(string="Is Under 18?",help="If the family member is under 18 years old he/she should upload this document")
    is_death = fields.Boolean(string="Is Widowed?",help="If the mother's husband is dead she should upload this document")
    is_divorce = fields.Boolean(string="Is Divorced?",help="If the family member is divorced he/she should upload this document")

    #Services
    services = fields.Many2many("product.template")
    is_orphan = fields.Boolean(string="Is Orphan?",help="If the family member's father is dead he/she should upload this document")
    is_needy_family = fields.Boolean(string="Is Needy Family?",help="If the family is a needy family they should upload this document")
    is_education = fields.Boolean(string="Is Education?",help="If the family member needs assistance in education he/she should upload this document")
    is_material = fields.Boolean(string="Is Material?", help="If the family needs material assistance they should upload this document")
    is_bill = fields.Boolean(string="Is Bill?",help="If the family bill payment assistance they should upload this document")

    #Notifications
    max_issuance_date = fields.Integer(string="Allow Before Issunace Date (Days)",default=30)
    max_expire_date = fields.Integer(string="Allow After Expire Date (Days)",default=30)
    issuance_date_is_mandatory = fields.Boolean(default=True)
    issuance_date_is_visible = fields.Boolean(default=True)
    expire_date_is_mandatory = fields.Boolean(default=True)
    expire_date_is_visible = fields.Boolean(default=True)

    @api.depends("type")
    def _document_domain_model_name(self):
        for rec in self:
            if rec.type == 'service':
                rec.document_domain_model_name = "helpdesk.ticket"
            else:
                rec.document_domain_model_name = "res.partner"

class Document(models.Model):
    _inherit = "documents.document"

    doc_type = fields.Many2one("swms.document.type")
    issuance_date = fields.Date()
    expire_date = fields.Date()

    is_expired = fields.Boolean()
    is_archived = fields.Boolean()

    def send_notifications(self):
        #documents
        self.document_expiry_noti()

        #researcher assignment to a case
        self.researcher_assignment_noti()

        #Reminder for pending approval to management
        self.management_reminder_noti()

        #TODO:Notification for case approval or rejection status
        #TODO:Case progress updates
        #TODO:Reminder for incomplete obligation entries.
        #TODO:Notification for incomplete income entries.

    def document_expiry_noti(self):
        documents = self.env["documents.document"].sudo().search([
            ('doc_type','!=',False),
            ('expire_date','!=',False),
        ])
        today = datetime.date.today()
        amonth = datetime.timedelta(days=30) #TODO: make time configurable
        before_time = today + amonth
        for doc in documents:
            if doc.doc_type:
                if doc.expire_date:
                    if before_time > doc.expire_date:
                        for follower in doc.doc_type.message_partner_ids.user_ids.ids:
                            activity_ids = self.env['mail.activity'].search([
                                ('user_id', '=', follower), 
                                ('res_id', '=', doc.id), 
                                ('activity_type_id', '=', doc.doc_type.choose_activity_type_id.id)
                            ])
                            if not activity_ids:
                                doc.activity_schedule(
                                    activity_type_id=doc.doc_type.choose_activity_type_id.id,
                                    date_deadline=doc.expire_date,
                                    user_id=follower
                                )
    
    def researcher_assignment_noti(self):
        todo_activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        requests = self.env["helpdesk.ticket"].sudo().search([
            ('is_swms','=',True),
            ('user_id','!=',False),
        ])
        for request in requests:
            if request.user_id:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', request.user_id.id), 
                    ('res_id', '=', request.id), 
                    ('activity_type_id', '=', todo_activity_type_id.id)
                ])
                if not activity_ids:
                    request.activity_schedule(
                        activity_type_id=todo_activity_type_id.id,
                        date_deadline=request.sla_deadline,
                        user_id=request.user_id.id
                    )
    
    def management_reminder_noti(self):
        todo_activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        requests = self.env["helpdesk.ticket"].sudo().search([
            ('is_swms','=',True),
            ('sla_fail','=',True),
        ])
        for request in requests:
            for follower in request.service.message_partner_ids:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', follower.user_id.id), 
                    ('res_id', '=', request.id), 
                    ('activity_type_id', '=', todo_activity_type_id.id)
                ])
                if not activity_ids:
                    request.activity_schedule(
                        activity_type_id=todo_activity_type_id.id,
                        date_deadline=request.sla_deadline,
                        user_id=follower.user_id.id
                    )