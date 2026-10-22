{
    'name': 'MRP Shifts',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Shift tracking on manufacturing orders and work orders',
    'description': """
Shift Tracking for Manufacturing
================================
* Define shifts (e.g. Morning, Evening, Night) as master data.
* Set a shift on the manufacturing order; it is automatically copied to all
  its work orders and kept in sync when the MO shift changes.
* Work order shifts can be adjusted independently of the MO.
* The work order shift is shown read-only in the work order's
  Time Tracking (time spent) table.
""",
    'author': 'Appness',
    'license': 'LGPL-3',
    'depends': ['mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/mrp_shift_data.xml',
        'views/mrp_shift_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_rename_views.xml',
        'views/mrp_rename_reports.xml',
    ],
    'installable': True,
    'application': False,
}
