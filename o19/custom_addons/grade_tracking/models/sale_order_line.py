from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
    )
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        help="Mining site (project) of the ordered ore.",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        domain="[('project_id', '=', mining_location_id)]",
    )
    average_grade = fields.Float(string="Average Grade (g/t)")

    def _prepare_procurement_values(self):
        """Pass grade data to the procurement group so it lands on the moves."""
        values = super()._prepare_procurement_values()
        if self.is_grade_tracked:
            values.update({
                "mining_location_id": self.mining_location_id.id,
                "mining_level_id": self.mining_level_id.id,
                "average_grade": self.average_grade,
            })
        return values
