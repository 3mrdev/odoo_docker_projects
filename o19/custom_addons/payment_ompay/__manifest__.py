# Copyright 2026 Emad. Licensed under LGPL-3.0-or-later.
{
    'name': 'Payment Provider: OMPay',
    'version': '19.0.1.1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': 'Accept OMR payments through OMPay hosted checkout.',
    'description': ' ',  # Do not load a README as the module description.
    'author': 'Emad',
    'website': 'https://developer.sandbox.truepay.ompay.om/docs',
    'depends': ['payment'],
    'data': [
        'views/payment_ompay_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'data/payment_ompay_cron.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
}
