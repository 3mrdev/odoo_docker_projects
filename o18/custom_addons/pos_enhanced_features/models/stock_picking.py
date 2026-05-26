import json
from collections import defaultdict
from itertools import groupby
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _create_move_from_pos_order_lines(self, lines):
        """
        Override to handle flavor mix products separately.
        Instead of creating one single stock move that gets exploded by MRP,
        we read the 'flavor_quantities' JSON from the POS order line
        and directly create the child component moves with the correct quantities.
        """
        mix_lines = lines.filtered(lambda l: l.product_id.is_flavor_mix)
        normal_lines = lines - mix_lines

        # 1. Standard Odoo flow for non-mix products
        if normal_lines:
            super()._create_move_from_pos_order_lines(normal_lines)

        # 2. Custom flow for flavor mix products
        if mix_lines:
            self.ensure_one()
            lines_by_product = groupby(sorted(mix_lines, key=lambda l: l.product_id.id), key=lambda l: l.product_id.id)
            
            move_vals = []
            for dummy, olines in lines_by_product:
                order_lines = self.env['pos.order.line'].concat(*olines)
                
                for line in order_lines:
                    if not line.flavor_quantities:
                        continue
                        
                    try:
                        # Load the selected quantities per PTAV, e.g. {"ptav_id_1": 2, "ptav_id_2": 1}
                        flavor_qtys = json.loads(line.flavor_quantities)
                    except json.JSONDecodeError:
                        flavor_qtys = {}
                        
                    if not flavor_qtys:
                        continue

                    # Find the phantom BOM for this product
                    bom = self.env['mrp.bom']._bom_find(line.product_id)[line.product_id]
                    if not bom or bom.type != 'phantom':
                        continue
                        
                    # Calculate outer quantity (e.g. ordered 2 mixes)
                    outer_qty = abs(line.qty)
                    
                    # For each BOM line, check if its PTAV was selected in the popup
                    for bom_line in bom.bom_line_ids:
                        # Find the matching no_variant attribute value on this BOM line
                        ptavs = bom_line.bom_product_template_attribute_value_ids.filtered(
                            lambda a: a.attribute_id.create_variant == 'no_variant'
                        )
                        
                        if not ptavs:
                            continue
                            
                        # The popup uses the PTAV ID as the key in flavor_quantities
                        ptav_id = str(ptavs[0].id)
                        
                        # If the user selected this flavor, create a move for it
                        if ptav_id in flavor_qtys and flavor_qtys[ptav_id] > 0:
                            count = flavor_qtys[ptav_id]
                            # The final quantity consumed is: count per mix * number of mixes * bom line quantity
                            consumed_qty = count * outer_qty * bom_line.product_qty
                            
                            move_vals.append({
                                'name': line.name,
                                'product_uom': bom_line.product_uom_id.id,
                                'picking_id': self.id,
                                'picking_type_id': self.picking_type_id.id,
                                'product_id': bom_line.product_id.id,
                                'product_uom_qty': consumed_qty,
                                'location_id': self.location_id.id,
                                'location_dest_id': self.location_dest_id.id,
                                'company_id': self.company_id.id,
                            })
                            
            if move_vals:
                moves = self.env['stock.move'].create(move_vals)
                confirmed_moves = moves._action_confirm()
                confirmed_moves._add_mls_related_to_order(mix_lines, are_qties_done=True)
                confirmed_moves.picked = True
                self._link_owner_on_return_picking(mix_lines)
