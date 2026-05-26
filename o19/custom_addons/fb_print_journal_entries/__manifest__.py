# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

{
    'name': 'FB Print All Journal Entries',
    'category': 'Account',
    'summary': 'Allow to print pdf report of Journal Entries all in one page with table and landscape.',
    'description': """
    Allow to print pdf report of Journal Entries.
    journal entry
    print journal entry 
    journal entries
    print journal entry reports
    account journal entry reports
    journal reports
    account entry reports

    
""",
    'author': 'FireBits',
    "license": "LGPL-3",
    'depends': [
        'base',
        'account',
        'bi_print_journal_entries',
    ],
    'data': [
            'report/report_journal_entries.xml',
            'report/report_journal_entries_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
