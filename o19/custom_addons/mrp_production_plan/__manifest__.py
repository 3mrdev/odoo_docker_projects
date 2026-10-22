{
    'name': 'MRP Production Plans',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Gold production planning: target vs actual per year/month/day with grade tracking',
    'description': """
Production Planning for Manufacturing
=====================================
* Define production plans (budget-style) with a period, a responsible and
  plan lines per final (grade-tracked) product.
* Break each line down into hierarchical targets by year, month and day,
  with a target quantity and an optional expected grade giving a fine gold
  content target.
* Actual quantities and gold content are computed from manufacturing
  orders (confirmed and beyond), using the grade tracking gold content of
  the produced lots.
* Optionally auto-link confirmed MOs to their matching plan target and
  warn when a confirmation would push production above the target.
* One-click generation of draft MOs from targets, with optional max
  quantity per MO (remaining quantity is split into several MOs dated
  across the period).
* Revise a confirmed plan (budget-style revision history) and keep the
  previous revisions read-only.
* Target vs actual analysis pivot/graph (SQL view) and a printable
  per-plan PDF report.
""",
    'author': 'Appness',
    'license': 'LGPL-3',
    'depends': ['mrp', 'grade_tracking'],
    'data': [
        'security/production_plan_security.xml',
        'security/ir.model.access.csv',
        'wizards/plan_target_generate_views.xml',
        'views/mrp_production_plan_views.xml',
        'views/mrp_production_plan_target_views.xml',
        'views/mrp_production_views.xml',
        'report/mrp_production_plan_report_views.xml',
        'report/mrp_production_plan_templates.xml',
    ],
    'installable': True,
    'application': False,
}
