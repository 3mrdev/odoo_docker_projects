{
    "name": "Oman - Payroll with Accounting",
    "author": "Appness Technology",
    "version": "1.0",
    "category": "Human Resources",
    "description": """
Accounting Data for Oman Payroll Rules
=======================================
Maps Oman salary rules to self-contained payroll accounts.
Auto-installs when both Payroll and Accounting are enabled for an Omani company.
    """,
    "depends": [
        "hr_payroll_account",
        "l10n_om_hr_payroll",
    ],
    "data": [
        "data/account_chart_template_data.xml",
        "data/hr_salary_rule_data.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": True,
}
