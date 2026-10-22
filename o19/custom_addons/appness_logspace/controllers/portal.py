# -*- coding: utf-8 -*-
import datetime
import logging
import urllib.parse
import pytz

from odoo import _, http, fields
from odoo.http import request

from .common import LogspaceController

_logger = logging.getLogger(__name__)


class LogspacePortal(LogspaceController):
    """Customer portal routes: account, profile, orders, tracking, notifications, ratings, refunds, tickets."""

    DRAFT_RETRY_AFTER = datetime.timedelta(minutes=30)


    # My Account Landing Page (Standard Odoo /my style)
    # /my and /my/home are NOT listed here on purpose: they are redirected here by
    # LogspacePortalHome.home (controllers/portal_home.py). Declaring the path on
    # this method too never worked - inside the merged controller class endpoints
    # are enumerated alphabetically, so the inherited core home() won the path.
    @http.route(['/logspace/my', '/logspace/my/home'], type='http', auth='user', website=True)
    def logspace_my_account(self, **kwargs):
        """My Account landing page with navigation cards"""
        partner = request.env.user.partner_id

        # Get real counts for dashboard
        order_counts = self._get_logspace_order_counts(partner.id)

        return request.render('appness_logspace.logspace_my_account',
                              self._get_page_context({
                                  'order_counts': order_counts,
                              }))

    # Screen 11: Profile - /my/account is redirected here by
    # LogspacePortalHome.account (controllers/portal_home.py); listing the path
    # here as well never took effect and the inherited core endpoint 500'd.
    @http.route(['/logspace/my/profile', '/my/profile'], type='http', auth='user', website=True, csrf=False)
    def logspace_profile(self, **kwargs):
        """Screen 11: Customer Profile - Real Data"""
        user = request.env.user
        partner = user.partner_id

        # Handle POST - update profile
        if request.httprequest.method == 'POST':
            update_vals = {}
            partner_vals = {}
            if kwargs.get('name'):
                update_vals['name'] = kwargs.get('name')
            if kwargs.get('email'):
                update_vals['email'] = kwargs.get('email')
            if kwargs.get('phone'):
                update_vals['phone'] = kwargs.get('phone')
            if kwargs.get('address'):
                partner_vals['street'] = kwargs.get('address')
            # Timezone: write to user.tz (related to partner.tz)
            if kwargs.get('tz'):
                tz_val = kwargs['tz']
                if tz_val in pytz.all_timezones:
                    update_vals['tz'] = tz_val
            if partner_vals:
                partner.sudo().write(partner_vals)
            if update_vals:
                user.write(update_vals)
            return request.redirect('/logspace/my/profile')

        # Build address string from partner fields
        address_parts = []
        if partner.street:
            address_parts.append(partner.street)
        if partner.city:
            address_parts.append(partner.city)
        if partner.state_id:
            address_parts.append(partner.state_id.name)
        if partner.zip:
            address_parts.append(partner.zip)
        address = ', '.join(address_parts) if address_parts else _('No address set')

        # Timezone list for the select dropdown
        # Filter to common zones first, then add the rest
        common_tzs = ['UTC', 'Asia/Muscat', 'Asia/Dubai', 'Asia/Riyadh',
                       'Europe/London', 'Europe/Paris', 'Europe/Berlin',
                       'America/New_York', 'America/Chicago', 'America/Denver',
                       'America/Los_Angeles', 'Asia/Tokyo', 'Asia/Shanghai',
                       'Australia/Sydney']
        other_tzs = [tz for tz in sorted(pytz.all_timezones)
                     if tz not in common_tzs and not tz.startswith('Etc/')]
        timezones = common_tzs + other_tzs

        return request.render('appness_logspace.logspace_profile_page',
                              self._get_page_context({
                                  'user': {
                                      'name': user.name,
                                      'email': user.email,
                                      'phone': partner.phone or _('Not set'),
                                      'address': address,
                                      'tz': user.tz or partner.tz or 'UTC',
                                  },
                                  'timezones': timezones,
                              }))

    # Helper: Get order counts for dashboard
    def _get_logspace_order_counts(self, partner_id):
        """Get order counts by status for a partner"""
        SaleOrder = request.env['sale.order'].sudo()

        # Base domain for all logspace orders for this partner
        base_domain = [
            '|',
            ('partner_id', '=', partner_id),
            ('partner_id.parent_id', '=', partner_id),
            ('is_logspace_order', '=', True),
        ]

        # Use search_count for efficient counting
        active_states = [
            'order_received', 'pickup_started', 'vendor_arrived_pickup',
            'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
            'arrived_destination'
        ]
        completed_states = ['dropoff_completed', 'grace_period', 'order_completed']
        cancelled_states = ['cancelled']

        return {
            'all': SaleOrder.search_count(base_domain),
            'active': SaleOrder.search_count(base_domain + [('logspace_state', 'in', active_states)]),
            'completed': SaleOrder.search_count(base_domain + [('logspace_state', 'in', completed_states)]),
            'cancelled': SaleOrder.search_count(base_domain + [('logspace_state', 'in', cancelled_states)]),
        }

    # Screen 12: Orders List - accessible from both /logspace/my/orders and standard /my/orders
    @http.route(['/logspace/my/orders', '/logspace/my/orders/<string:status>', '/my/orders', '/my/orders/<string:status>'], type='http', auth='user', website=True)
    def logspace_orders(self, status='all', **kwargs):
        """Screen 12: Orders list with tabs - REAL DATA"""
        current_user = request.env.user
        partner = current_user.partner_id

        # A driver delivers the orders a provider assigns to them; they never
        # place one. The "My Orders" card is hidden from them on /logspace/my, so
        # this is the matching guard on the URL behind it - otherwise hiding the
        # card would be cosmetic. Mirrors how the driver pages bounce non-drivers
        # back to /logspace/my (controllers/driver.py:118-120).
        if partner.is_driver:
            return request.redirect('/logspace/driver/orders')

        # Get real order counts
        counts = self._get_logspace_order_counts(partner.id)

        # Get orders from database
        orders_list = self._get_real_orders(partner.id, status)

        return request.render('appness_logspace.logspace_tracking_infos_page',
                              self._get_page_context({
                                  'orders_list': orders_list,
                                  'current_status': status,
                                  'datetime': datetime,
                                  'counts': counts,
                                  'user': current_user,
                              }))

    # Screen 13: Track Order (NO MAP - Timeline only) - REAL DATA
    # auth='public' so guests can open their token-protected order view;
    # authenticated visitors keep the normal partner-scoped access below.
    @http.route(['/logspace/my/orders/track', '/logspace/my/orders/track/<string:order_id>', '/my/orders/track', '/my/orders/track/<string:order_id>'], type='http', auth='public', website=True)
    def logspace_track(self, order_id=None, access_token=None, **kwargs):
        """Screen 13: Order tracking with timeline (no map) - REAL DATA"""
        current_user = request.env.user
        partner = current_user.partner_id
        is_public = current_user._is_public()

        # `/logspace/my/orders/track/cancel` is a sibling POST-only route. Werkzeug
        # prefers the static rule for POST, so cancelling is unaffected; a GET on
        # that path has no method match and falls through to here with
        # order_id='cancel'. That used to be accidental - it only worked because an
        # order name never matches, so the lookup failed and bounced to the orders
        # list. Stated explicitly so nobody "simplifies" this route's matching
        # later and silently breaks order cancellation.
        if order_id == 'cancel':
            return request.redirect('/logspace/my/orders')

        if is_public:
            # Guests (booked without an account) may only view an order through
            # its token-protected URL, e.g. coming from the payment result page.
            order = request.env['sale.order'].sudo().search([
                ('name', '=', order_id or ''),
                ('is_logspace_order', '=', True),
            ], limit=1)
            if not order or not access_token or access_token != order._portal_ensure_token():
                return request.redirect('/web/login')
        else:
            # Find order by name - check both partner and parent company
            domain = [
                '|',
                ('partner_id', '=', partner.id),
                ('partner_id.parent_id', '=', partner.id),
                ('is_logspace_order', '=', True),
            ]
            if order_id:
                domain.append(('name', '=', order_id))
            order = request.env['sale.order'].sudo().search(domain, limit=1, order='create_date desc')

        if not order:
            # Redirect to orders list if not found
            return request.redirect('/logspace/my/orders')

        # Get real timeline
        timeline = self._get_real_order_timeline(order)

        # Determine which verification codes to show
        show_pickup_code = order.logspace_state in [
            'order_received', 'pickup_started', 'vendor_arrived_pickup',
            'pickup_addons', 'pickup_completed', 'pre_dropoff_addons', 'arrived_destination'
        ]
        show_dropoff_code = order.logspace_state in [
            'arrived_destination', 'dropoff_completed', 'grace_period', 'order_completed'
        ]
        # The vehicle code is internal until the dropoff is done: customers see
        # it on the tracking page only once the dropoff has been completed.
        show_vehicle_code = order.logspace_state in [
            'dropoff_completed', 'grace_period', 'order_completed'
        ]
        timeframe_labels = request.env['logspace.time.slot']._get_labels_by_code()

        tracking_info = {
            'id': order.name,
            'status': (order.logspace_state or '').replace('_', ' ').title() or 'Draft',
            'amount': order.amount_total,
            'formatted_amount': order.currency_id.format(order.amount_total),
            'currency_symbol': order.currency_id.symbol or '',
            'pickup': order.pickup_address or 'Not set',
            'dropoff': order.dropoff_address or 'Not set',
            'pickup_zone': order.pickup_zone_id.display_name if order.pickup_zone_id else '',
            'dropoff_zone': order.dropoff_zone_id.display_name if order.dropoff_zone_id else '',
            'truck': order.logspace_vehicle_id.vehicle_type_id.name if order.logspace_vehicle_id and order.logspace_vehicle_id.vehicle_type_id else 'Logspace Service',
            'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Not assigned',
            'vendor_email': order.logspace_provider_id.email if order.logspace_provider_id else '',
            'vendor_phone': (order.logspace_provider_id.phone or '') if order.logspace_provider_id else '',
            'vehicle_code': order.logspace_vehicle_id.name if order.logspace_vehicle_id else '',
            'show_vehicle_code': show_vehicle_code,
            'driver': order.logspace_driver_id.name if order.logspace_driver_id else _('Not assigned'),
            'driver_phone': order.logspace_driver_id.phone if order.logspace_driver_id else _('Not available'),
            'create_date': order.create_date.strftime('%b %d, %Y') if order.create_date else _('N/A'),
            'scheduled_datetime': order.scheduled_date.strftime('%b %d, %Y') if order.scheduled_date else _('N/A'),
            'approve_date': order.date_order.strftime('%b %d, %Y') if order.date_order else False,
            'pickup_timeframe': timeframe_labels.get(order.pickup_timeframe, order.pickup_timeframe or _('Not set')),
            'dropoff_timeframe': timeframe_labels.get(order.dropoff_timeframe, order.dropoff_timeframe or ''),
            'item_description': order.item_description or '',
            'pickup_contact_name': order.pickup_contact_name or '',
            'pickup_contact_phone': order.pickup_contact_phone or '',
            'dropoff_contact_name': order.dropoff_contact_name or '',
            'dropoff_contact_phone': order.dropoff_contact_phone or '',
            'pickup_verification_code': order.verification_code_pickup if show_pickup_code else None,
            'dropoff_verification_code': order.verification_code_dropoff if show_dropoff_code else None,
            'payment_status': order.payment_status,
        }

        # Full price breakdown mirroring the checkout page: the first order line
        # is the truck service, the remaining ones are the selected add-ons.
        order_lines = order.order_line
        tracking_info['price_breakdown'] = {
            'truck_name': order_lines[0].name if order_lines else 'Truck Service',
            'truck_price': order_lines[0].price_unit if order_lines else 0.0,
            'addons': [
                {'name': line.name, 'price': line.price_unit}
                for line in order_lines[1:]
            ],
            'subtotal': order.amount_untaxed,
            'tax': order.amount_tax,
            'total': order.amount_total,
        }

        # Payment recovery: let the customer pay an unpaid order that never got
        # through checkout (e.g. the payment tab was closed by accident).
        unpaid_and_open = (
            order.state in ('draft', 'sent') and order.payment_status != 'paid'
        )
        has_blocking_tx = bool(order._get_blocking_logspace_transactions(self.DRAFT_RETRY_AFTER))
        pay_query = urllib.parse.urlencode({'access_token': order._portal_ensure_token()})
        tracking_info.update({
            'can_pay': unpaid_and_open and not has_blocking_tx,
            'payment_in_progress': unpaid_and_open and has_blocking_tx,
            'pay_url': f'/logspace/booking/payment/{order.id}?{pay_query}',
        })

        # User can cancel order before pickup_completed stage
        cancelable_states = ['order_received', 'pickup_started', 'vendor_arrived_pickup', 'pickup_addons']
        can_cancel = order.logspace_state in cancelable_states

        # User can rate only after dropoff is completed
        rateable_states = ['dropoff_completed', 'grace_period', 'order_completed']
        can_rate = order.logspace_state in rateable_states

        # Count unread notifications for this order
        unread_notif_count = request.env['logspace.notification'].sudo().search_count([
            ('user_id', '=', current_user.id),
            ('is_read', '=', False),
            ('action_link', 'like', f'/logspace/my/orders/track/{order.name}'),
        ])

        return request.render('appness_logspace.logspace_track_page',
                              self._get_page_context({
                                  'order': order,
                                  'currency': order.currency_id,
                                  'tracking_info': tracking_info,
                                  'timeline': timeline,
                                  'order_id': order.name,
                                  'order': order,
                                  'can_cancel': can_cancel and not is_public,
                                  'can_rate': can_rate and not is_public,
                                  'is_public': is_public,
                                  'unread_notif_count': unread_notif_count,
                              }))

    # Cancel order route - user cancels own order
    @http.route(['/logspace/my/orders/track/cancel'], type='http', auth='user', website=True, csrf=False, methods=['POST'])
    def logspace_cancel_order(self, **kwargs):
        """Cancel a logspace order - user can cancel before pickup_completed"""
        current_user = request.env.user
        partner = current_user.partner_id
        order_id = kwargs.get('order_id')

        if not order_id:
            return request.redirect('/logspace/my/orders')

        # Find order - must belong to this partner
        order = request.env['sale.order'].sudo().search([
            '|',
            ('partner_id', '=', partner.id),
            ('partner_id.parent_id', '=', partner.id),
            ('is_logspace_order', '=', True),
            ('name', '=', order_id),
        ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Only allow cancellation before pickup_completed
        cancelable_states = ['order_received', 'pickup_started', 'vendor_arrived_pickup', 'pickup_addons']
        if order.logspace_state in cancelable_states:
            order.action_cancel_logspace()
            request.env['logspace.notification'].sudo().create_notification(
                user_id=current_user.id,
                title=_('Order Cancelled'),
                message=_('Your order %s has been cancelled.', order.name),
                type='warning',
                action_link='/logspace/my/orders/track/%s' % order.name,
            )

        return request.redirect('/logspace/my/orders/track/%s' % order_id)

    # Screen 14: Notifications - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/notifications', '/logspace/my/notifications', '/my/notifications'], type='http', auth='user', website=True, csrf=False)
    def logspace_notifications(self, order_id=None, **kwargs):
        """Screen 14: Notifications list - REAL DATA"""
        user = request.env.user

        # Handle POST - mark notifications as read
        if request.httprequest.method == 'POST':
            notif_ids = kwargs.get('notif_ids', [])
            if notif_ids:
                notif_ids = [int(x) for x in notif_ids.split(',') if x.isdigit()]
                notifications = request.env['logspace.notification'].sudo().browse(notif_ids)
                notifications.action_mark_read()
            elif kwargs.get('mark_all') == 'true':
                request.env['logspace.notification'].action_mark_all_read(user.id)
            return request.redirect('/logspace/my/notifications')

        # Get real notifications
        notifications = request.env['logspace.notification'].sudo().search([
            ('user_id', '=', user.id),
        ], order='create_date desc', limit=50)

        notifications_list = []
        for notif in notifications:
            time_diff = fields.Datetime.now() - notif.create_date
            hours = time_diff.total_seconds() / 3600
            if hours < 1:
                time_ago = f"{int(time_diff.total_seconds() / 60)} mins ago"
            elif hours < 24:
                time_ago = f"{int(hours)} hours ago"
            else:
                time_ago = f"{int(hours / 24)} days ago"

            notifications_list.append({
                'id': notif.id,
                'title': notif.title,
                'message': notif.message,
                'time': time_ago,
                'type': notif.type,
                'icon': notif.icon or 'fa-bell',
                'read': notif.is_read,
                'action_link': notif.action_link,
            })

        return request.render('appness_logspace.logspace_notifications_page',
                              self._get_page_context({
                                  'notifications': notifications_list,
                                  'order_id': order_id or '',
                                  'unread_count': len([n for n in notifications_list if not n['read']]),
                              }))

    # Screen 15: Rate Driver - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/rate', '/logspace/rate', '/logspace/rate/<string:order_id>', '/my/rate', '/my/rate/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def logspace_rate(self, order_id=None, **kwargs):
        """Screen 15: Rate Driver - REAL DATA with form submission"""
        user = request.env.user
        partner = user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Check if order is delivered
        if order.logspace_state not in ['dropoff_completed', 'grace_period', 'order_completed']:
            return request.redirect(f'/logspace/my/orders/track/{order_id}')

        # Check if already rated
        already_rated = bool(order.logspace_customer_rating)

        # Handle POST - save rating on order (only if not already rated)
        if request.httprequest.method == 'POST' and not already_rated:
            overall_rating = int(kwargs.get('overall_rating', 0))
            comments = kwargs.get('comments', '')

            if overall_rating > 0:
                order.sudo().write({
                    'logspace_customer_rating': overall_rating,
                    'logspace_customer_rating_comment': comments or False,
                })

                # Create notification for customer
                request.env['logspace.notification'].sudo().create_notification(
                    user_id=user.id,
                    title=_('Rating Submitted'),
                    message=_('Thank you for rating your experience with %s',
                              order.logspace_provider_id.name or _('the provider')),
                    type='success',
                    action_link=f'/logspace/my/orders/track/{order.name}',
                )

            return request.redirect(f'/logspace/my/orders/track/{order_id}')

        return request.render('appness_logspace.logspace_rate_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'vendor': order.logspace_provider_id.name if order.logspace_provider_id else _('Unknown'),
                                  'driver': order.logspace_driver_id.name if order.logspace_driver_id else _('Not assigned'),
                                  'already_rated': already_rated,
                              }))

    # Screen 16: Refund Request (New Form) - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/refunds/new', '/logspace/refund', '/logspace/refund/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def logspace_refund(self, order_id=None, **kwargs):
        """Screen 16: Refund Request Form - REAL DATA"""
        user = request.env.user
        partner = user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Handle POST - create refund request
        if request.httprequest.method == 'POST':
            reason = kwargs.get('reason', 'other')
            details = kwargs.get('details', '')

            # Create refund record
            refund_vals = {
                'order_id': order.id,
                'amount': order.amount_total,
                'reason': reason,
                'details': details,
            }
            refund = request.env['logspace.refund'].sudo().create(refund_vals)

            # Submit the refund
            refund.action_submit()

            # Create notification
            request.env['logspace.notification'].sudo().create_notification(
                user_id=user.id,
                title=_('Refund Requested'),
                message=_('Your refund request for order %s has been submitted and is under review.', order.name),
                type='info',
                action_link=f'/logspace/my/orders/{order_id}/refunds',
            )

            return request.redirect(f'/logspace/my/orders/{order_id}/refunds')

        # Get refundable amount (order total)
        refundable_amount = order.amount_total

        return request.render('appness_logspace.logspace_refund_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'currency': order.currency_id,
                                  'tracking_info_id': order.name,
                                  'amount': refundable_amount,
                                  'formatted_amount': order.currency_id.format(refundable_amount),
                                  'reasons': [
                                      ('service_not_provided', _('Service was not provided')),
                                      ('late_delivery', _('Late delivery')),
                                      ('damaged_goods', _('Damaged goods')),
                                      ('wrong_vehicle', _('Wrong vehicle type')),
                                      ('overcharged', _('Overcharged')),
                                      ('cancelled_by_provider', _('Cancelled by provider')),
                                      ('other', _('Other reason'))
                                  ]
                              }))

    # Screen 16b: Refund List for an Order - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/refunds'], type='http', auth='user', website=True)
    def logspace_refund_list(self, order_id=None, **kwargs):
        """Refund list for a specific order - REAL DATA"""
        partner = request.env.user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Get real refunds for this order
        refunds = request.env['logspace.refund'].sudo().search([
            ('order_id', '=', order.id),
        ])

        refunds_list = []
        for refund in refunds:
            currency = refund.currency_id or (order.currency_id if order else request.env.company.currency_id)
            status_labels = {
                'draft': _('Draft'),
                'submitted': _('Submitted'),
                'under_review': _('Under Review'),
                'approved': _('Approved'),
                'rejected': _('Rejected'),
                'processed': _('Processed'),
            }
            refunds_list.append({
                'id': refund.name,
                'refund_id': refund.id,
                'date': refund.submitted_date.strftime('%b %d, %Y') if refund.submitted_date else refund.create_date.strftime('%b %d, %Y'),
                'amount': refund.amount,
                'formatted_amount': currency.format(refund.amount) if currency else f'{refund.amount:.2f}',
                'currency_symbol': currency.symbol if currency else '',
                'reason': dict(refund._fields['reason'].selection).get(refund.reason, refund.reason),
                'status': refund.state,
                'status_label': status_labels.get(refund.state, refund.state.title()),
            })

        return request.render('appness_logspace.logspace_refund_list_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'refunds': refunds_list,
                              }))

    # Screen 17: Support Ticket (New Form) - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/tickets/new', '/logspace/ticket', '/logspace/ticket/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def logspace_ticket(self, order_id=None, **kwargs):
        """Screen 17: Helpdesk/Support Ticket Form - REAL DATA"""
        user = request.env.user
        partner = user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        # Handle POST - create ticket
        if request.httprequest.method == 'POST':
            category = kwargs.get('category', 'other')
            subject = kwargs.get('subject', '')
            description = kwargs.get('description', '')

            # Create helpdesk ticket
            ticket_vals = {
                'name': subject,
                'description': description,
                'partner_id': partner.id,
                'is_logspace_ticket': True,
                'logspace_order_id': order.id if order else False,
                'logspace_ticket_type': category,
            }

            # Get or create the Logspace support team
            team = request.env['helpdesk.team'].sudo().search([
                ('name', 'ilike', 'logspace'),
            ], limit=1) or request.env['helpdesk.team'].sudo().search([], limit=1)

            if team:
                ticket_vals['team_id'] = team.id

            ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)

            # Create notification
            request.env['logspace.notification'].sudo().create_notification(
                user_id=user.id,
                title=_('Support Ticket Created'),
                message=_('Your ticket #%s has been created and will be reviewed shortly.', ticket.name),
                type='success',
                action_link=f'/logspace/my/orders/{order_id}/tickets' if order_id else '/logspace/my/notifications',
            )

            if order_id:
                return request.redirect(f'/logspace/my/orders/{order_id}/tickets')
            return request.redirect('/logspace/my/notifications')

        return request.render('appness_logspace.logspace_ticket_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'categories': [
                                      ('booking', 'Booking Issue'),
                                      ('payment', 'Payment Issue'),
                                      ('delivery', 'Delivery Problem'),
                                      ('driver', 'Driver Complaint'),
                                      ('refund', 'Refund Request'),
                                      ('other', 'Other')
                                  ]
                              }))

    # Screen 17b: Ticket List for an Order - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/tickets'], type='http', auth='user', website=True)
    def logspace_ticket_list(self, order_id=None, **kwargs):
        """Ticket list for a specific order - REAL DATA"""
        partner = request.env.user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Get real tickets for this order
        tickets = request.env['helpdesk.ticket'].sudo().search([
            ('logspace_order_id', '=', order.id),
            ('is_logspace_ticket', '=', True),
        ])

        tickets_list = []
        for ticket in tickets:
            # Map stage to status
            status_map = {
                'new': 'open',
                'in_progress': 'open',
                'solved': 'resolved',
                'cancelled': 'resolved',
            }
            status_label_map = {
                'new': _('Open'),
                'in_progress': _('In Progress'),
                'solved': _('Resolved'),
                'cancelled': _('Cancelled'),
            }
            stage_name = ticket.stage_id.name.lower() if ticket.stage_id else 'new'
            status = status_map.get(stage_name, 'open')
            status_label = status_label_map.get(stage_name, stage_name.title())

            tickets_list.append({
                'id': ticket.name,
                'ticket_id': ticket.id,
                'date': ticket.create_date.strftime('%b %d, %Y') if ticket.create_date else _('N/A'),
                'subject': ticket.name,
                'category': dict(ticket._fields['logspace_ticket_type'].selection).get(ticket.logspace_ticket_type, _('Other')),
                'status': status,
                'status_label': status_label,
            })

        return request.render('appness_logspace.logspace_ticket_list_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'tickets': tickets_list,
                              }))

    # Ticket Detail Page
    @http.route(['/logspace/my/orders/<string:order_id>/tickets/<int:ticket_id>'], type='http', auth='user', website=True)
    def logspace_ticket_detail(self, order_id=None, ticket_id=None, **kwargs):
        """Ticket detail for a specific order"""
        partner = request.env.user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Get the ticket
        ticket = request.env['helpdesk.ticket'].sudo().search([
            ('id', '=', ticket_id),
            ('logspace_order_id', '=', order.id),
            ('is_logspace_ticket', '=', True),
        ], limit=1)

        if not ticket:
            return request.redirect(f'/logspace/my/orders/{order_id}/tickets')

        # Map stage to status
        status_map = {
            'new': 'open',
            'in_progress': 'open',
            'solved': 'resolved',
            'cancelled': 'resolved',
        }
        status_label_map = {
            'new': _('Open'),
            'in_progress': _('In Progress'),
            'solved': _('Resolved'),
            'cancelled': _('Cancelled'),
        }
        stage_name = ticket.stage_id.name.lower() if ticket.stage_id else 'new'
        status = status_map.get(stage_name, 'open')
        status_label = status_label_map.get(stage_name, stage_name.title())

        ticket_data = {
            'id': ticket.name,
            'ticket_id': ticket.id,
            'date': ticket.create_date.strftime('%b %d, %Y') if ticket.create_date else _('N/A'),
            'subject': ticket.name,
            'category': dict(ticket._fields['logspace_ticket_type'].selection).get(ticket.logspace_ticket_type, _('Other')),
            'status': status,
            'status_label': status_label,
            'description': ticket.description or '',
        }

        return request.render('appness_logspace.logspace_ticket_detail_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'ticket': ticket_data,
                              }))

    # Refund Detail Page
    @http.route(['/logspace/my/orders/<string:order_id>/refunds/<int:refund_id>'], type='http', auth='user', website=True)
    def logspace_refund_detail(self, order_id=None, refund_id=None, **kwargs):
        """Refund detail for a specific order"""
        partner = request.env.user.partner_id

        # Find order by name
        order = False
        if order_id:
            order = request.env['sale.order'].sudo().search([
                ('partner_id', '=', partner.id),
                ('is_logspace_order', '=', True),
                ('name', '=', order_id),
            ], limit=1)

        if not order:
            return request.redirect('/logspace/my/orders')

        # Get the refund
        refund = request.env['logspace.refund'].sudo().search([
            ('id', '=', refund_id),
            ('order_id', '=', order.id),
        ], limit=1)

        if not refund:
            return request.redirect(f'/logspace/my/orders/{order_id}/refunds')

        state_label_map = {
            'draft': _('Draft'),
            'submitted': _('Submitted'),
            'under_review': _('Under Review'),
            'approved': _('Approved'),
            'rejected': _('Rejected'),
            'processed': _('Processed'),
        }

        currency = refund.currency_id or (order.currency_id if order else request.env.company.currency_id)
        refund_data = {
            'id': refund.name,
            'date': refund.create_date.strftime('%b %d, %Y') if refund.create_date else _('N/A'),
            'amount': refund.amount,
            'formatted_amount': currency.format(refund.amount) if currency else f'{refund.amount:.2f}',
            'currency_symbol': currency.symbol if currency else '',
            'currency': currency,
            'reason': refund.reason,
            'reason_label': dict(refund._fields['reason'].selection).get(refund.reason, refund.reason),
            'status': refund.state,
            'status_label': state_label_map.get(refund.state, refund.state),
            'details': refund.details or '',
            'rejection_reason': refund.rejection_reason or '',
        }

        return request.render('appness_logspace.logspace_refund_detail_page',
                              self._get_page_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'currency': currency,
                                  'refund': refund_data,
                              }))

    # Rating List Page - Redirect to rate page (ratings now stored on order directly)
    @http.route(['/logspace/my/orders/<string:order_id>/ratings'], type='http', auth='user', website=True)
    def logspace_rating_list(self, order_id=None, **kwargs):
        """Redirect to rate page since ratings are now stored on the order directly"""
        return request.redirect(f'/logspace/my/orders/{order_id}/rate')

    # Rating Detail Page - Redirect to rate page (ratings now stored on order directly)
    @http.route(['/logspace/my/orders/<string:order_id>/ratings/<int:rating_id>'], type='http', auth='user', website=True)
    def logspace_rating_detail(self, order_id=None, rating_id=None, **kwargs):
        """Redirect to rate page since ratings are now stored on the order directly"""
        return request.redirect(f'/logspace/my/orders/{order_id}/rate')

