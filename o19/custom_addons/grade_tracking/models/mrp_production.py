from odoo import fields, models


class MRPProduction(models.Model):
    _inherit = "mrp.production"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
        store=True,
    )
    # mining_location_id = fields.Many2one(
    #     "project.project",
    #     string="Mining Location",
    #     help="Mining site (project) stamped on the produced lot.",
    # )
    # mining_level_id = fields.Many2one(
    #     "grade.mining.level",
    #     string="Mining Level",
    #     domain="[('project_id', '=', mining_location_id)]",
    # )
    average_grade = fields.Float(string="Average Grade (g/t)")

    def _prepare_stock_lot_values(self):
        """Override to include grade data when creating the finished good lot."""
        vals = super()._prepare_stock_lot_values()
        if self.is_grade_tracked:
            vals.update({
                # "mining_location_id": self.mining_location_id.id,
                # "mining_level_id": self.mining_level_id.id,
                "average_grade": self.average_grade,
            })
        return vals
