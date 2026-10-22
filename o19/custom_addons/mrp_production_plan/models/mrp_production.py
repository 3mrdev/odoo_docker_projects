from odoo import _, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    plan_target_id = fields.Many2one(
        'mrp.production.plan.target', 'Plan Target', copy=False, index=True,
        help="Production plan target this MO counts towards. Assigned "
             "automatically at confirmation when an active plan matches "
             "this product and date, or set manually.")
    plan_id = fields.Many2one(
        related='plan_target_id.line_id.plan_id', store=True, index=True,
        string='Production Plan')

    def _plan_actuals_for_product(self, product):
        """Aggregate (qty, gold content) this MO recordset produces for `product`.

        Counts the product both as the MO's main product and as a by-product
        (finished moves of other products), so a plan can track products that
        have no standalone MO. Mirrors the main-product convention of counting
        the planned quantity until the MO is done.
        """
        qty = gold = 0.0
        for mo in self:
            if mo.product_id == product:
                qty += mo.product_qty
                gold += sum(mo.lot_producing_ids.mapped('gold_content'))
            byproduct_moves = mo.move_finished_ids.filtered(
                lambda m: m.product_id == product and m.product_id != mo.product_id)
            qty += sum(byproduct_moves.mapped('product_qty'))
            gold += sum(byproduct_moves.lot_ids.mapped('gold_content'))
        return qty, gold

    def action_confirm(self):
        res = super().action_confirm()
        confirmed = self.filtered(
            lambda mo: mo.state not in ('draft', 'cancel') and not mo.plan_target_id)
        return confirmed._assign_plan_target_and_warn() or res

    def _assign_plan_target_and_warn(self):
        """Auto-link each MO to the most specific matching plan target and
        warn (non-blocking) when the confirmation pushes production above it.

        Runs as superuser: MO users may not have plan ACLs (grade_tracking
        pattern), but the link must be stamped regardless.
        """
        for production in self:
            target_date = production.date_finished.date() if production.date_finished else None
            if not target_date or not production.product_id:
                continue
            sudo_target_model = self.env['mrp.production.plan.target'].sudo()
            matching = sudo_target_model.search([
                ('product_id', '=', production.product_id.id),
                ('company_id', '=', production.company_id.id),
                ('state', '=', 'confirmed'),
                ('date_from', '<=', target_date),
                ('date_to', '>=', target_date),
            ], order='date_from DESC, id')
            if matching:
                # Most specific target = the shortest matching period; on
                # range ties (plan vs its revisions) prefer the latest
                # revision (the one without children).
                target = min(
                    matching,
                    key=lambda t: ((t.date_to - t.date_from).days,
                                   -1 if not t.line_id.plan_id.children_ids else 0,
                                   -t.id))
                production.sudo().plan_target_id = target
                cumulative = sum(self.env['mrp.production'].sudo().search([
                    ('product_id', '=', production.product_id.id),
                    ('company_id', '=', production.company_id.id),
                    ('state', 'not in', ('draft', 'cancel')),
                    ('date_finished', '>=', fields.Datetime.to_datetime(target.date_from)),
                    ('date_finished', '<=', fields.Datetime.to_datetime(
                        target.date_to).replace(hour=23, minute=59, second=59)),
                ]).mapped('product_qty'))
                if target.target_qty and cumulative > target.target_qty:
                    message = _(
                        'Plan target exceeded for %(product)s (%(plan)s, %(date_from)s - '
                        '%(date_to)s): actual %(actual).2f > target %(target).2f.',
                        product=production.product_id.display_name,
                        plan=target.line_id.plan_id.name,
                        date_from=target.date_from, date_to=target.date_to,
                        actual=cumulative, target=target.target_qty)
                    production.message_post(body=message)
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'warning',
                            'title': _('Production Plan'),
                            'message': message,
                            'next': {'type': 'ir.actions.act_window_close'},
                        },
                    }
        return False
