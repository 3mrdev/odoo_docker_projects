{
    'name': 'Approvals Custom Base',
    'version': '1.0',
    'category': 'Approvals',
    'description': """
Base module for approvals custom modules.
Provides common fields, methods, and hooks for journal entry generation
from approval requests.
    """,
    'depends': ['approvals', 'account'],
    'data': [
        'data/mail_templates.xml',
        'views/approval_request_views.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Appness',
    'license': 'LGPL-3',
}
