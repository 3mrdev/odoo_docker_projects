from odoo import models, fields, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    credit_note_id = fields.Many2one('account.move', string="Credit Note")