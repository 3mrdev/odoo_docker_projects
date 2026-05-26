{
    "name":"Appness ROHM Attachment",
    "summery":"",
    "description":"""
    """,
    "sequence": -1,
    "version": '17.0',
    "author": "Appness",
    "maintainer":"Amr Abd-Alkrim",
    "support": 'bashir_idris@appness.net',
    "website": "https://www.appness.net",
    "live_test_url": "https://www.youtube.com/appness",
    "category": "Disucss",
    "version": "16.0",
    "license": "AGPL-3",
    "depends": [
        "project",
        "helpdesk",
        "web",
    ],
    "data": [
        "views/settings.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "appness_rohm_attach/static/src/js/file_uploader.js",
        ]
    },
    "installable": True,
    "application": True,
    "auto_install": False,
}