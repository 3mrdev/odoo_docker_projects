{
    'name': 'Logspace',
    'version': '19.0.2.6.0',
    'category': 'Website',
    'summary': 'Logspace customer and provider logistics platform',
    'description': """
        Logspace Logistics Platform:
        - 23 Frontend Screens (Customer, Provider journeys)
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
        'account',      # For provider vendor bills and financial integration
        'mail',
        'hr',           # For job positions (contact roles)
        'helpdesk',     # For support tickets
        'payment',      # Odoo payment gateway integration
        'resource',     # For provider working calendar
        'documents',    # For provider document management
    ],
    'data': [
        'data/logspace_sequences.xml',
        'data/logspace_email_templates.xml',
        'data/website_menu.xml',
        # Master Data (updatable)
        'data/data_products.xml',
        # Categories must load BEFORE the types that reference them.
        'data/data_vehicle_categories.xml',
        'data/data_vehicle_types.xml',
        'data/data_addons.xml',
        # Time slots master data
        'data/data_time_slots.xml',
        # Oman geo-zoning data
        # 'data/data_oman_zones.xml',
        # Same-zone (intra-governorate) distance estimates; needs the zones
        # 'data/data_zone_distances.xml',
        # Module Configuration
        'data/logspace_config_data.xml',
        # Demo Data (noupdate)
        # 'demo_data/demo_providers.xml',
        # 'demo_data/demo_timeframes.xml',
        # 'demo_data/demo_vehicles.xml',
        # 'demo_data/demo_price_matrix.xml',
        'security/logspace_groups.xml',
        'security/ir.model.access.csv',
        'security/logspace_security.xml',
        'views/logspace_layout_templates.xml',
        'views/logspace_search_templates.xml',
        'views/logspace_vendor_templates.xml',
        'views/logspace_booking_templates.xml',
        'views/logspace_portal_templates.xml',
        # Overrides of CORE portal templates (the only ones in this module).
        'views/logspace_portal_nav_templates.xml',
        # Driver portal - separate file on purpose: the customer track page
        # renders the pickup/dropoff verification codes in plain text and a
        # driver must never see either one.
        'views/logspace_driver_templates.xml',
        'views/logspace_provider_templates.xml',
        # Backend views - Master data first
        # Backend views - Master data
        'views/backend/logspace_zone_views.xml',
        'views/backend/logspace_zone_distance_views.xml',
        'views/backend/logspace_vehicle_category_views.xml',
        'views/backend/logspace_vehicle_type_views.xml',
        'views/backend/logspace_addon_views.xml',
        'views/backend/logspace_vehicle_views.xml',
        'views/backend/logspace_state_duration_views.xml',

        # Wizard (must load before res_partner_views which references its action)
        'wizard/logspace_zone_setup_wizard_views.xml',
        'views/logspace_verification_wizard_views.xml',

        # Provider management (using res.partner)
        'views/backend/logspace_price_matrix_views.xml',
        'views/backend/logspace_provider_vtype_addon_views.xml',
        'views/backend/logspace_fleet_summary_views.xml',
        'views/backend/logspace_time_frame_views.xml',
        'views/backend/logspace_special_instruction_views.xml',
        'views/backend/res_partner_views.xml',       # Provider via res.partner
        'views/backend/hr_job_views.xml',           # Contact roles via hr.job

        # Order management (using sale.order)
        'views/backend/sale_order_views.xml',

        # Customer support (using helpdesk.ticket)
        'views/backend/helpdesk_ticket_views.xml',

        # Note: logspace_provider model removed - using res.partner instead
        # 'views/backend/logspace_provider_views.xml',  # DEPRECATED
        'views/backend/logspace_refund_views.xml',
        # 'views/backend/logspace_ticket_views.xml',
        'views/backend/logspace_notification_views.xml',

        # Provider commission vendor bills (read-only, no journal references -
        # a provider cannot read account.journal)
        'views/backend/account_move_views.xml',

        # Settings (res.config.settings - policies)
        'views/backend/res_config_settings_views.xml',

        # Menus
        'views/backend/logspace_menus.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace/static/lib/intl-tel-input/css/intlTelInput.css',
            'appness_logspace/static/src/scss/logspace.scss',
            'appness_logspace/static/src/js/logspace.js',
            'appness_logspace/static/src/js/logspace_driver.js',
            'appness_logspace/static/lib/intl-tel-input/js/intlTelInput.js',
            'appness_logspace/static/src/js/logspace_phone_widget.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
