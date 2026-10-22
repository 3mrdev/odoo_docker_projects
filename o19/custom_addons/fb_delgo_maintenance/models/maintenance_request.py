from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    # Fields that stay editable once the request reached a done stage.
    CLOSED_WRITE_WHITELIST = {
        'description',
        'instruction_type',
        'instruction_pdf',
        'instruction_google_slide',
        'instruction_text',
        # Status housekeeping done by the core Cancel button.
        'archive',
        'recurring_maintenance',
    }
    # Dates reserved to group_maintenance_schedule_edit on open requests.
    SCHEDULE_FIELDS = {'schedule_date', 'schedule_end', 'close_date'}

    request_code = fields.Char(
        string='Request Reference', readonly=True, copy=False,
        index='btree_not_null',
        help="Reference generated from the maintenance team code, e.g. ELEC/2026/0001.")
    next_stage_id = fields.Many2one(
        'maintenance.stage', string='Next Stage', compute='_compute_stage_navigation')
    previous_stage_id = fields.Many2one(
        'maintenance.stage', string='Previous Stage', compute='_compute_stage_navigation')
    maintenance_category_id = fields.Many2one(
        'maintenance.request.category', string='Maintenance Category',
        index='btree_not_null', check_company=True, tracking=True,
        help="Extra categorization level of the maintenance request.")
    approval_request_ids = fields.One2many(
        'approval.request', 'maintenance_request_id', string='Approval Requests')
    approval_request_count = fields.Integer(
        string='Approvals Count', compute='_compute_approval_request_count')
    can_edit_schedule_fields = fields.Boolean(
        compute='_compute_can_edit_schedule_fields')

    # -------------------------------------------------------------
    # Computes
    # -------------------------------------------------------------
    @api.depends('stage_id')
    def _compute_stage_navigation(self):
        stages = self.env['maintenance.stage'].search([], order='sequence, id')
        stage_pos = {stage.id: idx for idx, stage in enumerate(stages)}
        for request in self:
            request.next_stage_id = False
            request.previous_stage_id = False
            if not request.stage_id:
                continue
            idx = stage_pos.get(request.stage_id.id)
            if idx is None:
                continue
            # No reopening from the UI once the request reached a done stage.
            if request.stage_id.done:
                continue
            if idx > 0:
                request.previous_stage_id = stages[idx - 1]
            if idx + 1 < len(stages):
                request.next_stage_id = stages[idx + 1]

    @api.depends('approval_request_ids')
    def _compute_approval_request_count(self):
        for request in self:
            request.approval_request_count = len(request.approval_request_ids)

    @api.depends_context('uid')
    def _compute_can_edit_schedule_fields(self):
        has_group = self.env.user.has_group(
            'fb_delgo_maintenance.group_maintenance_schedule_edit')
        for request in self:
            request.can_edit_schedule_fields = has_group or self.env.su

    @api.depends('name', 'request_code')
    def _compute_display_name(self):
        """Always show request code in display name when available."""
        requests_without_code = self.env['maintenance.request']
        for request in self:
            if request.request_code:
                request.display_name = f"{request.request_code}-{request.name}"
            else:
                requests_without_code |= request
        
        if requests_without_code:
            super(MaintenanceRequest, requests_without_code)._compute_display_name()

    # -------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_schedule_rights(vals)
        requests = super().create(vals_list)
        for request in requests.filtered(lambda r: not r.request_code):
            sequence = request.maintenance_team_id.sequence_id
            if sequence:
                request.request_code = sequence.next_by_id()
        return requests

    def write(self, vals):
        self._check_locked_writes(vals)
        self._check_schedule_rights(vals)
        # The core write() force-updates close_date on every stage move (today
        # when the new stage is done, False otherwise) and copies recurring
        # requests. Flag the context so those internal follow-up writes skip
        # the checks, which already ran on the initiating values above.
        stage_done = (
            'stage_id' in vals
            and self.env['maintenance.stage'].browse(vals['stage_id']).done
        )
        manual_close_dates = {}
        if stage_done:
            # A close date set manually or in this same call must survive the
            # core's automatic stamping.
            manual_close_dates = {
                request.id: vals['close_date'] if 'close_date' in vals else request.close_date
                for request in self if request.close_date or 'close_date' in vals
            }
        self = self.with_context(delgo_stage_move=True)
        res = super().write(vals)
        for request_id, close_date in manual_close_dates.items():
            request = self.browse(request_id)
            if request.close_date != close_date:
                request.write({'close_date': close_date})
        return res

    def reset_equipment_request(self):
        # Reopening a cancelled request bypasses the done-stage lock.
        return super(
            MaintenanceRequest, self.with_context(bypass_delgo_lock=True)
        ).reset_equipment_request()

    # -------------------------------------------------------------
    # Stage navigation buttons
    # -------------------------------------------------------------
    def button_next_stage(self):
        for request in self.filtered(lambda r: r.next_stage_id):
            request.stage_id = request.next_stage_id

    def button_previous_stage(self):
        for request in self.filtered(lambda r: r.previous_stage_id):
            request.stage_id = request.previous_stage_id

    # -------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------
    def action_view_approval_requests(self):
        self.ensure_one()
        return {
            'name': _('Approval Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'view_mode': 'list,form',
            'domain': [('maintenance_request_id', '=', self.id)],
            'context': {'default_maintenance_request_id': self.id},
        }

    def action_open_spare_parts_wizard(self):
        """Open the spare-parts wizard (type picked by the header button)."""
        self.ensure_one()
        approval_type = self.env.context.get('default_approval_type')
        return {
            'name': _('Request Spare Parts'),
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.spare.parts.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_maintenance_request_id': self.id,
                'default_approval_type': approval_type or 'stock_material_purchase',
            },
        }

    # -------------------------------------------------------------
    # Checks
    # -------------------------------------------------------------
    def _check_locked_writes(self, vals):
        """Lock closed requests: only notes and instructions stay editable."""
        if (
            self.env.su
            or self.env.context.get('bypass_delgo_lock')
            or self.env.context.get('delgo_stage_move')
        ):
            return
        disallowed = set(vals) - self.CLOSED_WRITE_WHITELIST
        if not disallowed:
            return
        locked = self.filtered(lambda r: r.stage_id.done)
        if locked:
            raise UserError(_(
                "The maintenance request(s) %(requests)s are closed: "
                "only the notes and the instructions can still be updated.",
                requests=', '.join(locked.mapped('request_code') or locked.mapped('display_name')),
            ))

    def _check_schedule_rights(self, vals):
        """Only the dedicated group may update the scheduled/closing dates."""
        if not self.SCHEDULE_FIELDS.intersection(vals):
            return
        if (
            self.env.su
            or self.env.context.get('bypass_delgo_lock')
            or self.env.context.get('delgo_stage_move')
        ):
            return
        if not self.env.user.has_group('fb_delgo_maintenance.group_maintenance_schedule_edit'):
            raise UserError(_(
                "Only members of the group \"Edit Scheduled Dates\" can update "
                "the scheduled or closing dates of a maintenance request."))
