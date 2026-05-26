{
    'name': 'Approvals - Stock Material + Purchase',
    'version': '1.0',
    'category': 'Inventory/Purchase/Approvals',
    'description': """
        Combines Stock Material Transfer and Purchase RFQ functionalities.
        Allows creating both stock transfers and purchase orders from a single approval request.

        Features:
        - Create Purchase Orders (RFQs) from approval request
        - Create Stock Transfers linked to PO receipts
        - Sequential workflow: PO → Receipt → Linked Transfers
        - Support for manual or automatic transfer creation modes
        - Handles multiple POs (one per vendor) and partial receipts
    """,
    'depends': [
        'approvals_stock_material',
        'approvals_purchase',
    ],
    'data': [
        'views/approval_category_views.xml',
        'views/approval_request_views.xml',
        'views/approval_product_line_views.xml',
    ],
    'installable': True,
    'application': False,
    'author': 'Appness',
    'license': 'LGPL-3',
}
