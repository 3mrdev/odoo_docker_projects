{
    "name": "Grade Tracking",
    "version": "1.1",
    "author": "Appness",
    "summary": "Track products by mining grade (location, level, average grade, tier, gold content) across purchase, inventory, sales, and manufacturing",
    "description": """
        Grade Tracking Module
        =====================
        - Track products by mining grade data (Mining Location, Level, Average Grade)
        - Auto-computed Grade Tier from configurable tier ranges (HGO/MGO/LGO)
        - Gold Content (g) computed as Average Grade x Quantity (tons)
        - Enter grade data on purchase orders and receipts
        - Grade data flows into lots on receiving and manufacturing
        - Grade change history audit trail on lots (Grade History group)
    """,
    "depends": [
        "project",
        "purchase_stock",
        "sale_stock",
        "mrp",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/grade_tier_views.xml",
        "views/grade_mining_level_views.xml",
        "views/grade_change_history_views.xml",
        "views/product_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_lot_views.xml",
        "views/stock_picking_views.xml",
        "views/stock_move_views.xml",
        "views/stock_move_line_views.xml",
        "views/stock_quant_views.xml",
        "views/sale_order_views.xml",
        "views/mrp_production_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
