from odoo import models, fields,api
from odoo.exceptions import UserError

class TransferToBranch(models.TransientModel):
    _name = 'kas.transfer.branch'
    _description = 'Transfer To Branch'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')
    line_product_id = fields.Many2one('product.product', string='Product', related='purchase_order_line_id.product_id')
    line_product_qty = fields.Float(string='Line Product Quantity', related='purchase_order_line_id.product_qty')
    branches_qty = fields.Integer(string='How many branches?',default=1)
    transfers = fields.One2many('kas.transfer.branch.line', 'transfer_id', string='Transfers')

    @api.onchange('purchase_order_id')
    def _onchange_purchase_order_id(self):
        for rec in self:
            transfers = []
            if rec.purchase_order_id:
                rec.transfers = False
                for transfer in rec.purchase_order_id.branch_transfers_ids:
                    transfers.append((0, 0, {
                        'product_id': transfer.product_id.id,
                        'quantity': transfer.product_qty,
                        'branch_id': transfer.branch_id.id
                    }))
                rec.transfers = transfers
    
    @api.onchange('branches_qty','line_product_id')
    def _onchange_qty(self):
        for rec in self:
            transfers = []
            if rec.purchase_order_line_id:
                rec.transfers = False
                for i in range(rec.branches_qty):
                    transfers.append((0, 0, {
                        'product_id': rec.purchase_order_line_id.product_id.id,
                        'quantity': 0
                    }))
                
                rec.transfers = transfers

    def action_transfer(self):
        for rec in self:
            branches = []

            for transfer in rec.transfers:
                if transfer.branch_id.id not in branches:
                    branches.append({
                        'branch_id': transfer.branch_id.id,
                        'branch_name': transfer.branch_id.display_name,
                    })
            
            for branch in branches:
                branch_picking = {
                    'partner_id': rec.purchase_order_id.partner_id.id,
                    'purchase_order_id': rec.purchase_order_id.id,
                    'picking_type_id': rec.purchase_order_id.picking_type_id.warehouse_id.int_type_id.id,
                    'location_dest_id': branch['branch_id'],
                    # 'location_id': rec.purchase_order_id.picking_type_id.default_location_src_id.id,
                    'user_id': False,
                    'date': rec.purchase_order_id.date_order,
                    'origin': rec.purchase_order_id.name,
                    'state': 'draft',
                }
                move_ids = []
                for transfer in rec.transfers:
                    if transfer.branch_id.id == branch['branch_id']:
                        move_ids.append((0, 0, {
                            'product_id': transfer.product_id.id,
                            'product_uom_qty': transfer.quantity,
                            'name': transfer.product_id.display_name,
                        }))
                branch_picking['move_ids'] = move_ids
                
                # search_picking = self.env['stock.picking'].search([('purchase_order_id', '=', rec.purchase_order_id.id), ('location_dest_id', '=', branch['branch_id'])])
                # if search_picking:
                #     raise UserError(f'Picking already exists for this branch {branch["branch_name"]}')
                # else:
                self.env['stock.picking'].create(branch_picking)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Internal Transfers',
                'res_model': 'stock.picking',
                'view_mode': 'list,form',
                'domain': [('purchase_order_id', '=', rec.purchase_order_id.id)],
                'target': 'current',
            }
            
    def action_save(self):
        for rec in self:
            total_qty = 0
            for transfer in rec.transfers:
                if transfer.quantity <= 0:
                    raise UserError(f'Quantity {transfer.quantity} is less than or equal to 0')
                total_qty += transfer.quantity
            
            if total_qty > rec.line_product_qty:
                raise UserError(f'Total quantity {total_qty} is greater than max quantity {rec.line_product_qty}')
            
            for transfer in rec.transfers:
                self.env['purchase.order.branch.transfer'].create({
                    'purchase_order_id': rec.purchase_order_line_id.order_id.id,
                    'purchase_order_line_id': rec.purchase_order_line_id.id,
                    'product_id': transfer.product_id.id,
                    'product_qty': transfer.quantity,
                    'branch_id': transfer.branch_id.id
                })

    def action_view_transfers(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Internal Transfers',
                'res_model': 'stock.picking',
                'view_mode': 'list,form',
                'domain': [('purchase_order_id', '=', rec.purchase_order_id.id)],
                'target': 'current',
            }

class TransferToBranchLine(models.TransientModel):
    _name = 'kas.transfer.branch.line'
    _description = 'Transfer To Branch Line'

    branch_id = fields.Many2one('stock.location', string='Branch')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity')
    transfer_id = fields.Many2one('kas.transfer.branch', string='Transfer')


    # def action_duplicate(self):
    #     for rec in self:
    #         rec.transfer_id.transfers += rec