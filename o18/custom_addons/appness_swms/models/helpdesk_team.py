from odoo import models,fields,api,_

class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"

    service = fields.Many2one("product.template",domain="[('is_swms','=',True),('type','=','service')]",\
        help="SWMS Service that is used in this helpdesk team for all the service requests")
    stages_allowed_to_edit_portal = fields.Many2many("helpdesk.stage",'rel_team_stage_swms_portal')
    is_swms = fields.Boolean(related="service.is_swms")
    sequence_id = fields.Many2one("ir.sequence", string="Request Sequence",related="service.sequence_id")
    is_draft_stage = fields.Many2one("helpdesk.stage")
    is_approve_stage = fields.Many2one("helpdesk.stage")
    is_done_stage = fields.Many2one("helpdesk.stage")
    is_reject_stage = fields.Many2one("helpdesk.stage")
    is_cancel_stage = fields.Many2one("helpdesk.stage")
    is_family_responsible = fields.Boolean(string="Is Family Responsible",default=False,help="Each user is assigned tickets for the families that he is responsible for.")    