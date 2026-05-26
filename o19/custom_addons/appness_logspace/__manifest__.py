{
    'name': 'Appness Logspace Booking',
    'version': '1.0',
    'author': 'Appness Technologies',
    'category': 'Website',
    'summary': 'Custom Truck Booking Page and Search Snippet',
    'depends': [
        'website',
        'crm',
        'sale_management',
        'documents',
        'contacts',
        'base_address_extended'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'views/product_template.xml',
        'views/snippets/s_booking_search.xml',
        'views/snippets/snippets.xml',
        'views/booking_page.xml',
        'views/documents.xml',
        'views/settings.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace/static/src/scss/booking.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
