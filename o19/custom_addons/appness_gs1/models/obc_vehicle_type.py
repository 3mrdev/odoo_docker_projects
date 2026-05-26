from odoo import models,fields

class OBCVehicleType(models.Model):
    _name = "obc.vehicle.type"
    _description = "OBC Vehicle Type"

    name = fields.Char(required=True)