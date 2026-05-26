from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    pickings_branch_ids = fields.One2many('stock.picking', 'purchase_order_id', string='Pickings Branch')
    pickings_branch_count = fields.Integer(string='Pickings Branch Count', compute='_compute_pickings_branch_count')

    branch_transfers_ids = fields.One2many('purchase.order.branch.transfer', 'purchase_order_id', string='Branch Transfers')
    branch_transfers_count = fields.Integer(string='Branch Transfers Count', compute='_compute_branch_transfers_count')

    def _compute_pickings_branch_count(self):
        for rec in self:
            rec.pickings_branch_count = len(rec.pickings_branch_ids)

    def _compute_branch_transfers_count(self):
        for rec in self:
            rec.branch_transfers_count = len(rec.branch_transfers_ids)

    def action_view_pickings_branch(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pickings Branch',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('purchase_order_id', '=', self.id)],
            'target': 'current',
        }

    def action_view_branch_transfers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Branch Transfers',
            'res_model': 'purchase.order.branch.transfer',
            'view_mode': 'list,form',
            'domain': [('purchase_order_id', '=', self.id)],
            'target': 'current',
        }

    def action_transfer_to_branches(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer To Branches',
            'res_model': 'kas.transfer.branch',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_order_id': self.id},
        }

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    def action_transfer_to_branches(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Transfer To Branches',
            'res_model': 'kas.transfer.branch',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_order_line_id': self.id},
        }

class PurchaseOrderBranchTransfer(models.Model):
    _name = 'purchase.order.branch.transfer'
    _description = 'Purchase Order Branch Transfer'

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Purchase Order Line')
    product_id = fields.Many2one('product.product', string='Product', related='purchase_order_line_id.product_id')
    product_qty = fields.Float(string='Product Quantity')
    branch_id = fields.Many2one('stock.location', string='Branch')
    
    
    