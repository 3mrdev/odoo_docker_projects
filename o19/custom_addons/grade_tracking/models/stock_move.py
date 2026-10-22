from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
        store=True,
        readonly=False,
    )
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        help="Mining site (project) from the source document.",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        domain="[('project_id', '=', mining_location_id)]",
    )
    average_grade = fields.Float(string="Average Grade (g/t)")

    def _create_lot_ids_from_move_line_vals(self, vals_list, product_id, company_id=False):
        """Override to stamp grade data onto the lots created from lot names.

        Only fills lots that have no grade data yet, so name-matched
        receipts of pre-graded lots are not overwritten.
        """
        super()._create_lot_ids_from_move_line_vals(vals_list, product_id, company_id)
        if not self.is_grade_tracked or not self.mining_location_id and not self.average_grade:
            return
        lot_ids = self.env["stock.lot"].browse([
            vals["lot_id"] for vals in vals_list if vals.get("lot_id")
        ])
        lots_to_update = lot_ids.filtered(
            lambda lot: not lot.average_grade and not lot.mining_location_id
        )
        if lots_to_update:
            lots_to_update.write({
                "mining_location_id": self.mining_location_id.id,
                "mining_level_id": self.mining_level_id.id,
                "average_grade": self.average_grade,
            })

    def _prepare_merge_moves_distinct_fields(self):
        """Override to prevent merging grade-tracked moves with different grade data."""
        fields = super()._prepare_merge_moves_distinct_fields()
        if self.filtered(lambda move: move.product_id.is_grade_tracked):
            fields += ["mining_location_id", "mining_level_id", "average_grade"]
        return fields
