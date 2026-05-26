from odoo import models,fields,api

class MrpProductionSerials(models.TransientModel):
    _inherit = 'mrp.production.serials'

    def action_apply(self):
        self.ensure_one()
        lots = list(filter(lambda serial_number: len(serial_number.strip()) > 0, self.serial_numbers.split('\n'))) if self.serial_numbers else []
        existing_lots = self.env['stock.lot'].search([
            '|', ('company_id', '=', False), ('company_id', '=', self.production_id.company_id.id),
            ('product_id', '=', self.production_id.product_id.id),
            ('name', 'in', lots),
        ])
        existing_lot_names = existing_lots.mapped('name')
        new_lots = []
        for lot_name in sorted(lots):
            if lot_name in existing_lot_names:
                continue

            if lot_name == self.production_id.product_id.serial_prefix_format + self.production_id.product_id.next_serial:
                if self.production_id.product_id.lot_sequence_id:
                    self.production_id.product_id.lot_sequence_id.number_next_actual += 1
            new_lots.append({
                'name': lot_name,
                'product_id': self.production_id.product_id.id,
                'volume_length': self.production_id.volume_length,
                'volume_width': self.production_id.volume_width,
                'volume_height': self.production_id.volume_height,
            })
        self.production_id.lot_producing_ids = existing_lots + self.env['stock.lot'].create(new_lots)
        if self.production_id.qty_producing != len(self.production_id.lot_producing_ids):
            self.production_id.qty_producing = len(self.production_id.lot_producing_ids)
        (self.workorder_id or self.production_id).set_qty_producing()

        print_actions = self.production_id._autoprint_mass_generated_lots()
        if print_actions:
            return {
                'type': 'ir.actions.client',
                'tag': 'do_multi_print',
                'context': {},
                'params': {
                    'reports': print_actions,
                }
            }