from odoo import models,fields,_

class DocumentType(models.Model):
    _inherit = "logspace.document.type"

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Code must be unique!'),
    ]
    
    steps_ids = fields.Many2many("logspace.stepper.step")
    code = fields.Char(required=True) #TODO: try to make it auto to be easy

