{
    "name":"Appness GS1 OBC",
    "version":"1.0",
    "author":"Appness",
    "license":"LGPL-3",
    "category":"Appness",
    "summary":"Appness GS1 OBC",
    "description":"Appness GS1 OBC",
    "depends":[
        "sale",
        "account",
        "sale_subscription",
        "sign"
    ],
    "data":[
        "security/groups.xml",
        "security/ir.model.access.csv",
        "reports/obc_rop_letter_report.xml",
        "reports/gs1_cert_report.xml",
        "views/sale_order_views.xml",
        "views/sale_order_line_views.xml",
        "views/res_users_views.xml",
        "views/obc_chassis_views.xml",
        "views/gln_cert_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
        "views/product_template_views.xml",
    ],
    "installable":True,
    "application":True,
    "auto_install":False
}