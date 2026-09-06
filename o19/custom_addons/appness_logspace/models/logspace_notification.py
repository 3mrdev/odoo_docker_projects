# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class LogspaceNotification(models.Model):
    """Logspace Notification - User Notification System"""
    _name = 'logspace.notification'
    _description = 'Logspace User Notification'
    _order = 'create_date desc'

    user_id = fields.Many2one('res.users', string='Recipient',
                                required=True, index=True,
                                ondelete='cascade',
                                default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner', string='Partner',
                                  related='user_id.partner_id',
                                  store=True, readonly=True)

    # Content
    type = fields.Selection([
        ('success', 'Success'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], string='Type', default='info', required=True)
    title = fields.Char(string='Title', required=True)
    message = fields.Text(string='Message', required=True)
    icon = fields.Char(string='Icon Class',
                       help='FontAwesome icon class override')

    # Read Status
    is_read = fields.Boolean(string='Read', default=False, index=True)
    read_date = fields.Datetime(string='Read Date')

    # Action Link
    action_link = fields.Char(string='Action URL',
                              help='Direct URL to navigate when clicked')
    action_model = fields.Char(string='Action Model',
                                help='e.g., sale.order')
    action_res_id = fields.Integer(string='Record ID')

    # System
    create_date = fields.Datetime(string='Created', readonly=True)

    def _get_default_icon(self):
        """Return default icon based on type"""
        icon_map = {
            'success': 'fa-check-circle',
            'info': 'fa-info-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-times-circle',
        }
        return icon_map.get(self.type, 'fa-bell')

    def action_mark_read(self):
        """Mark notification as read"""
        for notif in self:
            notif.write({
                'is_read': True,
                'read_date': fields.Datetime.now(),
            })

    @api.model
    def action_mark_all_read(self, user_id=None):
        """Mark all user's notifications as read"""
        if not user_id:
            user_id = self.env.user.id
        notifications = self.search([
            ('user_id', '=', user_id),
            ('is_read', '=', False)
        ])
        notifications.write({
            'is_read': True,
            'read_date': fields.Datetime.now(),
        })
        return len(notifications)

    @api.model
    def create_notification(self, user_id, title, message, type='info',
                            action_model=None, action_res_id=None,
                            action_link=None):
        """Helper method to create notifications"""
        return self.create({
            'user_id': user_id,
            'title': title,
            'message': message,
            'type': type,
            'action_model': action_model,
            'action_res_id': action_res_id,
            'action_link': action_link,
        })

    @api.model_create_multi
    def create(self, vals_list):
        """Set default icon if not provided"""
        for vals in vals_list:
            if not vals.get('icon'):
                icon_map = {
                    'success': 'fa-check-circle',
                    'info': 'fa-info-circle',
                    'warning': 'fa-exclamation-triangle',
                    'error': 'fa-times-circle',
                }
                vals['icon'] = icon_map.get(vals.get('type'), 'fa-bell')
        return super(LogspaceNotification, self).create(vals_list)
