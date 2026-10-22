from odoo import _, api, fields, models


class MrpProductionPlanLine(models.Model):
    _name = 'mrp.production.plan.line'
    _description = 'Production Plan Line'
    _order = 'sequence, id'

    def _get_plan_period_domain(self):
        """Domain of MOs counting as actual production for this line.

        Matches MOs producing the line's product — as main product or as a
        by-product (finished moves) — on the MO end date (planned until done,
        actual afterwards) within the plan period. Returns a never-matching
        domain while the plan period is not set (new/unsaved records during
        onchange).
        """
        self.ensure_one()
        if not self.plan_id.date_from or not self.plan_id.date_to or not self.product_id:
            return [('id', '=', False)]
        date_to_end = fields.Datetime.to_datetime(self.plan_id.date_to).replace(
            hour=23, minute=59, second=59)
        return [
            '|',
            ('product_id', '=', self.product_id.id),
            ('move_finished_ids.product_id', '=', self.product_id.id),
            ('company_id', '=', self.plan_id.company_id.id),
            ('state', 'not in', ('draft', 'cancel')),
            ('date_finished', '>=', fields.Datetime.to_datetime(self.plan_id.date_from)),
            ('date_finished', '<=', date_to_end),
        ]

    name = fields.Char(related='plan_id.name', string='Plan Name')
    sequence = fields.Integer(default=10)
    plan_id = fields.Many2one(
        'mrp.production.plan', required=True, ondelete='cascade', index=True)
    state = fields.Selection(related='plan_id.state', store=True, readonly=True)
    company_id = fields.Many2one(related='plan_id.company_id', store=True, readonly=True)
    date_from = fields.Date(related='plan_id.date_from', store=True)
    date_to = fields.Date(related='plan_id.date_to', store=True)
    product_id = fields.Many2one(
        'product.product', 'Final Product', required=True, index=True,
        domain="[('is_grade_tracked', '=', True)]")
    product_uom_id = fields.Many2one(related='product_id.uom_id')
    # Mirror of mrp.production: the BoM domain must reference this related
    # field, not a dotted path — the web client cannot resolve paths through
    # an m2o when evaluating a field domain inside an editable list row.
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id')
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Materials',
        domain="[('product_tmpl_id', '=', product_tmpl_id), '|', "
               "('product_id', '=', product_id), ('product_id', '=', False)]",
        check_company=True,
        help="Used when generating draft MOs from this line's targets.")
    target_ids = fields.One2many(
        'mrp.production.plan.target', 'line_id', 'Targets', copy=True)

    target_qty_total = fields.Float(
        compute='_compute_actuals', string='Target Qty')
    target_gold_total = fields.Float(
        compute='_compute_actuals', string='Target Gold Content (g)')
    actual_qty = fields.Float(
        compute='_compute_actuals', string='Actual Qty')
    actual_gold_content = fields.Float(
        compute='_compute_actuals', string='Actual Gold Content (g)')
    achieved_percentage = fields.Float(
        compute='_compute_actuals', string='Achieved (%)', aggregator='avg')
    theoretical_qty = fields.Float(
        compute='_compute_theoretical', string='Theoretical Qty',
        help='Target quantity prorated by the elapsed part of the plan period.')
    mo_count = fields.Integer(
        compute='_compute_actuals', string='MOs')

    @api.depends('plan_id.date_from', 'plan_id.date_to')
    def _compute_theoretical(self):
        today = fields.Date.context_today(self)
        for line in self:
            date_from, date_to = line.plan_id.date_from, line.plan_id.date_to
            if not date_from or not date_to or today <= date_from:
                line.theoretical_qty = 0.0
                continue
            total_days = (date_to - date_from).days + 1
            elapsed_days = (min(today, date_to) - date_from).days + 1
            line.theoretical_qty = line.target_qty_total * elapsed_days / total_days

    def _compute_actuals(self):
        for line in self:
            targets = line.target_ids
            line.target_qty_total = sum(targets.mapped('target_qty'))
            line.target_gold_total = sum(targets.mapped('target_gold_content'))
            mos = self.env['mrp.production'].search(line._get_plan_period_domain())
            actual_qty, actual_gold = mos._plan_actuals_for_product(line.product_id)
            line.actual_qty = actual_qty
            line.actual_gold_content = actual_gold
            line.mo_count = len(mos)
            line.achieved_percentage = (
                line.target_qty_total and line.actual_qty / line.target_qty_total)

    def action_open_line_targets(self):
        """Open this line's targets in an editable-bottom list (draft plans)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Targets %(product)s', product=self.product_id.display_name),
            'res_model': 'mrp.production.plan.target',
            'view_mode': 'list,form',
            'domain': [('line_id', '=', self.id)],
            'context': {'default_line_id': self.id},
            'views': [
                (self.env.ref(
                    'mrp_production_plan.view_mrp_production_plan_target_list_editable').id,
                 'list'),
                (False, 'form'),
            ],
        }

    def action_open_mo_details(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Actual MOs %(product)s', product=self.product_id.display_name),
            'res_model': 'mrp.production',
            'view_mode': 'list,form',
            'domain': self._get_plan_period_domain(),
            'context': {
                'default_product_id': self.product_id.id,
                'default_company_id': self.plan_id.company_id.id,
            },
        }
