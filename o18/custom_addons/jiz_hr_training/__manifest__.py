# -*- coding: utf-8 -*-
{
    'name': 'JAB HR Training',
    'version': '18.0.1.0.0',
    'summary': 'Manage and track employee training programs.',
    'author': 'Amr Appness',
    'website': 'https://appness.ai',
    'category': 'Human Resources/Training',
    'depends': [
        'hr'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/jiz_training_views.xml',
        'views/jiz_training_type_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}