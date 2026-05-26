from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_flavor_mix = fields.Boolean("Is Mix?")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        result += ['is_flavor_mix']
        return result


class ProductTemplateAttributeLine(models.Model):
    _name = 'product.template.attribute.line'
    _inherit = 'product.template.attribute.line'

    mix_is_active = fields.Boolean("Active in Mix", default=True,
        help="If unchecked, this attribute will not appear in the POS mix popup.")
    mix_max_qty = fields.Integer("Mix Max Qty", default=0,
        help="Maximum number of selections for this attribute in the POS mix popup.")

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        result += ['mix_is_active', 'mix_max_qty']
        return result


class ProductTemplateAttributeValue(models.Model):
    _name = 'product.template.attribute.value'
    _inherit = 'product.template.attribute.value'

    mix_max_value_qty = fields.Integer(
        string="Mix Value Limit",
        default=0,
        help="Maximum times this value can be selected in the POS mix popup. 0 = unlimited."
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        result = super()._load_pos_data_fields(config_id)
        result += ['mix_max_value_qty']
        return result