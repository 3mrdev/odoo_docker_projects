from odoo import models,fields,api
from odoo.exceptions import UserError

class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_products = fields.Integer(compute="_count_packages_products",store=True)

    @api.depends('move_ids.quantity')
    def _count_packages_products(self):
        for rec in self:
            total_products = 0
            
            for move in rec.move_ids:
                total_products += move.quantity
            
            rec.total_products = total_products

    def button_validate(self):
        res = super().button_validate()
        error_messages = ""
        if self.picking_type_id.code in ["outgoing", "incoming"]:
            for move in self.move_ids:
                if move.is_volume_tracked:
                    for move_line in move.move_line_ids:
                        if move_line.lot_id:
                            if move_line.lot_id.volume_length != move.volume_length or move_line.lot_id.volume_width != move.volume_width or move_line.lot_id.volume_height != move.volume_height:
                                error_messages += f"Lot {move_line.lot_id.display_name} dimensions do not match {move.product_id.name} dimensions {move.volume_display}\n"
        if error_messages:
            raise UserError(error_messages)
        return res