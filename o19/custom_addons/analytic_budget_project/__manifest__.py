{
    'name': 'Analytic Budget Project',
    'version': '1.0',
    'category': 'Project/Budget',
    'description': """
This module links analytic budgets directly with projects, allowing
project users to create and manage budgets within their projects.
Users can only see budgets related to their projects.
    """,
    'depends': ['account_budget', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/budget_project_views.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Appness',
    'license': 'LGPL-3',
}
