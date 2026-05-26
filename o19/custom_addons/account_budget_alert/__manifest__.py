{
    "name":"Account Budget Alert",
    "summary":"Account Budget Alert",
    "description":"Account Budget Alert",
    "author":"Appness",
    "website":"https://appness.ai",
    "category":"Accounting",
    "version":"1.0.0",
    "data":[
        "security/groups.xml",
        "views/budget_analytic_views.xml",
        "views/account_move_views.xml",
        "views/purchase_order_views.xml",
        "views/hr_expense_views.xml",
        "views/account_report_budget_views.xml"
    ],
    "depends":[
        "account",
        "account_budget",
        "account_reports",
        "account_budget_purchase",
        "hr_expense"
    ],
    "installable":True,
    "application":True,
    "auto_install":False,
    "license":"LGPL-3"
}