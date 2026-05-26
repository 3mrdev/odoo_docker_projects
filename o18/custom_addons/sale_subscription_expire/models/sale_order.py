from odoo import models,fields,api,_
from datetime import timedelta
from ast import literal_eval
import logging
log = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    def _cron_check_subscription_expiry(self, days=7):
        subscription_expiry_domain = self.env['ir.config_parameter'].sudo().get_param(
            'sale_subscription_expire.subscription_expiry_domain', default='[]'
        )

        domain = [
            ('is_subscription', '=', True),
            ('end_date', '>=', fields.Date.today()),
            ('end_date', '<=', fields.Date.today() + timedelta(days=days))
        ]

        if subscription_expiry_domain:
            domain += self._parse_domain(subscription_expiry_domain)

        log.info("Domain: %s", str(domain))
        subs = self.env["sale.order"].search(domain)
        for order in subs:
            body = _('%s subscription has expired') % (order.name)
            # order.message_post(body=body, partner_ids=[order.user_id.partner_id.id])
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            self.env['mail.activity'].search([
                ('res_id', '=', order.id), 
                ('user_id', '=', order.user_id.id),
                ('activity_type_id', '=',activity_type_id)
            ]).unlink()
            order.activity_schedule(
                activity_type_id=activity_type_id,
                date_deadline=fields.Date.today(),
                summary="Subscription Expiry",
                note=body,
                user_id=order.user_id.id
            )

    def _parse_domain(self,domain):
        try:
            domain = literal_eval(domain)
        except Exception:
            domain = [('id', 'in', [])]
        return domain