from odoo import models,fields,api
from odoo.exceptions import ValidationError,UserError

class SWMSReportsWizard(models.TransientModel):
    _name = 'swms.reports.wizard'
    _description = "SWMS Reports Wizard"

    from_date = fields.Date(default=fields.Date.today,required=True)
    to_date = fields.Date(default=fields.Date.today,required=True)

    sponser_id = fields.Many2one('res.partner',string='Sponser',domain=[('is_sponser', '=', True)])
    family = fields.Many2one('res.partner',string='Family',domain=[('is_family', '=', True),('is_company', '=', True)])
    orphan = fields.Many2one('res.partner',string='Orphan',domain=[('is_orphan', '=', True)])
    
    sort_reports = fields.Boolean(default=False)
    reports_ids = fields.One2many("swms.reports.wizard.report","wizard_id")

    report1 = fields.Boolean("Family Statment Report",default=False)
    report2 = fields.Boolean("Member Report",default=False)
    report3 = fields.Boolean("Income Report",default=False)
    report4 = fields.Boolean("Obligations Report",default=False)
    report5 = fields.Boolean("Families Report",default=False)
    report6 = fields.Boolean("Orphans Report",default=False)
    report7 = fields.Boolean("Family Report",default=False)

    select_all = fields.Boolean("Select All",default=False)

    @api.onchange("sort_reports")
    def onchange_sort_reports(self):
        for rec in self:
            reports = [
                "Family Statment Report",
                "Member Report",
                "Income Report",
                "Obligations Report",
                "Families Report",
                "Orphans Report",
                "Family Report",
            ]
            ids = []
            for i in range(len(reports)):
                ids.append((0, 0, {
                    "name":reports[i],
                    "num":i+1,
                }))
            rec.reports_ids = False
            rec.reports_ids = ids

    @api.onchange("select_all")
    def onchange_select_all(self):
        for rec in self:
            if rec.select_all:
                rec.report1 = True
                rec.report2 = True
                rec.report3 = True
                rec.report4 = True
                rec.report5 = True
                rec.report6 = True
                rec.report7 = True
                if self.sort_reports:
                    for report in self.reports_ids:
                        report.check = True
            else:
                rec.report1 = False
                rec.report2 = False
                rec.report3 = False
                rec.report4 = False
                rec.report5 = False
                rec.report6 = False
                rec.report7 = False
                if not self.sort_reports:
                    for report in self.reports_ids:
                        report.check = False

    def print_report(self):
        """Call when button 'Get Report' clicked.
        """    
        domain = [
            ("is_family","=",True)
        ]

        # if self.sponser_id:
        #     domain.append(('sponser_id','=',self.sponser_id.id))

        if self.family:
            domain.append(('id','=',self.family.id))
            domain.append(("is_company","=",True))

        if self.orphan:
            domain.append(('id','=',self.orphan.parent_id.id))

        partners = self.env["res.partner"].search(domain)

        families_list = []
        orphans_list = []
        for family in partners:
            member_list = []
            income_list = []
            obligation_list = []
            total_income = 0
            total_obligations = 0

            member_list.append({
                "name":family.name,
                "is_orphan":family.is_orphan,
                "member_no":family.family_seq,
                "civil_number":family.civil_number,
                "gender":family.gender,
                "relationship":family.relationship,
                "marital":family.marital,
                "age":family.age,
                "work_field":family.work_field,
                "employer":family.employer or False,
                "employment_date":str(family.employment_date),
                "certificate":family.certificate,
                "study_field":family.study_field,
                "study_school":family.study_school,
                "study_class":family.study_class,
                "address_area":family.address_area,
                "address_city":family.address_city,
                "address_country":family.address_country,
            })

            for income in family.income_sources:
                total_income += income.amount
                income_list.append({
                    "name":income.doc_type,
                    "amount":income.amount,
                    "interval":income.interval,
                    "frequency":income.frequency,
                    "partner_id":income.partner_id.name or False,
                })

            for obligation in family.obligations:
                total_obligations += obligation.remaining_amount
                obligation_list.append({
                    "name":obligation.doc_type,
                    "creditor":obligation.creditor_name,
                    "payment_method":obligation.payment_method,
                    "total_amount":obligation.total_amount,
                    "remaining_amount":obligation.remaining_amount,
                    "interval":obligation.interval,
                    "frequency":obligation.frequency,
                    "partner_id":obligation.partner_id.name or False,
                })

            for member in family.child_ids:
                member_list.append({
                    "name":member.name,
                    "is_orphan":family.is_orphan,
                    "member_no":member.member_seq,
                    "civil_number":member.civil_number,
                    "gender":member.gender,
                    "relationship":member.relationship,
                    "marital":member.marital,
                    "age":member.age,
                    "work_field":member.work_field,
                    "employer":member.employer or False,
                    "employment_date":str(member.employment_date),
                    "certificate":member.certificate,
                    "study_field":member.study_field,
                    "study_school":member.study_school,
                    "study_class":member.study_class,
                    "address_area":member.address_area,
                    "address_city":member.address_city,
                    "address_country":member.address_country,
                })

                for income in member.income_sources:
                    total_income += income.amount
                    income_list.append({
                        "name":income.doc_type,
                        "amount":income.amount,
                        "interval":income.interval,
                        "frequency":income.frequency,
                        "partner_id":income.partner_id.name or False,
                    })

                for obligation in member.obligations:
                    total_obligations += obligation.remaining_amount
                    obligation_list.append({
                        "name":obligation.doc_type,
                        "creditor":obligation.creditor_name,
                        "payment_method":obligation.payment_method,
                        "total_amount":obligation.total_amount,
                        "remaining_amount":obligation.remaining_amount,
                        "interval":obligation.interval,
                        "frequency":obligation.frequency,
                        "partner_id":obligation.partner_id.name or False,
                    })

            sponsorship_state = "None"
            sponsor = "None"

            if family.is_company:
                for sponsorship in family.sponserships_family:
                    sponsorship_state = sponsorship.subscription_state
                    sponsor = sponsorship.partner_id.name
                families_list.append({
                    "family_no":family.family_seq,
                    "family_name":family.name,
                    "is_orphan":family.is_orphan,
                    "members": member_list,
                    "members_count": len(member_list),
                    "income": member_list,
                    "obligations": member_list,
                    "total_income":total_income,
                    "total_obligations":total_obligations,
                    "total_net":total_income - total_obligations,
                    "sponsorship_state":sponsorship_state,
                    "sponsor":sponsor,
                })
            
            if family.is_orphan:
                for sponsorship in family.sponserships_member:
                    sponsorship_state = sponsorship.subscription_state
                    sponsor = sponsorship.partner_id.name
                orphans_list.append({
                    "orphan_id":family.member_seq,
                    "name":family.name,
                    "age":family.age,
                    "education":family.member_seq,
                    "sponsorship_state":sponsorship_state,
                    "sponsor":sponsor,
                })

        sorted_reports = []
        if self.sort_reports:
            for report in self.reports_ids:
                sorted_reports.append({
                    "seq":report.seq,
                    "name":report.name,
                    "num":report.num,
                    "check":report.check,
                })

        # raise UserError(f"{sorted_reports}")
        data = {
            'doc_ids': self.ids,
            'doc_model': self._name,
            'report1': self.report1,
            'report2': self.report2,
            'report3': self.report3,
            'report4': self.report4,
            'report5': self.report5,
            'report6': self.report6,
            'report7': self.report7,
            'sort_reports': self.sort_reports,
            'sorted_reports': sorted_reports,
            'from_date': str(self.from_date),
            'to_date': str(self.to_date),
            'sponser': self.sponser_id.name,
            'families':families_list,
            'orphans':orphans_list
        }

        # use `module_name.report_id` as reference.
        # `report_action()` will call `get_report_values()` and pass `data` automatically.
        return self.env.ref('appness_swms.action_swms_report').report_action(self, data=data)

    #Other Income Report
    def get_report1(self,properties):
        docs = []
        docs_total = 0
        for property in properties:
            for inv in property.account_moves_ids:
                if inv.invoice_date:
                    if inv.invoice_date >= self.from_date and inv.invoice_date <= self.to_date:
                        if inv.other_rental_invoice_types == 'income':
                            invoice = {
                                "unit_number":inv.other_property_id.property_seq,
                                "amount":inv.amount_total,
                                "type":dict(inv._fields['other_rental_invoice_types'].selection).get(inv.other_rental_invoice_types),
                                "date":str(inv.invoice_date),
                                "description":inv.description,
                            }
                            docs.append(invoice)
                            docs_total = docs_total + inv.amount_total
        return docs,docs_total
    
    #Other Expenses Report
    def get_report2(self,properties):
        docs = []
        docs_total = 0
        for property in properties:
            for inv in property.account_moves_ids:
                if inv.invoice_date:
                    if inv.invoice_date >= self.from_date and inv.invoice_date <= self.to_date:
                        if inv.other_rental_invoice_types == 'expense':
                            invoice = {
                                "unit_number":inv.other_property_id.property_seq,
                                "amount":inv.amount_total,
                                "type":dict(inv._fields['other_rental_invoice_types'].selection).get(inv.other_rental_invoice_types),
                                "date":str(inv.invoice_date),
                                "description":inv.description,
                            }
                            docs.append(invoice)
                            docs_total = docs_total + inv.amount_total
        return docs,docs_total

class SWMSReportsTemplate(models.AbstractModel):
    """Abstract Model for report template.
    for `_name` model, please use `report.` as prefix then add `module_name.report_name`.
    """

    _name = 'report.appness_swms.swms_report_template'
    _description = "SWMS Reports Wizard Report Template"

    @api.model
    def _get_report_values(self, docids, data=None):
        return data
    
class SWMSReportsWizardReport(models.TransientModel):
    _name = 'swms.reports.wizard.report'
    _description = "SWMS Reports Wizard Report"
    _order = "seq"

    wizard_id = fields.Many2one("swms.reports.wizard")
    seq = fields.Integer()
    num = fields.Integer()
    name = fields.Char(required=True)
    check = fields.Boolean()