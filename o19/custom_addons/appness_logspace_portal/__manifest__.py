{
    "name":"Logspace Portal",
    "author":"Appness Technologies",
    "license":"LGPL-3",
    "data":[
        #Security
        "security/ir.model.access.csv",

        #Views
        "views/menus.xml",
        "views/settings.xml",
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
        "appness_logspace",
        "portal",
        "website"
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace_portal/static/src/css/logspace.css',
            'appness_logspace_portal/static/src/js/logspace_o2m.js',
            'appness_logspace_portal/static/src/js/logspace_otp.js',
            'appness_logspace_portal/static/src/js/logspace_validation.js',
            'appness_logspace_portal/static/src/js/phone_widget_frontend.js',
            'appness_logspace_portal/static/lib/intl-tel-input/css/intlTelInput.css',
            'appness_logspace_portal/static/lib/intl-tel-input/js/intlTelInput.js',
        ],
        'web.assets_backend': [
            'appness_logspace_portal/static/src/js/file_uploader.js',
        ],
    }
}