{
    "name":"Maintinance Access Rights",
    "depends":[
        "maintenance",
        "maintenance_plan",
        "hr_maintenance",
        "maintenance_custom",
        "stock",
        "purchase"
    ],
    "data":[
        "security/sec.xml",
        "security/ir.model.access.csv",
        "views/seq.xml",
        "wizard/spareparts.xml",
        "views/views.xml",
        "reports/report.xml"
    ],
    "assets": {
        "web.assets_backend": [
            "fb_wajiz_maintenance/static/src/js/file_uploader.js",
        ]
    },
}