from odoo import models,fields,api,_
from datetime import timedelta , datetime ,date

class Sponsership(models.Model):
    _inherit = "sale.order"

    is_swms = fields.Boolean()
    request_id = fields.Many2one("helpdesk.ticket")
    family = fields.Many2one("res.partner",domain="[('is_family','=',True),('is_company','=',True)]")
    card_id = fields.Many2one("swms.card")
    family_member = fields.Many2one("res.partner",domain="[('parent_id','=',family)]")
    show_member = fields.Boolean(compute="_show_member",store=True)

    @api.depends("order_line.product_id.document_types")
    def _show_member(self):
        for rec in self:
            show_member = False
            for line in rec.order_line:
                if line.product_id:
                    for type in line.product_id.document_types:
                        if type.is_orphan or type.is_education:
                            show_member = True
            rec.show_member = show_member

    def update_info_pause_subs(self):
        ICP = self.env['ir.config_parameter'].sudo()

        pause_days = ICP.get_param('appness_swms.pause_days') or 0

        if pause_days > 0:
            today = date.today()
            records = self.env["sale.order"].search([
                ('is_swms','=',True),
                ('is_subscription','=',True),
                # ('date_order','<=',str(today)),
            ])
            needs_info_records = records.filtered(lambda rec:  today >= rec.start_date + timedelta(days=pause_days))
            if needs_info_records:
                needs_info_records.pause_subscription()
                #TODO: Send SMS or Notification to Customer