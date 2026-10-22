from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_grade_tracked = fields.Boolean(
        string="Track by Grade",
        help="Enable mining grade tracking (Mining Location, Level, Average Grade, "
             "Grade Tier, Gold Content) for this product. Requires lot or serial tracking.",
    )

    @api.constrains("tracking", "is_grade_tracked")
    def _check_grade_tracking(self):
        for product in self:
            if product.is_grade_tracked and product.tracking == "none":
                raise ValidationError(
                    _("Product %s requires lot or serial tracking to track by grade.")
                    % product.display_name
                )
