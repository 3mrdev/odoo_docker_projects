# -*- coding: utf-8 -*-
{
    'name': 'JAB Event Project Integration',
    'version': '18.0.1.0.0',
    'summary': 'Automatically create a project from a template when an event is created.',
    'author': 'Amr Appness',
    'website': 'https://appness.ai',
    'category': 'Marketing/Events',
    'depends': [
        'event',
        'project',
        'survey',
        'website_slides_survey'
    ],
    'data': [
        'views/event_type_views.xml',
        'views/event_event_views.xml',
        'views/survey_survey_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}