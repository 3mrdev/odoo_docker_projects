from odoo import models, fields, api
from datetime import date, datetime, timedelta

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    address_id = fields.Many2one('res.partner', string='Address')



class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    address_id = fields.Many2one('res.partner', string='Address')