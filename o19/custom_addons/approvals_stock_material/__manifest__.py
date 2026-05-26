{
    'name': 'Approvals Stock Material Transfer',
    'version': '1.0',
    'category': 'Inventory/Approvals',
    'description': """
This module adds to the approvals workflow the possibility to generate
stock transfers between warehouses through transit locations.
    """,
    'depends': ['approvals_custom_base', 'stock'],
    'data': [
        'views/approval_category_views.xml',
        'views/approval_request_views.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Appness',
    'license': 'LGPL-3',
}
