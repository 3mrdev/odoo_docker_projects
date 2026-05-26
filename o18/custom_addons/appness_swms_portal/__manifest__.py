{
    "name":"Social Welfare Portal",
    "license":"LGPL-3",
    "data":[
        #Security
        "security/ir.model.access.csv",

        #Views
        "views/menus.xml",
        "views/settings.xml",
        "views/company.xml",
        "views/stepper.xml",
        "views/document.xml",

        #Portal 
        "views/portal_form_templates.xml",
        "views/portal_auth_templates.xml",
        "views/portal_home_templates.xml",
        "views/portal_service_templates.xml",
        "views/portal_request_templates.xml",
    ],
    "depends":[
        "appness_swms",
        "portal",
        "website"
    ],
    'assets': {
        'web.assets_frontend': [
            # 'appness_swms_portal/static/src/js/portal_timeout.js',
            'appness_swms_portal/static/src/css/swms.css',
            'appness_swms_portal/static/src/js/swms_o2m.js',
            'appness_swms_portal/static/src/js/swms_otp.js',
            'appness_swms_portal/static/src/js/swms_validation.js',
            'appness_swms_portal/static/src/js/phone_widget_frontend.js',
            'appness_swms_portal/static/lib/intl-tel-input/css/intlTelInput.css',
            # 'appness_swms_portal/static/lib/intl-tel-input/js/utils.js',
            'appness_swms_portal/static/lib/intl-tel-input/js/intlTelInput.js',
            # 'https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/js/intlTelInput.js',
            # 'https://cdn.jsdelivr.net/npm/intl-tel-input@17.0.3/build/css/intlTelInput.css',
            # 'https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/css/intlTelInput.css',
            # 'https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/intlTelInput.min.js',
        ],
        'web.assets_backend': [
            'appness_swms_portal/static/src/js/file_uploader.js',
        ],
    }
}