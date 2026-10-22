from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        related="lot_id.mining_location_id",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        related="lot_id.mining_level_id",
    )
    average_grade = fields.Float(
        string="Average Grade (g/t)",
        related="lot_id.average_grade",
    )
    grade_tier_id = fields.Many2one(
        "grade.tier",
        string="Grade Tier",
        related="lot_id.grade_tier_id",
    )
    gold_content = fields.Float(
        string="Gold Content (g)",
        related="lot_id.gold_content",
    )
