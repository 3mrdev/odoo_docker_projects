{
    'name': 'Approvals Liquidity Transfer',
    'version': '1.0',
    'category': 'Human Resources/Approvals',
    'description': """
This module adds to the approvals workflow the possibility to generate
journal entries from an approval liquidity transfer request.
    """,
    'depends': ['approvals', 'account'],
    'data': [
        'views/approval_request_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}