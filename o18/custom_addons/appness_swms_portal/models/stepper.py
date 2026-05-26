import trace
from odoo import models,fields,api,_

class Stepper(models.Model):
    _name = "swms.stepper"
    _description = "Stepper"
    
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(compute="_compute_name", store=True, translate=True)
    active = fields.Boolean(default=True)
    type = fields.Selection([
        ("family", "Family"),
        ("member","Member"),
        ("service","Service"),
    ],required=True)
    description = fields.Text()
    service_id = fields.Many2one("product.template")
    stepper_model_id = fields.Many2one("ir.model",compute="_get_stepper_model_id",store=True)
    steps_ids = fields.One2many("swms.stepper.step", "stepper_id")
    
    @api.depends("type")
    def _get_stepper_model_id(self):
        for rec in self:
            models_names = {
                "family":"res.partner",
                "member":"res.partner",
                "service":"helpdesk.ticket",
            }
            if rec.type:
                model_id = self.env["ir.model"].sudo().search([('model','=',models_names[rec.type])],limit=1)
                if model_id:
                    rec.stepper_model_id = model_id.id

    @api.depends("type","service_id")
    def _compute_name(self):
        for rec in self:
            if rec.type == "service":
                if rec.service_id:
                    rec.name = rec.service_id.name
                else:
                    rec.name = _("Service")
            elif rec.type == "family":
                rec.name = _("Family")
            elif rec.type == "member":
                rec.name = _("Member")
            else:
                rec.name = False

class Step(models.Model):
    _name = "swms.stepper.step"
    _description = "Stepper Step"
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(required=True,translate=True)
    icon = fields.Char(required=True,string="Step Icon",help="Font Awesome Icons ex. fa fa-upload")
    sequence = fields.Integer()
    stepper_id = fields.Many2one("swms.stepper",required=True)
    document_types_ids = fields.Many2many("swms.document.type",domain="[('type','in',['family','service'])]")
    lines = fields.One2many("swms.stepper.step.line","step_id")

class StepLine(models.Model):
    _name = "swms.stepper.step.line"
    _description = "Stepper Step Line"
    _inherit = ['mail.thread','mail.activity.mixin']
    _rec = "name"
    
    name = fields.Char(translate=True)
    tip = fields.Char(translate=True)
    validation_type = fields.Selection([
        ("none","None"),
        ("phone","Phone"),
        ("number","Number"),
        ("civil_number","Civil Number"),
        ("birthday","Birthday"),
        ("country","Country"),
        ("state","State"),
        ("city","City"),
        ("area","Area"),
    ],default="none")
    is_mandatory = fields.Boolean(default=True)

    sequence = fields.Integer()
    stepper_model_id = fields.Many2one("ir.model",required=True,ondelete='cascade',related="step_id.stepper_id.stepper_model_id")
    
    line_field = fields.Many2one("ir.model.fields", domain="[('model_id','=',stepper_model_id)]",required=True,ondelete='cascade')
    line_field_relation_model_name = fields.Char(related='line_field.relation', readonly=True, related_sudo=True)
    line_domain = fields.Char()

    line_field_model_id = fields.Many2one("ir.model",compute="_get_line_field_model_id",store=True)
    line_fields_ids = fields.Many2many("ir.model.fields",domain="[('model_id','=',line_field_model_id)]")
    line_fields_v2_ids = fields.One2many("swms.stepper.step.line.v2line","step_line")
    step_id = fields.Many2one("swms.stepper.step", required=True)
    
    @api.onchange("line_field")
    def _onchange_line_field(self):
        for rec in self:
            if rec.line_field:
                rec.name = rec.line_field.field_description
            else:
                rec.name = False

    @api.depends("line_field")
    def _get_line_field_model_id(self):
        for rec in self:
            model_id = self.env["ir.model"].sudo().search([('model','=',rec.line_field.relation)],limit=1)
            if model_id:
                rec.line_field_model_id = model_id.id

class StepV2Line(models.Model):
    _name = "swms.stepper.step.line.v2line"
    _description = "Stepper Step Line V2 Line"
    _rec = "name"
    
    name = fields.Char(translate=True)
    is_mandatory = fields.Boolean(default=True)
    sequence = fields.Integer()

    step_line = fields.Many2one("swms.stepper.step.line",required=True)
    line_field_model_id = fields.Many2one("ir.model", related="step_line.line_field_model_id", store=True)
    v2line_field = fields.Many2one("ir.model.fields", domain="[('model_id','=',line_field_model_id),('ttype','not in',['one2many','many2many'])]",required=True,ondelete='cascade')
    v2line_field_relation_model_name = fields.Char(related='v2line_field.relation', readonly=True, related_sudo=True)
    v2line_domain = fields.Char()

    @api.onchange("v2line_field")
    def _onchange_v2line_field(self):
        for rec in self:
            if rec.v2line_field:
                rec.name = rec.v2line_field.field_description
            else:
                rec.name = False