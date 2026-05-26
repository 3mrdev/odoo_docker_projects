{
    "name":"Social Welfare",
    "license":"LGPL-3",
    "data":[
        #Security
        "security/groups.xml",
        "security/ir.model.access.csv",

        #Data
        "data/mail_activity_type.xml",
        "data/ir_sequence.xml",

        #Views
        "views/settings.xml",
        
        "views/sale_order.xml",
        "views/res_partner.xml",
        "views/document.xml",
        "views/address.xml",
        "views/income.xml",
        "views/card.xml",
        "views/property.xml",
        "views/crm.xml",
        "views/product_template.xml",
        "views/helpdesk_team.xml",
        "views/helpdesk_ticket.xml",
        "views/case_study.xml",
        "views/service_line.xml",
        "views/stock_picking.xml",
        "views/project_project.xml",
        "views/cron.xml",
        "views/account_move.xml",
        "views/fleet_vehicle.xml",
        "views/hr_expense.xml",
        "views/menus.xml",

        #To restrict access to swms data in these modules
        "views/purchase_order.xml",

        #Reports
        "reports/stats_report.xml",
        "reports/family_report.xml",
        "reports/member_report.xml",
        "reports/income_report.xml",
        "reports/obligations_report.xml",
        "reports/families_report.xml",
        "reports/orphans_report.xml",
        "reports/swms_reports.xml",
        "reports/service_report.xml",

        #Wizards
        "wizards/swms_reports_wizard.xml"
    ],
    "depends":[
        "helpdesk",
        "documents",
        "sale_subscription",
        "crm",
        "project",
        "sale_project",
        "stock",
        "account_budget",
        "analytic",
        "base_address_extended",
        "purchase",
        "hr_fleet",
        "hr_expense"
    ]
}