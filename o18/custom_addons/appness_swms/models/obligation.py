from odoo import models,fields,api,_

class PersonalObligation(models.Model):
    _name = "swms.obligation"
    _description = "Personal Obligation"
    _rec = "doc_type"

    doc_type = fields.Many2one("swms.document.type",domain="[('type','=','obligation')]",string="Type")
    # creditor = fields.Many2one("res.partner", domain="[('is_family','=',False)]")
    creditor_name = fields.Char()
    creditor_phone = fields.Char()
    payment_method = fields.Many2one("swms.payment.method")
    interval = fields.Integer(default=1)
    frequency = fields.Selection([
        ("one","One Time"),
        ("day","Daily"),
        ("week","Weekly"),
        ("month","Monthly"),
        ("year","Yearly")
    ])
    amount = fields.Float()
    total_amount = fields.Float()
    remaining_amount = fields.Float()
    monthly_amount = fields.Float(compute='_compute_monthly_amount',store=True)
    partner_id = fields.Many2one("res.partner")

    @api.depends("amount","frequency","interval")
    def _compute_monthly_amount(self):
        for record in self:
            if record.frequency == "one":
                record.monthly_amount = record.amount
            elif record.frequency == "day":
                record.monthly_amount = record.amount * 30 
            elif record.frequency == "week":
                record.monthly_amount = record.amount * 4 
            elif record.frequency == "month":
                record.monthly_amount = record.amount 
            elif record.frequency == "year":
                record.monthly_amount = record.amount / 12 