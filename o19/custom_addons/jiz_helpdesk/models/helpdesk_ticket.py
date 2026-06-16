# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from . import helpers

class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _inherit = ['helpdesk.ticket', 'documents.mixin']
    _description = "Helpdesk Ticket"

    amount = fields.Float(string='Amount Requested')
    date = fields.Date(string='Date', default=fields.Date.today)
    noti_documents = fields.Text()

    evaluation_ids = fields.One2many('jiz.evaluation', 'ticket_id', string='Evaluations')
    total_evaluation_score = fields.Float(string='Total Evaluation Score', compute='_compute_total_evaluation_score', store=True)
    evaluation_score_percentage = fields.Float(string='Evaluation Score Percentage', compute='_compute_evaluation_score_percentage', store=True)
    evaluation_score_percentage_total = fields.Float(string='Evaluation Score Percentage Total', compute='_compute_evaluation_score_percentage', store=True)

    team_action_on_acceptance = fields.Selection(related='team_id.action_on_acceptance', readonly=True)
    project_id = fields.Many2one('project.project', string='Project', readonly=True)
    event_id = fields.Many2one('event.event', string='Event', readonly=True)
    bill_id = fields.Many2one('account.move', string='Vendor Bill', readonly=True)

    project_count = fields.Integer(string='Project Count', compute='_compute_linked_record_counts', store=True)
    event_count = fields.Integer(string='Event Count', compute='_compute_linked_record_counts', store=True)
    bill_count = fields.Integer(string='Bill Count', compute='_compute_linked_record_counts', store=True)

    show_submit_button = fields.Boolean(compute='_compute_show_buttons')
    show_accept_button = fields.Boolean(compute='_compute_show_buttons')
    show_reject_button = fields.Boolean(compute='_compute_show_buttons')
    show_hold_button = fields.Boolean(compute='_compute_show_buttons')
    show_reset_to_draft_button = fields.Boolean(compute='_compute_show_buttons')
    document_count = fields.Integer(compute='_compute_document_count', string='Documents', store=True)
    documents = fields.One2many('documents.document', 'ataa_id', string='Documents')

    is_draft_stage = fields.Boolean(compute='_compute_is_draft_stage', store=True)
    is_evaluation_stage = fields.Boolean(compute='_compute_is_evaluation_stage', store=True)

    @api.depends('stage_id')
    def _compute_is_draft_stage(self):
        for ticket in self:
            ticket.is_draft_stage = ticket.stage_id == ticket.team_id.draft_stage_id

    @api.depends('stage_id')
    def _compute_is_evaluation_stage(self):
        for ticket in self:
            ticket.is_evaluation_stage = ticket.stage_id == ticket.team_id.evaluation_stage_id

    @api.depends('project_id','event_id','bill_id')
    def _compute_linked_record_counts(self):
        for ticket in self:
            ticket.project_count = 1 if ticket.project_id else 0
            ticket.event_count = 1 if ticket.event_id else 0
            ticket.bill_count = 1 if ticket.bill_id else 0

    def action_view_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Project',
            'res_model': 'project.project',
            'view_mode': 'form',
            'res_id': self.project_id.id,
        }

    def action_view_event(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Event',
            'res_model': 'event.event',
            'view_mode': 'form',
            'res_id': self.event_id.id,
        }

    def action_view_bill(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vendor Bill',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
        }

    @api.constrains('document_count','stage_id')
    def check_documents(self):
        for rec in self:
            vdoc = helpers.validate_documents(self)
            if vdoc['types']:
                rec.noti_documents = _("Missing Documents:")+f""" \n{vdoc['types']}"""
            else:
                rec.noti_documents = False
    
    @api.depends('documents')
    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.documents)

    def _get_document_folder(self):
        return self.company_id.documents_ataa_folder

    def _get_document_tags(self):
        return self.company_id.documents_ataa_tags

    def _check_create_documents(self):
        return self.company_id.documents_ataa_settings and super()._check_create_documents()

    def action_open_attachments(self):
        self.ensure_one()
        if not self.company_id.documents_ataa_settings:
            return True
        ataa_folder = self._get_document_folder()
        ataa_tags = self._get_document_tags()
        action = self.env['ir.actions.act_window']._for_xml_id('documents.document_action')
        action['domain'] = [
            '|',
                ('type', '=', 'folder'),
                '&',
                    ('res_model', '=', self._name),
                    ('res_id', '=', self.id),
        ]
        action['context'] = {
            'default_res_id': self.id,
            'default_res_model': self._name,
            'searchpanel_default_folder_id': ataa_folder.id,
            'searchpanel_default_tag_ids': ataa_tags.ids,
        }
        return action

    @api.depends('stage_id', 'team_id.draft_stage_id', 'team_id.evaluation_stage_id', 'team_id.accepted_stage_id', 'team_id.rejected_stage_id', 'team_id.on_hold_stage_id')
    def _compute_show_buttons(self):
        for ticket in self:
            ticket.show_submit_button = ticket.stage_id == ticket.team_id.draft_stage_id and ticket.team_action_on_acceptance
            ticket.show_accept_button = ticket.stage_id == ticket.team_id.evaluation_stage_id and ticket.team_action_on_acceptance
            ticket.show_reject_button = ticket.stage_id == ticket.team_id.evaluation_stage_id and ticket.team_action_on_acceptance
            ticket.show_hold_button = ticket.stage_id == ticket.team_id.evaluation_stage_id and ticket.team_action_on_acceptance
            ticket.show_reset_to_draft_button = ticket.stage_id in (ticket.team_id.accepted_stage_id, ticket.team_id.rejected_stage_id, ticket.team_id.on_hold_stage_id) and ticket.team_action_on_acceptance

    @api.depends('evaluation_ids.category_score')
    def _compute_total_evaluation_score(self):
        for ticket in self:
            total_evaluation_score = 0

            standards = self.env['jiz.standard'].search([])
            for standard in standards:
                category_metrics = ticket.evaluation_ids.filtered(lambda x: x.standard_id == standard)
                if category_metrics:
                    total_evaluation_score += sum(category_metrics.mapped('category_score'))
            
            ticket.total_evaluation_score = total_evaluation_score

    @api.depends('total_evaluation_score')
    def _compute_evaluation_score_percentage(self):
        for ticket in self:
            # percentage = (total evaluation score / (sum of standards weight * 5) ) * 100
            standards = self.env['jiz.standard'].search([])
            standards_total_weight = sum(standard.weight for standard in standards)
            ticket.evaluation_score_percentage_total = standards_total_weight * 5
            
            if standards_total_weight == 0:
                ticket.evaluation_score_percentage = 0
            else:
                ticket.evaluation_score_percentage = (ticket.total_evaluation_score / (standards_total_weight * 5)) * 100

    def _create_evaluation_lines(self):
        """Create evaluation lines from all available metrics, grouped by category."""
        self.ensure_one()
        self.evaluation_ids.unlink()
        if not self.evaluation_ids:
            vals_list = []
            standards = self.env['jiz.standard'].search([], order='id')
            for standard in standards:
                vals_list.append({
                    'ticket_id': self.id,
                    'display_type': 'line_section',
                    'name': standard.name,
                })
                for scale in standard.scale_ids:
                    vals_list.append({
                        'ticket_id': self.id,
                        'scale_id': scale.id,
                        'name': scale.name,
                        'scale_weight': scale.evaluation_weight,
                    })
            self.env['jiz.evaluation'].create(vals_list)

    def action_submit_for_evaluation(self):
        self.check_documents()
        if self.team_id.evaluation_stage_id:
            self.stage_id = self.team_id.evaluation_stage_id
            self._create_evaluation_lines()

            if self.amount < 1:
                raise UserError(_("You cannot submit this ataa with a amount of less than one."))

    def action_accept(self):
        vdoc = helpers.validate_documents(self)
        if vdoc['types']:
            raise UserError(_("Missing Documents:")+f""" \n{vdoc['types']}""")
        
        standards = self.env['jiz.standard'].search([])
        for standard in standards:
            total_weight = sum(self.evaluation_ids.filtered(lambda x: x.standard_id == standard).mapped(lambda x: x.scale_weight))
            if total_weight not in (0, 1):
                raise UserError(f"Total weight of metrics inside category {standard.name} must be equal to 1 or 0")
            # if total_weight != 0 and total_weight != 1:
            #     raise UserError("Total weight of metrics inside category " + standard.name + " must be equal to 1")

        if self.team_id.accepted_stage_id:
            self.stage_id = self.team_id.accepted_stage_id
            # Trigger post-acceptance actions based on team settings
            if self.team_id.action_on_acceptance:
                self.team_id.execute_post_acceptance_action(self)

            if self.amount < 1:
                raise UserError(_("You cannot accept this ataa with a amount of less than one."))
            

    def action_reject(self):
        if self.team_id.rejected_stage_id:
            self.stage_id = self.team_id.rejected_stage_id

    def action_hold(self):
        if self.team_id.on_hold_stage_id:
            self.stage_id = self.team_id.on_hold_stage_id

    def action_reset_to_draft(self):
        if self.team_id.draft_stage_id:
            self.stage_id = self.team_id.draft_stage_id
