# -*- coding: utf-8 -*-
{
    'name': 'JAB Helpdesk (Ataa)',
    'version': '18.0.1.0.0',
    'summary': 'Manage Ataa (grant) requests using the Helpdesk module.',
    'author': 'Amr Appness',
    'website': 'https://appness.ai',
    'category': 'Services/Helpdesk',
    'depends': [
        'helpdesk',
        'project',
        'event',
        'account',
        'documents',
        'jiz_base',
        'helpdesk_sms',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/documents_folder_data.xml',
        'views/jiz_standard_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/helpdesk_team_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}