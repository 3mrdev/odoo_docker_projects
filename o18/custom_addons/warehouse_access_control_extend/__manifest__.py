{
    'name': 'Warehouse Access Control - Extend',
    'version': '18.0.1.0',
    'summary': 'Extends warehouse access control to replenishments and routes',
    'category': 'Warehouse',
    'author': 'Appness',
    'license': 'LGPL-3',
    'depends': ['sttl_warehouse_access_control'],
    'description': '''
        Extends warehouse access control to replenishments (stock.warehouse.orderpoint)
        and routes (stock.route).
    ''',
    'data': [
        'security/access_control_rules.xml',
        'views/res_users_views.xml',
    ],
    'installable': True,
    'application': False,
}
