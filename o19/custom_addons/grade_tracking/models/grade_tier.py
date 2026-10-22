from odoo import fields, models


class GradeTier(models.Model):
    _name = "grade.tier"
    _description = "Grade Tier"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    name = fields.Char(required=True)
    min_grade = fields.Float(string="Min Grade (g/t)", required=True)
    max_grade = fields.Float(string="Max Grade (g/t)", required=True)

    _grade_range = models.Constraint(
        "check(max_grade > min_grade)",
        "The maximum grade must be greater than the minimum grade.",
    )

    def action_update_all_grade_tiers(self):
        """Force-recompute grade_tier_id on all grade-tracked lots.

        The stored computed field grade_tier_id has no dependency on tier
        ranges, so range changes do not refresh existing lots automatically.
        Overlapping ranges are resolved by the lowest sequence (see the
        compute search order).
        """
        lots = self.env["stock.lot"].search([("product_id.is_grade_tracked", "=", True)])
        if lots:
            self.env.add_to_compute(lots._fields["grade_tier_id"], lots)
            self.env.flush_all()
