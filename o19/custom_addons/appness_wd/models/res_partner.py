from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Evaluation fields
    evaluation_ids = fields.One2many('wd.evaluation', 'partner_id', string='Evaluations')
    is_evaluation_stage = fields.Boolean(string='Evaluation Stage', default=False)
    total_evaluation_score = fields.Float(string='Total Evaluation Score', compute='_compute_total_evaluation_score', store=True)
    evaluation_score_percentage = fields.Float(string='Evaluation Score Percentage', compute='_compute_evaluation_score_percentage', store=True,tracking=True)
    evaluation_score_percentage_total = fields.Float(string='Evaluation Score Percentage Total', compute='_compute_evaluation_score_percentage', store=True,tracking=True)

    # Credit Level fields
    credit_level_id = fields.Many2one(
        'wd.customer.credit.level',
        string='Credit Level',
        tracking=True,
        help="Manually assign a credit level to this customer. "
             "When set, the credit limit will be automatically updated."
    )

    credit_limit = fields.Float(
        string='Credit Limit', help='Credit limit specific to this partner.',
        compute='_compute_credit_limit', store=True, tracking=True,
        groups='account.group_account_invoice,account.group_account_readonly,sales_team.group_sale_salesman,sales_team.group_sale_manager',
        company_dependent=True, copy=False, readonly=False)

    @api.depends('credit_level_id.credit_limit')
    def _compute_credit_limit(self):
        for record in self:
            if record.credit_level_id:
                record.credit_limit = record.credit_level_id.credit_limit
                record.use_partner_credit_limit = True
            else:
                record.credit_limit = 0
                record.use_partner_credit_limit = False

    # @api.onchange('credit_level_id')
    # def _onchange_credit_level_id(self):
    #     """Sync the credit_limit field when a credit level is selected."""
    #     if self.credit_level_id:
    #         self.credit_limit = self.credit_level_id.credit_limit
    #         self.use_partner_credit_limit = True

    @api.model_create_multi
    def create(self, vals_list):
        """Sync credit_limit from credit_level_id on create."""
        for vals in vals_list:
            if vals.get('credit_level_id'):
                level = self.env['wd.customer.credit.level'].browse(vals['credit_level_id'])
                if level:
                    vals['credit_limit'] = level.credit_limit
                    vals['use_partner_credit_limit'] = True
        return super().create(vals_list)

    def write(self, vals):
        """Sync credit_limit from credit_level_id on write."""
        if 'credit_level_id' in vals:
            level_id = vals.get('credit_level_id')
            if level_id:
                level = self.env['wd.customer.credit.level'].browse(level_id)
                vals['credit_limit'] = level.credit_limit
                vals['use_partner_credit_limit'] = True
        return super().write(vals)
    def _create_evaluation_lines(self):
        """Create evaluation lines from all available metrics, grouped by category."""
        self.ensure_one()
        self.evaluation_ids.unlink()
        if not self.evaluation_ids:
            vals_list = []
            standards = self.env['wd.standard'].search([], order='id')
            for standard in standards:
                vals_list.append({
                    'partner_id': self.id,
                    'display_type': 'line_section',
                    'name': standard.name,
                })
                for scale in standard.scale_ids:
                    vals_list.append({
                        'partner_id': self.id,
                        'scale_id': scale.id,
                        'name': scale.name,
                        'scale_weight': scale.evaluation_weight,
                    })
            self.env['wd.evaluation'].create(vals_list)
            
    @api.depends('evaluation_ids.category_score')
    def _compute_total_evaluation_score(self):
        for partner in self:
            total_evaluation_score = 0

            standards = self.env['wd.standard'].search([])
            for standard in standards:
                category_metrics = partner.evaluation_ids.filtered(lambda x: x.standard_id == standard)
                if category_metrics:
                    total_evaluation_score += sum(category_metrics.mapped('category_score'))
            
            partner.total_evaluation_score = total_evaluation_score

    @api.depends('total_evaluation_score')
    def _compute_evaluation_score_percentage(self):
        for partner in self:
            # percentage = (total evaluation score / (sum of standards weight * 5) ) * 100
            standards = self.env['wd.standard'].search([])
            standards_total_weight = sum(standard.weight for standard in standards)
            partner.evaluation_score_percentage_total = standards_total_weight * 5
            
            if standards_total_weight == 0:
                partner.evaluation_score_percentage = 0
            else:
                partner.evaluation_score_percentage = (partner.total_evaluation_score / (standards_total_weight * 5)) * 100

    def action_submit_for_evaluation(self):
        self.is_evaluation_stage = True
        self._create_evaluation_lines()

    @api.onchange('user_id')
    def onchange_user_id(self):
        for record in self:
            record.is_evaluation_stage = False

    def action_accept(self):
        standards = self.env['wd.standard'].search([])
        flag_no_error = True
        for standard in standards:
            total_weight = sum(self.evaluation_ids.filtered(lambda x: x.standard_id == standard).mapped(lambda x: x.scale_weight))
            if total_weight not in (0, 1):
                flag_no_error = False
                raise UserError(f"Total weight of metrics inside category {standard.name} must be equal to 1 or 0")
        
        if flag_no_error:
            self.is_evaluation_stage = False