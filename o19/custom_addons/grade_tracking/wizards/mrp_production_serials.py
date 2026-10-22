from odoo import models


class MrpProductionSerials(models.TransientModel):
    _inherit = "mrp.production.serials"

    def action_apply(self):
        res = super().action_apply()
        production = self.production_id
        if production.is_grade_tracked:
            lots = production.lot_producing_ids.filtered(
                lambda lot: not lot.mining_location_id
                and not lot.mining_level_id
                and not lot.average_grade
            )
            lots.write({
                "mining_location_id": production.mining_location_id.id,
                "mining_level_id": production.mining_level_id.id,
                "average_grade": production.average_grade,
            })
        return res
