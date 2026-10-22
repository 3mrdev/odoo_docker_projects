{
    'name': 'Delgo Maintenance Extensions',
    'version': '19.0.2.0.0',
    'category': 'Maintenance',
    'summary': 'Stage locking, per-team sequences, request categories, spare-parts approvals and maintenance accounting for equipment',
    'description': """
Delgo Maintenance Extensions
============================
- Maintenance request stages changed via header buttons only, closed requests are
  locked except notes and instructions.
- Scheduled End (downtime) editable by dedicated access group while request is open.
- Unique team code driving a per-team request reference sequence (TEAMCODE/2026/0001).
- Extra maintenance request categorization.
- Analytic distribution and maintenance expense account on equipment (category as
  fallback), applied to inventory-loss consumptions linked through approval requests.
- Spare-parts requests from the maintenance request form through the approvals
  module (consume from stock or purchase), consumed on the company maintenance
  loss location with equipment-driven expense account and analytic distribution.
""",
    'author': 'FB Delgo',
    'license': 'LGPL-3',
    'depends': [
        'maintenance',
        'hr_maintenance',
        'approvals_stock_material',
        'approvals_stock_material_purchase',
        'stock_account',
        'account',
        'analytic',
    ],
    'data': [
        'security/fb_delgo_maintenance_security.xml',
        'security/ir.model.access.csv',
        'views/maintenance_request_views.xml',
        'views/maintenance_equipment_views.xml',
        'views/maintenance_team_views.xml',
        'views/maintenance_request_category_views.xml',
        'views/maintenance_stage_views.xml',
        'views/approval_request_views.xml',
        'views/maintenance_spare_parts_wizard_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
}
