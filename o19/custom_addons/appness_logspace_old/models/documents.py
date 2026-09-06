from odoo import models,fields,api,_
import datetime

class DocumentType(models.Model):
    _name = "logspace.document.type"
    _description = "Document Type"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(required=True, translate=True)
    description = fields.Text(translate=True)
    choose_activity_type_id = fields.Many2one("mail.activity.type", required=True,
        default=lambda self: self.env.ref('appness_logspace.mail_activity_document_expire', raise_if_not_found=False))
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

    #Services
    services = fields.Many2many("product.template")

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
                rec.document_domain_model_name = "sale.order"
            else:
                rec.document_domain_model_name = "res.partner"

class Document(models.Model):
    _inherit = "documents.document"

    doc_type = fields.Many2one("logspace.document.type")
    issuance_date = fields.Date()
    expire_date = fields.Date()

    is_expired = fields.Boolean()
    is_archived = fields.Boolean()

    def send_notifications(self):
        #documents
        self.document_expiry_noti()

        #researcher assignment to a case
        # self.researcher_assignment_noti()

        #Reminder for pending approval to management
        # self.management_reminder_noti()

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
        orders = self.env["sale.order"].sudo().search([
            ('is_logspace','=',True),
            ('user_id','!=',False),
            ('state','in',['sale','done']),
        ])
        for order in orders:
            if order.user_id:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', order.user_id.id), 
                    ('res_id', '=', order.id), 
                    ('activity_type_id', '=', todo_activity_type_id.id)
                ])
                if not activity_ids:
                    order.activity_schedule(
                        activity_type_id=todo_activity_type_id.id,
                        date_deadline=order.date_order,
                        user_id=order.user_id.id
                    )
    
    def management_reminder_noti(self):
        todo_activity_type_id = self.env.ref('mail.mail_activity_data_todo')
        orders = self.env["sale.order"].sudo().search([
            ('is_logspace','=',True),
            ('state','in',['sale','done']),
        ])
        for order in orders:
            for follower in order.message_partner_ids:
                activity_ids = self.env['mail.activity'].search([
                    ('user_id', '=', follower.user_id.id), 
                    ('res_id', '=', order.id), 
                    ('activity_type_id', '=', todo_activity_type_id.id)
                ])
                if not activity_ids:
                    order.activity_schedule(
                        activity_type_id=todo_activity_type_id.id,
                        date_deadline=order.date_order,
                        user_id=follower.user_id.id
                    )