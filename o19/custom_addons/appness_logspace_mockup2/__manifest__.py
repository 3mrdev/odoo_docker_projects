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
        'payment',      # Odoo payment gateway integration
        'resource',     # For provider working calendar
    ],
    'data': [
        'data/logspace_sequences.xml',
        'data/logspace_email_templates.xml',
        'data/website_menu.xml',
        # Master Data (updatable)
        'data/data_products.xml',
        'data/data_vehicle_types.xml',
        'data/data_addons.xml',
        # Oman geo-zoning data
        'data/data_oman_zones.xml',
        # Demo Data (noupdate)
        'demo_data/demo_providers.xml',
        'demo_data/demo_vehicles.xml',
        # 'demo_data/demo_price_matrix.xml',
        'security/logspace_groups.xml',
        'security/ir.model.access.csv',
        'security/logspace_security.xml',
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
        'views/backend/logspace_zone_distance_views.xml',
        'views/backend/logspace_vehicle_type_views.xml',
        'views/backend/logspace_addon_views.xml',
        'views/backend/logspace_vehicle_views.xml',

        # Wizard (must load before res_partner_views which references its action)
        'wizard/logspace_zone_setup_wizard_views.xml',

        # Provider management (using res.partner)
        'views/backend/logspace_price_matrix_views.xml',
        'views/backend/logspace_provider_vtype_addon_views.xml',
        'views/backend/res_partner_views.xml',       # Provider via res.partner
        'views/backend/hr_job_views.xml',           # Contact roles via hr.job

        # Order management (using sale.order)
        'views/backend/sale_order_views.xml',

        # Customer support (using helpdesk.ticket)
        'views/backend/helpdesk_ticket_views.xml',

        # Note: logspace_provider model removed - using res.partner instead
        # 'views/backend/logspace_provider_views.xml',  # DEPRECATED
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
