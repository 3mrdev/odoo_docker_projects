from odoo import models,fields,api,_

class Project(models.Model):
    _inherit = "project.project"

    is_swms = fields.Boolean()
    request_id = fields.Many2one("helpdesk.ticket")
    family_id = fields.Many2one("res.partner",string="Family",related="request_id.partner_id",store=True)