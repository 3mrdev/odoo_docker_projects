from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    is_grade_tracked = fields.Boolean(
        related="product_id.is_grade_tracked",
        string="Grade Tracked",
    )
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        help="Mining site (project) this lot was extracted from.",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        domain="[('project_id', '=', mining_location_id)]",
        help="Mining level within the mining location.",
    )
    average_grade = fields.Float(
        string="Average Grade (g/t)",
        help="Average grade of gold per ton of ore.",
    )
    grade_tier_id = fields.Many2one(
        "grade.tier",
        string="Grade Tier",
        compute="_compute_grade_tier_id",
        store=True,
        compute_sudo=True,
        help="Automatically computed from the Average Grade and the tier ranges "
             "configured in Inventory > Configuration > Grade Tracking. Empty when "
             "no range matches. Use 'Update All Grade Tiers' on the Grade Tier form "
             "to refresh all lots after changing ranges.",
    )
    gold_content = fields.Float(
        string="Gold Content (g)",
        compute="_compute_gold_content",
        store=True,
        help="Average Grade x on-hand quantity (ore is measured in tons).",
    )
    grade_history_ids = fields.One2many(
        "grade.change.history",
        "lot_id",
        string="Grade History",
    )
    grade_history_count = fields.Integer(
        compute="_compute_grade_history_count",
    )

    def _compute_grade_history_count(self):
        for lot in self:
            lot.grade_history_count = len(lot.grade_history_ids)

    @api.depends("average_grade")
    def _compute_grade_tier_id(self):
        tiers = self.env["grade.tier"].search([], order="sequence, id")
        for lot in self:
            if lot.average_grade:
                lot.grade_tier_id = tiers.filtered(
                    lambda t: t.min_grade <= lot.average_grade <= t.max_grade
                )[:1]
            else:
                lot.grade_tier_id = False

    # stock.lot.product_qty is a non-stored compute; depending on quant_ids /
    # quant_ids.quantity is what retriggers this stored compute on stock moves.
    @api.depends("average_grade", "quant_ids", "quant_ids.quantity")
    def _compute_gold_content(self):
        for lot in self:
            lot.gold_content = lot.average_grade * lot.product_qty

    @api.onchange("mining_location_id")
    def _onchange_mining_location_id(self):
        if self.mining_level_id and self.mining_level_id.project_id != self.mining_location_id:
            self.mining_level_id = False

    @api.constrains("mining_location_id", "mining_level_id")
    def _check_mining_level_location(self):
        for lot in self:
            if lot.mining_level_id and lot.mining_location_id and \
                    lot.mining_level_id.project_id != lot.mining_location_id:
                raise ValidationError(
                    _("Mining level %s does not belong to mining location %s.")
                    % (lot.mining_level_id.display_name, lot.mining_location_id.display_name)
                )

    # ------------------------------------------------------------------
    # Grade change history (audit trail)
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        lots = super().create(vals_list)
        # Log the initial grade assignment (empty "from" values): grade data
        # set at lot creation (receipt flow, manual creation, MRP).
        snapshots = {
            lot: (False, 0.0)
            for lot in lots.filtered(
                lambda l: l.is_grade_tracked and (l.mining_level_id or l.average_grade))
        }
        if snapshots:
            self.env["grade.change.history"]._log_lot_changes(snapshots)
        return lots

    def write(self, vals):
        tracked_fields = {"mining_level_id", "average_grade"}
        if not (set(vals) & tracked_fields):
            return super().write(vals)
        # Capture old values before the write for grade-tracked lots only.
        snapshots = {
            lot: (lot.mining_level_id.display_name or False, lot.average_grade)
            for lot in self.filtered("is_grade_tracked")
        }
        res = super().write(vals)
        if snapshots:
            self.env["grade.change.history"]._log_lot_changes(snapshots)
        return res

    def action_view_grade_history(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Grade History",
            "res_model": "grade.change.history",
            "view_mode": "list,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {"default_lot_id": self.id},
        }
