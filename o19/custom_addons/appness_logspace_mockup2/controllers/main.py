# -*- coding: utf-8 -*-
from odoo import http, fields, Command
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
import random


class LogspaceMockup2(http.Controller):
    """Main controller for Logspace Mockup 2 - 23 interconnected screens"""

    def _get_mock_context(self, extra=None):
        """Get base context with mock data flag"""
        ctx = {'is_mockup': True}
        if extra:
            ctx.update(extra)
        return ctx

    # ========== DUMMY DATA ==========

    def _get_trucks(self):
        """Return dummy truck listings with enhanced info"""
        return [
            {
                'id': 1,
                'name': 'Flatbed Truck 3T',
                'vendor': 'ABC Logistics',
                'vendor_id': 1,
                'price': 150.0,
                'rating': 4.5,
                'reviews': 128,
                'image': '/appness_logspace_mockup2/static/src/img/truck_flatbed.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['GPS Tracking', 'Insurance Included', '3 Ton Capacity'],
                'pickup_timeframe': '10:00 AM - 12:00 PM',
                'dropoff_timeframe': '2:00 PM - 4:00 PM',
                'city_location': 'New York, NY',
                'storage_dimensions': '300 x 200 x 150 cm',
                'service_type': 'Flatbed Truck',
            },
            {
                'id': 2,
                'name': 'Box Truck 5T',
                'vendor': 'Fast Movers Ltd',
                'vendor_id': 2,
                'price': 200.0,
                'rating': 4.8,
                'reviews': 256,
                'image': '/appness_logspace_mockup2/static/src/img/truck_box.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['Refrigerated', '5 Ton Capacity', 'Real-time Tracking'],
                'pickup_timeframe': '9:00 AM - 11:00 AM',
                'dropoff_timeframe': '3:00 PM - 5:00 PM',
                'city_location': 'Los Angeles, CA',
                'storage_dimensions': '450 x 220 x 230 cm',
                'service_type': 'Box Truck',
            },
            {
                'id': 3,
                'name': 'Mini Truck 1T',
                'vendor': 'City Express',
                'vendor_id': 3,
                'price': 80.0,
                'rating': 4.2,
                'reviews': 89,
                'image': '/appness_logspace_mockup2/static/src/img/truck_mini.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['Compact', 'City Access', '1 Ton Capacity'],
                'pickup_timeframe': '1:00 PM - 3:00 PM',
                'dropoff_timeframe': '5:00 PM - 7:00 PM',
                'city_location': 'Chicago, IL',
                'storage_dimensions': '200 x 150 x 120 cm',
                'service_type': 'Mini Truck',
            },
            {
                'id': 4,
                'name': 'Heavy Hauler 10T',
                'vendor': 'Industrial Transports',
                'vendor_id': 4,
                'price': 350.0,
                'rating': 4.9,
                'reviews': 312,
                'image': '/appness_logspace_mockup2/static/src/img/truck_heavy.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['10 Ton Capacity', 'Long Distance', 'Full Insurance'],
                'pickup_timeframe': '8:00 AM - 10:00 AM',
                'dropoff_timeframe': '4:00 PM - 6:00 PM',
                'city_location': 'Houston, TX',
                'storage_dimensions': '600 x 250 x 280 cm',
                'service_type': 'Heavy Hauler',
            },
            {
                'id': 5,
                'name': 'Pickup Truck',
                'vendor': 'Quick Delivery',
                'vendor_id': 5,
                'price': 60.0,
                'rating': 4.0,
                'reviews': 64,
                'image': '/appness_logspace_mockup2/static/src/img/truck_pickup.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['Small Loads', 'Express', 'Same Day'],
                'pickup_timeframe': '11:00 AM - 1:00 PM',
                'dropoff_timeframe': '3:00 PM - 5:00 PM',
                'city_location': 'Phoenix, AZ',
                'storage_dimensions': '180 x 120 x 60 cm',
                'service_type': 'Pickup Truck',
            },
            {
                'id': 6,
                'name': 'Refrigerated Truck 5T',
                'vendor': 'Cold Chain Solutions',
                'vendor_id': 6,
                'price': 250.0,
                'rating': 4.7,
                'reviews': 178,
                'image': '/appness_logspace_mockup2/static/src/img/truck_reefer.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
                'features': ['Temperature Controlled', '5 Ton Capacity', 'Food Grade'],
                'pickup_timeframe': '7:00 AM - 9:00 AM',
                'dropoff_timeframe': '1:00 PM - 3:00 PM',
                'city_location': 'Seattle, WA',
                'storage_dimensions': '420 x 210 x 220 cm',
                'service_type': 'Refrigerated Truck',
            },
        ]

    def _get_vendor(self, vendor_id):
        """Return dummy vendor details with enhanced info"""
        vendors = {
            1: {
                'id': 1,
                'name': 'ABC Logistics',
                'rating': 4.5,
                'reviews': 128,
                'trips': 3420,
                'joined': '2020-03-15',
                'description': 'Professional logistics company specializing in flatbed transportation for construction and industrial materials.',
                'phone': '+1 555-0101',
                'email': 'contact@abclogistics.com',
                'price_per_km': 2.5,
                'base_price': 50.0,
                'service_name': 'Flatbed Truck 3T',
                'about_service': 'Our flatbed trucks are perfect for transporting construction materials, heavy equipment, and oversized loads. All trucks come with securing straps, tarps, and GPS tracking for real-time monitoring.',
                'storage_dimensions': '300 x 200 x 150 cm',
                'storage_details': 'Flatbed surface: 3m length x 2m width. Maximum height clearance: 1.5m. Load capacity: 3 tons (3,000 kg).',
                'required_documents': ['Valid ID', 'Delivery Note', 'Insurance Certificate'],
                'pickup_timeframe': '10:00 AM - 12:00 PM',
                'dropoff_timeframe': '2:00 PM - 4:00 PM',
                'city_location': 'New York, NY',
                'available_timeframes': [
                    '10:00 AM - 12:00 PM',
                    '12:00 PM - 2:00 PM',
                    '2:00 PM - 4:00 PM',
                    '4:00 PM - 6:00 PM',
                ],
                'image': '/appness_logspace_mockup2/static/src/img/truck_flatbed.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
            },
            2: {
                'id': 2,
                'name': 'Fast Movers Ltd',
                'rating': 4.8,
                'reviews': 256,
                'trips': 5210,
                'joined': '2019-08-22',
                'description': 'Fast and reliable moving services with modern refrigerated fleet for perishable goods.',
                'phone': '+1 555-0102',
                'email': 'book@fastmovers.com',
                'price_per_km': 3.0,
                'base_price': 75.0,
                'service_name': 'Box Truck 5T',
                'about_service': 'Climate-controlled box trucks ideal for moving household goods, furniture, and temperature-sensitive items. Fully equipped with loading ramps, dollies, and blankets.',
                'storage_dimensions': '450 x 220 x 230 cm',
                'storage_details': 'Enclosed cargo box: 4.5m length x 2.2m width x 2.3m height. Load capacity: 5 tons (5,000 kg). Climate control available.',
                'required_documents': ['Valid ID', 'Packing List', 'Temperature Requirements (if applicable)'],
                'pickup_timeframe': '9:00 AM - 11:00 AM',
                'dropoff_timeframe': '3:00 PM - 5:00 PM',
                'city_location': 'Los Angeles, CA',
                'available_timeframes': [
                    '8:00 AM - 10:00 AM',
                    '9:00 AM - 11:00 AM',
                    '11:00 AM - 1:00 PM',
                    '3:00 PM - 5:00 PM',
                ],
                'image': '/appness_logspace_mockup2/static/src/img/truck_box.jpg',
                'logo': '/appness_logspace_mockup2/static/description/logo.png',
            },
        }
        return vendors.get(vendor_id, vendors[1])

    def _get_addons(self):
        """Return available add-ons for booking"""
        return [
            {'id': 1, 'name': 'Loading Assistance', 'price': 25.0, 'description': 'Professional loading service'},
            {'id': 2, 'name': 'Unloading Assistance', 'price': 25.0, 'description': 'Professional unloading service'},
            {'id': 3, 'name': 'Express Delivery', 'price': 50.0, 'description': 'Same day priority delivery'},
            {'id': 4, 'name': 'Fragile Handling', 'price': 30.0, 'description': 'Extra care for delicate items'},
            {'id': 5, 'name': 'Return Service', 'price': 40.0, 'description': 'Round trip for return items'},
        ]

    def _get_order_timeline(self):
        """Return order tracking timeline (NO MAP) - 10 statuses"""
        return [
            {'status': 'order_received', 'label': 'Order Received', 'time': 'Jan 15, 09:00', 'done': True, 'current': False, 'icon': 'fa-inbox'},
            {'status': 'pickup_started', 'label': 'Pickup Started', 'time': 'Jan 15, 09:45', 'done': True, 'current': False, 'icon': 'fa-play-circle'},
            {'status': 'vendor_arrived_pickup', 'label': 'Vendor Arrived at Pickup', 'time': 'Jan 15, 10:15', 'done': True, 'current': False, 'icon': 'fa-map-marker'},
            {'status': 'pickup_addons', 'label': 'Pickup Add-ons Performed', 'time': 'Jan 15, 10:30', 'done': True, 'current': False, 'icon': 'fa-plus-circle'},
            {'status': 'pickup_completed', 'label': 'Pickup Completed', 'time': 'Jan 15, 10:50', 'done': True, 'current': False, 'icon': 'fa-check-circle'},
            {'status': 'pre_dropoff_addons', 'label': 'Pre-Drop-off Add-ons', 'time': 'Jan 15, 12:30', 'done': True, 'current': True, 'icon': 'fa-cogs'},
            {'status': 'arrived_destination', 'label': 'Arrived at Destination', 'time': 'Expected 13:30', 'done': False, 'current': False, 'icon': 'fa-flag'},
            {'status': 'dropoff_completed', 'label': 'Drop-off Completed', 'time': 'Expected 14:00', 'done': False, 'current': False, 'icon': 'fa-arrow-circle-down'},
            {'status': 'grace_period', 'label': 'Grace Period', 'time': 'Expected 14:30', 'done': False, 'current': False, 'icon': 'fa-clock-o'},
            {'status': 'order_completed', 'label': 'Order Completed', 'time': 'Expected 15:00', 'done': False, 'current': False, 'icon': 'fa-trophy'},
        ]

    def _get_notifications(self):
        """Return dummy notifications"""
        return [
            {'id': 1, 'title': 'Order Picked Up', 'message': 'Your order #LOG-1234 has been picked up', 'time': '10 mins ago', 'type': 'info', 'read': False},
            {'id': 2, 'title': 'Driver Arriving', 'message': 'Driver will arrive at pickup location in 15 mins', 'time': '1 hour ago', 'type': 'success', 'read': False},
            {'id': 3, 'title': 'Payment Confirmed', 'message': 'Payment of $250 received for order #LOG-1234', 'time': '3 hours ago', 'type': 'success', 'read': True},
            {'id': 4, 'title': 'Promotion', 'message': 'Get 20% off your next booking with code LOG20', 'time': '1 day ago', 'type': 'warning', 'read': True},
        ]

    def _get_orders(self, status=None):
        """Return dummy orders with enhanced date and verification info"""
        orders = [
            {
                'id': 'LOG-1234',
                'status': 'in_transit',
                'status_label': 'In Transit',
                'pickup': '123 Main St, City',
                'dropoff': '456 Oak Ave, Town',
                'truck': 'Flatbed Truck 3T',
                'date': 'Jan 15, 2025',
                'amount': 250.0,
                'vendor': 'ABC Logistics',
                'create_date': 'Jan 14, 2025 09:30',
                'scheduled_datetime': 'Jan 15, 2025',
                'approve_date': 'Jan 14, 2025 14:15',
                'pickup_timeframe': '10:00 AM - 12:00 PM',
                'dropoff_timeframe': '2:00 PM - 4:00 PM',
                'pickup_verification_code': '7842',
                'dropoff_verification_code': '9321',
            },
            {
                'id': 'LOG-1235',
                'status': 'completed',
                'status_label': 'Delivered',
                'pickup': '789 Pine Rd, City',
                'dropoff': '321 Elm St, Town',
                'truck': 'Box Truck 5T',
                'date': 'Jan 10, 2025',
                'amount': 180.0,
                'vendor': 'Fast Movers Ltd',
                'create_date': 'Jan 8, 2025 16:45',
                'scheduled_datetime': 'Jan 10, 2025',
                'approve_date': 'Jan 9, 2025 10:20',
                'pickup_timeframe': '9:00 AM - 11:00 AM',
                'dropoff_timeframe': '3:00 PM - 5:00 PM',
                'pickup_verification_code': '1234',
                'dropoff_verification_code': '5678',
            },
            {
                'id': 'LOG-1236',
                'status': 'pending',
                'status_label': 'Pending',
                'pickup': '555 Cedar Ln, City',
                'dropoff': '777 Maple Dr, Town',
                'truck': 'Mini Truck 1T',
                'date': 'Jan 18, 2025',
                'amount': 120.0,
                'vendor': 'City Express',
                'create_date': 'Jan 16, 2025 11:20',
                'scheduled_datetime': 'Jan 18, 2025',
                'approve_date': 'Jan 17, 2025 09:10',
                'pickup_timeframe': '1:00 PM - 3:00 PM',
                'dropoff_timeframe': '5:00 PM - 7:00 PM',
                'pickup_verification_code': '9012',
                'dropoff_verification_code': None,
            },
            {
                'id': 'LOG-1237',
                'status': 'cancelled',
                'status_label': 'Cancelled',
                'pickup': '999 Birch Blvd, City',
                'dropoff': '111 Spruce Way, Town',
                'truck': 'Pickup Truck',
                'date': 'Jan 5, 2025',
                'amount': 60.0,
                'vendor': 'Quick Delivery',
                'create_date': 'Jan 3, 2025 14:00',
                'scheduled_datetime': 'Jan 5, 2025',
                'approve_date': None,
                'pickup_timeframe': '11:00 AM - 1:00 PM',
                'dropoff_timeframe': '3:00 PM - 5:00 PM',
                'pickup_verification_code': None,
                'dropoff_verification_code': None,
            },
        ]
        if status and status != 'all':
            status_map = {
                'active': ['in_transit', 'pending'],
                'completed': ['completed'],
                'cancelled': ['cancelled']
            }
            return [o for o in orders if o['status'] in status_map.get(status, [status])]
        return orders

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
            create_date = order.create_date.strftime('%b %d, %Y') if order.create_date else 'N/A'
            scheduled_date = order.scheduled_date.strftime('%b %d, %Y') if order.scheduled_date else 'N/A'
            approve_date = False
            if order.logspace_state != 'order_received' and order.write_date:
                approve_date = order.write_date.strftime('%b %d, %Y')

            result.append({
                'id': order.name,
                'order_id': order.id,
                'status': state_category_map.get(order.logspace_state, 'pending'),
                'status_label': order.logspace_state.replace('_', ' ').title() if order.logspace_state else 'Order Received',
                'pickup': order.pickup_address or 'Not set',
                'dropoff': order.dropoff_address or 'Not set',
                'zone_from': order.pickup_zone_id.name if order.pickup_zone_id else 'Not set',
                'zone_to': order.dropoff_zone_id.name if order.dropoff_zone_id else 'Not set',
                'truck': vehicle_type_name,
                'date': create_date,
                'create_date': create_date,
                'scheduled_datetime': scheduled_date,
                'approve_date': approve_date,
                'amount': order.amount_total or order.amount_untaxed or 0,
                'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Not assigned',
                'logspace_state': order.logspace_state,
            })

        return result

    def _get_real_order_timeline(self, order):
        """Get full timeline showing all statuses with actual times from recorded events"""
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
            'booked': {'label': 'Booked', 'icon': 'fa-calendar-check-o'},
            'payment_received': {'label': 'Payment Received', 'icon': 'fa-credit-card'},
            'order_received': {'label': 'Order Received', 'icon': 'fa-inbox'},
            'pickup_started': {'label': 'Pickup Started', 'icon': 'fa-play-circle'},
            'vendor_arrived_pickup': {'label': 'Vendor Arrived at Pickup', 'icon': 'fa-map-marker'},
            'pickup_addons': {'label': 'Pickup Add-ons Performed', 'icon': 'fa-plus-circle'},
            'pickup_completed': {'label': 'Pickup Completed', 'icon': 'fa-check-circle'},
            'pre_dropoff_addons': {'label': 'Pre-Drop-off Add-ons', 'icon': 'fa-cogs'},
            'arrived_destination': {'label': 'Arrived at Destination', 'icon': 'fa-flag'},
            'dropoff_completed': {'label': 'Drop-off Completed', 'icon': 'fa-arrow-circle-down'},
            'grace_period': {'label': 'Grace Period', 'icon': 'fa-clock-o'},
            'order_completed': {'label': 'Order Completed', 'icon': 'fa-trophy'},
        }

        # Build a map of recorded events by type
        recorded_events = {}
        for event in order.timeline_ids:
            recorded_events[event.event_type] = event

        # Find current state index
        current_idx = state_sequence.index(order.logspace_state) if order.logspace_state in state_sequence else -1

        # Build timeline showing all statuses
        for i, status in enumerate(state_sequence):
            event_info = event_type_map.get(status)
            if not event_info:
                continue

            is_current = order.logspace_state == status
            is_done = i <= current_idx

            # Get time from recorded event if available
            recorded_event = recorded_events.get(status)
            if recorded_event and recorded_event.event_time:
                time_str = recorded_event.event_time.strftime('%b %d, %H:%M')
            elif status == 'order_received' and order.create_date:
                time_str = order.create_date.strftime('%b %d, %H:%M')
            else:
                time_str = 'Expected'

            timeline.append({
                'status': status,
                'label': event_info['label'],
                'time': time_str,
                'done': is_done,
                'current': is_current,
                'icon': event_info['icon'],
            })

        return timeline

    # ========== CUSTOMER SCREENS ==========

    # Screen 1 & 2: Search and Results (combined) - REAL DATA
    @http.route(['/logspace', '/logspace/search'], type='http', auth='public', website=True, csrf=False)
    def mockup_search(self, **kwargs):
        """Screen 1 & 2: Search page with real results from price matrix"""
        # Get all zones and vehicle types for the search form
        # Only show leaf zones (zones without children) - parent zones shouldn't be selectable
        all_zones = request.env['logspace.zone'].sudo().search([('active', '=', True)])
        zones = all_zones.filtered(lambda z: not z.child_ids)
        vehicle_types = request.env['logspace.vehicle.type'].sudo().search([('active', '=', True)])

        # Initialize context — no results by default; user must search
        ctx = {
            'zones': zones,
            'vehicle_types': vehicle_types,
            'show_results': False,
            'results': [],
            'search_params': {},
            'is_filtered_search': False,
        }

        # Always populate search_params from kwargs so the form retains values
        zone_from_id = int(kwargs.get('zone_from_id', 0))
        zone_to_id = int(kwargs.get('zone_to_id', 0))
        vehicle_type_id = int(kwargs.get('vehicle_type_id', 0))
        pickup_date = kwargs.get('pickup_date', '')
        pickup_timeframe = kwargs.get('pickup_timeframe', '')
        dropoff_timeframe = kwargs.get('dropoff_timeframe', '')

        ctx['search_params'] = {
            'zone_from_id': zone_from_id,
            'zone_to_id': zone_to_id,
            'vehicle_type_id': vehicle_type_id,
            'pickup_date': pickup_date,
            'pickup_timeframe': pickup_timeframe,
            'dropoff_timeframe': dropoff_timeframe,
        }

        # Check if this is a filtered search (user clicked search button)
        is_filtered = request.httprequest.method == 'POST' or kwargs.get('zone_from_id')

        if is_filtered:
            ctx['is_filtered_search'] = True

            # Only search if all required params provided
            if zone_from_id and zone_to_id and vehicle_type_id:
                results = []

                # Step 1: Find price matrices for this route with this vehicle type
                price_matrices = request.env['logspace.price.matrix'].sudo().search([
                    ('vehicle_type_id', '=', vehicle_type_id),
                    ('zone_from_id', '=', zone_from_id),
                    ('zone_to_id', '=', zone_to_id),
                    ('is_active', '=', True),
                    ('provider_id.is_provider', '=', True),
                    ('provider_id.state', '=', 'approved'),
                ])

                for matrix in price_matrices:
                    provider = matrix.provider_id

                    # Step 2: Get vehicles available for this provider/type/zones on the requested date
                    vehicles = request.env['logspace.vehicle'].sudo().get_available_vehicles(
                        provider_id=provider.id,
                        vehicle_type_id=vehicle_type_id,
                        zone_from_id=zone_from_id,
                        zone_to_id=zone_to_id,
                        date_str=pickup_date or None,
                    )

                    if not vehicles:
                        continue  # Skip if no vehicles available (zone mismatch, date conflict, or non-working day)

                    # Step 3: Get available timeframes for this provider + vehicle type
                    timeframes = provider.time_frame_ids.filtered(
                        lambda t: t.vehicle_type_id.id == vehicle_type_id
                    )

                    # Check if requested pickup timeframe is available
                    timeframe_available = True
                    if pickup_timeframe and timeframes:
                        # Parse "10:00-12:00" to (10.0, 12.0)
                        try:
                            start_str, end_str = pickup_timeframe.split('-')
                            req_start = float(start_str.replace(':', '.'))
                            req_end = float(end_str.replace(':', '.'))

                            timeframe_available = any(
                                tf.time_start <= req_start and tf.time_end >= req_end
                                for tf in timeframes
                            )
                        except (ValueError, AttributeError):
                            timeframe_available = True  # If parsing fails, show all

                    # Step 4: Get special instructions for this provider + vehicle type
                    special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
                        ('partner_id', '=', provider.id),
                        ('vehicle_type_id', '=', vehicle_type_id),
                        ('is_active', '=', True),
                    ], limit=1)

                    # Get fleet count
                    fleet_summary = provider.fleet_summary_ids.filtered(
                        lambda f: f.vehicle_type_id.id == vehicle_type_id
                    )
                    fleet_count = sum(fs.fleet_count for fs in fleet_summary) or len(vehicles)

                    # Get vehicle type details
                    vehicle_type = request.env['logspace.vehicle.type'].sudo().browse(vehicle_type_id)

                    # Select first available vehicle for this provider/type/zone
                    selected_vehicle = vehicles[0] if vehicles else False

                    # Build result
                    results.append({
                        'price_matrix_id': matrix.id,
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'vehicle_type_id': vehicle_type_id,
                        'vehicle_type_name': vehicle_type.name,
                        'vehicle_type_image': vehicle_type.image_url or '/appness_logspace_mockup2/static/src/img/truck_default.jpg',
                        'vehicle_id': selected_vehicle.id if selected_vehicle else False,
                        'price': matrix.customer_price,
                        'provider_price': matrix.provider_price,
                        'platform_fee': matrix.platform_fee,
                        'rating': provider.logspace_rating or 0.0,
                        'reviews': provider.logspace_review_count or 0,
                        'zone_from': matrix.zone_from_id.name,
                        'zone_to': matrix.zone_to_id.name,
                        'zone_from_id': zone_from_id,
                        'zone_to_id': zone_to_id,
                        'timeframes': timeframes,
                        'timeframe_available': timeframe_available,
                        'requested_timeframe': pickup_timeframe,
                        'fleet_count': fleet_count,
                        'special_instructions': special_instruction.instructions if special_instruction else '',
                        'special_instruction_id': special_instruction.id if special_instruction else False,
                        # For booking link - point to vehicle info page, which then leads to booking
                        'vehicle_info_url': '/logspace/vendor/vehicle/%d?provider_id=%d&vehicle_type_id=%d&zone_from_id=%d&zone_to_id=%d&price=%s&matrix_id=%d%s%s%s' % (
                            selected_vehicle.id if selected_vehicle else 0,
                            provider.id, vehicle_type_id, zone_from_id, zone_to_id, matrix.customer_price, matrix.id,
                            '&pickup_date=%s' % pickup_date if pickup_date else '',
                            '&pickup_timeframe=%s' % pickup_timeframe if pickup_timeframe else '',
                            '&dropoff_timeframe=%s' % dropoff_timeframe if dropoff_timeframe else '',
                        ),
                    })

                ctx['results'] = results
                ctx['show_results'] = True

        return request.render('appness_logspace_mockup2.mockup2_search_page', ctx)

    def _get_all_available_vehicles(self):
        """Get all available vehicles from approved providers for default display"""
        results = []

        # Get all active price matrices from approved providers
        price_matrices = request.env['logspace.price.matrix'].sudo().search([
            ('is_active', '=', True),
            ('provider_id.is_provider', '=', True),
            ('provider_id.state', '=', 'approved'),
        ])

        for matrix in price_matrices:
            provider = matrix.provider_id
            vehicle_type = matrix.vehicle_type_id

            # Check if provider has vehicles of this type
            vehicles = request.env['logspace.vehicle'].sudo().search([
                ('provider_id', '=', provider.id),
                ('vehicle_type_id', '=', vehicle_type.id),
                ('is_active', '=', True),
            ])

            if not vehicles:
                continue

            # Get timeframes for this provider + vehicle type
            timeframes = provider.time_frame_ids.filtered(
                lambda t: t.vehicle_type_id.id == vehicle_type.id
            )

            # Get special instructions
            special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
                ('partner_id', '=', provider.id),
                ('vehicle_type_id', '=', vehicle_type.id),
                ('is_active', '=', True),
            ], limit=1)

            # Get fleet count
            fleet_summary = provider.fleet_summary_ids.filtered(
                lambda f: f.vehicle_type_id.id == vehicle_type.id
            )
            fleet_count = sum(fs.fleet_count for fs in fleet_summary) or len(vehicles)

            # Select first available vehicle
            selected_vehicle = vehicles[0] if vehicles else False

            # Build result
            results.append({
                'price_matrix_id': matrix.id,
                'provider_id': provider.id,
                'provider_name': provider.name,
                'vehicle_type_id': vehicle_type.id,
                'vehicle_type_name': vehicle_type.name,
                'vehicle_type_image': vehicle_type.image_url or '/appness_logspace_mockup2/static/src/img/truck_default.jpg',
                'vehicle_id': selected_vehicle.id if selected_vehicle else False,
                'price': matrix.customer_price,
                'provider_price': matrix.provider_price,
                'platform_fee': matrix.platform_fee,
                'rating': provider.logspace_rating or 0.0,
                'reviews': provider.logspace_review_count or 0,
                'zone_from': matrix.zone_from_id.name,
                'zone_to': matrix.zone_to_id.name,
                'zone_from_id': matrix.zone_from_id.id,
                'zone_to_id': matrix.zone_to_id.id,
                'timeframes': timeframes,
                'timeframe_available': True,
                'requested_timeframe': None,
                'fleet_count': fleet_count,
                'special_instructions': special_instruction.instructions if special_instruction else '',
                'special_instruction_id': special_instruction.id if special_instruction else False,
                # For booking link - point to vehicle info page
                'vehicle_info_url': '/logspace/vendor/vehicle/%d?provider_id=%d&vehicle_type_id=%d&zone_from_id=%d&zone_to_id=%d&price=%s&matrix_id=%d' % (
                    selected_vehicle.id if selected_vehicle else 0,
                    provider.id, vehicle_type.id, matrix.zone_from_id.id, matrix.zone_to_id.id, matrix.customer_price, matrix.id
                ),
            })

        return results

    # Screen 3: Vendor/Item Page
    @http.route(['/logspace/vendor/<int:vendor_id>'], type='http', auth='public', website=True)
    def mockup_vendor(self, vendor_id, **kwargs):
        """Screen 3: Vendor/Truck detail page (mock data, legacy)"""
        vendor = self._get_vendor(vendor_id)
        addons = self._get_addons()
        return request.render('appness_logspace_mockup2.mockup2_vendor_page',
                              self._get_mock_context({'vendor': vendor, 'addons': addons}))

    # Screen 3b: Vehicle Info Page (real data) - between search and booking
    @http.route(['/logspace/vendor/vehicle/<int:vehicle_id>'], type='http', auth='public', website=True)
    def vehicle_info(self, vehicle_id, **kwargs):
        """Show vehicle + provider + vehicle type details before booking.

        Workflow: search > vehicle info > book
        All booking params (date, timeframes, zones, price, etc.) are passed through
        from search results and forwarded to the booking page.
        """
        vehicle = request.env['logspace.vehicle'].sudo().browse(vehicle_id)
        if not vehicle.exists():
            return request.redirect('/logspace/search')

        provider = vehicle.provider_id
        vehicle_type = vehicle.vehicle_type_id
        zone = vehicle.zone_id

        # Build booking URL with all params passed through from search
        booking_params = [
            ('provider_id', kwargs.get('provider_id', provider.id)),
            ('vehicle_type_id', kwargs.get('vehicle_type_id', vehicle_type.id)),
            ('zone_from_id', kwargs.get('zone_from_id')),
            ('zone_to_id', kwargs.get('zone_to_id')),
            ('price', kwargs.get('price')),
            ('matrix_id', kwargs.get('matrix_id')),
            ('vehicle_id', vehicle_id),
            ('pickup_date', kwargs.get('pickup_date')),
            ('pickup_timeframe', kwargs.get('pickup_timeframe')),
            ('dropoff_timeframe', kwargs.get('dropoff_timeframe')),
        ]
        query_string = '&'.join('%s=%s' % (k, v) for k, v in booking_params if v)
        booking_url = '/logspace/booking/details?%s' % query_string if query_string else '/logspace/booking/details'

        # Get provider timeframes for this vehicle type
        timeframes = provider.time_frame_ids.filtered(
            lambda t: t.vehicle_type_id.id == vehicle_type.id
        )

        # Get special instructions
        special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
            ('partner_id', '=', provider.id),
            ('vehicle_type_id', '=', vehicle_type.id),
            ('is_active', '=', True),
        ], limit=1)

        return request.render('appness_logspace_mockup2.mockup2_vehicle_info_page',
                              self._get_mock_context({
                                  'vehicle': vehicle,
                                  'provider': provider,
                                  'vehicle_type': vehicle_type,
                                  'zone': zone,
                                  'timeframes': timeframes,
                                  'special_instruction': special_instruction,
                                  'booking_url': booking_url,
                                  'price': kwargs.get('price'),
                                  'pickup_date': kwargs.get('pickup_date'),
                                  'zone_from_id': kwargs.get('zone_from_id'),
                                  'zone_to_id': kwargs.get('zone_to_id'),
                              }))

    # Screen 4: Add-ons (Now Step 2) - With Session Storage
    @http.route(['/logspace/booking/addons'], type='http', auth='public', website=True, csrf=False)
    def mockup_addons(self, **kwargs):
        """Screen 4: Booking Step 2 - Add-ons with session storage"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')


        # Handle POST - save selected addons to session
        if request.httprequest.method == 'POST':
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info("ADDONS DEBUG POST: kwargs = %s", kwargs)
            addon_ids = []
            for key, value in kwargs.items():
                if key.startswith('addon_') and value:
                    addon_id = int(key.replace('addon_', ''))
                    addon_ids.append(addon_id)
            # Create a new dict copy so request.session registers the modification
            booking_data = dict(booking_data, addon_ids=addon_ids)
            request.session['logspace_booking'] = booking_data
            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            _logger.info("ADDONS DEBUG POST: booking_data after save = %s", booking_data)
            return request.redirect('/logspace/booking/checkout')

        # Get available addons for the provider and vehicle type
        available_addons = []
        if booking_data.get('provider_id') and booking_data.get('vehicle_type_id'):
            # Get provider-specific addons for this vehicle type
            provider_addons = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('vehicle_type_id', '=', booking_data['vehicle_type_id']),
                ('is_active', '=', True),
            ])
            for pa in provider_addons:
                available_addons.append({
                    'id': pa.addon_id.id,
                    'name': pa.addon_id.name,
                    'description': pa.addon_id.description,
                    'price': pa.provider_price,
                    'icon': pa.addon_id.icon or 'fa-plus',
                })

        # If no provider-specific addons, get master addons
        if not available_addons:
            master_addons = request.env['logspace.addon'].sudo().search([('active', '=', True)])
            for addon in master_addons:
                available_addons.append({
                    'id': addon.id,
                    'name': addon.name,
                    'description': addon.description,
                    'price': addon.price,
                    'icon': addon.icon or 'fa-plus',
                })

        return request.render('appness_logspace_mockup2.mockup2_addons_page',
                              self._get_mock_context({
                                  'addons': available_addons,
                                  'current_step': 2,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                              }))

    # Screen 5: Booking Details (Now Step 1) - With Session Storage
    @http.route(['/logspace/booking/details'], type='http', auth='public', website=True, csrf=False)
    def mockup_details(self, **kwargs):
        """Screen 5: Booking Step 1 - Item Details with session storage"""

        # Handle POST - save to session and redirect to add-ons
        if request.httprequest.method == 'POST':
            # Get provider special instructions
            provider_id = int(kwargs.get('provider_id', 0))
            vehicle_type_id = int(kwargs.get('vehicle_type_id', 0))
            provider_special_instructions = ''
            if provider_id and vehicle_type_id:
                special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
                    ('partner_id', '=', provider_id),
                    ('vehicle_type_id', '=', vehicle_type_id),
                ], limit=1)
                provider_special_instructions = special_instruction.instructions if special_instruction else ''

            # Get vehicle_id from URL params
            vehicle_id = int(kwargs.get('vehicle_id', 0))

            # Store booking data in session
            request.session['logspace_booking'] = {
                'provider_id': provider_id,
                'vehicle_type_id': vehicle_type_id,
                'vehicle_id': vehicle_id,
                'zone_from_id': int(kwargs.get('zone_from_id', 0)),
                'zone_to_id': int(kwargs.get('zone_to_id', 0)),
                'price_matrix_id': int(kwargs.get('price_matrix_id', 0)),
                'price': float(kwargs.get('price', 0)),
                'pickup_date': kwargs.get('pickup_date'),
                'pickup_timeframe': kwargs.get('pickup_timeframe'),
                'dropoff_timeframe': kwargs.get('dropoff_timeframe'),
                'pickup_address': kwargs.get('pickup_address'),
                'dropoff_address': kwargs.get('dropoff_address'),
                'pickup_contact_name': kwargs.get('pickup_contact_name'),
                'pickup_contact_phone': kwargs.get('pickup_contact_phone'),
                'dropoff_contact_name': kwargs.get('dropoff_contact_name'),
                'dropoff_contact_phone': kwargs.get('dropoff_contact_phone'),
                'item_description': kwargs.get('item_description'),
            }
            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/addons')

        # GET request - show form with initial data from query params or session
        booking_data = request.session.get('logspace_booking', {})

        # Allow URL params to override session data (for new searches)
        if kwargs.get('provider_id'):
            booking_data['provider_id'] = int(kwargs.get('provider_id'))
        if kwargs.get('vehicle_type_id'):
            booking_data['vehicle_type_id'] = int(kwargs.get('vehicle_type_id'))
        if kwargs.get('vehicle_id'):
            booking_data['vehicle_id'] = int(kwargs.get('vehicle_id'))
        if kwargs.get('zone_from_id'):
            booking_data['zone_from_id'] = int(kwargs.get('zone_from_id'))
        if kwargs.get('zone_to_id'):
            booking_data['zone_to_id'] = int(kwargs.get('zone_to_id'))
        if kwargs.get('price'):
            booking_data['price'] = float(kwargs.get('price'))
        if kwargs.get('matrix_id'):
            booking_data['price_matrix_id'] = int(kwargs.get('matrix_id'))
        if kwargs.get('pickup_date'):
            booking_data['pickup_date'] = kwargs.get('pickup_date')
        if kwargs.get('pickup_timeframe'):
            booking_data['pickup_timeframe'] = kwargs.get('pickup_timeframe')
        if kwargs.get('dropoff_timeframe'):
            booking_data['dropoff_timeframe'] = kwargs.get('dropoff_timeframe')

        # Get zones and vehicle types for dropdowns
        zones = request.env['logspace.zone'].sudo().search([('active', '=', True)])
        vehicle_types = request.env['logspace.vehicle.type'].sudo().search([('active', '=', True)])

        # Get available timeframes for the selected provider and vehicle type
        timeframes = request.env['logspace.provider.time.frame']
        if booking_data.get('provider_id') and booking_data.get('vehicle_type_id'):
            timeframes = request.env['logspace.provider.time.frame'].sudo().search([
                ('partner_id', '=', booking_data['provider_id']),
                ('vehicle_type_id', '=', booking_data['vehicle_type_id']),
            ])

        # Get selected zone names for display
        zone_from_name = ''
        zone_to_name = ''
        if booking_data.get('zone_from_id'):
            zone_from = request.env['logspace.zone'].sudo().browse(booking_data['zone_from_id'])
            zone_from_name = zone_from.name if zone_from.exists() else ''
        if booking_data.get('zone_to_id'):
            zone_to = request.env['logspace.zone'].sudo().browse(booking_data['zone_to_id'])
            zone_to_name = zone_to.name if zone_to.exists() else ''

        return request.render('appness_logspace_mockup2.mockup2_details_page',
                              self._get_mock_context({
                                  'current_step': 1,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'zones': zones,
                                  'vehicle_types': vehicle_types,
                                  'timeframes': timeframes,
                                  'zone_from_name': zone_from_name,
                                  'zone_to_name': zone_to_name,
                              }))

    # Screen 6: Checkout - Calculate totals from session
    @http.route(['/logspace/booking/checkout'], type='http', auth='public', website=True, csrf=True)
    def mockup_checkout(self, **kwargs):
        """Screen 6: Booking Step 3 - Checkout with calculated totals from session"""
        import datetime

        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')


        # Handle POST - save guest info, create order, and go to payment
        if request.httprequest.method == 'POST':
            import logging
            _logger = logging.getLogger(__name__)

            # Get and validate guest email
            guest_email = kwargs.get('guest_email', '').strip()
            guest_phone = kwargs.get('guest_phone', '').strip()

            if not guest_email and (not request.env.user or request.env.user._is_public()):
                return request.render('appness_logspace_mockup2.mockup2_checkout_page', {
                    'error': 'Email is required for guest checkout.',
                    'booking_data': booking_data,
                })

            is_public = not request.env.user or request.env.user._is_public()

            # Create a new dict copy so request.session registers the modification
            booking_data = dict(booking_data,
                                guest_email=guest_email.lower() if guest_email else '',
                                guest_phone=guest_phone,
                                is_guest=is_public)
            request.session['logspace_booking'] = booking_data
            request.session['logspace_guest_email'] = guest_email.lower() if guest_email else ''
            request.session['logspace_guest_phone'] = guest_phone

            # Get or create partner for the order
            if not is_public:
                partner = request.env.user.partner_id
            else:
                existing = request.env['res.partner'].sudo().search(
                    [('email', '=', guest_email.lower())], limit=1)
                if existing:
                    partner = existing
                else:
                    partner = request.env['res.partner'].sudo().create({
                        'name': booking_data.get('pickup_contact_name') or guest_email.split('@')[0],
                        'email': guest_email.lower(),
                        'phone': guest_phone,
                        'type': 'contact',
                    })

            # Create the sale order NOW (before payment) so transaction can link to it
            order = self._create_logspace_sale_order(booking_data, partner)
            request.session['logspace_order_id'] = order.id

            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/payment')

        # Calculate totals from session data
        truck_price = float(booking_data.get('price', 0) or 0)
        addon_total = 0
        selected_addons = []

        for addon_id in booking_data.get('addon_ids', []):
            # Get addon price from provider-specific or master addon
            provider_addon = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)

            if provider_addon:
                addon_price = provider_addon.provider_price
                addon_name = provider_addon.addon_id.name
                addon_product_tmpl = provider_addon.addon_id.product_tmpl_id
            else:
                master_addon = request.env['logspace.addon'].sudo().browse(addon_id)
                addon_price = master_addon.price if master_addon else 0
                addon_name = master_addon.name if master_addon else 'Unknown'
                addon_product_tmpl = master_addon.product_tmpl_id if master_addon else False

            addon_total += addon_price
            selected_addons.append({
                'id': addon_id,
                'name': addon_name,
                'price': addon_price,
                'product_tmpl_id': addon_product_tmpl.id if addon_product_tmpl else False,
            })

        subtotal = truck_price + addon_total

        # Calculate taxes using product template tax configuration (using sudo for access)
        # Get the main service product template - all access via sudo
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref('appness_logspace_mockup2.product_logspace_service_product_template', raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search([('default_code', '=', 'LOGSPACE-SVC')], limit=1)

        tax_amount = 0.0
        currency = request.env.company.currency_id

        if service_product_tmpl and service_product_tmpl.exists() and service_product_tmpl.taxes_id:
            taxes = service_product_tmpl.taxes_id.compute_all(truck_price, currency=currency, quantity=1, product=service_product_tmpl)
            tax_amount += taxes['total_included'] - taxes['total_excluded']

        for addon in selected_addons:
            if addon.get('product_tmpl_id'):
                addon_prod_tmpl = ProductTmpl.browse(addon['product_tmpl_id'])
                if addon_prod_tmpl.exists() and addon_prod_tmpl.taxes_id:
                    taxes = addon_prod_tmpl.taxes_id.compute_all(addon['price'], currency=currency, quantity=1, product=addon_prod_tmpl)
                    tax_amount += taxes['total_included'] - taxes['total_excluded']

        tax = tax_amount if tax_amount > 0 else 0.0
        total = subtotal + tax

        # Get provider and vehicle type info for display
        provider = request.env['res.partner'].sudo().browse(booking_data.get('provider_id'))
        vehicle_type = request.env['logspace.vehicle.type'].sudo().browse(booking_data.get('vehicle_type_id'))

        # Get zones
        zone_from = request.env['logspace.zone'].sudo().browse(booking_data.get('zone_from_id'))
        zone_to = request.env['logspace.zone'].sudo().browse(booking_data.get('zone_to_id'))

        checkout_data = {
            'truck_price': truck_price,
            'selected_addons': selected_addons,
            'addon_total': addon_total,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'provider_name': provider.name if provider else 'Unknown',
            'vehicle_type_name': vehicle_type.name if vehicle_type else 'Unknown',
            'zone_from_name': zone_from.name if zone_from else 'Unknown',
            'zone_to_name': zone_to.name if zone_to else 'Unknown',
            'pickup_date': booking_data.get('pickup_date'),
            'pickup_timeframe': booking_data.get('pickup_timeframe'),
            'dropoff_timeframe': booking_data.get('dropoff_timeframe'),
            'pickup_address': booking_data.get('pickup_address'),
            'dropoff_address': booking_data.get('dropoff_address'),
            'item_description': booking_data.get('item_description'),
            'estimated_weight_kg': booking_data.get('estimated_weight_kg', 0),
            'datetime': datetime,
            'current_step': 3,
            'total_steps': 4,
            'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
            'booking_data': booking_data,
            'user': request.env.user,
        }

        return request.render('appness_logspace_mockup2.mockup2_checkout_page',
                              self._get_mock_context(checkout_data))

    # =========================================================================
    # Payment Calculation Helper
    # =========================================================================
    def _calculate_booking_total(self, booking_data):
        """Calculate total, tax, and breakdown from booking session data."""
        truck_price = float(booking_data.get('price', 0) or 0)
        addon_total = 0
        addon_lines_data = []

        for addon_id in booking_data.get('addon_ids', []):
            provider_addon = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)
            if provider_addon:
                addon_total += provider_addon.provider_price
                addon_lines_data.append({
                    'product_tmpl_id': provider_addon.addon_id.product_tmpl_id.id if provider_addon.addon_id.product_tmpl_id else False,
                    'price': provider_addon.provider_price,
                    'name': provider_addon.addon_id.name,
                })
            else:
                master_addon = request.env['logspace.addon'].sudo().browse(addon_id)
                if master_addon:
                    addon_total += master_addon.price
                    addon_lines_data.append({
                        'product_tmpl_id': master_addon.product_tmpl_id.id if master_addon.product_tmpl_id else False,
                        'price': master_addon.price,
                        'name': master_addon.name,
                    })

        subtotal = truck_price + addon_total
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref('appness_logspace_mockup2.product_logspace_service_product_template', raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search([('default_code', '=', 'LOGSPACE-SVC')], limit=1)

        tax_amount = 0.0
        currency = request.env.company.currency_id
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

    # =========================================================================
    # Helper: Create Sale Order from Session Booking Data
    # =========================================================================
    def _create_logspace_sale_order(self, booking_data, partner):
        """Create a draft sale order from booking session data. Returns the order."""
        truck_price = float(booking_data.get('price', 0) or 0)
        addon_total = 0
        addon_lines_data = []

        # Get service product
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref(
            'appness_logspace_mockup2.product_logspace_service_product_template',
            raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search(
                [('default_code', '=', 'LOGSPACE-SVC')], limit=1)
        service_product = False
        if service_product_tmpl:
            service_product = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', service_product_tmpl.id)], limit=1)

        for addon_id in booking_data.get('addon_ids', []):
            provider_addon = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)
            if provider_addon:
                addon_price = provider_addon.provider_price
                addon_name = provider_addon.addon_id.name
                addon_total += addon_price
                addon_product = request.env['product.product'].sudo().search(
                    [('product_tmpl_id', '=', provider_addon.addon_id.product_tmpl_id.id)],
                    limit=1) if provider_addon.addon_id.product_tmpl_id else False
                addon_lines_data.append({'product': addon_product, 'price': addon_price, 'name': addon_name})
            else:
                master_addon = request.env['logspace.addon'].sudo().browse(addon_id)
                if master_addon:
                    addon_total += master_addon.price
                    addon_product = request.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', master_addon.product_tmpl_id.id)],
                        limit=1) if master_addon.product_tmpl_id else False
                    addon_lines_data.append({'product': addon_product, 'price': master_addon.price, 'name': master_addon.name})

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

        order = request.env['sale.order'].sudo().create({
            'partner_id': partner.id,
            'is_logspace_order': True,
            'logspace_provider_id': booking_data.get('provider_id'),
            'logspace_vehicle_id': vehicle_id,
            'logspace_driver_id': driver_id,
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
            'order_line': order_lines,
        })

        if booking_data.get('addon_ids'):
            order.logspace_addon_ids = [(6, 0, booking_data['addon_ids'])]

        return order

    # =========================================================================
    # Screen 7: Payment — Integrated with Odoo Payment Gateway
    # =========================================================================
    @http.route(['/logspace/booking/payment'], type='http', auth='public', website=True, csrf=True)
    def mockup_payment(self, **kwargs):
        """Screen 7: Payment — shows Odoo payment providers + preview mockup."""
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        totals = self._calculate_booking_total(booking_data)

        # Get the partner (current user or guest)
        partner = request.env.user.partner_id if not request.env.user._is_public() else False
        partner_id = partner.id if partner else False

        # For guest users, create a temporary partner for payment processing
        if not partner_id:
            guest_email = booking_data.get('guest_email', '')
            guest_name = booking_data.get('pickup_contact_name', '') or guest_email.split('@')[0] or 'Guest'
            if guest_email:
                existing = request.env['res.partner'].sudo().search([('email', '=', guest_email)], limit=1)
                partner_id = existing.id if existing else request.env['res.partner'].sudo().create({
                    'name': guest_name,
                    'email': guest_email,
                    'phone': booking_data.get('guest_phone', ''),
                    'type': 'contact',
                }).id

        # Fetch compatible Odoo payment providers
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            request.env.company.id,
            partner_id or request.env.user.partner_id.id,
            totals['total'],
            currency_id=totals['currency'].id,
        ) if partner_id or not request.env.user._is_public() else request.env['payment.provider'].sudo().search([
            ('state', 'in', ['enabled', 'test']),
            ('company_id', '=', request.env.company.id),
        ])

        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_id or request.env.user.partner_id.id,
            currency_id=totals['currency'].id,
        ) if providers_sudo else request.env['payment.method']

        return request.render('appness_logspace_mockup2.mockup2_payment_page',
                              self._get_mock_context({
                                  'total': totals['total'],
                                  'subtotal': totals['subtotal'],
                                  'tax': totals['tax'],
                                  'truck_price': totals['truck_price'],
                                  'current_step': 4,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'providers_sudo': providers_sudo,
                                  'payment_methods_sudo': payment_methods_sudo,
                                  'partner_id': partner_id,
                                  'currency': totals['currency'],
                                  'show_preview': kwargs.get('preview') == '1',
                              }))

    # =========================================================================
    # Create Payment Transaction (JSON-RPC)
    # =========================================================================
    @http.route('/logspace/booking/payment/transaction', type='json', auth='public')
    def logspace_payment_transaction(self, provider_id, payment_method_id, **kwargs):
        """Create a payment.transaction for the logspace booking.
        Uses Odoo's standard redirect flow: creates tx with online_redirect,
        monitors it, and returns processing values with redirect_form_html.
        """
        import logging
        _logger = logging.getLogger(__name__)

        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return {'error': 'No booking data found'}

        totals = self._calculate_booking_total(booking_data)
        order_id = request.session.get('logspace_order_id')
        partner = request.env.user.partner_id if not request.env.user._is_public() else False

        if not partner:
            guest_email = booking_data.get('guest_email', '')
            guest_name = booking_data.get('pickup_contact_name', '') or guest_email.split('@')[0] or 'Guest'
            existing = request.env['res.partner'].sudo().search(
                [('email', '=', guest_email)], limit=1) if guest_email else False
            partner = existing or request.env['res.partner'].sudo().create({
                'name': guest_name,
                'email': guest_email,
                'phone': booking_data.get('guest_phone', ''),
                'type': 'contact',
            })

        provider_sudo = request.env['payment.provider'].sudo().browse(int(provider_id))
        if not provider_sudo.exists():
            return {'error': 'Invalid payment provider'}

        # Create payment transaction with redirect flow (same as Odoo standard)
        order_id = request.session.get('logspace_order_id')
        reference = 'LOGSPACE-%s-%s' % (
            booking_data.get('provider_id', 'UNK'),
            fields.Datetime.now().strftime('%Y%m%d%H%M%S'),
        )

        landing_route = '/logspace/booking/done'
        if order_id:
            landing_route = '/logspace/booking/done?order_id=%d' % order_id

        tx_sudo = request.env['payment.transaction'].sudo().create({
            'provider_id': provider_sudo.id,
            'payment_method_id': int(payment_method_id),
            'reference': reference,
            'amount': totals['total'],
            'currency_id': totals['currency'].id,
            'partner_id': partner.id,
            'operation': 'online_redirect',
            'landing_route': landing_route,
            'logspace_order_id': order_id or False,
        })

        # Monitor the transaction (Odoo standard — required for /payment/status)
        PaymentPostProcessing.monitor_transaction(tx_sudo)

        # Also store tx_id in our session key for easy lookup
        request.session['logspace_tx_id'] = tx_sudo.id

        processing_values = tx_sudo._get_processing_values()
        _logger.info("Logspace payment tx created: id=%s, provider=%s, redirect_form=%s",
                     tx_sudo.id, provider_sudo.code, 'redirect_form_html' in processing_values)
        return processing_values

    # =========================================================================
    # Override Odoo's /payment/status to handle logspace wire transfer (pending)
    # =========================================================================
    @http.route('/payment/status', type='http', auth='public', website=True,
                sitemap=False, list_as_website_content="Payment Status")
    def logspace_payment_status_override(self, **kwargs):
        """Override to show Odoo's standard payment status page for logspace transactions.
        Wire transfer will display bank details from the provider's pending_msg.
        Then redirect to our done page after user confirms.
        """
        monitored_tx = request.env['payment.transaction'].sudo().browse(
            request.session.get('__payment_monitored_tx_id__')
        ).exists()
        if monitored_tx and monitored_tx.logspace_order_id:
            # Trigger post-processing NOW (for wire transfer, sets state to pending)
            if not monitored_tx.is_post_processed:
                try:
                    monitored_tx._post_process()
                except Exception:
                    pass
            # Render Odoo's standard payment status page (shows bank details for wire transfer)
            # with a link to our done page
            values = {'tx': monitored_tx}
            response = request.render('payment.payment_status', values)
            return response
        # Not a logspace transaction — use Odoo's standard status page
        values = {'tx': monitored_tx} if monitored_tx else {'payment_not_found': True}
        return request.render('payment.payment_status', values)

    # Screen 8: Booking Done — Confirm existing order created at checkout
    @http.route(['/logspace/booking/done'], type='http', auth='public', website=True, csrf=False)
    def mockup_booking_done(self, **kwargs):
        """Screen 8: Booking Complete — confirm the order created at checkout."""
        import logging
        _logger = logging.getLogger(__name__)

        # Get order from session or URL param
        order_id = kwargs.get('order_id') or request.session.get('logspace_order_id')
        if not order_id:
            return request.redirect('/logspace/booking/details')

        order = request.env['sale.order'].sudo().browse(int(order_id))
        if not order.exists():
            return request.redirect('/logspace/booking/details')

        # Link payment transaction if exists
        tx_id = request.session.get('logspace_tx_id') or request.session.get('__payment_monitored_tx_id__')
        if tx_id:
            tx = request.env['payment.transaction'].sudo().browse(tx_id)
            if tx.exists():
                # Ensure transaction is linked to this order
                if not tx.logspace_order_id or tx.logspace_order_id.id != order.id:
                    tx.write({'logspace_order_id': order.id})
                # For wire transfer (still in draft), set to pending
                if tx.state == 'draft' and tx.provider_code == 'custom':
                    tx._set_pending()
                # Update order payment fields from transaction state
                state_map = {'draft': 'pending', 'pending': 'pending', 'done': 'paid',
                             'authorized': 'paid', 'cancel': 'failed', 'error': 'failed'}
                order.write({
                    'payment_status': state_map.get(tx.state, 'pending'),
                    'payment_method': 'other',
                    'transaction_ref': tx.reference,
                })
                # Create payment timeline event
                request.env['logspace.order.timeline'].sudo().create({
                    'order_id': order.id,
                    'event_type': 'payment_received',
                    'description': 'Payment via %s (Ref: %s) — %s' % (
                        tx.provider_id.name, tx.reference, tx.state),
                    'event_time': fields.Datetime.now(),
                })

        # Confirm the order (generates verification codes + confirms sale order)
        if order.state == 'draft':
            order.action_logspace_confirm()
            order.action_confirm()

            # Create booking timeline event
            request.env['logspace.order.timeline'].sudo().create({
                'order_id': order.id,
                'event_type': 'booked',
                'description': 'Booking confirmed',
                'event_time': fields.Datetime.now(),
            })

            # Create user account for guest if needed
            current_user = request.env.user
            is_public = not current_user or current_user._is_public()
            guest_email = order.guest_email or request.session.get('logspace_guest_email', '')

            if is_public and guest_email:
                existing_user = request.env['res.users'].sudo().search(
                    [('login', '=', guest_email)], limit=1)
                if not existing_user:
                    try:
                        user = request.env['res.users'].sudo().with_context(
                            no_reset_password=True)._create_user_from_template({
                                'name': order.partner_id.name,
                                'login': guest_email.lower().strip(),
                                'email': guest_email.lower().strip(),
                                'partner_id': order.partner_id.id,
                            })
                        user.action_reset_password()
                    except Exception:
                        pass

            # Create notification
            if not is_public:
                request.env['logspace.notification'].sudo().create_notification(
                    user_id=current_user.id,
                    title='Booking Confirmed',
                    message='Your booking %s has been confirmed.' % order.name,
                    type='success',
                    action_link='/logspace/my/orders/track/%s' % order.name,
                )

            # Send confirmation email
            try:
                template = request.env.ref(
                    'appness_logspace_mockup2.email_template_booking_confirmation')
                if template:
                    template.send_mail(order.id, force_send=True)
            except Exception:
                pass

        # Clear session
        request.session.pop('logspace_booking', None)
        request.session.pop('logspace_order_id', None)
        request.session.pop('logspace_tx_id', None)

        is_public = not request.env.user or request.env.user._is_public()

        return request.render('appness_logspace_mockup2.mockup2_done_page',
                              self._get_mock_context({
                                  'order_number': order.name,
                                  'order_id': order.id,
                                  'tracking_url': '/logspace/my/orders/track/%s' % order.name,
                                  'is_guest': is_public,
                                  'guest_email': order.guest_email or '',
                              }))

    # Screen 9: Login (simplified, NO OTP)
    @http.route(['/logspace/login'], type='http', auth='public', website=True)
    def mockup_login(self, **kwargs):
        """Screen 9: Simple login (no OTP)"""
        return request.render('appness_logspace_mockup2.mockup2_login_page',
                              self._get_mock_context({'redirect': kwargs.get('redirect', '/logspace/my/orders')}))

    # Screen 10: Signup (simplified, NO OTP)
    @http.route(['/logspace/signup'], type='http', auth='public', website=True)
    def mockup_signup(self, **kwargs):
        """Screen 10: Simple signup (no OTP)"""
        return request.render('appness_logspace_mockup2.mockup2_signup_page',
                              self._get_mock_context({'redirect': kwargs.get('redirect', '/logspace/my/profile')}))

    # ========== CUSTOMER PORTAL SCREENS (11-17) - REAL DATA ==========

    # My Account Landing Page (Standard Odoo /my style)
    @http.route(['/logspace/my', '/logspace/my/home', '/my/home'], type='http', auth='user', website=True)
    def mockup_my_account(self, **kwargs):
        """My Account landing page with navigation cards"""
        partner = request.env.user.partner_id

        # Get real counts for dashboard
        order_counts = self._get_logspace_order_counts(partner.id)

        return request.render('appness_logspace_mockup2.mockup2_my_account',
                              self._get_mock_context({
                                  'order_counts': order_counts,
                              }))

    # Screen 11: Profile - accessible from both /logspace/my/profile and standard /my/account
    @http.route(['/logspace/my/profile', '/my/account', '/my/profile'], type='http', auth='user', website=True, csrf=False)
    def mockup_profile(self, **kwargs):
        """Screen 11: Customer Profile - Real Data"""
        user = request.env.user
        partner = user.partner_id

        # Handle POST - update profile
        if request.httprequest.method == 'POST':
            update_vals = {}
            if kwargs.get('name'):
                update_vals['name'] = kwargs.get('name')
            if kwargs.get('email'):
                update_vals['email'] = kwargs.get('email')
            if kwargs.get('phone'):
                update_vals['phone'] = kwargs.get('phone')
            if kwargs.get('address'):
                # Update partner address
                partner.write({'street': kwargs.get('address')})
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
        address = ', '.join(address_parts) if address_parts else 'No address set'

        return request.render('appness_logspace_mockup2.mockup2_profile_page',
                              self._get_mock_context({
                                  'user': {
                                      'name': user.name,
                                      'email': user.email,
                                      'phone': partner.phone or partner.mobile or 'Not set',
                                      'address': address,
                                  }
                              }))

    # Helper: Get order counts for dashboard
    def _get_logspace_order_counts(self, partner_id):
        """Get order counts by status for a partner"""
        SaleOrder = request.env['sale.order'].sudo()

        # Get all logspace orders for this partner (including company contacts)
        all_orders = SaleOrder.search([
            '|',
            ('partner_id', '=', partner_id),
            ('partner_id.parent_id', '=', partner_id),
            ('is_logspace_order', '=', True),
        ])

        # Updated states to match new logspace_state values
        active_states = [
            'order_received', 'pickup_started', 'vendor_arrived_pickup',
            'pickup_addons', 'pickup_completed', 'pre_dropoff_addons',
            'arrived_destination'
        ]
        completed_states = ['dropoff_completed', 'grace_period', 'order_completed']
        cancelled_states = ['cancelled']

        return {
            'all': len(all_orders),
            'active': len([o for o in all_orders if o.logspace_state in active_states]),
            'completed': len([o for o in all_orders if o.logspace_state in completed_states]),
            'cancelled': len([o for o in all_orders if o.logspace_state in cancelled_states]),
        }

    # Screen 12: Orders List - accessible from both /logspace/my/orders and standard /my/orders
    @http.route(['/logspace/my/orders', '/logspace/my/orders/<string:status>', '/my/orders', '/my/orders/<string:status>'], type='http', auth='user', website=True)
    def mockup_orders(self, status='all', **kwargs):
        """Screen 12: Orders list with tabs - REAL DATA"""
        import datetime
        current_user = request.env.user
        partner = current_user.partner_id

        # Get real order counts
        counts = self._get_logspace_order_counts(partner.id)

        # Get orders from database
        orders_list = self._get_real_orders(partner.id, status)

        return request.render('appness_logspace_mockup2.mockup2_tracking_infos_page',
                              self._get_mock_context({
                                  'orders_list': orders_list,
                                  'current_status': status,
                                  'datetime': datetime,
                                  'counts': counts,
                                  'user': current_user,
                              }))

    # Screen 13: Track Order (NO MAP - Timeline only) - REAL DATA
    @http.route(['/logspace/my/orders/track', '/logspace/my/orders/track/<string:order_id>', '/my/orders/track', '/my/orders/track/<string:order_id>'], type='http', auth='user', website=True)
    def mockup_track(self, order_id=None, **kwargs):
        """Screen 13: Order tracking with timeline (no map) - REAL DATA"""
        current_user = request.env.user
        partner = current_user.partner_id

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

        tracking_info = {
            'id': order.name,
            'status': order.logspace_state.replace('_', ' ').title(),
            'pickup': order.pickup_address or 'Not set',
            'dropoff': order.dropoff_address or 'Not set',
            'truck': order.logspace_vehicle_id.vehicle_type_id.name if order.logspace_vehicle_id and order.logspace_vehicle_id.vehicle_type_id else 'Logspace Service',
            'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Not assigned',
            'driver': order.logspace_driver_id.name if order.logspace_driver_id else 'Not assigned',
            'driver_phone': order.logspace_driver_id.phone if order.logspace_driver_id else 'Not available',
            'create_date': order.create_date.strftime('%b %d, %Y') if order.create_date else 'N/A',
            'scheduled_datetime': order.scheduled_date.strftime('%b %d, %Y') if order.scheduled_date else 'N/A',
            'approve_date': order.date_order.strftime('%b %d, %Y') if order.date_order else False,
            'pickup_timeframe': order.pickup_timeframe or 'Not set',
            'dropoff_timeframe': order.dropoff_timeframe or 'Not set',
            'pickup_verification_code': order.verification_code_pickup if show_pickup_code else None,
            'dropoff_verification_code': order.verification_code_dropoff if show_dropoff_code else None,
        }
        return request.render('appness_logspace_mockup2.mockup2_track_page',
                              self._get_mock_context({
                                  'tracking_info': tracking_info,
                                  'timeline': timeline,
                                  'order_id': order.name,
                                  'order': order,
                              }))

    # Screen 14: Notifications - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/notifications', '/logspace/my/notifications', '/my/notifications'], type='http', auth='user', website=True, csrf=False)
    def mockup_notifications(self, order_id=None, **kwargs):
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

        return request.render('appness_logspace_mockup2.mockup2_notifications_page',
                              self._get_mock_context({
                                  'notifications': notifications_list,
                                  'order_id': order_id or '',
                                  'unread_count': len([n for n in notifications_list if not n['read']]),
                              }))

    # Screen 15: Rate Driver - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/rate', '/logspace/rate', '/logspace/rate/<string:order_id>', '/my/rate', '/my/rate/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def mockup_rate(self, order_id=None, **kwargs):
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
        existing_rating = request.env['logspace.rating'].sudo().search([
            ('order_id', '=', order.id),
        ], limit=1)

        # Handle POST - save rating
        if request.httprequest.method == 'POST':
            overall_rating = int(kwargs.get('overall_rating', 0))
            timeliness = kwargs.get('timeliness', 'good')
            driver_behavior = kwargs.get('driver_behavior', 'good')
            vehicle_condition = kwargs.get('vehicle_condition', 'good')
            comments = kwargs.get('comments', '')

            if overall_rating > 0:
                rating_vals = {
                    'order_id': order.id,
                    'overall_rating': overall_rating,
                    'timeliness_rating': timeliness,
                    'driver_behavior_rating': driver_behavior,
                    'vehicle_condition_rating': vehicle_condition,
                    'comments': comments,
                    'is_published': True,
                }

                if existing_rating:
                    existing_rating.write(rating_vals)
                else:
                    request.env['logspace.rating'].sudo().create(rating_vals)

                # Create notification for customer
                request.env['logspace.notification'].sudo().create_notification(
                    user_id=user.id,
                    title='Rating Submitted',
                    message=f'Thank you for rating your experience with {order.logspace_provider_id.name or "the provider"}',
                    type='success',
                    action_link=f'/logspace/my/orders/track/{order.name}',
                )

            return request.redirect(f'/logspace/my/orders/track/{order_id}')

        return request.render('appness_logspace_mockup2.mockup2_rate_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'vendor': order.logspace_provider_id.name if order.logspace_provider_id else 'Unknown',
                                  'driver': order.logspace_driver_id.name if order.logspace_driver_id else 'Not assigned',
                                  'existing_rating': existing_rating,
                              }))

    # Screen 16: Refund Request (New Form) - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/refunds/new', '/logspace/refund', '/logspace/refund/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def mockup_refund(self, order_id=None, **kwargs):
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
                title='Refund Requested',
                message=f'Your refund request for order {order.name} has been submitted and is under review.',
                type='info',
                action_link=f'/logspace/my/orders/{order_id}/refunds',
            )

            return request.redirect(f'/logspace/my/orders/{order_id}/refunds')

        # Get refundable amount (order total)
        refundable_amount = order.amount_total

        return request.render('appness_logspace_mockup2.mockup2_refund_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'tracking_info_id': order.name,
                                  'amount': refundable_amount,
                                  'reasons': [
                                      ('service_not_provided', 'Service was not provided'),
                                      ('late_delivery', 'Late delivery'),
                                      ('damaged_goods', 'Damaged goods'),
                                      ('wrong_vehicle', 'Wrong vehicle type'),
                                      ('overcharged', 'Overcharged'),
                                      ('cancelled_by_provider', 'Cancelled by provider'),
                                      ('other', 'Other reason')
                                  ]
                              }))

    # Screen 16b: Refund List for an Order - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/refunds'], type='http', auth='user', website=True)
    def mockup_refund_list(self, order_id=None, **kwargs):
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
            status_labels = {
                'draft': 'Draft',
                'submitted': 'Submitted',
                'under_review': 'Under Review',
                'approved': 'Approved',
                'rejected': 'Rejected',
                'processed': 'Processed',
            }
            refunds_list.append({
                'id': refund.name,
                'refund_id': refund.id,
                'date': refund.submitted_date.strftime('%b %d, %Y') if refund.submitted_date else refund.create_date.strftime('%b %d, %Y'),
                'amount': refund.amount,
                'reason': dict(refund._fields['reason'].selection).get(refund.reason, refund.reason),
                'status': refund.state,
                'status_label': status_labels.get(refund.state, refund.state.title()),
            })

        return request.render('appness_logspace_mockup2.mockup2_refund_list_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'refunds': refunds_list,
                              }))

    # Screen 17: Support Ticket (New Form) - REAL DATA
    @http.route(['/logspace/my/orders/<string:order_id>/tickets/new', '/logspace/ticket', '/logspace/ticket/<string:order_id>'], type='http', auth='user', website=True, csrf=False)
    def mockup_ticket(self, order_id=None, **kwargs):
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
                title='Support Ticket Created',
                message=f'Your ticket #{ticket.name} has been created and will be reviewed shortly.',
                type='success',
                action_link=f'/logspace/my/orders/{order_id}/tickets' if order_id else '/logspace/my/notifications',
            )

            if order_id:
                return request.redirect(f'/logspace/my/orders/{order_id}/tickets')
            return request.redirect('/logspace/my/notifications')

        return request.render('appness_logspace_mockup2.mockup2_ticket_page',
                              self._get_mock_context({
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
    def mockup_ticket_list(self, order_id=None, **kwargs):
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
                'new': 'Open',
                'in_progress': 'In Progress',
                'solved': 'Resolved',
                'cancelled': 'Cancelled',
            }
            stage_name = ticket.stage_id.name.lower() if ticket.stage_id else 'new'
            status = status_map.get(stage_name, 'open')
            status_label = status_label_map.get(stage_name, stage_name.title())

            tickets_list.append({
                'id': ticket.name,
                'ticket_id': ticket.id,
                'date': ticket.create_date.strftime('%b %d, %Y') if ticket.create_date else 'N/A',
                'subject': ticket.name,
                'category': dict(ticket._fields['logspace_ticket_type'].selection).get(ticket.logspace_ticket_type, 'Other'),
                'status': status,
                'status_label': status_label,
            })

        return request.render('appness_logspace_mockup2.mockup2_ticket_list_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'tickets': tickets_list,
                              }))

    # Ticket Detail Page
    @http.route(['/logspace/my/orders/<string:order_id>/tickets/<int:ticket_id>'], type='http', auth='user', website=True)
    def mockup_ticket_detail(self, order_id=None, ticket_id=None, **kwargs):
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
            'new': 'Open',
            'in_progress': 'In Progress',
            'solved': 'Resolved',
            'cancelled': 'Cancelled',
        }
        stage_name = ticket.stage_id.name.lower() if ticket.stage_id else 'new'
        status = status_map.get(stage_name, 'open')
        status_label = status_label_map.get(stage_name, stage_name.title())

        ticket_data = {
            'id': ticket.name,
            'ticket_id': ticket.id,
            'date': ticket.create_date.strftime('%b %d, %Y') if ticket.create_date else 'N/A',
            'subject': ticket.name,
            'category': dict(ticket._fields['logspace_ticket_type'].selection).get(ticket.logspace_ticket_type, 'Other'),
            'status': status,
            'status_label': status_label,
            'description': ticket.description or '',
        }

        return request.render('appness_logspace_mockup2.mockup2_ticket_detail_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'ticket': ticket_data,
                              }))

    # Refund Detail Page
    @http.route(['/logspace/my/orders/<string:order_id>/refunds/<int:refund_id>'], type='http', auth='user', website=True)
    def mockup_refund_detail(self, order_id=None, refund_id=None, **kwargs):
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
            'draft': 'Draft',
            'submitted': 'Submitted',
            'under_review': 'Under Review',
            'approved': 'Approved',
            'rejected': 'Rejected',
            'processed': 'Processed',
        }

        refund_data = {
            'id': refund.name,
            'date': refund.create_date.strftime('%b %d, %Y') if refund.create_date else 'N/A',
            'amount': refund.amount,
            'reason': refund.reason,
            'reason_label': dict(refund._fields['reason'].selection).get(refund.reason, refund.reason),
            'status': refund.state,
            'status_label': state_label_map.get(refund.state, refund.state),
            'details': refund.details or '',
            'rejection_reason': refund.rejection_reason or '',
        }

        return request.render('appness_logspace_mockup2.mockup2_refund_detail_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'refund': refund_data,
                              }))

    # Rating List Page
    @http.route(['/logspace/my/orders/<string:order_id>/ratings'], type='http', auth='user', website=True)
    def mockup_rating_list(self, order_id=None, **kwargs):
        """Rating list for a specific order"""
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

        # Get real ratings for this order
        ratings = request.env['logspace.rating'].sudo().search([
            ('order_id', '=', order.id),
        ])

        ratings_list = []
        for rating in ratings:
            ratings_list.append({
                'id': rating.id,
                'date': rating.create_date.strftime('%b %d, %Y') if rating.create_date else 'N/A',
                'overall_rating': rating.overall_rating,
                'timeliness_rating': rating.timeliness_rating,
                'driver_behavior_rating': rating.driver_behavior_rating,
                'vehicle_condition_rating': rating.vehicle_condition_rating,
                'comments': rating.comments or '',
                'provider': rating.provider_id.name or 'N/A',
                'is_published': rating.is_published,
            })

        return request.render('appness_logspace_mockup2.mockup2_rating_list_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'ratings': ratings_list,
                              }))

    # Rating Detail Page
    @http.route(['/logspace/my/orders/<string:order_id>/ratings/<int:rating_id>'], type='http', auth='user', website=True)
    def mockup_rating_detail(self, order_id=None, rating_id=None, **kwargs):
        """Rating detail for a specific order"""
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

        # Get the rating
        rating = request.env['logspace.rating'].sudo().search([
            ('id', '=', rating_id),
            ('order_id', '=', order.id),
        ], limit=1)

        if not rating:
            return request.redirect(f'/logspace/my/orders/{order_id}/ratings')

        rating_data = {
            'id': rating.id,
            'date': rating.create_date.strftime('%b %d, %Y') if rating.create_date else 'N/A',
            'overall_rating': rating.overall_rating,
            'timeliness_rating': rating.timeliness_rating,
            'driver_behavior_rating': rating.driver_behavior_rating,
            'vehicle_condition_rating': rating.vehicle_condition_rating,
            'comments': rating.comments or '',
            'provider': rating.provider_id.name or 'N/A',
            'is_published': rating.is_published,
        }

        return request.render('appness_logspace_mockup2.mockup2_rating_detail_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'order': order,
                                  'rating': rating_data,
                              }))

    # Screen 18-22: Provider Registration Stepper (5 steps) - REAL DATA
    @http.route(['/logspace/provider/register', '/logspace/provider/register/<int:step>'], type='http', auth='public', website=True, csrf=False)
    def mockup_provider_register(self, step=1, **kwargs):
        """Screens 18-22: Provider registration stepper - creates draft partner at step 1"""
        import base64

        templates = {
            1: 'appness_logspace_mockup2.mockup2_provider_step1',
            2: 'appness_logspace_mockup2.mockup2_provider_step2',
            3: 'appness_logspace_mockup2.mockup2_provider_step3',
            4: 'appness_logspace_mockup2.mockup2_provider_step4',
            5: 'appness_logspace_mockup2.mockup2_provider_step5',
        }
        template = templates.get(step, templates[1])

        # Get draft provider ID from session
        provider_data = request.session.get('logspace_provider_registration', {})
        draft_provider_id = provider_data.get('draft_provider_id')
        draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id) if draft_provider_id else None

        # Handle form submissions for each step
        if request.httprequest.method == 'POST':
            if step == 1:
                # Save business details - create draft provider
                years_map = {
                    'Less than 1 year': 'less_1',
                    '1-2 years': '1_2',
                    '3-5 years': '3_5',
                    '5-10 years': '5_10',
                    'More than 10 years': 'more_10',
                }

                partner_vals = {
                    'name': kwargs.get('business_name', 'Draft Provider'),
                    'email': kwargs.get('email'),
                    'phone': kwargs.get('phone'),
                    'street': kwargs.get('address'),
                    'is_provider': True,
                    'is_approved_provider': False,
                    'state': 'draft',
                    'tax_id': kwargs.get('tax_id'),
                    'cr_number': kwargs.get('cr_number'),
                    'years_experience': years_map.get(kwargs.get('years_experience'), '3_5'),
                }

                if draft_provider and draft_provider.exists():
                    draft_provider.write(partner_vals)
                else:
                    draft_provider = request.env['res.partner'].sudo().create(partner_vals)

                provider_data = {
                    'draft_provider_id': draft_provider.id,
                    'business': {
                        'name': kwargs.get('business_name'),
                        'email': kwargs.get('email'),
                        'phone': kwargs.get('phone'),
                        'tax_id': kwargs.get('tax_id'),
                        'cr_number': kwargs.get('cr_number'),
                        'years_experience': kwargs.get('years_experience'),
                        'address': kwargs.get('address'),
                    }
                }
                request.session['logspace_provider_registration'] = provider_data
                return request.redirect('/logspace/provider/register/2')

            elif step == 2:
                # Save contacts directly to draft provider
                draft_provider_id = provider_data.get('draft_provider_id')
                if draft_provider_id:
                    draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id)
                    if draft_provider.exists():
                        form = request.httprequest.form
                        names = form.getlist('contact_name[]')
                        roles = form.getlist('contact_role[]')
                        phones = form.getlist('contact_phone[]')
                        emails = form.getlist('contact_email[]')
                        contact_ids = form.getlist('contact_id[]')

                        role_display_map = {
                            'owner': 'Owner',
                            'manager': 'Manager',
                            'driver': 'Driver',
                            'dispatcher': 'Dispatcher',
                            'accountant': 'Accountant',
                            'other': 'Other',
                        }

                        submitted_ids = []
                        for i in range(len(names)):
                            if names[i]:
                                cid = int(contact_ids[i]) if i < len(contact_ids) and contact_ids[i] else 0
                                contact_vals = {
                                    'name': names[i],
                                    'function': role_display_map.get(roles[i], roles[i]) if i < len(roles) else 'Other',
                                    'phone': phones[i] if i < len(phones) else '',
                                    'email': emails[i] if i < len(emails) else '',
                                    'type': 'contact',
                                }
                                if cid > 0:
                                    # Update existing contact
                                    existing = request.env['res.partner'].sudo().browse(cid)
                                    if existing.exists() and existing.parent_id.id == draft_provider.id:
                                        existing.write(contact_vals)
                                        submitted_ids.append(cid)
                                else:
                                    # Create new contact
                                    contact_vals['parent_id'] = draft_provider.id
                                    new_contact = request.env['res.partner'].sudo().create(contact_vals)
                                    submitted_ids.append(new_contact.id)

                        # Remove contacts that were deleted by user
                        existing_contacts = draft_provider.child_ids.filtered(lambda c: c.type == 'contact')
                        for c in existing_contacts:
                            if c.id not in submitted_ids:
                                c.unlink()

                request.session['logspace_provider_registration'] = provider_data
                return request.redirect('/logspace/provider/register/3')

            elif step == 3:
                # Save fleet directly to draft provider
                draft_provider_id = provider_data.get('draft_provider_id')
                if draft_provider_id:
                    draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id)
                    if draft_provider.exists():
                        form = request.httprequest.form
                        vehicle_types = form.getlist('vehicle_type[]')
                        fleet_counts = form.getlist('fleet_count[]')
                        capacities = form.getlist('capacity[]')
                        dimensions = form.getlist('dimensions[]')
                        fleet_ids = form.getlist('fleet_id[]')

                        submitted_ids = []
                        for i in range(len(vehicle_types)):
                            if vehicle_types[i]:
                                fid = int(fleet_ids[i]) if i < len(fleet_ids) and fleet_ids[i] else 0
                                vehicle_type = request.env['logspace.vehicle.type'].sudo().search([
                                    '|',
                                    ('code', '=', vehicle_types[i]),
                                    ('name', 'ilike', vehicle_types[i]),
                                ], limit=1)

                                if vehicle_type:
                                    capacity_tons = 0.0
                                    try:
                                        cap_str = capacities[i] if i < len(capacities) else '0'
                                        if 'Ton' in cap_str:
                                            capacity_tons = float(cap_str.replace(' Ton', '').replace('s', '').replace('+', ''))
                                    except:
                                        capacity_tons = 0.0

                                    fleet_vals = {
                                        'vehicle_type_id': vehicle_type.id,
                                        'fleet_count': int(fleet_counts[i]) if i < len(fleet_counts) and fleet_counts[i] else 1,
                                        'capacity_tons': capacity_tons,
                                        'dimensions': dimensions[i] if i < len(dimensions) else '',
                                    }
                                    if fid > 0:
                                        # Update existing fleet
                                        existing = request.env['logspace.provider.fleet.summary'].sudo().browse(fid)
                                        if existing.exists() and existing.partner_id.id == draft_provider.id:
                                            existing.write(fleet_vals)
                                            submitted_ids.append(fid)
                                    else:
                                        # Create new fleet
                                        fleet_vals['partner_id'] = draft_provider.id
                                        new_fleet = request.env['logspace.provider.fleet.summary'].sudo().create(fleet_vals)
                                        submitted_ids.append(new_fleet.id)

                        # Remove fleet entries that were deleted by user
                        for fs in draft_provider.fleet_summary_ids:
                            if fs.id not in submitted_ids:
                                fs.unlink()

                request.session['logspace_provider_registration'] = provider_data
                return request.redirect('/logspace/provider/register/4')

            elif step == 4:
                # Save documents directly to draft provider
                draft_provider_id = provider_data.get('draft_provider_id')
                doc_types = [
                    ('vehicles_doc', 'Vehicles Documents'),
                    ('company_doc', 'Company Registration'),
                    ('bank_statement', 'Bank Statement'),
                ]

                if draft_provider_id:
                    draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id)
                    if draft_provider.exists():
                        for field_name, doc_name in doc_types:
                            uploaded_file = kwargs.get(field_name)
                            if uploaded_file and hasattr(uploaded_file, 'read') and hasattr(uploaded_file, 'filename'):
                                # Remove existing attachment of same type
                                existing = request.env['ir.attachment'].sudo().search([
                                    ('res_model', '=', 'res.partner'),
                                    ('res_id', '=', draft_provider.id),
                                    ('name', 'like', doc_name),
                                ])
                                existing.unlink()

                                attachment_vals = {
                                    'name': '%s - %s' % (doc_name, uploaded_file.filename),
                                    'type': 'binary',
                                    'datas': base64.b64encode(uploaded_file.read()).decode('utf-8'),
                                    'res_model': 'res.partner',
                                    'res_id': draft_provider.id,
                                    'mimetype': uploaded_file.mimetype or 'application/pdf',
                                }
                                request.env['ir.attachment'].sudo().create(attachment_vals)

                # Track which documents were uploaded in session
                documents_status = {}
                for field_name, doc_name in doc_types:
                    uploaded_file = kwargs.get(field_name)
                    if uploaded_file and hasattr(uploaded_file, 'filename'):
                        documents_status[field_name] = {'filename': uploaded_file.filename}
                provider_data['documents'] = documents_status
                request.session['logspace_provider_registration'] = provider_data
                return request.redirect('/logspace/provider/register/5')

        # Get vehicle types for dropdown
        vehicle_type_records = request.env['logspace.vehicle.type'].sudo().search([('active', '=', True)])
        vehicle_types_list = [(vt.code or str(vt.id), vt.name) for vt in vehicle_type_records]

        # Build context
        ctx = {
            'current_step': step,
            'total_steps': 5,
            'steps': ['Business', 'Contacts', 'Fleet', 'Documents', 'Review'],
            'vehicle_types': vehicle_types_list or [
                ('flatbed', 'Flatbed Truck'),
                ('box', 'Box Truck'),
                ('refrigerated', 'Refrigerated Truck'),
                ('mini', 'Mini Truck'),
                ('pickup', 'Pickup Truck'),
                ('heavy', 'Heavy Hauler'),
            ],
            'provider_data': provider_data,
        }

        # Load existing contacts/fleet from DB for steps 2 and 3 (going back shows saved rows)
        if draft_provider_id and draft_provider and draft_provider.exists():
            if step == 2:
                ctx['existing_contacts'] = [
                    {
                        'id': c.id,
                        'name': c.name,
                        'role': (c.function or '').lower().split()[0] if c.function else 'other',
                        'phone': c.phone or '',
                        'email': c.email or '',
                    }
                    for c in draft_provider.child_ids.filtered(lambda c: c.type == 'contact')
                ]
            elif step == 3:
                ctx['existing_fleet'] = [
                    {
                        'id': fs.id,
                        'vehicle_type_code': fs.vehicle_type_id.code or str(fs.vehicle_type_id.id),
                        'fleet_count': fs.fleet_count,
                        'capacity': '%s Tons' % fs.capacity_tons if fs.capacity_tons else '',
                        'dimensions': fs.dimensions or '',
                    }
                    for fs in draft_provider.fleet_summary_ids
                ]

        # For step 5, load data from draft provider
        if step == 5 and draft_provider_id:
            draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id)
            if draft_provider.exists():
                # Business info
                ctx['business'] = {
                    'name': draft_provider.name,
                    'email': draft_provider.email,
                    'phone': draft_provider.phone,
                    'tax_id': draft_provider.tax_id,
                    'cr_number': draft_provider.cr_number,
                    'years_experience': dict(draft_provider._fields['years_experience'].selection).get(draft_provider.years_experience, draft_provider.years_experience),
                    'address': draft_provider.street or '',
                }

                # Contacts from child_ids
                contacts = []
                for contact in draft_provider.child_ids.filtered(lambda c: c.type == 'contact'):
                    contacts.append({
                        'name': contact.name,
                        'role': contact.function or 'other',
                        'phone': contact.phone or '',
                        'email': contact.email or '',
                    })
                ctx['contacts'] = contacts

                # Fleet from fleet_summary_ids
                fleet = []
                for fs in draft_provider.fleet_summary_ids:
                    fleet.append({
                        'vehicle_type_code': fs.vehicle_type_id.name,
                        'fleet_count': fs.fleet_count,
                        'capacity': '%s Tons' % fs.capacity_tons if fs.capacity_tons else '',
                        'dimensions': fs.dimensions or '',
                    })
                ctx['fleet'] = fleet

                # Documents from attachments
                attachments = request.env['ir.attachment'].sudo().search([
                    ('res_model', '=', 'res.partner'),
                    ('res_id', '=', draft_provider.id),
                ])
                documents = {}
                for att in attachments:
                    if 'Vehicles Documents' in att.name:
                        documents['vehicles_doc'] = {'filename': att.name.replace('Vehicles Documents - ', '')}
                    elif 'Company Registration' in att.name:
                        documents['company_doc'] = {'filename': att.name.replace('Company Registration - ', '')}
                    elif 'Bank Statement' in att.name:
                        documents['bank_statement'] = {'filename': att.name.replace('Bank Statement - ', '')}
                ctx['documents'] = documents

        return request.render(template, self._get_mock_context(ctx))

    # Success page after provider submission - REAL DATA
    @http.route(['/logspace/provider/done'], type='http', auth='public', website=True, csrf=False)
    def mockup_provider_done(self, **kwargs):
        """Provider registration complete - Update draft provider to pending"""
        # Get session data
        provider_data = request.session.get('logspace_provider_registration', {})
        if not provider_data:
            return request.redirect('/logspace/provider/register')

        draft_provider_id = provider_data.get('draft_provider_id')
        if not draft_provider_id:
            return request.redirect('/logspace/provider/register')

        provider = request.env['res.partner'].sudo().browse(draft_provider_id)
        if not provider.exists():
            return request.redirect('/logspace/provider/register')

        # Check if already submitted
        if request.httprequest.method == 'POST' or kwargs.get('submit') == 'true':
            # Update provider state to pending - data already saved during steps
            provider.write({
                'state': 'pending',
            })

            # Send application received email
            try:
                template = request.env.ref('appness_logspace_mockup2.email_template_provider_application_received')
                if template:
                    template.send_mail(provider.id, force_send=True)
            except Exception:
                pass  # Don't fail if email sending fails

            # Clear session
            request.session.pop('logspace_provider_registration', None)
            return request.render('appness_logspace_mockup2.mockup2_provider_done',
                                  self._get_mock_context({
                                      'status': 'pending_approval',
                                      'provider_id': provider.id,
                                      'provider_name': provider.name,
                                  }))

        # GET request - show the done page with confirmation
        return request.render('appness_logspace_mockup2.mockup2_provider_done',
                              self._get_mock_context({
                                  'status': 'pending_approval',
                                  'provider_id': provider.id,
                                  'provider_name': provider.name,
                              }))
    
    @http.route('/logspace/provider/<int:provider_id>/vehicles/export', type='http', auth='user', website=True)
    def download_vehicles_excel(self, provider_id):
        """Download vehicles as Excel file"""
        #return empty response
        return request.make_response(
            'Excel file for provider ' + str(provider_id) + ' is not implemented yet.',
        )
