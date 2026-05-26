# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceRating(models.Model):
    """Logspace Rating - Customer Reviews for Providers"""
    _name = 'logspace.rating'
    _description = 'Logspace Rating'
    _order = 'create_date desc'

    name = fields.Char(string='Rating Reference', compute='_compute_name')
    order_id = fields.Many2one('sale.order', string='Order', required=True,
                                ondelete='cascade', index=True)
    provider_id = fields.Many2one('res.partner',
                                   string='Provider',
                                   related='order_id.logspace_provider_id',
                                   store=True, index=True, readonly=True)
    customer_id = fields.Many2one('res.partner', string='Customer',
                                    related='order_id.partner_id',
                                    store=True, readonly=True)

    # Rating Fields
    overall_rating = fields.Integer(string='Overall Rating', required=True,
                                    help='1-5 stars')
    timeliness_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string='Timeliness', default='good', required=True)
    driver_behavior_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string='Driver Behavior', default='good', required=True)
    vehicle_condition_rating = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('average', 'Average'),
        ('poor', 'Poor'),
    ], string='Vehicle Condition', default='good', required=True)

    comments = fields.Text(string='Comments')
    is_published = fields.Boolean(string='Published on Profile',
                                     default=False,
                                     help='Show on provider public profile')

    # Computed
    average_rating = fields.Float(string='Average',
                                   compute='_compute_average', store=True,
                                   digits=(2, 1))

    @api.depends('overall_rating', 'timeliness_rating',
                 'driver_behavior_rating', 'vehicle_condition_rating')
    def _compute_average(self):
        rating_map = {
            'excellent': 5, 'good': 4, 'average': 3, 'poor': 2
        }
        for rating in self:
            vals = [
                rating.overall_rating,
                rating_map.get(rating.timeliness_rating, 3),
                rating_map.get(rating.driver_behavior_rating, 3),
                rating_map.get(rating.vehicle_condition_rating, 3),
            ]
            rating.average_rating = sum(vals) / len(vals)

    def _compute_name(self):
        for rating in self:
            rating.name = f"Rating: {rating.order_id.name}"

    @api.constrains('overall_rating')
    def _check_overall_rating(self):
        for rating in self:
            if rating.overall_rating < 1 or rating.overall_rating > 5:
                raise models.ValidationError(
                    _('Overall rating must be between 1 and 5.'))
