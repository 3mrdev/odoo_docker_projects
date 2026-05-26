from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'
    
    equity_account_id = fields.Many2one('account.account', string='Equity Account')
    equity_journal_id = fields.Many2one('account.journal', string='Equity Journal')
    is_automated = fields.Boolean(string='Is Automated', default=False)