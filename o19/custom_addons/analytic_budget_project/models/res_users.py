from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    project_account_ids = fields.Many2many(
        'account.analytic.account',
        compute='_compute_project_account_ids',
        string='Project Analytic Accounts',
    )

    @api.depends_context('uid')
    def _compute_project_account_ids(self):
        # Get projects accessible to current user via privacy/membership rules
        projects = self.env['project.project'].sudo().search([
            '|',
            ('privacy_visibility', 'in', ['employees', 'portal']),
            ('message_partner_ids', 'in', [self.env.user.partner_id.id]),
        ])
        account_ids = projects.mapped('account_id').ids
        for user in self:
            user.project_account_ids = [(6, 0, account_ids)]
