{
    'name': 'Subscription Penalty - Inline',
    'version': '1.0',
    'author':"Appness",
    'category': 'Sales/Subscription',
    'summary': 'Add penalty charges as invoice lines for late subscription payments',
    'description': """
Subscription Late Payment Penalties - Inline Approach
======================================================

Automatically adds penalty charges as invoice lines directly to unpaid 
subscription invoices.

Features:
---------
* Adds penalty as invoice line (not separate invoice)
* Yearly recurring penalties for unpaid invoices
* Configurable penalty amount and product
* Automatic daily cron job
* Penalties stop when invoice is paid
* Smart button showing penalty count
* Visual highlighting of penalty lines

How it works:
-------------
1. Subscription invoice becomes late (past deferred_end_date)
2. First penalty line is added to the invoice
3. Each year the invoice remains unpaid, another penalty line is added
4. When invoice is paid, no more penalties are added

Configuration:
--------------
Settings > Sales > Subscriptions > Late Payment Penalties (Inline)
    """,
    'depends': [
        'sale_subscription',
        'account',
    ],
    'data': [
        'data/ir_cron_data.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
