# -*- coding: utf-8 -*-

{
    'name': 'POS Enhanced Features',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Advanced customization for Point of Sale with enhanced order management capabilities, custom receipt printing options, improved permission control, and special product configuration for mix-and-match items',
    'description': """ Advanced customization for Point of Sale with enhanced order management capabilities, custom receipt printing options, improved permission control, and special product configuration for mix-and-match items """,
    'depends': ["point_of_sale", "mail", "mrp"],
    'data': [
        'security/groups.xml',
        'views/product_template.xml',
        'views/res_config_settings.xml',
    ],
    'installable': True,
    'application': False,
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_enhanced_features/static/src/components/**/*',
            'pos_enhanced_features/static/src/css/*',
            'pos_enhanced_features/static/src/models/*',
            'pos_enhanced_features/static/src/xml/*',
        ],
    },
    'license': 'LGPL-3',
}
