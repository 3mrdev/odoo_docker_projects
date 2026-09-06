{
    'name': 'Approvals Project',
    'version': '1.0',
    'category': 'Project/Approvals',
    'description': """
This module adds to the approvals workflow the possibility to link
projects.
    """,
    'depends': [
        'approvals_custom_base',
        'approvals_stock_material',
        'project',
        'project_stock',
        'stock',
    ],
    'data': [
        'views/approval_request_views.xml',
        'views/project_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Appness',
    'license': 'LGPL-3',
}
