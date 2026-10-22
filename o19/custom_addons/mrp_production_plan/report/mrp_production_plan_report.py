from odoo import fields, models
from odoo.tools import SQL


class MrpProductionPlanReport(models.Model):
    _name = 'mrp.production.plan.report'
    _description = 'Production Plan Analysis'
    _auto = False
    _order = 'date_from, id'

    plan_id = fields.Many2one('mrp.production.plan', readonly=True)
    plan_name = fields.Char(readonly=True)
    plan_state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('revised', 'Revised'),
            ('done', 'Done'), ('cancelled', 'Cancelled')], readonly=True)
    line_id = fields.Many2one('mrp.production.plan.line', readonly=True)
    target_id = fields.Many2one('mrp.production.plan.target', readonly=True)
    product_id = fields.Many2one('product.product', readonly=True)
    company_id = fields.Many2one('res.company', readonly=True)
    period_type = fields.Selection(
        selection=[('year', 'Year'), ('month', 'Month'), ('day', 'Day')], readonly=True)
    date_from = fields.Date(readonly=True)
    date_to = fields.Date(readonly=True)
    date = fields.Date(readonly=True)
    res_model = fields.Char(readonly=True)
    res_id = fields.Many2oneReference('Document', model_field='res_model', readonly=True)
    line_type = fields.Selection(
        [('target', 'Target'), ('actual', 'Actual')], 'Type', readonly=True)
    target_qty = fields.Float(readonly=True)
    target_gold_content = fields.Float(readonly=True)
    actual_qty = fields.Float(readonly=True)
    actual_gold_content = fields.Float(readonly=True)

    @property
    def _table_query(self):
        return SQL(
            "%s UNION ALL %s UNION ALL %s",
            self._get_target_query(),
            self._get_main_actual_query(),
            self._get_byproduct_actual_query(),
        )

    def _get_target_lateral(self):
        """Most specific target of the line whose period contains the MO date.

        Mirrors the compute tie-break (shortest range first, latest target on
        range ties). NULL for MOs outside every target range — they still
        count at line level, matching the actuals computes.
        """
        return SQL("""
             LEFT JOIN LATERAL (
                        SELECT t.id AS target_id, t.period_type,
                               t.date_from, t.date_to
                          FROM mrp_production_plan_target t
                         WHERE t.line_id = l.id
                           AND t.date_from <= mo.date_finished::DATE
                           AND t.date_to >= mo.date_finished::DATE
                      ORDER BY (t.date_to - t.date_from) ASC, t.id DESC
                         LIMIT 1) mt ON True
            """)

    def _get_target_query(self):
        return SQL(
            """
            SELECT CONCAT('target', t.id::TEXT) AS id,
                   p.id AS plan_id,
                   p.name AS plan_name,
                   p.state AS plan_state,
                   l.id AS line_id,
                   t.id AS target_id,
                   l.product_id AS product_id,
                   l.company_id AS company_id,
                   t.period_type AS period_type,
                   t.date_from AS date_from,
                   t.date_to AS date_to,
                   t.date_from AS date,
                   'mrp.production.plan.target' AS res_model,
                   t.id AS res_id,
                   'target' AS line_type,
                   t.target_qty AS target_qty,
                   t.target_gold_content AS target_gold_content,
                   0 AS actual_qty,
                   0 AS actual_gold_content
              FROM mrp_production_plan_target t
              JOIN mrp_production_plan_line l ON l.id = t.line_id
              JOIN mrp_production_plan p ON p.id = l.plan_id
            """
        )

    def _get_main_actual_query(self):
        """Actual rows when the line's product is the MO's main product.

        Matched budget-style per plan line (product + company + MO end date
        within the plan period) — no MO link required, so overlapping plans
        each independently see the same MOs.
        """
        return SQL(
            """
            SELECT CONCAT('mo', mo.id::TEXT, '-', l.id::TEXT) AS id,
                   p.id AS plan_id,
                   p.name AS plan_name,
                   p.state AS plan_state,
                   l.id AS line_id,
                   mt.target_id,
                   l.product_id AS product_id,
                   l.company_id AS company_id,
                   mt.period_type,
                   mt.date_from,
                   mt.date_to,
                   mo.date_finished::DATE AS date,
                   'mrp.production' AS res_model,
                   mo.id AS res_id,
                   'actual' AS line_type,
                   0 AS target_qty,
                   0 AS target_gold_content,
                   mo.product_qty AS actual_qty,
                   COALESCE((SELECT SUM(sl.gold_content)
                               FROM mrp_production_stock_lot_rel rel
                               JOIN stock_lot sl ON sl.id = rel.stock_lot_id
                              WHERE rel.mrp_production_id = mo.id), 0)
                      AS actual_gold_content
              FROM mrp_production mo
              JOIN mrp_production_plan_line l
                ON l.product_id = mo.product_id
               AND l.company_id = mo.company_id
              JOIN mrp_production_plan p ON p.id = l.plan_id
            %s
             WHERE mo.state NOT IN ('draft', 'cancel')
               AND mo.date_finished::DATE >= p.date_from
               AND mo.date_finished::DATE <= p.date_to
            """,
            self._get_target_lateral(),
        )

    def _get_byproduct_actual_query(self):
        """Actual rows when the line's product is produced as a by-product.

        One row per (plan line, by-product finished move) of matching MOs —
        tracks products that appear only as by-products and have no
        standalone MO. Gold content comes from the lots recorded on the
        by-product move lines (grade_tracking).
        """
        return SQL(
            """
            SELECT CONCAT('mobp', m.id::TEXT, '-', l.id::TEXT) AS id,
                   p.id AS plan_id,
                   p.name AS plan_name,
                   p.state AS plan_state,
                   l.id AS line_id,
                   mt.target_id,
                   l.product_id AS product_id,
                   l.company_id AS company_id,
                   mt.period_type,
                   mt.date_from,
                   mt.date_to,
                   mo.date_finished::DATE AS date,
                   'mrp.production' AS res_model,
                   mo.id AS res_id,
                   'actual' AS line_type,
                   0 AS target_qty,
                   0 AS target_gold_content,
                   m.product_qty AS actual_qty,
                   COALESCE((SELECT SUM(sl.gold_content)
                               FROM (SELECT DISTINCT sml.lot_id
                                       FROM stock_move_line sml
                                      WHERE sml.move_id = m.id
                                        AND sml.lot_id IS NOT NULL) lots
                               JOIN stock_lot sl ON sl.id = lots.lot_id), 0)
                      AS actual_gold_content
              FROM stock_move m
              JOIN mrp_production mo ON mo.id = m.production_id
              JOIN mrp_production_plan_line l
                ON l.product_id = m.product_id
               AND l.company_id = mo.company_id
              JOIN mrp_production_plan p ON p.id = l.plan_id
            %s
             WHERE mo.state NOT IN ('draft', 'cancel')
               AND m.product_id != mo.product_id
               AND mo.date_finished::DATE >= p.date_from
               AND mo.date_finished::DATE <= p.date_to
            """,
            self._get_target_lateral(),
        )
