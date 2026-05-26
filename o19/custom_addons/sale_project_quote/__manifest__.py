{
    "name": "Sales Project Quote",
    "version": "1.2",
    "author": "Appness",
    "summary": "Allow project team to edit sales quotes without seeing prices",
    "description": """
        Sales Project Quote
        =============================
        - Allow project team to edit sales quotes
        - Hide prices from project team members
        - Prevent project team from confirming orders
    """,
    "depends": [
        "sale",
        "sales_team",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}