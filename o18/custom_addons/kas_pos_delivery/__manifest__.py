# -*- coding: utf-8 -*-
{
    'name': 'KAS POS Delivery',
    'version': '18.0.1.1.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Auto-assign default customer and auto-pay with Customer Account in POS',
    'description': """
KAS POS Delivery
================
This module adds features to streamline POS operations:

Features:
---------
* Add 'Default Customer' field to restaurant floors
* Auto-assign customer when table is selected in POS
* Add 'Use POS Customer Account' field to customers
* Auto-pay with Customer Account and skip payment screen for faster checkout
    """,
    'depends': ['pos_restaurant'],
    'data': [
        'views/restaurant_floor_views.xml',
        'views/res_partner_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'kas_pos_delivery/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
