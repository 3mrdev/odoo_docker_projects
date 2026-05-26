from odoo import models,fields,api,_

class Product(models.Model):
    _inherit = "product.template"

    is_swms = fields.Boolean()
    can_be_repeated = fields.Boolean()
    is_published_swms = fields.Boolean(help="Is published in the website portal ?")
    sequence_id = fields.Many2one("ir.sequence",string="Request Sequence")
    budget_analytic_accounts_ids = fields.Many2many("account.analytic.account")
    # choose_activity_type_id = fields.Many2one("mail.activity.type")
    # choose_activity_manager = fields.Many2one("res.users")
    plan_id = fields.Many2one("sale.subscription.plan",string="Recurring Plan")
    document_types = fields.Many2many("swms.document.type",domain="[('type','=','service')]")
    action_types = fields.Selection([
        ('none','None'),
        ('one','One Time'),
        ('recurring','Recurring'),
        ('project','Project Based'),
        ('material','Material'),
    ], default='none', help=""""
When you click on the done button in the last stage of a request a few actions can happen automatically:
    - None: Nothing will happen
    - One Time: The system will create a bill for one time with the recommended amount
    - Recurring: The system will create a bills monthly untill a certin date depending on the plan
    - Project: The system will create a project
    - Material: The system will create a delivery order in inventory
    """)
    # archive_after = fields.Float(help="Number of days to archive the the service requested containing this service automatically")

    allowed_address = fields.One2many("swms.address","service_id")