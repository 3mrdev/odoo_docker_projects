{
    'name': 'FB Documents',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'FB Documents',
    'description': """
    FB Documents
    """,
    'depends': [
        'base',
        'hr',
        'mail',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/ir_attachment_views.xml',
        'data/sequences.xml',
    ],
    'installable': True,
    'application': True,
}