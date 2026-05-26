# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LogspaceProvider(models.Model):
    """Logspace Provider - Logistics Service Provider with Approval Workflow"""
    _name = 'logspace.provider'
    _description = 'Logspace Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Info
    name = fields.Char(string='Provider Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Contact',
                                  help='Linked contact record for address/phone',
                                  ondelete='restrict')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ], string='Status', default='draft', required=True, tracking=True,
       index=True)

    # Business Info
    tax_id = fields.Char(string='Tax ID / EIN', tracking=True)
    cr_number = fields.Char(string='CR Number', tracking=True, help='Commercial Registration Number')
    website = fields.Char(string='Website')
    years_experience = fields.Selection([
        ('less_1', 'Less than 1 year'),
        ('1_2', '1-2 years'),
        ('3_5', '3-5 years'),
        ('5_10', '5-10 years'),
        ('more_10', 'More than 10 years'),
    ], string='Years of Experience', default='3_5')
    is_verified = fields.Boolean(string='Verified', default=False,
                                  tracking=True)
    platform_fee_percentage = fields.Float(string='Platform Fee (%)', default=0.1,
                                           tracking=True, help='Percentage taken by the platform per booking')

    # Workflow Dates
    approval_date = fields.Date(string='Approval Date', tracking=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    suspension_reason = fields.Text(string='Suspension Reason')

    # Workflow Dates

    # Related Records
    vehicle_ids = fields.One2many('logspace.vehicle', 'provider_id',
                                     string='Vehicles')
    price_matrix_ids = fields.One2many('logspace.price.matrix', 'provider_id',
                                       string='Price Matrix')
    # Note: Vehicle type add-ons now managed via res.partner model

    # Computed Fields
    vehicle_count = fields.Integer(string='Vehicle Count',
                                    compute='_compute_vehicle_count',
                                    store=True)
    active_order_count = fields.Integer(string='Active Orders',
                                         compute='_compute_order_counts')
    rating = fields.Float(string='Average Rating', compute='_compute_rating',
                          store=True, digits=(2, 1))
    review_count = fields.Integer(string='Review Count',
                                   compute='_compute_rating', store=True)

    # Contact Fields (synced from partner or standalone)
    phone = fields.Char(string='Phone', related='partner_id.phone',
                        readonly=False, store=True)
    email = fields.Char(string='Email', related='partner_id.email',
                        readonly=False, store=True)
    street = fields.Char(string='Street', related='partner_id.street',
                         readonly=False, store=True)
    city = fields.Char(string='City', related='partner_id.city',
                       readonly=False, store=True)
    country_id = fields.Many2one('res.country',
                                  related='partner_id.country_id',
                                  readonly=False, store=True)
    image = fields.Binary("Image")

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        for provider in self:
            provider.vehicle_count = len(provider.vehicle_ids)

    def _compute_order_counts(self):
        # Will be implemented when orders are created
        for provider in self:
            provider.active_order_count = 0

    @api.depends('vehicle_ids')
    def _compute_rating(self):
        for provider in self:
            ratings = self.env['logspace.rating'].search([
                ('provider_id', '=', provider.id),
                ('is_published', '=', True)
            ])
            if ratings:
                provider.rating = sum(r.overall_rating for r in ratings) / len(ratings)
                provider.review_count = len(ratings)
            else:
                provider.rating = 0.0
                provider.review_count = 0

    # Workflow Actions
    def action_submit(self):
        """Submit provider for approval"""
        for provider in self:
            if provider.state != 'draft':
                raise UserError(_('Only draft providers can be submitted.'))
            if not provider.vehicle_ids:
                raise UserError(_('At least one vehicle is required.'))
            provider.state = 'pending'

    def action_approve(self):
        """Approve the provider"""
        for provider in self:
            if provider.state != 'pending':
                raise UserError(_('Only pending providers can be approved.'))
            provider.write({
                'state': 'approved',
                'approval_date': fields.Date.today(),
                'is_verified': True,
            })

    def action_reject(self, reason=None):
        """Reject the provider"""
        for provider in self:
            if provider.state != 'pending':
                raise UserError(_('Only pending providers can be rejected.'))
            provider.write({
                'state': 'rejected',
                'rejection_reason': reason or '',
            })

    def action_resubmit(self):
        """Resubmit rejected provider"""
        for provider in self:
            if provider.state != 'rejected':
                raise UserError(_('Only rejected providers can be resubmitted.'))
            provider.state = 'draft'

    def action_suspend(self, reason=None):
        """Suspend an approved provider"""
        for provider in self:
            if provider.state != 'approved':
                raise UserError(_('Only approved providers can be suspended.'))
            provider.write({
                'state': 'suspended',
                'suspension_reason': reason or '',
            })

    def action_reactivate(self):
        """Reactivate suspended provider"""
        for provider in self:
            if provider.state != 'suspended':
                raise UserError(_('Only suspended providers can be reactivated.'))
            provider.state = 'approved'

    def action_download_vehicles_excel(self):
        """Download vehicles as Excel file"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/logspace/provider/{self.id}/vehicles/export',
        }

    # def _get_vehicles_excel(self):
    #     """Generate Excel file with vehicles data"""
    #     self.ensure_one()
    #     workbook = openpyxl.Workbook()
    #     sheet = workbook.active
    #     sheet.title = 'Vehicles'
        
    #     # Header row
    #     header = ['Vehicle ID', 'Registration Number', 'Type', 'Year', 'Status']
    #     sheet.append(header)
        
    #     # Vehicle data
    #     for vehicle in self.vehicle_ids:
    #         sheet.append([
    #             vehicle.id,
    #             vehicle.registration_number,
    #             vehicle.vehicle_type_id.name,
    #             vehicle.year,
    #             vehicle.state,
    #         ])
        
    #     # Save to bytes
    #     output = io.BytesIO()
    #     workbook.save(output)
    #     output.seek(0)
    #     return output.getvalue()

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-create partner if not provided"""
        for vals in vals_list:
            if not vals.get('partner_id'):
                partner_vals = {
                    'name': vals.get('name'),
                    'phone': vals.get('phone'),
                    'email': vals.get('email'),
                    'email': vals.get('email'),
                }
                partner = self.env['res.partner'].create(partner_vals)
                vals['partner_id'] = partner.id
        return super(LogspaceProvider, self).create(vals_list)
