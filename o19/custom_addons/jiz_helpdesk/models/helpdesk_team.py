# -*- coding: utf-8 -*-

from odoo import models, fields, api

class HelpdeskTeam(models.Model):
    _inherit = 'helpdesk.team'

    action_on_acceptance = fields.Selection([
        ('create_project', 'Create a new Project'),
        ('create_event', 'Create a new Event'),
        ('generate_bill', 'Generate a Vendor Bill')
    ], string='Action on Acceptance')

    project_template_id = fields.Many2one('project.project', string='Project Template',
        help="Select a project template to be used when a new project is created.")
    event_template_id = fields.Many2one('event.type', string='Event Template',
        help="Select an event template to be used when a new event is created.")
    product_id = fields.Many2one('product.product', string='Product',
        help="Select a product to be used when a new bill is created.")

    draft_stage_id = fields.Many2one('helpdesk.stage', string='Draft Stage', domain="[('team_ids', 'in', id)]")
    evaluation_stage_id = fields.Many2one('helpdesk.stage', string='Evaluation Stage', domain="[('team_ids', 'in', id)]")
    accepted_stage_id = fields.Many2one('helpdesk.stage', string='Accepted Stage', domain="[('team_ids', 'in', id)]")
    rejected_stage_id = fields.Many2one('helpdesk.stage', string='Rejected Stage', domain="[('team_ids', 'in', id)]")
    on_hold_stage_id = fields.Many2one('helpdesk.stage', string='On Hold Stage', domain="[('team_ids', 'in', id)]")

    def execute_post_acceptance_action(self, ticket):
        self.ensure_one()
        if self.action_on_acceptance == 'create_project':
            self._create_project_from_ticket(ticket)
        elif self.action_on_acceptance == 'create_event':
            self._create_event_from_ticket(ticket)
        elif self.action_on_acceptance == 'generate_bill':
            self._create_bill_from_ticket(ticket)

    def _create_project_from_ticket(self, ticket):
        if not self.project_template_id:
            return
        project = self.project_template_id.copy({
            'name': f"Ataa: {ticket.name}",
            'partner_id': ticket.partner_id.id,
        })
        project.write({'is_template': False})
        project._create_analytic_account()
        ticket.project_id = project.id
        return project

    def _create_event_from_ticket(self, ticket):
        if not self.event_template_id:
            return
        event = self.env['event.event'].create({
            'name': f"Ataa: {ticket.name}",
            'event_type_id': self.event_template_id.id,
            'organizer_id': ticket.partner_id.id,
        })
        ticket.event_id = event.id
        return event

    def _create_bill_from_ticket(self, ticket):
        # This requires a partner with accounting info.
        if not ticket.partner_id or not ticket.amount or not self.product_id:
            return

        bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': ticket.partner_id.id,
            'team_id': False,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'name': f"Ataa Grant: {ticket.name}",
                'quantity': 1,
                'price_unit': ticket.amount,
            })],
        })
        ticket.bill_id = bill.id
