from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    name_arabic = fields.Char("Name (Arabic)")
    cr_reg_date = fields.Date("C.R Registration Date")
    cr_expiry_date = fields.Date("C.R Expiry Date")
    profile_id = fields.Char("Profile ID")
    tax_reg_num = fields.Char("Tax Registration Number")
    po_box = fields.Char("P.O Box")
    fax_num = fields.Char("Fax Number")
    legal_type = fields.Char("Legal Type")
    number_of_employees = fields.Integer("Number of Employees")
    
    allow_companies_only = fields.Boolean(related='company_id.allow_companies_only', store=True)
    tag_as_manufacturer = fields.Boolean(related='company_id.tag_as_manufacturer', store=True)
    default_industry_on_partner_creation = fields.Many2one("res.partner.industry",related='company_id.default_industry_on_partner_creation', store=True)

    @api.onchange('allow_companies_only')
    def onchange_allow_companies_only(self):
        for rec in self:
            if rec.allow_companies_only:
                rec.company_type = 'company'

    @api.model
    def default_get(self, fields):
        result = super().default_get(fields)
        if self.env.company:
            result['company_id'] = self.env.company.id
        return result

    @api.onchange('tag_as_manufacturer')
    def onchange_tag_as_manufacturer(self):
        for rec in self:
            if rec.tag_as_manufacturer:
                if rec.default_industry_on_partner_creation:
                    rec.industry_id = rec.default_industry_on_partner_creation.id
                else:
                    raise UserError("Please configure a default industry in this partner company")