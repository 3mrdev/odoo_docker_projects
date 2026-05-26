from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    team_user_ids = fields.Many2many('res.users', string='Project Team')

    def add_project_team(self):
        for record in self:
            group_sale_project_quote_user = self.env.ref('sale_project_quote.group_sale_project_quote_user')
            group_sale_project_quote_manager = self.env.ref('sale_project_quote.group_sale_project_quote_manager')
            team_user_ids = group_sale_project_quote_user.user_ids | group_sale_project_quote_manager.user_ids
            record.team_user_ids = team_user_ids.ids

            body = _('%s please review this quotation') % (record.name)
            # record.message_post(body=body, partner_ids=team_user_ids.partner_id.ids)
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id
            for user in team_user_ids:
                self.env['mail.activity'].search([
                    ('res_id', '=', record.id), 
                    ('user_id', '=', user.id),
                    ('activity_type_id', '=',activity_type_id)
                ]).unlink()
                record.activity_schedule(
                    activity_type_id=activity_type_id,
                    date_deadline=fields.Date.today(),
                    summary="Review Quotation",
                    note=body,
                    user_id=user.id
                )

    def remove_project_team(self):
        for record in self:
            activity_type_id = self.env.ref('mail.mail_activity_data_todo').id

            if record.team_user_ids:
                self.env['mail.activity'].search([
                    ('res_id', '=', record.id),
                    ('user_id', 'in', record.team_user_ids.ids),
                    ('activity_type_id', '=',activity_type_id)
                ]).unlink()
                record.team_user_ids = False

    def action_confirm(self):
        """Override to prevent project team members from confirming orders they are assigned to."""
        for order in self:
            is_project_team = (
                order.env.user.has_group('sale_project_quote.group_sale_project_quote_user') or
                order.env.user.has_group('sale_project_quote.group_sale_project_quote_manager')
            )
            if is_project_team and order.team_user_ids and order.env.user.id in order.team_user_ids.ids:
                raise AccessError(_("Project team members are not allowed to confirm sales orders."))
        return super(SaleOrder, self).action_confirm()