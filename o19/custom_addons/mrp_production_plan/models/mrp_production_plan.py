import re
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class MrpProductionPlan(models.Model):
    _name = 'mrp.production.plan'
    _description = 'Production Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc, id desc'

    name = fields.Char('Plan Name', required=True)
    parent_id = fields.Many2one(
        'mrp.production.plan', 'Revision Of', index=True, ondelete='cascade')
    children_ids = fields.One2many(
        'mrp.production.plan', 'parent_id', 'Revisions')
    user_id = fields.Many2one(
        'res.users', 'Responsible', default=lambda self: self.env.user)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('revised', 'Revised'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        required=True, default='draft', readonly=True, copy=False, tracking=True)
    line_ids = fields.One2many(
        'mrp.production.plan.line', 'plan_id', 'Plan Lines', copy=True)
    company_id = fields.Many2one(
        'res.company', 'Company', default=lambda self: self.env.company, required=True)
    target_qty_total = fields.Float(
        compute='_compute_plan_totals', string='Total Target Qty')
    actual_qty_total = fields.Float(
        compute='_compute_plan_totals', string='Total Actual Qty')
    target_gold_total = fields.Float(
        compute='_compute_plan_totals', string='Total Target Gold Content')
    actual_gold_total = fields.Float(
        compute='_compute_plan_totals', string='Total Actual Gold Content')

    _date_range_check = models.Constraint(
        'CHECK (date_from <= date_to)',
        'The plan end date may not be before the starting date.')
    _parent_cycle_check = models.Constraint(
        'CHECK (id != parent_id)',
        'You cannot revise a plan with itself.')

    @api.constrains('parent_id')
    def _check_parent_cycle(self):
        for plan in self:
            current, hops = plan.parent_id, 0
            while current and hops < 100:
                if current == plan:
                    raise ValidationError(_('You cannot create recursive plan revisions.'))
                current = current.parent_id
                hops += 1

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft_or_cancelled(self):
        for plan in self:
            if plan.state not in ('draft', 'cancelled'):
                raise UserError(_(
                    'Only draft or cancelled plans can be deleted. '
                    'Revised plans are kept for history.'))

    def _compute_plan_totals(self):
        for plan in self:
            plan.target_qty_total = sum(plan.line_ids.mapped('target_qty_total'))
            plan.actual_qty_total = sum(plan.line_ids.mapped('actual_qty'))
            plan.target_gold_total = sum(plan.line_ids.mapped('target_gold_total'))
            plan.actual_gold_total = sum(plan.line_ids.mapped('actual_gold_content'))

    # ------------------------------------------------------------------
    # Lifecycle (budget.analytic pattern)
    # ------------------------------------------------------------------

    def action_confirm(self):
        for plan in self:
            if plan.state != 'draft':
                raise UserError(_('Only draft plans can be confirmed.'))
        self.parent_id.filtered(lambda p: p.state == 'confirmed').state = 'revised'
        self.state = 'confirmed'

    def action_draft(self):
        self.state = 'draft'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_done(self):
        self.state = 'done'

    def create_revised_plan(self):
        revised = self.browse()
        for plan in self:
            if plan.state != 'confirmed':
                raise UserError(_('Only confirmed plans can be revised.'))
            revised_plan = plan.copy(default={
                'name': plan._get_revised_plan_name(),
                'parent_id': plan.id,
            })
            revised += revised_plan
            plan.message_post(body=Markup(
                '%s: <a href="#" data-oe-model="mrp.production.plan" data-oe-id="%s">%s</a>'
            ) % (_('New revision'), revised_plan.id, revised_plan.name))
        return revised._get_records_action()

    def _get_revised_plan_name(self):
        self.ensure_one()
        timestamp = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        datetime_str = timestamp.strftime('%Y-%m-%d %H:%M')
        match = re.search(r'(.*) - REV\([^)]+\)$', self.name.strip())
        base_name = match.group(1).strip() if match else self.name.strip()
        return f'{base_name} - REV({datetime_str})'

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_generate_mo(self):
        """Generate draft MOs for every target of every line."""
        self.line_ids.target_ids._generate_mo()

    def action_open_plan_analysis(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Plan Analysis'),
            'res_model': 'mrp.production.plan.report',
            'view_mode': 'pivot,graph,list',
            'domain': [('plan_id', '=', self.id)],
            'context': {},
        }

    def action_open_plan_targets(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Plan Targets'),
            'res_model': 'mrp.production.plan.target',
            'view_mode': 'list,form',
            'domain': [('line_id.plan_id', 'in', self.ids)],
        }

    def _get_records_action(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Production Plans'),
            'res_model': 'mrp.production.plan',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.ids)],
        }

    def action_print_plan(self):
        return self.env.ref(
            'mrp_production_plan.action_report_production_plan'
        ).report_action(self)
