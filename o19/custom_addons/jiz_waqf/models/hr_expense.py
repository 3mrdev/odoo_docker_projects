# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    waqf_id = fields.Many2one('jiz.waqf', string='Waqf')