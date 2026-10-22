from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
    )
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        help="Mining site (project) of the received ore.",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        domain="[('project_id', '=', mining_location_id)]",
    )
    average_grade = fields.Float(string="Average Grade (g/t)")

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        """Override to pass grade data from the PO line to the stock move."""
        vals = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        if self.is_grade_tracked:
            vals.update({
                "mining_location_id": self.mining_location_id.id,
                "mining_level_id": self.mining_level_id.id,
                "average_grade": self.average_grade,
            })
        return vals
