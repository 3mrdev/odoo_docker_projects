from odoo import models,fields,api,_
from odoo.exceptions import ValidationError
from datetime import timedelta , datetime ,date

class Serviceline(models.Model):
    _name = "swms.service.line"
    _description = "Sponsership Waiting List"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(default="New",string="Waiting No.")
    product = fields.Many2one("product.product",domain="[('type','=','service')]",tracking=True)
    family = fields.Many2one("res.partner",domain="[('is_family','=',True),('is_company','=',True)]",tracking=True)
    card_id = fields.Many2one("swms.card",tracking=True)
    card_used = fields.Boolean(related="card_id.card_used",store=True)
    family_member = fields.Many2one("res.partner", domain="[('parent_id','=',family)]", tracking=True)
    birthday = fields.Date('Date of Birth',related="family_member.birthday",store=True)
    age = fields.Integer(related="family_member.age",store=True)
    qty = fields.Integer()
    lead = fields.Many2one("crm.lead",string="Opportunity",tracking=True)
    sponsership = fields.Many2one("sale.order",tracking=True)
    sponsership_state = fields.Selection(related="sponsership.subscription_state",store=True)
    request = fields.Many2one("helpdesk.ticket",tracking=True)
    approved_date = fields.Datetime()
    waiting_date = fields.Datetime()
    state = fields.Selection([
        ('draft','Draft'),
        ('reported','Reported'),
        ('submitted','Submitted'),
        ('approved','Approved'),
        ('waiting','Waiting'),
        ('done','Done'),
        ('refused','Refused'),
    ],default="draft",string="Status",tracking=True)

    def draft(self):
        for rec in self:
            rec.state = "draft"

    def reported(self):
        for rec in self:
            rec.state = "reported"
    
    def submitted(self):
        for rec in self:
            rec.state = "submitted"
            salesman_group_id = self.env.ref('sales_team.group_sale_salesman').id
            sales_manager_group_id = self.env.ref('sales_team.group_sale_manager').id
            sales_team_group_sale_salesman_all_leads = self.env.ref('sales_team.group_sale_salesman_all_leads').id

            users = self.env['res.users'].search([('groups_id', 'in', [salesman_group_id,sales_manager_group_id,sales_team_group_sale_salesman_all_leads])])
            partner_ids = users.partner_id.ids
            body = _('%s has been added to the waiting list') % (rec.family.name)
            rec.message_post(body=body, partner_ids=partner_ids)
            rec.message_subscribe(partner_ids=partner_ids)
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            for user in users:
                rec.activity_schedule(
                    activity_type_id=activity_type_id,
                    date_deadline=fields.Date.today(),
                    summary="Assign a sponser",
                    note=body,
                    user_id=user.id
                )

    def approved(self):
        for rec in self:
            if rec.name == "New":
                rec.name = self.env['ir.sequence'].next_by_code("waiting.seq") or '/'
                rec.approved_date = fields.Datetime.now()
                rec.state = "approved"
            else:
                rec.approved_date = fields.Datetime.now()
                rec.state = "approved"

    def waiting(self):
        for rec in self:
            rec.waiting_date = fields.Datetime.now()
            rec.state = "waiting"

    def done(self):
        ICP = self.env['ir.config_parameter'].sudo()

        orphan_age = ICP.get_param('appness_swms.orphan_age')
        needy_family_period = ICP.get_param('appness_swms.needy_family_period')

        for rec in self:
            request = rec.request
            lead = rec.lead
            rec.card_id.family_id = rec.family.id

            data = {
                "partner_id":lead.partner_id.id,
                "plan_id":rec.product.plan_id.id,
                "opportunity_id":lead.id,
                "request_id":request.id,
                "family":rec.family.id,
                "card_id":rec.card_id.id,
                "is_swms":True,
                "order_line": [
                    fields.Command.create({
                        "product_id": rec.product.id,
                        "product_uom_qty": 1,
                        "price_unit": request.total_amount,
                    })
                ]
            }

            if rec.family_member:
                data["family_member"] = rec.family_member.id
                if rec.birthday:
                    if orphan_age:
                        end_date = rec.birthday + timedelta(days=(int(orphan_age) * 365))
                        data["end_date"] = str(end_date)
            else:
                if needy_family_period:
                    end_date = fields.Date.today() + timedelta(days=(int(needy_family_period) * 30))
                    data["end_date"] = str(end_date)
            
            sponsership_id = self.env["sale.order"].sudo().create(data)
            if sponsership_id:
                rec.state = "done"
                rec.sponsership.action_cancel()
                rec.sponsership = sponsership_id.id
                sponsership_id.action_confirm()

    def refused(self):
        for rec in self:
            rec.state = "refused"

    def unlink(self):
        for rec in self:
            if rec.state in ["approved","waiting","done","refused"]:
                raise ValidationError("You can't delete sponsership from the waiting list")
            return super().unlink()