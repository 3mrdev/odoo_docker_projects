from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class PlanTargetGenerate(models.TransientModel):
    _name = 'mrp.production.plan.target.generate'
    _description = 'Break Down Plan Target into Periods'

    target_id = fields.Many2one(
        'mrp.production.plan.target', required=True, ondelete='cascade')
    period_type = fields.Selection(
        selection=[('month', 'Monthly'), ('day', 'Daily')],
        default='month', required=True)
    split_mode = fields.Selection(
        selection=[('equal', 'Split equally'), ('empty', 'Leave quantities empty')],
        default='equal', required=True)

    def action_generate(self):
        self.ensure_one()
        parent = self.target_id
        if self.period_type == 'month':
            child_bounds = self._month_bounds(parent.date_from, parent.date_to)
        else:
            child_bounds = [
                (parent.date_from + relativedelta(days=offset),
                 parent.date_from + relativedelta(days=offset))
                for offset in range((parent.date_to - parent.date_from).days + 1)
            ]
        if not child_bounds:
            raise UserError(_('The target period is empty.'))

        per_qty = parent.target_qty / len(child_bounds) if self.split_mode == 'equal' else 0.0
        vals_list = []
        for index, (date_from, date_to) in enumerate(child_bounds):
            # Even split, with the rounding remainder folded into the last row.
            if self.split_mode == 'equal':
                qty = (per_qty if index < len(child_bounds) - 1
                       else parent.target_qty - per_qty * (len(child_bounds) - 1))
            else:
                qty = 0.0
            vals_list.append({
                'line_id': parent.line_id.id,
                'period_type': self.period_type,
                'date_from': date_from,
                'date_to': date_to,
                'target_qty': qty,
                'expected_grade': parent.expected_grade,
                'max_mo_qty': parent.max_mo_qty,
            })
        self.env['mrp.production.plan.target'].create(vals_list)
        return {'type': 'ir.actions.act_window_close'}

    @staticmethod
    def _month_bounds(date_from, date_to):
        """Consecutive calendar-month (start, end) tuples covering the range."""
        bounds = []
        current = date_from.replace(day=1)
        while current <= date_to:
            month_end = current + relativedelta(months=1) - relativedelta(days=1)
            bounds.append((max(current, date_from), min(month_end, date_to)))
            current += relativedelta(months=1)
        return bounds
