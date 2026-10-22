{
    'name': 'Approvals Liquidity Transfer',
    'version': '1.1',
    'category': 'Human Resources/Approvals',
    "author":"Appness",
	"license":"LGPL-3",
    'description': """
This module adds to the approvals workflow the possibility to generate
journal entries from an approval liquidity transfer request.
    """,
    'depends': ['approvals_custom_base'],
    'data': [
        'views/approval_request_views.xml',
    ],
    'installable': True,
    'application': True
}