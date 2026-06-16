# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Extend res.partner for Logspace Provider management"""
    _inherit = 'res.partner'

    # =========================================================================
    # Provider Identification
    # =========================================================================
    is_provider = fields.Boolean(
        string='Is Logspace Provider',
        default=False,
        help='Check this if this contact is a Logspace logistics provider'
    )
    is_approved_provider = fields.Boolean(
        string='Approved Provider',
        default=False,
        help='Automatically set when provider is approved'
    )

    # =========================================================================
    # Provider State Workflow
    # =========================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ], string='Provider Status', default='draft', tracking=True,
       help='Provider workflow state')

    # =========================================================================
    # Business Information (visible if is_provider)
    # =========================================================================
    tax_id = fields.Char(
        string='Tax ID / EIN',
        tracking=True,
        help='Tax Identification Number or Employer Identification Number'
    )
    cr_number = fields.Char(
        string='CR Number',
        tracking=True,
        help='Commercial Registration Number'
    )
    years_experience = fields.Selection([
        ('less_1', 'Less than 1 year'),
        ('1_2', '1-2 years'),
        ('3_5', '3-5 years'),
        ('5_10', '5-10 years'),
        ('more_10', 'More than 10 years'),
    ], string='Years of Experience', default='3_5',
       help='Years of logistics experience')

    # =========================================================================
    # Financial & Workflow
    # =========================================================================
    platform_fee_percentage = fields.Float(
        string='Platform Fee (%)',
        default=0.1,
        tracking=True,
        help='Percentage taken by the platform per booking (0.1 = 10%)'
    )
    approval_date = fields.Date(
        string='Approval Date',
        tracking=True
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        help='Reason for provider rejection'
    )
    suspension_reason = fields.Text(
        string='Suspension Reason',
        help='Reason for provider suspension'
    )

    # =========================================================================
    # Working Schedule (uses Odoo resource.calendar)
    # =========================================================================
    calendar_id = fields.Many2one(
        'resource.calendar',
        string='Working Hours',
        help='Provider working days and hours. Vehicles are only searchable on working days.'
    )

    # =========================================================================
    # Related Records
    # =========================================================================
    # Fleet Summary - counts per vehicle type
    fleet_summary_ids = fields.One2many(
        'logspace.provider.fleet.summary',
        'partner_id',
        string='Fleet Summary',
        help='Fleet capacity by vehicle type'
    )
    # Available time frames per vehicle type
    time_frame_ids = fields.One2many(
        'logspace.provider.time.frame',
        'partner_id',
        string='Available Time Frames',
        help='Pickup and dropoff time slots offered by this provider'
    )
    # Special instructions per vehicle type
    special_instruction_ids = fields.One2many(
        'logspace.provider.special.instruction',
        'partner_id',
        string='Special Instructions',
        help='Instructions for customers per vehicle type'
    )
    # Vehicles owned by this provider
    logspace_vehicle_ids = fields.One2many(
        'logspace.vehicle',
        'provider_id',
        string='Vehicles'
    )
    # Pricing matrix entries
    logspace_price_matrix_ids = fields.One2many(
        'logspace.price.matrix',
        'provider_id',
        string='Price Matrix'
    )
    # Vehicle type add-ons
    vehicle_type_addon_ids = fields.One2many(
        'logspace.provider.vehicle.type.addon',
        'provider_id',
        string='Vehicle Type Add-ons'
    )

    # =========================================================================
    # Computed Fields
    # =========================================================================
    logspace_vehicle_count = fields.Integer(
        string='Vehicle Count',
        compute='_compute_logspace_vehicle_count',
        store=True
    )
    logspace_rating = fields.Float(
        string='Average Rating',
        compute='_compute_logspace_rating',
        store=True,
        digits=(2, 1)
    )
    logspace_review_count = fields.Integer(
        string='Review Count',
        compute='_compute_logspace_rating',
        store=True
    )

    # =========================================================================
    # Compute Methods
    # =========================================================================
    @api.depends('logspace_vehicle_ids')
    def _compute_logspace_vehicle_count(self):
        for partner in self:
            partner.logspace_vehicle_count = len(partner.logspace_vehicle_ids)

    @api.depends('logspace_vehicle_ids')
    def _compute_logspace_rating(self):
        rating_model = self.env.get('logspace.rating')
        if not rating_model:
            for partner in self:
                partner.logspace_rating = 0.0
                partner.logspace_review_count = 0
            return

        for partner in self:
            ratings = rating_model.search([
                ('provider_id', '=', partner.id),
                ('is_published', '=', True)
            ])
            if ratings:
                partner.logspace_rating = sum(r.overall_rating for r in ratings) / len(ratings)
                partner.logspace_review_count = len(ratings)
            else:
                partner.logspace_rating = 0.0
                partner.logspace_review_count = 0

    # =========================================================================
    # Workflow Actions
    # =========================================================================
    def action_submit_provider(self):
        """Submit provider for approval"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'draft':
                raise UserError(_('Only draft providers can be submitted.'))
            if not partner.logspace_vehicle_ids:
                raise UserError(_('At least one vehicle is required.'))
            partner.state = 'pending'

    def action_approve_provider(self):
        """Approve the provider and create portal user"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'pending':
                raise UserError(_('Only pending providers can be approved.'))

            # Create portal user if not exists
            existing_user = self.env['res.users'].sudo().search([
                ('login', '=', partner.email)
            ], limit=1) if partner.email else False

            if existing_user:
                # Link existing user to this partner
                if existing_user.partner_id != partner:
                    existing_user.write({'partner_id': partner.id})
            else:
                # Create new internal user for provider
                # Get the internal user group
                group_user = self.env.ref('base.group_user')
                group_partner_manager = self.env.ref('base.group_partner_manager')
                group_logspace_provider = self.env.ref('appness_logspace_mockup2.group_logspace_provider')
                group_sale_salesman = self.env.ref('sales_team.group_sale_salesman')

                user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
                    'name': partner.name,
                    'login': partner.email or f"provider_{partner.id}",
                    'email': partner.email,
                    'partner_id': partner.id,
                    'group_ids': [Command.set([group_user.id, group_partner_manager.id, group_logspace_provider.id, group_sale_salesman.id])],
                })
                # user.write({
                #     'group_ids': [Command.set([group_user.id, group_partner_manager.id])],
                # })
                # Send welcome/set password email
                user.action_reset_password()

            partner.write({
                'state': 'approved',
                'is_approved_provider': True,
                'approval_date': fields.Date.today(),
            })

            # Send approval email
            try:
                template = self.env.ref('appness_logspace_mockup2.email_template_provider_approved')
                if template:
                    template.send_mail(partner.id, force_send=True)
            except Exception:
                pass  # Don't fail if email sending fails

    def action_reject_provider(self, reason=None):
        """Reject provider application"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'pending':
                raise UserError(_('Only pending providers can be rejected.'))
            partner.write({
                'state': 'rejected',
                'rejection_reason': reason or '',
            })

    def action_resubmit_provider(self):
        """Resubmit rejected provider"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'rejected':
                raise UserError(_('Only rejected providers can be resubmitted.'))
            partner.state = 'draft'

    def action_suspend_provider(self, reason=None):
        """Suspend approved provider"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'approved':
                raise UserError(_('Only approved providers can be suspended.'))
            partner.write({
                'state': 'suspended',
                'suspension_reason': reason or '',
            })

    def action_reactivate_provider(self):
        """Reactivate suspended provider"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'suspended':
                raise UserError(_('Only suspended providers can be reactivated.'))
            partner.state = 'approved'

    def action_download_vehicles_excel(self):
        """Download vehicles as Excel file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/logspace/provider/{self.id}/vehicles/export',
        }
