from odoo import fields, models


class MrpProductionGroup(models.Model):
    _inherit = 'mrp.production.group'

    child_ids = fields.Many2many(string='Child Production Orders')
    parent_ids = fields.Many2many(string='Parent Production Orders')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    _description = 'Production Order'


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    production_id = fields.Many2one(string='Production Order')


class MrpWorkcenterProductivity(models.Model):
    _inherit = 'mrp.workcenter.productivity'

    production_id = fields.Many2one(string='Production Order')


class MrpUnbuild(models.Model):
    _inherit = 'mrp.unbuild'

    mo_id = fields.Many2one(string='Production Order')


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    type = fields.Selection([
        ('normal', 'Produce this product'),
        ('phantom', 'Kit')])
    ready_to_produce = fields.Selection(string='Production Readiness')
    days_to_prepare_mo = fields.Integer(string='Days to prepare Production Order')
