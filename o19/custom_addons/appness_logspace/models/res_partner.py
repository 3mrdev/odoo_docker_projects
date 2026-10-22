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
    # Driver Identification
    # =========================================================================
    # Set on a *child contact* of a provider. Flipping it on creates a portal
    # (not internal) login for that contact so they can advance the delivery
    # status of the orders they are assigned to from /logspace/driver/orders.
    is_driver = fields.Boolean(
        string='Is Driver',
        default=False,
        help='Check this on a provider contact to give them a driver portal account'
    )
    driver_portal_user_id = fields.Many2one(
        'res.users',
        string='Driver Portal User',
        compute='_compute_driver_portal_user_id',
        help='Portal login linked to this driver contact'
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
    # Driver contacts of this provider (child_ids filtered on is_driver)
    logspace_driver_ids = fields.One2many(
        'res.partner',
        'parent_id',
        string='Drivers',
        domain=[('is_driver', '=', True)],
        context={'default_is_driver': True, 'default_type': 'contact'},
    )
    # Vehicle types the provider can currently price / offer add-ons for:
    # the types of his ACTIVE vehicles. Used as the record-limiting domain on
    # the vehicle-type selectors (price matrix, add-ons, zone setup wizard).
    logspace_active_vehicle_type_ids = fields.Many2many(
        'logspace.vehicle.type',
        compute='_compute_logspace_active_vehicle_type_ids',
        string='Active Vehicle Types',
        help='Vehicle types in which this provider has at least one active vehicle.',
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

    @api.depends('logspace_vehicle_ids.is_active', 'logspace_vehicle_ids.vehicle_type_id')
    def _compute_logspace_active_vehicle_type_ids(self):
        for partner in self:
            partner.logspace_active_vehicle_type_ids = (
                partner.logspace_vehicle_ids.filtered('is_active').mapped('vehicle_type_id')
            )

    @api.depends('fleet_summary_ids', 'logspace_price_matrix_ids', 'time_frame_ids',
                 'special_instruction_ids', 'vehicle_type_addon_ids')
    def _compute_logspace_sub_counts(self):
        for partner in self:
            partner.logspace_fleet_summary_count = len(partner.fleet_summary_ids)
            partner.logspace_price_matrix_count = len(partner.logspace_price_matrix_ids)
            partner.logspace_time_frame_count = len(partner.time_frame_ids)
            partner.logspace_special_instruction_count = len(partner.special_instruction_ids)
            partner.logspace_vtype_addon_count = len(partner.vehicle_type_addon_ids)

    @api.depends('user_ids')
    def _compute_driver_portal_user_id(self):
        driver_group = self.env.ref('appness_logspace.group_logspace_driver', raise_if_not_found=False)
        for partner in self:
            if not partner.is_driver:
                partner.driver_portal_user_id = False
                continue
            users = partner.sudo().user_ids
            if driver_group:
                users = users.filtered(lambda u: driver_group in u.sudo().group_ids)
            partner.driver_portal_user_id = users[:1].id

    @api.constrains('is_driver', 'is_company', 'parent_id')
    def _check_is_driver(self):
        for partner in self.filtered(lambda p: p.is_driver):
            if partner.is_company:
                raise UserError(_('A driver must be an individual contact, not a company.'))
            if not partner.parent_id.is_provider:
                raise UserError(_(
                    'A driver must be a contact of a Logspace provider. '
                    'Set this on a contact inside the provider record.'
                ))

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
    _PROVIDER_ADMIN_ONLY_FIELDS = {
        'state', 'is_provider', 'is_approved_provider', 'approval_date',
        'platform_fee_percentage', 'rejection_reason', 'suspension_reason',
        'tax_id', 'cr_number', 'years_experience',
    }

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        # A contact created directly with is_driver=True (e.g. from the provider's
        # Drivers tab) gets its portal login right away.
        partners.filtered(lambda p: p.is_driver and p.email)._create_driver_portal_user()
        return partners

    def write(self, vals):
        """Guard: provider-group users may not alter provider business/admin
        fields (workflow state, fee, IDs). They can still edit their own
        contact info (name, email, phone, ...) and related records.
        Admins and system users (sudo) bypass this guard.
        """
        protected = self._PROVIDER_ADMIN_ONLY_FIELDS & set(vals)
        if protected and any(p.is_provider for p in self):
            is_admin = (
                self.env.su
                or self.env.user._is_superuser()
                or self.env.user.has_group('base.group_system')
            )
            if not is_admin and self.env.user.has_group('appness_logspace.group_logspace_provider'):
                raise UserError(_(
                    'You are not allowed to modify the following fields: %s.',
                    ', '.join(
                        self._fields[f].get_description(self.env)['string']
                        for f in sorted(protected)
                    ),
                ))
        # Contacts flagged as drivers just now, so we know which ones to provision.
        # The provider guard above does not fire on child contacts (is_provider is
        # False for them), so this write is not blocked.
        newly_drivers = self.browse()
        if vals.get('is_driver'):
            newly_drivers = self.filtered(lambda p: not p.is_driver)
        res = super().write(vals)
        if newly_drivers:
            newly_drivers.filtered(lambda p: p.email)._create_driver_portal_user()
        return res

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
            # sudo: providers may trigger resubmit of their own record, but
            # 'state' itself is an admin-only field (see write guard).
            partner.sudo().state = 'draft'

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
            # partner_share auto-recomputes from user_ids; flush pending computes
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
                if group_logspace_provider not in existing_user.group_ids:
                    vals['group_ids'] = [Command.link(group_logspace_provider.id)]
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

            # partner_share auto-recomputes from user_ids; flush pending computes
        self.env.flush_all()

    def _create_driver_portal_user(self):
        """Create (or link) a PORTAL user for each driver contact.

        Mirrors action_create_provider_user but grants base.group_portal +
        group_logspace_driver instead of base.group_user. The distinction is
        load-bearing: res.users._compute_share marks any user holding
        base.group_user as internal, which would drop the driver into the
        backend rather than the website portal.
        """
        driver_group = self.env.ref('appness_logspace.group_logspace_driver', raise_if_not_found=False)
        portal_group = self.env.ref('base.group_portal')
        if not driver_group:
            return self.env['res.users']

        created = self.env['res.users']
        for partner in self.filtered(lambda p: p.is_driver and p.email):
            existing_user = self.env['res.users'].with_context(active_test=False).sudo().search([
                ('partner_id', '=', partner.id),
            ], limit=1)

            if existing_user:
                existing_user = existing_user.sudo()
                vals = {}
                missing = [g for g in (portal_group, driver_group) if g not in existing_user.group_ids]
                if missing:
                    vals['group_ids'] = [Command.link(g.id) for g in missing]
                if not existing_user.active:
                    vals['active'] = True
                if vals:
                    existing_user.write(vals)
                # An existing internal user must not be silently converted: skip it
                # and let the provider resolve the conflict deliberately.
                if existing_user._is_internal():
                    continue
                existing_user.action_reset_password()
                created |= existing_user
            else:
                user = self.env['res.users'].with_context(no_reset_password=True).sudo().create({
                    'name': partner.name,
                    'login': partner.email,
                    'email': partner.email,
                    'partner_id': partner.id,
                    'group_ids': [Command.set([portal_group.id, driver_group.id])],
                })
                user.action_reset_password()
                created |= user

        self.env.flush_all()
        return created

    def action_create_driver_portal_user(self):
        """Button: provision / re-invite the driver portal account."""
        for partner in self:
            if not partner.is_driver:
                raise UserError(_('Only contacts flagged as drivers can get a driver portal account.'))
            if not partner.email:
                raise UserError(_('The driver must have an email to create a portal account.'))
        self._create_driver_portal_user()
        return True

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
