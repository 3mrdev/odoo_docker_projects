from odoo import models,fields,api,_

class Country(models.Model):
    _inherit = "res.country"

    swms_allow = fields.Boolean()

class State(models.Model):
    _inherit = "res.country.state"

    swms_allow = fields.Boolean()

class City(models.Model):
    _inherit = "res.city"

    swms_allow = fields.Boolean()

class Area(models.Model):
    _name = "swms.area"
    _description = "Area"
    
    name = fields.Char()
    city_id = fields.Many2one("res.city")

class Address(models.Model):
    _name = "swms.address"
    _description = "Address"

    city_ids = fields.Many2many('res.city', string='City',domain="[('country_id', '=?', country_id),('swms_allow','=',True)]")
    state_ids = fields.Many2many("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id),('swms_allow','=',True)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',domain="[('swms_allow','=',True)]")
    service_id = fields.Many2one("product.template")