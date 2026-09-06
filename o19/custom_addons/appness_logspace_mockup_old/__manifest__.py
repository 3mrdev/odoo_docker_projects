{
    'name': 'Logspace Mockup',
    'version': '1.0',
    'category': 'Website/Website',
    'summary': 'Mockup screens for Logspace customer journey',
    'description': """
        17 Mockup screens for Logspace customer journey using Odoo guidelines.
    """,
    'author': 'Your Company',
    'depends': ['website', 'portal'],
    'data': [
        'views/mockup_layout_templates.xml',
        'views/mockup_search_templates.xml',
        'views/mockup_vendor_templates.xml',
        'views/mockup_booking_templates.xml',
        'views/mockup_auth_templates.xml',
        'views/mockup_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace_mockup/static/src/scss/mockup.scss',
            'appness_logspace_mockup/static/src/js/mockup.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
