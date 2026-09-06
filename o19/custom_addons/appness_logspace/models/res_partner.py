# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import UserError


class ResPartner(models.Model):
    """Extend res.partner for Logspace Provider management"""
    _inherit = 'res.partner'

    # =========================================================================
    # Portal: Allow timezone editing from the portal profile
    # =========================================================================
    @api.model
    def _get_frontend_writable_fields(self):
        writable = super()._get_frontend_writable_fields()
        writable.add('tz')
        return writable

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
    logspace_fleet_summary_count = fields.Integer(
        string='Fleet Summary Count',
        compute='_compute_logspace_sub_counts',
        store=True
    )
    logspace_price_matrix_count = fields.Integer(
        string='Price Matrix Count',
        compute='_compute_logspace_sub_counts',
        store=True
    )
    logspace_time_frame_count = fields.Integer(
        string='Time Frame Count',
        compute='_compute_logspace_sub_counts',
        store=True
    )
    logspace_special_instruction_count = fields.Integer(
        string='Special Instruction Count',
        compute='_compute_logspace_sub_counts',
        store=True
    )
    logspace_vtype_addon_count = fields.Integer(
        string='Vehicle Type Add-on Count',
        compute='_compute_logspace_sub_counts',
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

    @api.depends('fleet_summary_ids', 'logspace_price_matrix_ids', 'time_frame_ids',
                 'special_instruction_ids', 'vehicle_type_addon_ids')
    def _compute_logspace_sub_counts(self):
        for partner in self:
            partner.logspace_fleet_summary_count = len(partner.fleet_summary_ids)
            partner.logspace_price_matrix_count = len(partner.logspace_price_matrix_ids)
            partner.logspace_time_frame_count = len(partner.time_frame_ids)
            partner.logspace_special_instruction_count = len(partner.special_instruction_ids)
            partner.logspace_vtype_addon_count = len(partner.vehicle_type_addon_ids)

    def _compute_logspace_rating(self):
        """Compute provider rating from sale.order logspace_customer_rating field.
        Triggered manually from sale.order.write() when rating changes.
        """
        for partner in self:
            if not partner.is_provider:
                partner.logspace_rating = 0.0
                partner.logspace_review_count = 0
                continue
            rated_orders = self.env['sale.order'].sudo().search([
                ('logspace_provider_id', '=', partner.id),
                ('logspace_customer_rating', '>', 0),
            ])
            if rated_orders:
                partner.logspace_rating = sum(o.logspace_customer_rating for o in rated_orders) / len(rated_orders)
                partner.logspace_review_count = len(rated_orders)
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
        """Approve the provider: create user account then update state."""
        providers = self.filtered(lambda p: p.is_provider)
        for partner in providers:
            if partner.state != 'pending':
                raise UserError(_('Only pending providers can be approved.'))

        # Create user accounts (reuses the same logic as the standalone action)
        providers.action_create_provider_user()

        # Update state and send approval email
        for partner in providers:
            partner.write({
                'state': 'approved',
                'is_approved_provider': True,
                'approval_date': fields.Date.today(),
            })

            try:
                template = self.env.ref('appness_logspace.email_template_provider_approved')
                if template:
                    template.send_mail(partner.id, force_send=True)
            except Exception:
                pass

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
        """Suspend approved provider — warns if orders are in progress"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'approved':
                raise UserError(_('Only approved providers can be suspended.'))

            # Check for in-progress orders assigned to this provider
            in_progress_states = [
                'order_received', 'pickup_started', 'vendor_arrived_pickup',
                'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
                'arrived_destination',
            ]
            active_orders = self.env['sale.order'].sudo().search([
                ('is_logspace_order', '=', True),
                ('logspace_provider_id', '=', partner.id),
                ('logspace_state', 'in', in_progress_states),
            ])

            if active_orders:
                order_list = '\n'.join(
                    '  • %s — %s (state: %s)' % (
                        o.name,
                        o.pickup_address or 'No address',
                        dict(o._fields['logspace_state'].selection).get(o.logspace_state, o.logspace_state),
                    )
                    for o in active_orders
                )
                raise UserError(_(
                    'This provider has %d order(s) currently in progress:\n\n%s\n\n'
                    'Suspending will block the provider from logging in and accessing their account.\n'
                    'Consider waiting until these orders are completed, or reassign them first.'
                ) % (len(active_orders), order_list))

            # Archive the user account to free up license and force logout
            if partner.email:
                linked_user = self.env['res.users'].with_context(active_test=False).sudo().search([
                    ('login', '=', partner.email),
                ], limit=1)
                if linked_user:
                    linked_user.active = False

            partner.write({
                'state': 'suspended',
                'suspension_reason': reason or '',
            })

    def action_reactivate_provider(self):
        """Reactivate suspended provider and send new login invitation"""
        for partner in self.filtered(lambda p: p.is_provider):
            if partner.state != 'suspended':
                raise UserError(_('Only suspended providers can be reactivated.'))

            if not partner.email:
                raise UserError(_('Provider must have an email to reactivate.'))

            # Check if user exists and reactivate, or create new user
            existing_user = self.env['res.users'].with_context(active_test=False).sudo().search([
                ('login', '=', partner.email),
            ], limit=1)

            if existing_user and not existing_user.active:
                # Reactivate archived user
                existing_user.active = True
                existing_user.action_reset_password()
            elif existing_user and existing_user.active:
                # User already active, just send password reset
                existing_user.action_reset_password()
            else:
                # Create new user (reuse approve logic)
                group_logspace_provider = self.env.ref('appness_logspace.group_logspace_provider')
                user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
                    'name': partner.name,
                    'login': partner.email,
                    'email': partner.email,
                    'partner_id': partner.id,
                    'group_ids': [Command.set([group_logspace_provider.id])],
                })
                user.action_reset_password()

            partner.write({
                'state': 'approved',
                'is_approved_provider': True,
            })
            # Recompute partner_share after user reactivation/creation
            self.env.add_todo(partner._fields['partner_share'], partner)
        self.env.flush_all()

    def action_create_provider_user(self):
        """Create an internal user with provider access without changing state.

        Unlike action_approve_provider, this does NOT approve the provider.
        It only creates (or links) an internal user with the Provider group
        so the provider can log in to the backend.
        Useful for demo data or when approval was done without user creation.
        """
        for partner in self.filtered(lambda p: p.is_provider):
            if not partner.email:
                raise UserError(_('Provider must have an email to create a user account.'))

            existing_user = self.env['res.users'].with_context(active_test=False).sudo().search([
                ('login', '=', partner.email),
            ], limit=1)

            if existing_user:
                # Link existing user and ensure provider group
                group_logspace_provider = self.env.ref('appness_logspace.group_logspace_provider')
                vals = {'partner_id': partner.id}
                if group_logspace_provider not in existing_user.groups_id:
                    vals['groups_id'] = existing_user.groups_id | group_logspace_provider
                existing_user.write(vals)
                if not existing_user.active:
                    existing_user.active = True
                existing_user.action_reset_password()
            else:
                group_logspace_provider = self.env.ref('appness_logspace.group_logspace_provider')
                user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
                    'name': partner.name,
                    'login': partner.email,
                    'email': partner.email,
                    'partner_id': partner.id,
                    'group_ids': [Command.set([group_logspace_provider.id])],
                })
                user.action_reset_password()

            # Recompute partner_share: now that an internal user is linked,
            # partner_share must become False so the global "res.partner company"
            # record rule allows write access on this partner.
            self.env.add_todo(partner._fields['partner_share'], partner)
        self.env.flush_all()

    # =========================================================================
    # Smart Button Actions
    # =========================================================================
    def action_open_vehicles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicles'),
            'res_model': 'logspace.vehicle',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }

    def action_open_fleet_summary(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fleet Summary'),
            'res_model': 'logspace.provider.fleet.summary',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_open_price_matrix(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Price Matrix'),
            'res_model': 'logspace.price.matrix',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }

    def action_open_time_frames(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Time Frames'),
            'res_model': 'logspace.provider.time.frame',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_open_special_instructions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Special Instructions'),
            'res_model': 'logspace.provider.special.instruction',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }

    def action_open_vtype_addons(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicle Type Add-ons'),
            'res_model': 'logspace.provider.vehicle.type.addon',
            'view_mode': 'list,form',
            'domain': [('provider_id', '=', self.id)],
            'context': {'default_provider_id': self.id},
        }

    def action_download_vehicles_excel(self):
        """Download vehicles as Excel file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/logspace/provider/{self.id}/vehicles/export',
        }
