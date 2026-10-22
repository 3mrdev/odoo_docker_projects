from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
    )
    # From the move: source data for newly created lots (the lot does not exist yet).
    mining_location_id_move = fields.Many2one(
        "project.project",
        string="Move Mining Location",
        related="move_id.mining_location_id",
        store=True,
    )
    mining_level_id_move = fields.Many2one(
        "grade.mining.level",
        string="Move Mining Level",
        related="move_id.mining_level_id",
        store=True,
    )
    average_grade_move = fields.Float(
        string="Move Average Grade (g/t)",
        related="move_id.average_grade",
        store=True,
    )
    # From the lot: display of the assigned lot's grade data.
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        related="lot_id.mining_location_id",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        related="lot_id.mining_level_id",
    )
    average_grade = fields.Float(
        string="Average Grade (g/t)",
        related="lot_id.average_grade",
    )
    grade_tier_id = fields.Many2one(
        "grade.tier",
        string="Grade Tier",
        related="lot_id.grade_tier_id",
    )
    gold_content = fields.Float(
        string="Gold Content (g)",
        compute="_compute_gold_content",
        store=True,
        help="Average Grade x moved quantity.",
    )

    @api.depends("average_grade", "average_grade_move", "quantity")
    def _compute_gold_content(self):
        for line in self:
            grade = line.average_grade or line.average_grade_move
            line.gold_content = grade * line.quantity

    def _prepare_new_lot_vals(self):
        """Override to include grade data when creating a new lot."""
        vals = super()._prepare_new_lot_vals()
        if self.is_grade_tracked:
            vals.update({
                "mining_location_id": self.mining_location_id_move.id,
                "mining_level_id": self.mining_level_id_move.id,
                "average_grade": self.average_grade_move,
            })
        return vals
