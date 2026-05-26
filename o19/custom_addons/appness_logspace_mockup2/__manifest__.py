{
    'name': 'Logspace Mockup 2',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Mockup screens for Logspace customer and provider journey',
    'description': """
        Logspace Logistics Platform:
        - 23 Frontend Mockup screens (Customer, Provider journeys)
        - Complete Backend with Provider Management
        - Price Matrix, Support Tickets, Refunds, Ratings
        - Guest checkout flow (no forced auth)
        - Professional design with Odoo standards
    """,
    'author': 'Appness Technologies',
    'depends': [
        'website',
        'portal',
        'web',
        'auth_signup',
        'sale',
        'mail',
        'hr',           # For job positions (contact roles)
        'helpdesk',     # For support tickets
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/logspace_security.xml',
        'data/website_menu.xml',
        'data/logspace_sequences.xml',
        'data/logspace_demo_data.xml',
        'views/mockup_layout_templates.xml',
        'views/mockup_search_templates.xml',
        'views/mockup_vendor_templates.xml',
        'views/mockup_booking_templates.xml',
        'views/mockup_auth_templates.xml',
        'views/mockup_portal_templates.xml',
        'views/mockup_provider_templates.xml',
        # Backend views - Master data first
        # Backend views - Master data
        'views/backend/logspace_zone_views.xml',
        'views/backend/logspace_vehicle_type_views.xml',
        'views/backend/logspace_addon_views.xml',
        'views/backend/logspace_vehicle_views.xml',

        # Provider management (using res.partner)
        'views/backend/logspace_price_matrix_views.xml',
        'views/backend/logspace_provider_vtype_addon_views.xml',
        'views/backend/res_partner_views.xml',       # Provider via res.partner
        'views/backend/hr_job_views.xml',           # Contact roles via hr.job

        # Order management (using sale.order)
        'views/backend/sale_order_views.xml',

        # Customer support (using helpdesk.ticket)
        'views/backend/helpdesk_ticket_views.xml',

        # Legacy views (keeping for compatibility)
        'views/backend/logspace_provider_views.xml',
        'views/backend/logspace_rating_views.xml',
        'views/backend/logspace_refund_views.xml',
        'views/backend/logspace_ticket_views.xml',
        'views/backend/logspace_notification_views.xml',

        # Menus
        'views/backend/logspace_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace_mockup2/static/src/scss/mockup2.scss',
            'appness_logspace_mockup2/static/src/js/mockup2.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
