# -*- coding: utf-8 -*-

import logging

from odoo import _, http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from .common import LogspaceController

_logger = logging.getLogger(__name__)


class LogspaceDriverPortal(LogspaceController):
    """Driver portal: the assigned driver advances the delivery status.

    Kept separate from controllers/portal.py on purpose. The customer track
    page renders verification_code_pickup / verification_code_dropoff in plain
    text, and a driver must never see either code - they read each one aloud
    from the customer. Sharing a template would make that leak easy to
    reintroduce by accident.
    """

    # Mirrors the status buckets in LogspaceController._get_real_orders so the
    # driver list and the customer list behave the same way.
    STATUS_MAP = {
        'active': [
            'order_received', 'pickup_started', 'vendor_arrived_pickup',
            'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
            'arrived_destination',
        ],
        'completed': ['dropoff_completed', 'grace_period', 'order_completed'],
        'cancelled': ['cancelled'],
    }
    STATUS_MAP['all'] = (
        STATUS_MAP['active'] + STATUS_MAP['completed'] + STATUS_MAP['cancelled']
    )

    STATE_CATEGORY = {
        'order_received': 'pending',
        'pickup_started': 'active',
        'vendor_arrived_pickup': 'active',
        'pickup_addons': 'active',
        'pickup_completed': 'active',
        'pre_dropoff_addons': 'active',
        'arrived_destination': 'active',
        'dropoff_completed': 'completed',
        'grace_period': 'completed',
        'order_completed': 'completed',
        'cancelled': 'cancelled',
    }

    @staticmethod
    def _secure_response(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response

    def _get_driver_partner(self):
        """Return the session user's partner when it is a driver, else False."""
        user = request.env.user
        if user._is_public():
            return False
        partner = user.partner_id
        return partner if partner.is_driver else False

    def _get_driver_order(self, order_name):
        """Fetch an order assigned to the current driver, or an empty recordset.

        Authorization lives in the domain (module convention) and is re-asserted
        by sale.order._check_logspace_driver_access() on any mutation.
        """
        driver = self._get_driver_partner()
        if not driver or not order_name:
            return request.env['sale.order'].sudo().browse()
        return request.env['sale.order'].sudo().search([
            ('is_logspace_order', '=', True),
            ('logspace_driver_id', '=', driver.id),
            ('name', '=', order_name),
        ], limit=1)

    def _format_order_item(self, order):
        vehicle_type_name = 'Logspace Service'
        if order.logspace_vehicle_id and order.logspace_vehicle_id.vehicle_type_id:
            vehicle_type_name = order.logspace_vehicle_id.vehicle_type_id.name

        create_date = order.create_date.strftime('%b %d, %Y') if order.create_date else _('N/A')
        scheduled_date = (
            order.scheduled_date.strftime('%b %d, %Y %H:%M')
            if order.scheduled_date else _('N/A')
        )
        return {
            'id': order.name,
            'order_id': order.id,
            'status': self.STATE_CATEGORY.get(order.logspace_state, 'pending'),
            'status_label': (
                (order.logspace_state or '').replace('_', ' ').title() or _('Order Received')
            ),
            'logspace_state': order.logspace_state,
            'pickup': order.pickup_address or _('Not set'),
            'dropoff': order.dropoff_address or _('Not set'),
            'zone_from': order.pickup_zone_id.name if order.pickup_zone_id else _('Not set'),
            'zone_to': order.dropoff_zone_id.name if order.dropoff_zone_id else _('Not set'),
            'truck': vehicle_type_name,
            'date': create_date,
            'scheduled_datetime': scheduled_date,
            'vendor': order.logspace_provider_id.name if order.logspace_provider_id else _('Not assigned'),
            'customer': order.partner_id.name if order.partner_id else '',
            'order': order,
        }

    @http.route([
        '/logspace/driver/orders',
        '/logspace/driver/orders/<string:status>',
    ], type='http', auth='user', website=True)
    def logspace_driver_orders(self, status='all', **kwargs):
        """List the deliveries assigned to the logged-in driver."""
        driver = self._get_driver_partner()
        if not driver:
            return request.redirect('/logspace/my')

        states = self.STATUS_MAP.get(status, self.STATUS_MAP['all'])
        orders = request.env['sale.order'].sudo().search([
            ('is_logspace_order', '=', True),
            ('logspace_driver_id', '=', driver.id),
            ('logspace_state', 'in', states),
        ], order='scheduled_date desc, create_date desc')

        items = [self._format_order_item(order) for order in orders]
        counts = {
            key: request.env['sale.order'].sudo().search_count([
                ('is_logspace_order', '=', True),
                ('logspace_driver_id', '=', driver.id),
                ('logspace_state', 'in', self.STATUS_MAP[key]),
            ])
            for key in ('all', 'active', 'completed')
        }

        response = request.render(
            'appness_logspace.logspace_driver_orders_page',
            self._get_page_context({
                'driver': driver,
                'orders': items,
                'order_count': len(items),
                'counts': counts,
                'current_status': status if status in self.STATUS_MAP else 'all',
            }),
        )
        return self._secure_response(response)

    @http.route([
        '/logspace/driver/orders/track',
        '/logspace/driver/orders/track/<string:order_id>',
    ], type='http', auth='user', website=True)
    def logspace_driver_track(self, order_id=None, **kwargs):
        """Delivery detail page with the status-transition buttons.

        NOTE: tracking_info deliberately omits verification_code_pickup and
        verification_code_dropoff. Do not add them - the driver must obtain each
        code from the customer, and the template is asserted code-free in tests.
        """
        driver = self._get_driver_partner()
        if not driver:
            return request.redirect('/logspace/my')

        if not order_id:
            latest = request.env['sale.order'].sudo().search([
                ('is_logspace_order', '=', True),
                ('logspace_driver_id', '=', driver.id),
            ], limit=1, order='create_date desc')
            if not latest:
                return request.redirect('/logspace/driver/orders')
            return request.redirect('/logspace/driver/orders/track/%s' % latest.name)

        order = self._get_driver_order(order_id)
        if not order:
            return request.redirect('/logspace/driver/orders')

        timeline = self._get_real_order_timeline(order)

        vehicle = order.logspace_vehicle_id
        tracking_info = {
            'id': order.name,
            'status': (order.logspace_state or '').replace('_', ' ').title() or 'Draft',
            'logspace_state': order.logspace_state,
            'pickup': order.pickup_address or 'Not set',
            'dropoff': order.dropoff_address or 'Not set',
            'pickup_zone': order.pickup_zone_id.display_name if order.pickup_zone_id else '',
            'dropoff_zone': order.dropoff_zone_id.display_name if order.dropoff_zone_id else '',
            'pickup_timeframe': order.pickup_timeframe or 'Not set',
            'dropoff_timeframe': order.dropoff_timeframe or '',
            'pickup_contact_name': order.pickup_contact_name or '',
            'pickup_contact_phone': order.pickup_contact_phone or '',
            'dropoff_contact_name': order.dropoff_contact_name or '',
            'dropoff_contact_phone': order.dropoff_contact_phone or '',
            'customer': order.partner_id.name if order.partner_id else '',
            'customer_phone': order.partner_id.phone or '',
            'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Not assigned',
            'vendor_phone': (
                order.logspace_provider_id.phone if order.logspace_provider_id else ''
            ) or '',
            'truck': vehicle.vehicle_type_id.name if vehicle and vehicle.vehicle_type_id else 'Logspace Service',
            'plate_number': vehicle.plate_number if vehicle else '',
            'scheduled_datetime': (
                order.scheduled_date.strftime('%b %d, %Y %H:%M') if order.scheduled_date else 'N/A'
            ),
            'item_description': order.item_description or '',
            'payment_status': order.payment_status,
            'is_confirmed': order.state == 'sale',
        }

        response = request.render(
            'appness_logspace.logspace_driver_track_page',
            self._get_page_context({
                'order': order,
                'driver': driver,
                'tracking_info': tracking_info,
                'timeline': timeline,
                'order_id': order.name,
                'driver_actions': order._get_logspace_driver_actions(),
            }),
        )
        return self._secure_response(response)

    @http.route(
        '/logspace/driver/orders/action',
        type='jsonrpc', auth='user', website=True,
    )
    def logspace_driver_action(self, order_name=None, action=None, code=None, **kwargs):
        """Apply one delivery status transition for the logged-in driver.

        Returns {'ok': True, 'state': ..., 'label': ...} on success or
        {'error': <message>} so the widget can show it inline and let the
        driver retry a mistyped code without losing the page.
        """
        driver = self._get_driver_partner()
        if not driver:
            return {'error': _('You are not signed in as a driver.')}

        order = self._get_driver_order(order_name)
        if not order:
            return {'error': _('This delivery could not be found.')}

        try:
            order.action_driver_transition(action, code=code)
        except (UserError, AccessError) as error:
            # Surface the message (wrong code, wrong state, locked) without the
            # traceback, and never echo the expected code back.
            return {'error': str(error)}
        except Exception:
            _logger.exception(
                "Driver transition failed for %s (action=%s)", order_name, action,
            )
            return {'error': _('The status could not be updated. Please try again.')}

        state_selection = dict(order._fields['logspace_state'].selection)
        return {
            'ok': True,
            'state': order.logspace_state,
            'label': state_selection.get(order.logspace_state, order.logspace_state or ''),
        }
