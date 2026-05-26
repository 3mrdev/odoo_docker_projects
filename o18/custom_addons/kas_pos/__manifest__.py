{
    "name": "Alkhaial Alarabi POS",
    "version": "1.0",
    "category": "Point of Sale",
    "summary": "Alkhaial Alarabi POS",
    "description": "Alkhaial Alarabi POS",
    "depends": [
        "point_of_sale", 
        "pos_hr",
        "mrp",
        "purchase",
        "stock_account",
        "pos_enhanced_features"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/decimal_accuracy.xml",
        "views/res_config_settings_views.xml",
        "views/purchase_order_views.xml",
        "views/purchase_order_branch_transfer.xml",
        "views/stock_picking_views.xml",
        "wizards/transfer_to_branch.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            'kas_pos/static/src/**/*',
        ],
    },
    "installable": True,
    "application": True,
}