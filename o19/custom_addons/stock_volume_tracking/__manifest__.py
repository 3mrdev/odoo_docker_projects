{
    "name": "Stock Volume Tracking",
    "version": "1.1",
    "author": "Appness",
    "summary": "Track products by volume (L × W × H) across purchase, inventory, and sales",
    "description": """
        Stock Volume Tracking Module
        =============================
        - Track products by dimensions (Length × Width × Height)
        - Enter dimensions on purchase orders
        - Auto-create or match lots based on dimensions
        - Select lots with visible dimensions on sales orders
        - Auto-assign reserved lots to deliveries
    """,
    "depends": [
        "mrp",
        "sale_stock",
        "purchase_stock",
        "stock_account",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "reports/report_saleorder_document.xml",
        "reports/report_delivery_document.xml",
        "views/product_views.xml",
        "views/purchase_order_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_lot_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_quant_views.xml",
        "views/sale_order_views.xml",
        "views/sale_mrp_bom_line_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}