from odoo import api, fields, models


class ApprovalCategory(models.Model):
    _inherit = "approval.category"

    approval_type = fields.Selection(selection_add=[("grade_sample", "Grade Sample")])

    @api.onchange("approval_type")
    def _onchange_approval_type(self):
        # Grade Sample requests carry their own Mining Location m2o;
        # the base char location would be redundant.
        if self.approval_type == "grade_sample":
            self.has_location = "no"
