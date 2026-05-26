from enum import unique
from odoo import models, fields, api, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
import datetime
from . import helpers

class Family(models.Model):
    _inherit = "res.partner"
    
    is_family = fields.Boolean()
    is_sponser = fields.Boolean()
    is_dead = fields.Boolean()
    allow_editing_portal = fields.Boolean()
    family_responsible_id = fields.Many2one("res.users",string="Family Responsible",tracking=True)
    is_orphan = fields.Boolean(compute="_cal_orphan",store=True)
    family_type = fields.Selection([
        ("member","Member"),
        ("family","Family"),
    ],default="family")
    family_seq = fields.Char(string="Family No.",default="New")
    member_seq = fields.Char(string="Member No.",default="New")

    accommodation_type = fields.Selection([
        ('owned', 'Owned'),
        ('rented', 'Rented'),
        ('inherited', 'Inherited'),
        ('attached', 'Attached (with relatives)'),
        ('other', 'Other'),
    ], 'Type of Accommodation',tracking=True)

    building_type = fields.Selection([
        ('ministry', 'Ministry of Housing'),
        ('personal', 'Personal'),
        ('social', 'Social Development'),
        ('rented', 'Rented'),
    ], 'Built by',tracking=True)

    area_id = fields.Many2one("swms.area")

    has_analytic_account = fields.Boolean()#TODO:compute="_generate_analytic_account",store=True
    analytic_account_id = fields.Many2one('account.analytic.account')#compute="_generate_analytic_account",store=True
    analytic_account_balance = fields.Monetary(related="analytic_account_id.balance")

    civil_number = fields.Char("Civil Number (ID)")
    card_history = fields.One2many("swms.card.spending","family_id") 
    birthday = fields.Date('Date of Birth',tracking=True)
    age = fields.Integer(compute="_cal_age",store=True)
    work_field = fields.Char("Field of Work",tracking=True)
    employer = fields.Char("Employeer",tracking=True)
    employment_date = fields.Date(tracking=True)
    certificate = fields.Selection([
        ('basic', 'Basic School'),
        ('middle', 'Middle School'),
        ('high', 'High School'),
        ('university', 'University'),
        ('graduate', 'Graduate'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('doctor', 'Doctor'),
        ('other', 'Other'),
    ], 'Certificate Level',tracking=True)
    study_field = fields.Char("Field of Study",tracking=True)
    study_school = fields.Char("School",tracking=True)
    study_class = fields.Integer("School Class",tracking=True)
    professional_status = fields.Selection([
        ('working', 'Working'),
        ('not_working', 'Not working'),
        ('job_seeker', 'Job seeker'),
        ('disabled', 'Disabled'),
        ('retired', 'Retired'),
        ('imprisoned', 'Imprisoned'),
        ('sick', 'Sick'),
        ('dead', 'Dead'),
        ('preschooler', 'Preschooler'),
        ('school_student', 'School student'),
        ('university_student', 'University student'),
    ], 'Professional Status',tracking=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ],tracking=True)
    relationship = fields.Selection([
        ('wife', 'Wife'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('grandfather', 'Grandfather'),
        ('grandmother', 'Grandmother'),
        ('son-wife', 'son"s wife'),
        ('grandson', 'Grandson'),
        ('other', 'Other')
    ],tracking=True)
    relationship_other = fields.Char("Relationship Other")
    marital = fields.Selection([
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed'),
        ('abandoned', 'Abandoned'),
        ('dead', 'Dead'),
    ],string='Marital Status',tracking=True)
    
    noti_documents = fields.Text()
    documents = fields.One2many("documents.document","partner_id",string="Family Documents")
    properties = fields.One2many("swms.property","partner_id")
    income_sources = fields.One2many("swms.income","partner_id")
    obligations = fields.One2many("swms.obligation","partner_id")
    sponserships_sponser = fields.One2many("sale.order","partner_id")
    sponserships_family = fields.One2many("sale.order","family")
    sponserships_member = fields.One2many("sale.order","family_member")
    requests_count = fields.Integer("Requests", compute='_compute_requests_count')
    members_count = fields.Integer("Members Count", compute='_compute_members_count',store=True)
    total_income = fields.Float("Monthly Total Income", compute='_compute_total_income',store=True)
    total_obligations = fields.Float("Monthly Total Obligations", compute='_compute_total_obligations',store=True)
    net_worth = fields.Float("Monthly Net Worth", compute='_compute_net_worth',store=True)
    member_net_worth = fields.Float("Member Net Worth", compute='_compute_net_worth',store=True)
    
    @api.depends("income_sources")
    def _compute_total_income(self):
        for record in self:
            record.total_income = sum(record.income_sources.mapped('monthly_amount'))
    
    @api.depends("obligations")
    def _compute_total_obligations(self):
        for record in self:
            record.total_obligations = sum(record.obligations.mapped('monthly_amount'))
    
    @api.depends("total_income","total_obligations")
    def _compute_net_worth(self):
        for record in self:
            record.net_worth = record.total_income - record.total_obligations
            record.member_net_worth = record.net_worth / record.members_count
    
    @api.depends("child_ids")
    def _compute_members_count(self):
        for record in self:
            count = len(record.child_ids.filtered(lambda r: r.family_type == 'member' and r.is_family == True and r.is_company == False))
            record.members_count = count+1

    def _get_complete_name(self):
        self.ensure_one()

        displayed_types = self._complete_name_displayed_types
        type_description = dict(self._fields['type']._description_selection(self.env))

        name = self.name or ''
        if self.is_family:
            if self.family_type == "family":
                name = f"[{self.family_seq}] {name}"
            elif self.family_type == "member":
                if self.parent_id:
                    if not name and self.type in displayed_types:
                        name = type_description[self.type]
                    if not self.is_company:
                        name = f"[{self.member_seq}] {name}, {self.commercial_company_name or self.sudo().parent_id.name}"
        else:
            if self.company_name or self.parent_id:
                if not name and self.type in displayed_types:
                    name = type_description[self.type]
                if not self.is_company:
                    name = f"{self.commercial_company_name or self.sudo().parent_id.name}, {name}"

        return name.strip()

    # @api.model
    # def _search_display_name(self, operator, value):
    #     domain = super()._search_display_name(operator, value)
    #     if value and operator not in expression.NEGATIVE_TERM_OPERATORS:
    #         if operator in ('ilike', '='):
    #             domain = expression.OR([
    #                 domain, self._get_name_search_domain(value, operator),
    #             ])
    #     return domain

    # def _get_name_search_domain(self, value, operator):
    #     return [
    #         ('|','|','name', operator, value.strip()),('family_seq', operator, value.strip()),('member_seq', operator, value.strip()),
    #     ]
    
    def _compute_requests_count(self):
        all_partners_subquery = self.with_context(active_test=False)._search([('id', 'child_of', self.ids)])

        # group tickets by partner, and account for each partner in self
        groups = self.env['helpdesk.ticket']._read_group(
            [('partner_id', 'in', all_partners_subquery)],
            groupby=['partner_id'], aggregates=['__count'],
        )
        self.requests_count = 0
        for partner, count in groups:
            while partner:
                if partner in self:
                    partner.requests_count += count
                partner = partner.with_context(prefetch_fields=False).parent_id
    
    _sql_constraints = [
        # ("phone_unique", "unique(phone)", "This number already exsist .. Phone number must be unique !!"),
        ("civil_number_unique", "unique(civil_number)", "This Civil Number already exists .. Civil Number must be unique !!")
    ]

    def action_reassign_all_requests_to_family_responsible(self):
        for record in self:
            if record.family_responsible_id:
                tickets = self.env['helpdesk.ticket'].search([
                    ('partner_id', '=', record.id),
                    ('user_id', '!=', record.family_responsible_id.id),
                ])
                for ticket in tickets:
                    ticket.write({'user_id': record.family_responsible_id.id})

    # @api.model
    # def create(self, vals):
    #     if vals.get('family_seq', 'New') == 'New' and vals.get('is_family', False) == True and vals.get('company_type', False) == "company":
    #         vals['family_seq'] = self.env['ir.sequence'].next_by_code('family.seq') or '/'

    #     if vals.get('member_seq', 'New') == 'New' and vals.get('parent_id', False) != False and vals.get('company_type', False) == "person":
    #         vals['member_seq'] = self.env['ir.sequence'].next_by_code('member.seq') or '/'
    #     newId = super(Family, self).create(vals)
    #     return newId

    @api.onchange("family_type")
    def _onchange_family_type(self):
        for rec in self:
            if rec.family_type == "member":
                rec.company_type = "person"
            elif rec.family_type == "family":
                rec.company_type = "company"

    @api.onchange("company_type")
    def _onchange_company_type(self):
        for rec in self:
            if rec.company_type == "person":
                rec.family_type = "member"
            elif rec.company_type == "company":
                rec.family_type = "family"

    @api.depends("has_analytic_account","is_family","family_seq","is_company")
    def _generate_analytic_account(self):
        for rec in self:
            ICP = self.env['ir.config_parameter'].sudo()

            family_analytic_plan = ICP.get_param('appness_swms.family_analytic_plan')
            if family_analytic_plan:
                if not rec.has_analytic_account and rec.is_family and rec.is_company and rec.family_seq:
                    analytic_account = self.env["account.analytic.account"].sudo().create({
                        "name":rec.name +" ["+rec.family_seq+"] ",
                        "plan_id":family_analytic_plan,
                        "partner_id":rec.id,
                    })
                    analytic_distribution = {f"{analytic_account.id}": 100}
                    analytic_distribution_model = self.env["account.analytic.distribution.model"].sudo().create({
                        "partner_id":rec.id,
                        "analytic_distribution": analytic_distribution
                    })
                    rec.analytic_account_id = analytic_account.id
                    rec.has_analytic_account = True
                else:
                    rec.has_analytic_account = False
            else:
                rec.has_analytic_account = False

    @api.depends("birthday")
    def _cal_age(self):
        #TODO: prevent negtive age
        for rec in self:
            today = datetime.datetime.today()
            if rec.birthday:
                rec.age = today.year - rec.birthday.year
            else:
                rec.age = 0

    @api.depends("is_family","is_company","parent_id.is_dead","relationship","age")
    def _cal_orphan(self):
        for rec in self:
            if rec.is_family and not rec.is_company and rec.parent_id \
                and rec.parent_id.is_dead and rec.relationship in ["son","daughter"] and rec.age < 18:
                rec.is_orphan = True
            else:
                rec.is_orphan = False

    @api.constrains('is_family','is_sponser')
    def _check_family_sponser(self):
        for rec in self:
            if rec.is_family and rec.is_sponser:
                raise ValidationError("Sorry but it can't be Sponser and a Family at the same time !! Please choose only one of the 2 options")

    @api.constrains('documents','marital','birthday','family_type','company_type','family_seq','member_seq')
    def check_documents(self):
        for rec in self:
            if rec.is_family:
                if rec.family_seq == 'New' and rec.company_type == "company" and rec.family_type == "family":
                    rec.family_seq = self.env['ir.sequence'].next_by_code('family.seq') or '/'

                if rec.member_seq == 'New' and rec.company_type == "person" and rec.family_type == "member":
                    rec.member_seq = self.env['ir.sequence'].next_by_code('member.seq') or '/'
                    
                vdoc = helpers.validate_documents(self, rec)
                if vdoc['types'] or vdoc['expired']:
                    rec.noti_documents = _("Missing Documents:")+f""" \n{vdoc['types']}\n{vdoc['expired']}"""
                    if vdoc['issuance'] or vdoc['expire']:
                        rec.noti_documents = rec.noti_documents+"\n"+_("Mandatory fields:")+f""" \n{vdoc['expire']}\n{vdoc['issuance']}"""
                    # raise ValidationError(f"""Missing Documents: \n{vdoc['types']}\nMandatory fields: \n{vdoc['expire']}\n{vdoc['issuance']}""")
                else:
                    rec.noti_documents = False
    
    @api.constrains('civil_number')
    def _check_civil_number(self):
        for rec in self:
            if rec.civil_number:
                families = self.search([('civil_number', '=', rec.civil_number)])
                for family in families:
                    if family.id != rec.id:
                        raise ValidationError(_("This Civil Number already exists .. Civil Number must be unique !!"))
                
                if not rec.civil_number.isdigit():
                    raise ValidationError(_("Civil Number must be a number"))
                