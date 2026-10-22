# -*- coding: utf-8 -*-
import logging
import datetime
import pytz

from odoo import _, http, fields
from odoo.exceptions import ValidationError
from odoo.http import request

from ..models.res_config_settings import (
    DEFAULT_CANCEL_REFUND_POLICY,
    DEFAULT_ESTIMATED_TIME_POLICY,
)

_logger = logging.getLogger(__name__)


class LogspaceController(http.Controller):
    """Base controller for Logspace - shared helper methods."""

    def _get_page_context(self, extra=None):
        """Get base page context with system and order currency support."""
        company_currency = request.env.company.currency_id
        params = request.env['ir.config_parameter'].sudo()
        ctx = {
            'company_currency': company_currency,
            'currency': company_currency,
            'currency_symbol': company_currency.symbol or '',
            'logspace_cancel_refund_policy': params.get_param(
                'appness_logspace.cancel_refund_policy',
                DEFAULT_CANCEL_REFUND_POLICY),
            'logspace_estimated_time_policy': params.get_param(
                'appness_logspace.estimated_time_policy',
                DEFAULT_ESTIMATED_TIME_POLICY),
        }
        if extra:
            ctx.update(extra)
        if not extra or 'currency' not in extra:
            order = ctx.get('order')
            if order and getattr(order, 'currency_id', False):
                ctx['currency'] = order.currency_id
                ctx['currency_symbol'] = order.currency_id.symbol or ''
        return ctx

    def _get_real_orders(self, partner_id, status='all'):
        """Get real orders from database for a partner"""
        SaleOrder = request.env['sale.order'].sudo()

        # Base domain - include orders where partner is the customer OR the contact
        domain = [
            '|',
            ('partner_id', '=', partner_id),
            ('partner_id.parent_id', '=', partner_id),  # For contacts of a company
            ('is_logspace_order', '=', True),
        ]

        # Apply status filter - Updated to match new logspace_state values
        status_map = {
            'active': [
                'order_received', 'pickup_started', 'vendor_arrived_pickup',
                'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
                'arrived_destination'
            ],
            'completed': ['dropoff_completed', 'grace_period', 'order_completed'],
            'cancelled': ['cancelled'],
            'all': [
                'order_received', 'pickup_started', 'vendor_arrived_pickup',
                'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
                'arrived_destination', 'dropoff_completed', 'grace_period',
                'order_completed', 'cancelled'
            ],
        }
        states = status_map.get(status, status_map['all'])
        domain.append(('logspace_state', 'in', states))

        orders = SaleOrder.search(domain, order='create_date desc')

        result = []
        for order in orders:
            # Map logspace state to display status category
            state_category_map = {
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

            # Get vehicle type name
            vehicle_type_name = 'Logspace Service'
            if order.logspace_vehicle_id and order.logspace_vehicle_id.vehicle_type_id:
                vehicle_type_name = order.logspace_vehicle_id.vehicle_type_id.name
            elif order.logspace_provider_id:
                # Try to get from order line product
                for line in order.order_line:
                    if line.product_id:
                        vehicle_type_name = line.product_id.name
                        break

            # Format dates
            create_date = order.create_date.strftime('%b %d, %Y') if order.create_date else _('N/A')
            scheduled_date = order.scheduled_date.strftime('%b %d, %Y') if order.scheduled_date else _('N/A')
            approve_date = False
            if order.logspace_state != 'order_received' and order.write_date:
                approve_date = order.write_date.strftime('%b %d, %Y')

            result.append({
                'id': order.name,
                'order_id': order.id,
                'status': state_category_map.get(order.logspace_state, 'pending'),
                'status_label': order.logspace_state.replace('_', ' ').title() if order.logspace_state else _('Order Received'),
                'pickup': order.pickup_address or _('Not set'),
                'dropoff': order.dropoff_address or _('Not set'),
                'zone_from': order.pickup_zone_id.name if order.pickup_zone_id else _('Not set'),
                'zone_to': order.dropoff_zone_id.name if order.dropoff_zone_id else _('Not set'),
                'truck': vehicle_type_name,
                'date': create_date,
                'create_date': create_date,
                'scheduled_datetime': scheduled_date,
                'approve_date': approve_date,
                'amount': order.amount_total or order.amount_untaxed or 0,
                'formatted_amount': order.currency_id.format(order.amount_total or order.amount_untaxed or 0),
                'currency_symbol': order.currency_id.symbol or '',
                'currency_id': order.currency_id,
                'order': order,
                'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Not assigned',
                'logspace_state': order.logspace_state,
                'has_rating': bool(order.logspace_customer_rating),
            })

        return result

    def _get_real_order_timeline(self, order):
        """Get full timeline showing all statuses with actual or estimated times."""
        from datetime import timedelta

        # Get user timezone for display
        user_tz_name = (
            request.env.user.tz
            or request.env.context.get('tz')
            or request.env.user.partner_id.tz
            or 'UTC'
        )
        try:
            user_tz = pytz.timezone(user_tz_name)
        except pytz.UnknownTimeZoneError:
            user_tz = pytz.utc
        utc_tz = pytz.utc

        timeline = []

        # Define all timeline statuses in order
        state_sequence = [
            'booked', 'payment_received',
            'order_received', 'pickup_started', 'vendor_arrived_pickup',
            'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
            'arrived_destination', 'dropoff_completed', 'grace_period', 'order_completed'
        ]

        # Event display info
        event_type_map = {
            'booked': {'label': _('Booked'), 'icon': 'fa-calendar-check-o'},
            'payment_received': {'label': _('Payment Received'), 'icon': 'fa-credit-card'},
            'order_received': {'label': _('Order Received'), 'icon': 'fa-inbox'},
            'pickup_started': {'label': _('Pickup Started'), 'icon': 'fa-play-circle'},
            'vendor_arrived_pickup': {'label': _('Vendor Arrived at Pickup'), 'icon': 'fa-map-marker'},
            'pickup_addons': {'label': _('Pickup Add-ons Performed'), 'icon': 'fa-plus-circle'},
            'pickup_completed': {'label': _('Pickup Completed'), 'icon': 'fa-check-circle'},
            'pre_dropoff_addons': {'label': _('Pre-Drop-off Add-ons'), 'icon': 'fa-cogs'},
            'arrived_destination': {'label': _('Arrived at Destination'), 'icon': 'fa-flag'},
            'dropoff_completed': {'label': _('Drop-off Completed'), 'icon': 'fa-arrow-circle-down'},
            'grace_period': {'label': _('Grace Period'), 'icon': 'fa-clock-o'},
            'order_completed': {'label': _('Order Completed'), 'icon': 'fa-trophy'},
        }

        # Build a map of recorded events by type
        recorded_events = {}
        for event in order.timeline_ids:
            recorded_events[event.event_type] = event

        # Find current state index
        current_idx = state_sequence.index(order.logspace_state) if order.logspace_state in state_sequence else -1

        # -----------------------------------------------------------------
        # Compute estimated times for future states
        # -----------------------------------------------------------------
        # Arrival states (vendor_arrived_pickup, arrived_destination) derive
        # their duration from zone distance — they represent the driver arriving
        # after traveling.  All other states use the configurable duration model.
        TRAVEL_STATES = {'vendor_arrived_pickup', 'arrived_destination'}

        duration_map = {}
        try:
            ConfigModel = request.env['logspace.state.duration.config'].sudo()
            duration_map = ConfigModel.get_duration_map()
        except Exception:
            pass

        # Determine travel minutes from zone distance data
        travel_to_pickup_min = 0
        travel_to_dropoff_min = 0
        ZoneDist = request.env['logspace.zone.distance'].sudo()
        if order.pickup_zone_id and order.dropoff_zone_id:
            # Look up zone distance using hierarchical fallback
            pickup_dist_rec = ZoneDist.get_distance_record(
                order.pickup_zone_id, order.dropoff_zone_id
            )
            if pickup_dist_rec:
                if pickup_dist_rec.estimated_minutes:
                    travel_to_pickup_min = pickup_dist_rec.estimated_minutes
                elif pickup_dist_rec.estimated_km:
                    # Fallback: ~40 km/h average in city
                    travel_to_pickup_min = int(pickup_dist_rec.estimated_km / 40.0 * 60)

            # Travel to dropoff: same route distance
            travel_to_dropoff_min = travel_to_pickup_min

        # Build per-state duration list (minutes from one state to the next)
        state_durations = {}
        for s in state_sequence:
            if s in ('booked', 'payment_received'):
                # Pre-workflow states: not estimated
                state_durations[s] = 0
            elif s in TRAVEL_STATES:
                # Use zone-based travel time; fallback to config
                if s == 'vendor_arrived_pickup':
                    state_durations[s] = travel_to_pickup_min or duration_map.get(s, 20)
                elif s == 'arrived_destination':
                    state_durations[s] = travel_to_dropoff_min or duration_map.get(s, 20)
            else:
                state_durations[s] = duration_map.get(s, 5)

        # Find the base datetime for estimation: use order.create_date or now
        base_dt = order.create_date or fields.Datetime.now()

        # Build cumulative estimated datetimes for each state from current onward
        # States before or at the current state don't need estimation
        estimated_dt = {}
        cumulative = base_dt
        for s in state_sequence:
            idx = state_sequence.index(s)
            if idx <= current_idx:
                # Past or current: use recorded time if available
                rec_event = recorded_events.get(s)
                if rec_event and rec_event.event_time:
                    cumulative = rec_event.event_time
                elif s == 'order_received' and order.create_date:
                    cumulative = order.create_date
                estimated_dt[s] = cumulative
            else:
                # Future state: add this state's duration
                cumulative = cumulative + timedelta(minutes=state_durations.get(s, 5))
                estimated_dt[s] = cumulative

        # Helper: format a UTC datetime in the user's timezone
        def _fmt_dt(dt):
            if not dt:
                return ''
            if dt.tzinfo is None:
                dt = utc_tz.localize(dt)
            local_dt = dt.astimezone(user_tz)
            # Format: "Jun 30, 14:30 Asia/Muscat (UTC+4)"
            utc_offset = local_dt.utcoffset()
            total_seconds = int(utc_offset.total_seconds())
            hours, remainder = divmod(abs(total_seconds), 3600)
            minutes = remainder // 60
            sign = '+' if total_seconds >= 0 else '-'
            if minutes:
                offset_str = f'UTC{sign}{hours}:{minutes:02d}'
            else:
                offset_str = f'UTC{sign}{hours}'
            tz_name = user_tz_name  # e.g. "Asia/Muscat"
            return local_dt.strftime('%b %d, %H:%M') + f' {tz_name} ({offset_str})'

        # Build timeline showing all statuses
        for i, status in enumerate(state_sequence):
            event_info = event_type_map.get(status)
            if not event_info:
                continue

            is_current = order.logspace_state == status
            is_done = i <= current_idx

            # Get time from recorded event if available
            recorded_event = recorded_events.get(status)
            is_estimated = False
            if recorded_event and recorded_event.event_time:
                time_str = _fmt_dt(recorded_event.event_time)
            elif status == 'order_received' and order.create_date:
                time_str = _fmt_dt(order.create_date)
            elif is_done:
                # Done but no recorded event — show as completed
                time_str = _('Completed')
            else:
                # Future state — show estimated time
                est_dt = estimated_dt.get(status)
                if est_dt:
                    time_str = '%s: %s' % (_('Estimated'), _fmt_dt(est_dt))
                    is_estimated = True
                else:
                    time_str = _('Expected')

            timeline.append({
                'status': status,
                'label': event_info['label'],
                'time': time_str,
                'estimated': is_estimated,
                'done': is_done,
                'current': is_current,
                'icon': event_info['icon'],
            })

        return timeline

    def _get_zone_hierarchical_address(self, zone):
        """Build full address by walking up the zone parent chain.

        If a country-type zone exists at the top (e.g. Oman), it appears
        naturally in the path.
        """
        if not zone:
            return ""
        parts = []
        curr = zone
        while curr:
            if curr.name and curr.name not in parts:
                parts.append(curr.name)
            curr = curr.parent_id

        return ", ".join(parts)

    def _calculate_dropoff_timeframe(self, zone_from_id, zone_to_id, pickup_timeframe):
        """Calculate dropoff timeframe based on distance and configured delay.

        Returns the calculated dropoff timeframe string ('morning', 'afternoon', 'evening')
        or empty string if calculation fails.
        """
        if not zone_from_id or not zone_to_id or not pickup_timeframe:
            return ''

        dist_rec = request.env['logspace.zone.distance'].sudo().search([
            ('zone_from_id', '=', zone_from_id),
            ('zone_to_id', '=', zone_to_id),
        ], limit=1)

        if not dist_rec:
            return ''

        extra_delay = int(request.env['ir.config_parameter'].sudo().get_param(
            'appness_logspace.dropoff_delay_minutes', 30
        ))
        total_min = dist_rec.estimated_minutes + extra_delay
        start_h = request.env['logspace.time.slot']._start_hour_by_code().get(pickup_timeframe, 6)
        drop_h = start_h + (total_min / 60)

        if drop_h < 12:
            return 'morning'
        elif drop_h < 18:
            return 'afternoon'
        else:
            return 'evening'

    def _get_validated_booking_data(self, booking_data):
        """Replace all client-controlled booking identifiers and prices with records."""
        required_ids = (
            'price_matrix_id', 'provider_id', 'vehicle_type_id', 'zone_from_id',
            'zone_to_id', 'vehicle_id',
        )
        try:
            identifiers = {
                field_name: int(booking_data.get(field_name) or 0)
                for field_name in required_ids
            }
        except (TypeError, ValueError):
            raise ValidationError(_('The selected booking is invalid.'))
        if any(value <= 0 for value in identifiers.values()):
            raise ValidationError(_('The selected booking is incomplete.'))

        selection = request.env['logspace.price.matrix'].sudo()._validate_booking_selection(
            matrix_id=identifiers['price_matrix_id'],
            provider_id=identifiers['provider_id'],
            vehicle_type_id=identifiers['vehicle_type_id'],
            zone_from_id=identifiers['zone_from_id'],
            zone_to_id=identifiers['zone_to_id'],
            vehicle_id=identifiers['vehicle_id'],
            pickup_date=booking_data.get('pickup_date'),
        )
        addon_values = selection['matrix']._get_validated_booking_addons(
            booking_data.get('addon_ids', [])
        )
        trusted_data = dict(booking_data, **identifiers)
        trusted_data.update({
            'price': selection['price'],
            'addon_ids': [value['addon'].id for value in addon_values],
        })
        return trusted_data, selection, addon_values

    def _calculate_booking_total(self, booking_data):
        """Calculate total, tax, and breakdown from booking session data."""
        booking_data, selection, addon_values = self._get_validated_booking_data(booking_data)
        truck_price = selection['price']
        addon_lines_data = [{
            'product_tmpl_id': value['addon'].product_tmpl_id.id
            if value['addon'].product_tmpl_id else False,
            'price': value['price'],
            'name': value['addon'].name,
        } for value in addon_values]
        addon_total = sum(value['price'] for value in addon_values)

        subtotal = truck_price + addon_total
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref('appness_logspace.product_logspace_service_product_template', raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search([('default_code', '=', 'LOGSPACE-SVC')], limit=1)

        tax_amount = 0.0
        currency = selection['currency']
        if service_product_tmpl and service_product_tmpl.exists() and service_product_tmpl.taxes_id:
            taxes = service_product_tmpl.taxes_id.compute_all(truck_price, currency=currency, quantity=1, product=service_product_tmpl)
            tax_amount += taxes['total_included'] - taxes['total_excluded']
        for addon_line in addon_lines_data:
            if addon_line.get('product_tmpl_id'):
                addon_prod_tmpl = ProductTmpl.browse(addon_line['product_tmpl_id'])
                if addon_prod_tmpl.exists() and addon_prod_tmpl.taxes_id:
                    taxes = addon_prod_tmpl.taxes_id.compute_all(addon_line['price'], currency=currency, quantity=1, product=addon_prod_tmpl)
                    tax_amount += taxes['total_included'] - taxes['total_excluded']

        return {
            'truck_price': truck_price,
            'addon_total': addon_total,
            'subtotal': subtotal,
            'tax': tax_amount if tax_amount > 0 else 0.0,
            'total': subtotal + (tax_amount if tax_amount > 0 else 0.0),
            'currency': currency,
            'addon_lines': addon_lines_data,
        }

    def _create_logspace_sale_order(self, booking_data, partner, order=None):
        """Create or fully refresh a session-owned draft sale order."""
        booking_data, selection, addon_values = self._get_validated_booking_data(booking_data)
        truck_price = selection['price']
        pricelist = partner.property_product_pricelist
        if not pricelist or pricelist.currency_id != selection['currency']:
            raise ValidationError(_(
                'The selected route currency is not available for this customer.'
            ))

        # Get service product
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref(
            'appness_logspace.product_logspace_service_product_template',
            raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search(
                [('default_code', '=', 'LOGSPACE-SVC')], limit=1)
        service_product = False
        if service_product_tmpl:
            service_product = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', service_product_tmpl.id)], limit=1)

        addon_lines_data = []
        for value in addon_values:
            addon = value['addon']
            addon_product = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', addon.product_tmpl_id.id)], limit=1
            ) if addon.product_tmpl_id else False
            addon_lines_data.append({
                'product': addon_product,
                'price': value['price'],
                'name': addon.name,
            })

        # Build order lines
        order_lines = []
        if service_product:
            order_lines.append((0, 0, {
                'product_id': service_product.id, 'name': service_product.name,
                'product_uom_qty': 1, 'price_unit': truck_price,
            }))
        else:
            order_lines.append((0, 0, {
                'name': 'Logspace Transport Service', 'product_uom_qty': 1, 'price_unit': truck_price,
            }))
        for addon_data in addon_lines_data:
            if addon_data.get('product'):
                order_lines.append((0, 0, {
                    'product_id': addon_data['product'].id, 'name': addon_data['name'],
                    'product_uom_qty': 1, 'price_unit': addon_data['price'],
                }))
            else:
                order_lines.append((0, 0, {
                    'name': addon_data['name'], 'product_uom_qty': 1, 'price_unit': addon_data['price'],
                }))

        # Get vehicle and driver
        vehicle_id = booking_data.get('vehicle_id')
        driver_id = False
        if vehicle_id:
            vehicle = request.env['logspace.vehicle'].sudo().browse(vehicle_id)
            if vehicle.exists():
                vehicle_id = vehicle.id
                driver_id = vehicle.driver_id.id if vehicle.driver_id else False

        is_public = not request.env.user or request.env.user._is_public()
        guest_email = booking_data.get('guest_email', '')

        # Resolve provider's user_id for salesperson assignment
        provider_user_id = False
        provider_partner = request.env['res.partner'].sudo().browse(booking_data.get('provider_id'))
        if provider_partner and provider_partner.user_ids:
            provider_user_id = provider_partner.user_ids[0].id

        order_values = {
            'partner_id': partner.id,
            'pricelist_id': pricelist.id,
            'is_logspace_order': True,
            'logspace_provider_id': booking_data.get('provider_id'),
            'logspace_vehicle_id': vehicle_id,
            'logspace_driver_id': driver_id,
            # Snapshot of what the matrix quoted; the completion bill pays the
            # quoted provider price instead of re-deriving the commission from
            # the customer subtotal (which would charge fee on the fee).
            'logspace_quoted_provider_price': selection['matrix'].provider_price,
            'logspace_quoted_platform_fee': selection['matrix'].platform_fee,
            'pickup_zone_id': booking_data.get('zone_from_id'),
            'dropoff_zone_id': booking_data.get('zone_to_id'),
            'pickup_address': booking_data.get('pickup_address'),
            'dropoff_address': booking_data.get('dropoff_address'),
            'pickup_contact_name': booking_data.get('pickup_contact_name'),
            'pickup_contact_phone': booking_data.get('pickup_contact_phone'),
            'dropoff_contact_name': booking_data.get('dropoff_contact_name'),
            'dropoff_contact_phone': booking_data.get('dropoff_contact_phone'),
            'scheduled_date': booking_data.get('pickup_date'),
            'pickup_timeframe': booking_data.get('pickup_timeframe'),
            'dropoff_timeframe': booking_data.get('dropoff_timeframe'),
            'item_description': booking_data.get('item_description'),
            'is_guest_order': is_public and bool(guest_email),
            'guest_email': guest_email if is_public else False,
            'guest_phone': booking_data.get('guest_phone') if is_public else False,
            'user_id': provider_user_id,
            'order_line': ([(5, 0, 0)] + order_lines) if order else order_lines,
        }

        if order:
            order.write(order_values)
        else:
            order = request.env['sale.order'].sudo().create(order_values)

        order.logspace_addon_ids = [(6, 0, booking_data.get('addon_ids', []))]

        return order

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
