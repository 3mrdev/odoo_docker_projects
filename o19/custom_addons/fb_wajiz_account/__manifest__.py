{
    "name":"FB Wajiz Account",
    "description":"""
    This module is used to manage the account settings for Wajiz.
    - Add fields to res.company model.
    - Add fields to res.partner model.
    - Add fields to account.payment model.

    if you activate the "use_outstanding_accounts" option in company profile the outstanding accounts will be ignored
    """,
    "author":"Firebits",
    "license":"LGPL-3",
    "data": [
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
    ],
    "depends":[
        "account",
        "account_payment"
    ],
}