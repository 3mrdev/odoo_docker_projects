from odoo import fields, models


class GradeChangeHistory(models.Model):
    _name = "grade.change.history"
    _description = "Grade Change History"
    _order = "change_datetime desc, id desc"

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial",
        required=True,
        ondelete="cascade",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Updated By",
        required=True,
        default=lambda self: self.env.user,
    )
    change_datetime = fields.Datetime(
        string="Changed On",
        required=True,
        default=fields.Datetime.now,
    )
    # Char snapshots of the level display names: they survive level deletion.
    level_from = fields.Char(string="Level From")
    level_to = fields.Char(string="Level To")
    average_grade_from = fields.Float(string="Average Grade From (g/t)")
    average_grade_to = fields.Float(string="Average Grade To (g/t)")
    quantity = fields.Float(
        string="Quantity (t)",
        help="Lot on-hand quantity at the moment of the change.",
    )
    gold_content = fields.Float(
        string="Gold Content (g)",
        help="Lot gold content at the moment of the change.",
    )

    def _log_lot_changes(self, snapshots):
        """Create history lines for grade data changes.

        ``snapshots``: {lot: (old_level_display_name, old_average_grade)}.
        Old values were captured before the write; reading the lots here
        (after the write) yields the new values. Lines are only created for
        real changes.
        """
        lines = []
        for lot, (old_level, old_grade) in snapshots.items():
            new_level = lot.mining_level_id.display_name or False
            new_grade = lot.average_grade
            if old_level == new_level and old_grade == new_grade:
                continue
            lines.append({
                "lot_id": lot.id,
                "user_id": self.env.uid,
                "change_datetime": fields.Datetime.now(),
                "level_from": old_level,
                "level_to": new_level,
                "average_grade_from": old_grade,
                "average_grade_to": new_grade,
                "quantity": lot.product_qty,
                "gold_content": lot.gold_content,
            })
        if lines:
            # sudo: the audit trail must be writable regardless of the user's
            # ACLs on this model (the group only gets read access).
            self.sudo().create(lines)
