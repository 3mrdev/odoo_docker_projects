{
    'name': 'Approvals HR Loans',
    'version': '1.0',
    'category': 'Human Resources/Approvals',
    'description': """
This module adds to the approvals workflow the possibility to generate
journal entries from an approval loan request.
    """,
    'depends': [
        'approvals_custom_base',
        'hr_payroll',
    ],
    'data': [
        'views/approval_request_views.xml',
        'views/approval_category_views.xml'
    ],
    'installable': True,
    'application': True,
    'author': 'Amr Appness',
    'license':'GPL-3',
}