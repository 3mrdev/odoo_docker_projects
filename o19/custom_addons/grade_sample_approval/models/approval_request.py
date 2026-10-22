from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import clean_context


class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial",
        domain=[("product_id.is_grade_tracked", "=", True)],
        check_company=True,
        copy=False,
    )
    average_grade = fields.Float(string="Average Grade (g/t)")
    # Related values: the sample is applied to ONE lot, so the mining data is
    # the lot's own data, displayed for information only.
    mining_location_id = fields.Many2one(
        "project.project",
        string="Mining Location",
        related="lot_id.mining_location_id",
    )
    mining_level_id = fields.Many2one(
        "grade.mining.level",
        string="Mining Level",
        related="lot_id.mining_level_id",
    )
    grade_applied = fields.Boolean(
        copy=False,
        help="The sample's average grade has been written to the selected lot.",
    )
    grade_lot_count = fields.Integer(
        compute="_compute_grade_lot_count",
    )

    def _compute_grade_lot_count(self):
        for request in self:
            request.grade_lot_count = 1 if request.lot_id else 0

    @api.constrains("category_id")
    def _check_grade_sample_category_access(self):
        if self.env.su:
            return
        for request in self:
            if request.approval_type == "grade_sample" \
                    and not self.env.user.has_group("grade_sample_approval.group_grade_lab_user"):
                raise AccessError(
                    _("Creating Grade Sample requests is reserved to Lab Users."))

    @api.constrains("lot_id", "category_id")
    def _check_grade_sample_lot(self):
        for request in self:
            if request.approval_type == "grade_sample" \
                    and request.lot_id and not request.lot_id.is_grade_tracked:
                raise ValidationError(_("Grade Sample requests only accept grade-tracked lots/serials."))

    def action_confirm(self):
        for request in self:
            if request.approval_type == "grade_sample" and not request.lot_id:
                raise UserError(_("You cannot submit a Grade Sample request without a lot/serial."))
        return super().action_confirm()

    def action_apply_grade(self):
        """Write the sample's average grade onto the selected lot.

        Only available once the request is approved. Applying the grade never
        changes the approval status of the request. The lot write is logged
        in the lot's Grade Change History (grade_tracking).
        """
        for request in self:
            if request.approval_type != "grade_sample":
                raise UserError(_("Apply Grade is only available on Grade Sample requests."))
            if request.request_status != "approved":
                raise UserError(_("The grade can only be applied after the request is approved."))
            if not request.lot_id:
                raise UserError(_("Select the lot/serial to apply the grade to."))
            if not request.average_grade:
                raise UserError(_("Set the average grade of the sample first."))
        if not self.env.su and not self.env.user.has_group("grade_sample_approval.group_grade_lab_manager"):
            raise AccessError(_("Only Lab Managers can apply grades."))
        for request in self:
            # sudo: the lab manager may neither be a stock manager (lot write
            # ACLs) nor the request owner / an approver (request write rules).
            # env.uid is preserved under sudo(), so the Grade Change History
            # still logs the real user.
            request.lot_id.sudo().write({"average_grade": request.average_grade})
            request.sudo().write({"grade_applied": True})
            request.message_post(body=_(
                "Average grade %(grade)s g/t applied to lot %(lot)s.",
                grade=request.average_grade,
                lot=request.lot_id.name,
            ))

    def action_open_grade_lots(self):
        """Open the lot/serial selected (and possibly graded) on this request."""
        self.ensure_one()
        return {
            "name": _("Lot/Serial"),
            "type": "ir.actions.act_window",
            "view_mode": "list,form",
            "res_model": "stock.lot",
            "domain": [("id", "in", self.lot_id.ids)],
            "context": clean_context(self.env.context),
        }
