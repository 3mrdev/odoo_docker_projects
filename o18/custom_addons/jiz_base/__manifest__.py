{
    'name': 'JAB Base',
    'version': '1.0',
    'summary': 'Base customizations for JAB Foundation',
    'description': 'Installs base models and modifications for other Jiz modules.',
    'author': 'Amr Appness',
    'website': 'https://appness.ai',
    'depends': [
        'base',
        'mail',
        'documents',
    ],
    'data': [
        'views/res_partner_view.xml',
        'views/documents_type.xml',
        'views/document.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
