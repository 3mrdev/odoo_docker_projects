from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.tools import float_round


class MrpProductionPlanTarget(models.Model):
    _name = 'mrp.production.plan.target'
    _description = 'Production Plan Target'
    _order = 'date_from, id'
    _inherit = ['mail.thread']

    def _get_target_period_domain(self):
        """Domain of MOs counting as actual production for this target.

        Matches MOs producing the line's product as main product or as a
        by-product (finished moves). Returns a never-matching domain while
        the period is not set (new/unsaved records during onchange).
        """
        self.ensure_one()
        line = self.line_id
        if not self.date_from or not self.date_to or not line.product_id:
            return [('id', '=', False)]
        date_to_end = fields.Datetime.to_datetime(self.date_to).replace(
            hour=23, minute=59, second=59)
        return [
            '|',
            ('product_id', '=', line.product_id.id),
            ('move_finished_ids.product_id', '=', line.product_id.id),
            ('company_id', '=', line.company_id.id),
            ('state', 'not in', ('draft', 'cancel')),
            ('date_finished', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('date_finished', '<=', date_to_end),
        ]

    line_id = fields.Many2one(
        'mrp.production.plan.line', 'Plan Line', required=True,
        ondelete='cascade', index=True)
    plan_id = fields.Many2one(related='line_id.plan_id', store=True, readonly=True)
    state = fields.Selection(related='line_id.plan_id.state', store=True, readonly=True)
    company_id = fields.Many2one(related='line_id.company_id', store=True, readonly=True)
    product_id = fields.Many2one(related='line_id.product_id', store=True, readonly=True)
    product_uom_id = fields.Many2one(related='line_id.product_uom_id')
    period_type = fields.Selection(
        selection=[('year', 'Year'), ('month', 'Month'), ('day', 'Day')],
        default='month', required=True)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    target_qty = fields.Float('Target Qty')
    expected_grade = fields.Float(
        'Expected Grade (g/t)',
        help="Expected average grade of the produced lots. When set, the "
             "fine gold content target is computed as Target Qty x Grade.")
    target_gold_content = fields.Float(
        'Target Gold Content (g)', compute='_compute_target_gold_content',
        store=True, readonly=False,
        help="Fine gold content targeted for this period, in grams. "
             "Computed from the expected grade, or set manually.")
    max_mo_qty = fields.Float(
        'Max Qty per MO',
        help="When generating draft MOs, split the remaining quantity into "
             "several MOs of at most this quantity, dated evenly across the "
             "period. Leave empty to generate a single MO.")

    actual_qty = fields.Float(compute='_compute_actuals', string='Actual Qty')
    actual_gold_content = fields.Float(
        compute='_compute_actuals', string='Actual Gold Content (g)')
    achieved_percentage = fields.Float(
        compute='_compute_actuals', string='Achieved (%)', aggregator='avg')
    mo_count = fields.Integer(compute='_compute_actuals', string='MOs')

    _date_range_check = models.Constraint(
        'CHECK (date_from <= date_to)',
        'The target end date may not be before the starting date.')

    @api.depends('target_qty', 'expected_grade')
    def _compute_target_gold_content(self):
        for target in self:
            if target.expected_grade:
                target.target_gold_content = target.target_qty * target.expected_grade
            # else: keep the manually entered value untouched

    def _compute_actuals(self):
        for target in self:
            mos = self.env['mrp.production'].search(target._get_target_period_domain())
            actual_qty, actual_gold = mos._plan_actuals_for_product(target.product_id)
            target.actual_qty = actual_qty
            target.actual_gold_content = actual_gold
            target.mo_count = len(mos)
            target.achieved_percentage = (
                target.target_qty and target.actual_qty / target.target_qty)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_open_mo_details(self):
        self.ensure_one()
        product = self.line_id.product_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Actual MOs %(product)s (%(date_from)s - %(date_to)s)',
                      product=product.display_name,
                      date_from=self.date_from, date_to=self.date_to),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': self._get_target_period_domain(),
            'context': {
                'default_product_id': product.id,
                'default_company_id': self.company_id.id,
            },
        }

    def action_generate_mo(self):
        self._generate_mo()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'info',
                'message': _('Draft MOs generated from the plan targets.'),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_open_breakdown_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Break Down Target'),
            'res_model': 'mrp.production.plan.target.generate',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_target_id': self.id},
        }

    def _generate_mo(self):
        """Create draft MOs covering the remaining quantity of the targets.

        Remaining = target qty - quantity already planned/produced by MOs in
        the target period. When max_mo_qty is set, the remaining quantity is
        split into MOs of at most max_mo_qty dated evenly across the period.
        """
        MrpProduction = self.env['mrp.production']
        for target in self:
            line = target.line_id
            mos = MrpProduction.search(target._get_target_period_domain())
            already_planned, _gold = mos._plan_actuals_for_product(line.product_id)
            remaining = target.target_qty - already_planned
            if float_round(remaining, precision_digits=6) <= 0:
                target.message_post(body=_(
                    'No draft MO generated: target already covered by planned/actual MOs.'))
                continue

            max_qty = target.max_mo_qty
            if max_qty and max_qty > 0:
                mo_count = int(-(-remaining // max_qty))  # ceil
                sizes = [max_qty] * (mo_count - 1) + [remaining - max_qty * (mo_count - 1)]
            else:
                mo_count = 1
                sizes = [remaining]

            # Evenly space the MO start dates across the target period.
            period_days = (target.date_to - target.date_from).days
            step = period_days / mo_count if mo_count > 1 else 0
            vals_list = []
            for index, size in enumerate(sizes):
                mo_date = target.date_from + relativedelta(
                    days=round(step * index))
                vals_list.append({
                    'product_id': line.product_id.id,
                    'bom_id': line.bom_id.id,
                    'product_qty': size,
                    'date_start': fields.Datetime.to_datetime(mo_date),
                    'date_finished': fields.Datetime.to_datetime(mo_date),
                    'plan_target_id': target.id,
                })
            MrpProduction.create(vals_list)
            target.message_post(body=_(
                '%(count)s draft MO(s) generated for %(qty).2f %(uom)s (target %(target).2f).',
                count=mo_count, qty=remaining,
                uom=line.product_uom_id.name or '', target=target.target_qty))
