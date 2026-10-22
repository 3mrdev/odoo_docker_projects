{
    "name": "Grade Sample Approvals",
    "version": "1.0",
    "author": "Appness",
    "category": "Inventory/Inventory",
    "summary": "Grade Sample approval requests: lab users request grade application on lots/serials, lab managers apply the approved grade",
    "description": """
Grade Sample Approvals
======================
- New approval type "Grade Sample" on approval categories
- Lab users submit grade samples with lots/serials, average grade, mining location and level
- After the request is approved, Lab Managers apply the sample's average grade onto the lots
- Applying the grade never changes the approval status
- Every applied grade is logged in the lot's Grade Change History (grade_tracking)
    """,
    "depends": [
        "grade_tracking",
        "approvals",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "data/approval_category_data.xml",
        "views/approval_category_views.xml",
        "views/approval_request_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
