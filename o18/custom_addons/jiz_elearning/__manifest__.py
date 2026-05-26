# -*- coding: utf-8 -*-
{
    'name': 'JAB eLearning Enhancements',
    'version': '18.0.1.0.0',
    'summary': 'Enhances the eLearning module with student-centric features.',
    'author': 'Amr Appness',
    'website': 'https://appness.ai',
    'category': 'Website/eLearning',
    'depends': [
        'website_slides',
        'jiz_base',
        'base',
        'survey',
        'website_ora_elearning'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/slide_slide_views.xml',
        'views/slide_channel_views.xml',
        'views/res_partner.xml',
        'views/survey_user_input_views.xml',
        'wizards/gen_cert.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}