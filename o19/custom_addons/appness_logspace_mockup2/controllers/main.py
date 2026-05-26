# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
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

    # ========== CUSTOMER SCREENS ==========

    # Screen 1 & 2: Search and Results (combined) - REAL DATA
    @http.route(['/logspace', '/logspace/search'], type='http', auth='public', website=True, csrf=False)
    def mockup_search(self, **kwargs):
        """Screen 1 & 2: Search page with real results from price matrix"""
        env = request.env.sudo()

        # Get all zones and vehicle types for the search form
        zones = env['logspace.zone'].search([('is_active', '=', True)])
        vehicle_types = env['logspace.vehicle.type'].search([('is_active', '=', True)])

        # Initialize context
        ctx = {
            'zones': zones,
            'vehicle_types': vehicle_types,
            'show_results': False,
            'results': [],
            'search_params': {},
        }

        if request.httprequest.method == 'POST' or kwargs.get('zone_from_id'):
            # Get search parameters
            zone_from_id = int(kwargs.get('zone_from_id', 0))
            zone_to_id = int(kwargs.get('zone_to_id', 0))
            vehicle_type_id = int(kwargs.get('vehicle_type_id', 0))
            pickup_date = kwargs.get('pickup_date')
            requested_timeframe = kwargs.get('timeframe')  # e.g., "10:00-12:00"

            ctx['show_results'] = True
            ctx['search_params'] = {
                'zone_from_id': zone_from_id,
                'zone_to_id': zone_to_id,
                'vehicle_type_id': vehicle_type_id,
                'pickup_date': pickup_date,
                'timeframe': requested_timeframe,
            }

            # Only search if all required params provided
            if zone_from_id and zone_to_id and vehicle_type_id:
                results = []

                # Step 1: Find price matrices for this route with this vehicle type
                price_matrices = env['logspace.price.matrix'].search([
                    ('vehicle_type_id', '=', vehicle_type_id),
                    ('zone_from_id', '=', zone_from_id),
                    ('zone_to_id', '=', zone_to_id),
                    ('is_active', '=', True),
                    ('provider_id.is_provider', '=', True),
                    ('provider_id.state', '=', 'approved'),
                ])

                for matrix in price_matrices:
                    provider = matrix.provider_id

                    # Step 2: Verify provider has vehicles of this type in pickup OR dropoff zone
                    vehicles = env['logspace.vehicle'].search([
                        ('provider_id', '=', provider.id),
                        ('vehicle_type_id', '=', vehicle_type_id),
                        ('is_active', '=', True),
                        '|',
                        ('zone_id', '=', zone_from_id),
                        ('zone_id', '=', zone_to_id),
                    ])

                    if not vehicles:
                        continue  # Skip if no vehicles in relevant zones

                    # Step 3: Get available timeframes for this provider + vehicle type
                    timeframes = provider.time_frame_ids.filtered(
                        lambda t: t.vehicle_type_id.id == vehicle_type_id and t.is_active
                    )

                    # Check if requested timeframe is available
                    timeframe_available = True
                    if requested_timeframe and timeframes:
                        # Parse "10:00-12:00" to (10.0, 12.0)
                        try:
                            start_str, end_str = requested_timeframe.split('-')
                            req_start = float(start_str.replace(':', '.'))
                            req_end = float(end_str.replace(':', '.'))

                            timeframe_available = any(
                                tf.time_start <= req_start and tf.time_end >= req_end
                                for tf in timeframes
                            )
                        except (ValueError, AttributeError):
                            timeframe_available = True  # If parsing fails, show all

                    # Step 4: Get special instructions for this provider + vehicle type
                    special_instruction = env['logspace.provider.special.instruction'].search([
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
                    vehicle_type = env['logspace.vehicle.type'].browse(vehicle_type_id)

                    # Build result
                    results.append({
                        'price_matrix_id': matrix.id,
                        'provider_id': provider.id,
                        'provider_name': provider.name,
                        'vehicle_type_id': vehicle_type_id,
                        'vehicle_type_name': vehicle_type.name,
                        'vehicle_type_image': vehicle_type.image_url or '/appness_logspace_mockup2/static/src/img/truck_default.jpg',
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
                        'requested_timeframe': requested_timeframe,
                        'fleet_count': fleet_count,
                        'special_instructions': special_instruction.instructions if special_instruction else '',
                        'special_instruction_id': special_instruction.id if special_instruction else False,
                        # For booking link
                        'booking_url': '/logspace/booking/details?provider_id=%d&vehicle_type_id=%d&zone_from_id=%d&zone_to_id=%d&price=%s&matrix_id=%d' % (
                            provider.id, vehicle_type_id, zone_from_id, zone_to_id, matrix.customer_price, matrix.id
                        ),
                    })

                ctx['results'] = results

        return request.render('appness_logspace_mockup2.mockup2_search_page', ctx)

    # Screen 3: Vendor/Item Page
    @http.route(['/logspace/vendor/<int:vendor_id>'], type='http', auth='public', website=True)
    def mockup_vendor(self, vendor_id, **kwargs):
        """Screen 3: Vendor/Truck detail page"""
        vendor = self._get_vendor(vendor_id)
        addons = self._get_addons()
        return request.render('appness_logspace_mockup2.mockup2_vendor_page',
                              self._get_mock_context({'vendor': vendor, 'addons': addons}))

    # Screen 4: Add-ons (Now Step 2) - With Session Storage
    @http.route(['/logspace/booking/addons'], type='http', auth='public', website=True, csrf=False)
    def mockup_addons(self, **kwargs):
        """Screen 4: Booking Step 2 - Add-ons with session storage"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        env = request.env.sudo()

        # Handle POST - save selected addons to session
        if request.httprequest.method == 'POST':
            addon_ids = []
            for key, value in kwargs.items():
                if key.startswith('addon_') and value:
                    addon_id = int(key.replace('addon_', ''))
                    addon_ids.append(addon_id)
            booking_data['addon_ids'] = addon_ids
            request.session['logspace_booking'] = booking_data
            return request.redirect('/logspace/booking/checkout')

        # Get available addons for the provider and vehicle type
        available_addons = []
        if booking_data.get('provider_id') and booking_data.get('vehicle_type_id'):
            # Get provider-specific addons for this vehicle type
            provider_addons = env['logspace.provider.vehicle.type.addon'].search([
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
            master_addons = env['logspace.addon'].search([('is_active', '=', True)])
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
        env = request.env.sudo()

        # Handle POST - save to session and redirect to add-ons
        if request.httprequest.method == 'POST':
            # Store booking data in session
            request.session['logspace_booking'] = {
                'provider_id': int(kwargs.get('provider_id', 0)),
                'vehicle_type_id': int(kwargs.get('vehicle_type_id', 0)),
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
                'item_quantity': int(kwargs.get('item_quantity', 1)),
                'estimated_weight_kg': int(kwargs.get('estimated_weight_kg', 0)),
                'special_instructions': kwargs.get('special_instructions'),
            }
            return request.redirect('/logspace/booking/addons')

        # GET request - show form with initial data from query params or session
        booking_data = request.session.get('logspace_booking', {})

        # Allow URL params to override session data (for new searches)
        if kwargs.get('provider_id'):
            booking_data['provider_id'] = int(kwargs.get('provider_id'))
        if kwargs.get('vehicle_type_id'):
            booking_data['vehicle_type_id'] = int(kwargs.get('vehicle_type_id'))
        if kwargs.get('zone_from_id'):
            booking_data['zone_from_id'] = int(kwargs.get('zone_from_id'))
        if kwargs.get('zone_to_id'):
            booking_data['zone_to_id'] = int(kwargs.get('zone_to_id'))
        if kwargs.get('price'):
            booking_data['price'] = float(kwargs.get('price'))
        if kwargs.get('matrix_id'):
            booking_data['price_matrix_id'] = int(kwargs.get('matrix_id'))

        # Get zones and vehicle types for dropdowns
        zones = env['logspace.zone'].search([('is_active', '=', True)])
        vehicle_types = env['logspace.vehicle.type'].search([('is_active', '=', True)])

        # Get available timeframes for the selected provider and vehicle type
        timeframes = env['logspace.provider.time.frame']
        if booking_data.get('provider_id') and booking_data.get('vehicle_type_id'):
            timeframes = env['logspace.provider.time.frame'].search([
                ('partner_id', '=', booking_data['provider_id']),
                ('vehicle_type_id', '=', booking_data['vehicle_type_id']),
                ('is_active', '=', True),
            ])

        return request.render('appness_logspace_mockup2.mockup2_details_page',
                              self._get_mock_context({
                                  'current_step': 1,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'zones': zones,
                                  'vehicle_types': vehicle_types,
                                  'timeframes': timeframes,
                              }))

    # Screen 6: Checkout - Calculate totals from session
    @http.route(['/logspace/booking/checkout'], type='http', auth='public', website=True, csrf=False)
    def mockup_checkout(self, **kwargs):
        """Screen 6: Booking Step 3 - Checkout with calculated totals from session"""
        import datetime

        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        env = request.env.sudo()

        # Handle POST - save guest info and go to payment
        if request.httprequest.method == 'POST':
            booking_data['guest_email'] = kwargs.get('guest_email')
            booking_data['guest_phone'] = kwargs.get('guest_phone')
            booking_data['is_guest'] = not request.env.user or request.env.user._is_public()
            request.session['logspace_booking'] = booking_data
            return request.redirect('/logspace/booking/payment')

        # Calculate totals from session data
        truck_price = booking_data.get('price', 0)
        addon_total = 0
        selected_addons = []

        for addon_id in booking_data.get('addon_ids', []):
            # Get addon price from provider-specific or master addon
            provider_addon = env['logspace.provider.vehicle.type.addon'].search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)

            if provider_addon:
                addon_price = provider_addon.provider_price
                addon_name = provider_addon.addon_id.name
            else:
                master_addon = env['logspace.addon'].browse(addon_id)
                addon_price = master_addon.price if master_addon else 0
                addon_name = master_addon.name if master_addon else 'Unknown'

            addon_total += addon_price
            selected_addons.append({
                'id': addon_id,
                'name': addon_name,
                'price': addon_price,
            })

        subtotal = truck_price + addon_total
        tax_rate = 0.10  # 10% tax
        tax = subtotal * tax_rate
        total = subtotal + tax

        # Get provider and vehicle type info for display
        provider = env['res.partner'].browse(booking_data.get('provider_id'))
        vehicle_type = env['logspace.vehicle.type'].browse(booking_data.get('vehicle_type_id'))

        # Get zones
        zone_from = env['logspace.zone'].browse(booking_data.get('zone_from_id'))
        zone_to = env['logspace.zone'].browse(booking_data.get('zone_to_id'))

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
            'item_quantity': booking_data.get('item_quantity', 1),
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

    # Screen 7: Payment - Placeholder for Paymob integration
    @http.route(['/logspace/booking/payment'], type='http', auth='public', website=True, csrf=False)
    def mockup_payment(self, **kwargs):
        """Screen 7: Booking Step 4 - Payment (placeholder for Paymob)"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        # Calculate total
        truck_price = booking_data.get('price', 0)
        addon_total = 0
        for addon_id in booking_data.get('addon_ids', []):
            provider_addon = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)
            if provider_addon:
                addon_total += provider_addon.provider_price
            else:
                master_addon = request.env['logspace.addon'].sudo().browse(addon_id)
                if master_addon:
                    addon_total += master_addon.price

        subtotal = truck_price + addon_total
        tax = subtotal * 0.10
        total = subtotal + tax

        return request.render('appness_logspace_mockup2.mockup2_payment_page',
                              self._get_mock_context({
                                  'total': total,
                                  'current_step': 4,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                              }))

    # Screen 8: Booking Done - Create Order from Session
    @http.route(['/logspace/booking/done'], type='http', auth='public', website=True, csrf=False)
    def mockup_booking_done(self, **kwargs):
        """Screen 8: Booking Complete - Create real order from session data"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        env = request.env.sudo()

        # Check if user is logged in or guest
        is_guest = not request.env.user or request.env.user._is_public()
        partner = request.env.user.partner_id if not is_guest else False

        # Handle Guest Checkout - Create partner and user
        if is_guest and booking_data.get('guest_email'):
            # Check if partner already exists with this email
            existing_partner = env['res.partner'].search([
                ('email', '=', booking_data['guest_email'])
            ], limit=1)

            if existing_partner:
                partner = existing_partner
            else:
                # Create new partner for guest
                partner_vals = {
                    'name': booking_data.get('pickup_contact_name', booking_data['guest_email'].split('@')[0]),
                    'email': booking_data['guest_email'],
                    'phone': booking_data.get('guest_phone'),
                    'type': 'contact',
                }
                partner = env['res.partner'].create(partner_vals)

            # Check if user exists for this partner
            existing_user = env['res.users'].search([
                ('login', '=', booking_data['guest_email'])
            ], limit=1)

            if not existing_user and booking_data.get('guest_email'):
                # Create portal user for guest
                user_vals = {
                    'name': partner.name,
                    'login': booking_data['guest_email'],
                    'email': booking_data['guest_email'],
                    'partner_id': partner.id,
                    'groups_id': [(6, 0, [env.ref('base.group_portal').id])],
                }
                new_user = env['res.users'].create(user_vals)
                # Send password reset email
                new_user.action_reset_password()
                user = new_user
            else:
                user = existing_user
        else:
            user = request.env.user

        # Calculate totals
        truck_price = booking_data.get('price', 0)
        addon_total = 0
        for addon_id in booking_data.get('addon_ids', []):
            provider_addon = env['logspace.provider.vehicle.type.addon'].search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', '=', addon_id),
            ], limit=1)
            if provider_addon:
                addon_total += provider_addon.provider_price
            else:
                master_addon = env['logspace.addon'].browse(addon_id)
                if master_addon:
                    addon_total += master_addon.price

        subtotal = truck_price + addon_total
        tax = subtotal * 0.10
        total = subtotal + tax

        # Create the Sale Order
        order_vals = {
            'partner_id': partner.id if partner else user.partner_id.id,
            'is_logspace_order': True,
            'logspace_provider_id': booking_data.get('provider_id'),
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
            'item_quantity': booking_data.get('item_quantity', 1),
            'estimated_weight_kg': booking_data.get('estimated_weight_kg', 0),
            'special_instructions': booking_data.get('special_instructions'),
            'is_guest_order': is_guest and booking_data.get('guest_email'),
            'guest_email': booking_data.get('guest_email') if is_guest else False,
            'guest_phone': booking_data.get('guest_phone') if is_guest else False,
            'order_line': [(0, 0, {
                'name': 'Logspace Transport Service',
                'product_uom_qty': 1,
                'price_unit': total,
            })],
        }

        order = env['sale.order'].create(order_vals)

        # Add selected addons to order
        if booking_data.get('addon_ids'):
            order.logspace_addon_ids = [(6, 0, booking_data['addon_ids'])]

        # Generate verification codes
        order.action_logspace_confirm()

        # Clear session data
        request.session.pop('logspace_booking', None)

        return request.render('appness_logspace_mockup2.mockup2_done_page',
                              self._get_mock_context({
                                  'order_number': order.name,
                                  'order_id': order.id,
                                  'tracking_url': '/logspace/my/orders/track/%s' % order.name,
                                  'is_guest': is_guest,
                                  'guest_email': booking_data.get('guest_email'),
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

    # ========== CUSTOMER PORTAL SCREENS (11-17) ==========

    # My Account Landing Page (Standard Odoo /my style)
    @http.route(['/logspace/my', '/logspace/my/home', '/my/home'], type='http', auth='user', website=True)
    def mockup_my_account(self, **kwargs):
        """My Account landing page with navigation cards"""
        return request.render('appness_logspace_mockup2.mockup2_my_account',
                              self._get_mock_context())

    # Screen 11: Profile - accessible from both /logspace/my/profile and standard /my/account
    @http.route(['/logspace/my/profile', '/my/account', '/my/profile'], type='http', auth='user', website=True)
    def mockup_profile(self, **kwargs):
        """Screen 11: Customer Profile"""
        return request.render('appness_logspace_mockup2.mockup2_profile_page',
                              self._get_mock_context({
                                  'user': {
                                      'name': request.env.user.name,
                                      'email': request.env.user.email,
                                      'phone': '+1 555-0199',
                                      'address': '123 Customer Ave, City, State 12345'
                                  }
                              }))

    # Screen 12: Orders List - accessible from both /logspace/my/orders and standard /my/orders
    @http.route(['/logspace/my/orders', '/logspace/my/orders/<string:status>', '/my/orders', '/my/orders/<string:status>'], type='http', auth='user', website=True)
    def mockup_orders(self, status='all', **kwargs):
        """Screen 12: Orders list with tabs"""
        import datetime
        orders = self._get_orders(status)
        return request.render('appness_logspace_mockup2.mockup2_tracking_infos_page',
                              self._get_mock_context({
                                  'orders_list': orders,
                                  'current_status': status,
                                  'datetime': datetime,
                                  'counts': {
                                      'all': 4,
                                      'active': 2,
                                      'completed': 1,
                                      'cancelled': 1
                                  }
                              }))

    # Screen 13: Track Order (NO MAP - Timeline only)
    @http.route(['/logspace/my/orders/track', '/logspace/my/orders/track/<string:order_id>', '/my/orders/track', '/my/orders/track/<string:order_id>'], type='http', auth='user', website=True)
    def mockup_track(self, order_id='LOG-1234', **kwargs):
        """Screen 13: Order tracking with timeline (no map)"""
        timeline = self._get_order_timeline()
        # Get full order details from orders list
        orders = self._get_orders()
        order_data = next((o for o in orders if o['id'] == order_id), orders[0])

        tracking_info = {
            'id': order_id,
            'status': order_data['status_label'],
            'pickup': order_data['pickup'],
            'dropoff': order_data['dropoff'],
            'truck': order_data['truck'],
            'vendor': order_data['vendor'],
            'driver': 'John Smith',
            'driver_phone': '+1 555-0155',
            'create_date': order_data.get('create_date', 'N/A'),
            'scheduled_datetime': order_data.get('scheduled_datetime', 'N/A'),
            'approve_date': order_data.get('approve_date'),
            'pickup_timeframe': order_data.get('pickup_timeframe'),
            'dropoff_timeframe': order_data.get('dropoff_timeframe'),
            'pickup_verification_code': order_data.get('pickup_verification_code'),
            'dropoff_verification_code': order_data.get('dropoff_verification_code'),
        }
        return request.render('appness_logspace_mockup2.mockup2_track_page',
                              self._get_mock_context({
                                  'tracking_info': tracking_info,
                                  'timeline': timeline,
                                  'order_id': order_id,
                              }))

    # Screen 14: Notifications
    @http.route(['/logspace/my/orders/<string:order_id>/notifications', '/logspace/my/notifications', '/my/notifications'], type='http', auth='user', website=True)
    def mockup_notifications(self, order_id='LOG-1234', **kwargs):
        """Screen 14: Notifications list"""
        notifications = self._get_notifications()
        return request.render('appness_logspace_mockup2.mockup2_notifications_page',
                              self._get_mock_context({
                                  'notifications': notifications,
                                  'order_id': order_id
                              }))

    # Screen 15: Rate Driver
    @http.route(['/logspace/my/orders/<string:order_id>/rate', '/logspace/rate', '/logspace/rate/<string:order_id>', '/my/rate', '/my/rate/<string:order_id>'], type='http', auth='user', website=True)
    def mockup_rate(self, order_id='LOG-1235', **kwargs):
        """Screen 15: Rate Driver"""
        return request.render('appness_logspace_mockup2.mockup2_rate_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'vendor': 'ABC Logistics',
                                  'driver': 'John Smith'
                              }))

    # Screen 16: Refund Request (New Form)
    @http.route(['/logspace/my/orders/<string:order_id>/refunds/new', '/logspace/refund', '/logspace/refund/<string:order_id>'], type='http', auth='user', website=True)
    def mockup_refund(self, order_id='LOG-1237', **kwargs):
        """Screen 16: Refund Request Form"""
        return request.render('appness_logspace_mockup2.mockup2_refund_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'tracking_info_id': order_id,
                                  'amount': 60.0,
                                  'reasons': [
                                      ('service_not_provided', 'Service was not provided'),
                                      ('late_delivery', 'Late delivery'),
                                      ('damaged_goods', 'Damaged goods'),
                                      ('incorrect_charges', 'Incorrect charges'),
                                      ('other', 'Other reason')
                                  ]
                              }))

    # Screen 16b: Refund List for an Order
    @http.route(['/logspace/my/orders/<string:order_id>/refunds'], type='http', auth='user', website=True)
    def mockup_refund_list(self, order_id='LOG-1237', **kwargs):
        """Refund list for a specific order"""
        refunds = [
            {'id': 'REF-001', 'date': 'Jan 16, 2025', 'amount': 60.0, 'reason': 'Late delivery', 'status': 'approved', 'status_label': 'Approved'},
            {'id': 'REF-002', 'date': 'Jan 18, 2025', 'amount': 30.0, 'reason': 'Damaged goods', 'status': 'pending', 'status_label': 'Pending Review'},
        ]
        return request.render('appness_logspace_mockup2.mockup2_refund_list_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'refunds': refunds,
                              }))

    # Screen 17: Support Ticket (New Form)
    @http.route(['/logspace/my/orders/<string:order_id>/tickets/new', '/logspace/ticket', '/logspace/ticket/<string:order_id>'], type='http', auth='user', website=True)
    def mockup_ticket(self, order_id=None, **kwargs):
        """Screen 17: Helpdesk/Support Ticket Form"""
        return request.render('appness_logspace_mockup2.mockup2_ticket_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'categories': [
                                      ('booking', 'Booking Issue'),
                                      ('payment', 'Payment Issue'),
                                      ('delivery', 'Delivery Problem'),
                                      ('driver', 'Driver Complaint'),
                                      ('refund', 'Refund Request'),
                                      ('other', 'Other')
                                  ]
                              }))

    # Screen 17b: Ticket List for an Order
    @http.route(['/logspace/my/orders/<string:order_id>/tickets'], type='http', auth='user', website=True)
    def mockup_ticket_list(self, order_id='LOG-1234', **kwargs):
        """Ticket list for a specific order"""
        tickets = [
            {'id': 'TKT-001', 'date': 'Jan 15, 2025', 'subject': 'Driver not responding', 'category': 'Driver Complaint', 'status': 'resolved', 'status_label': 'Resolved'},
            {'id': 'TKT-002', 'date': 'Jan 17, 2025', 'subject': 'Wrong pickup address', 'category': 'Booking Issue', 'status': 'open', 'status_label': 'Open'},
        ]
        return request.render('appness_logspace_mockup2.mockup2_ticket_list_page',
                              self._get_mock_context({
                                  'order_id': order_id,
                                  'tickets': tickets,
                              }))

    # Screen 18-22: Provider Registration Stepper (5 steps)
    @http.route(['/logspace/provider/register', '/logspace/provider/register/<int:step>'], type='http', auth='public', website=True)
    def mockup_provider_register(self, step=1, **kwargs):
        """Screens 18-22: Provider registration stepper (5 steps)"""
        templates = {
            1: 'appness_logspace_mockup2.mockup2_provider_step1',
            2: 'appness_logspace_mockup2.mockup2_provider_step2',
            3: 'appness_logspace_mockup2.mockup2_provider_step3',
            4: 'appness_logspace_mockup2.mockup2_provider_step4',
            5: 'appness_logspace_mockup2.mockup2_provider_step5',
        }
        template = templates.get(step, templates[1])

        return request.render(template,
                              self._get_mock_context({
                                  'current_step': step,
                                  'total_steps': 5,
                                  'steps': ['Business', 'Contacts', 'Fleet', 'Documents', 'Review'],
                                  'vehicle_types': [
                                      ('flatbed', 'Flatbed Truck'),
                                      ('box', 'Box Truck'),
                                      ('refrigerated', 'Refrigerated Truck'),
                                      ('mini', 'Mini Truck'),
                                      ('pickup', 'Pickup Truck'),
                                      ('heavy', 'Heavy Hauler'),
                                  ],
                              }))

    # Success page after provider submission
    @http.route(['/logspace/provider/done'], type='http', auth='public', website=True)
    def mockup_provider_done(self, **kwargs):
        """Provider registration complete"""
        return request.render('appness_logspace_mockup2.mockup2_provider_done',
                              self._get_mock_context({'status': 'pending_approval'}))
    
    @http.route('/logspace/provider/<int:provider_id>/vehicles/export', type='http', auth='user', website=True)
    def download_vehicles_excel(self, provider_id):
        """Download vehicles as Excel file"""
        #return empty response
        return request.make_response(
            'Excel file for provider ' + str(provider_id) + ' is not implemented yet.',
        )
