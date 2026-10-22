# -*- coding: utf-8 -*-
import datetime
import json
import logging
from urllib.parse import urlencode

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from markupsafe import Markup

from .common import LogspaceController

_logger = logging.getLogger(__name__)


class LogspaceSearch(LogspaceController):
    """Search and vehicle info routes."""

    @http.route(['/logspace', '/logspace/search'], type='http', auth='public', website=True, csrf=True)
    def logspace_search(self, **kwargs):
        """Screen 1 & 2: Search page with real results from price matrix"""
        # Get all zones and vehicle types for the search form
        # Only show leaf zones (zones without children) - parent zones shouldn't be selectable
        zones = request.env['logspace.zone'].sudo().search([
            ('active', '=', True),
            ('child_ids', '=', False)
        ])
        vehicle_types = request.env['logspace.vehicle.type'].sudo().search([('active', '=', True)])
        vehicle_categories = request.env['logspace.vehicle.category'].sudo().search([('active', '=', True)])

        # Construct full addresses JSON for frontend autocomplete
        zones_data = []
        for z in zones:
            zones_data.append({
                'id': z.id,
                'name': z.name,
                'full_address': self._get_zone_hierarchical_address(z),
                'zone_type': z.zone_type or '',
            })
        zones_json = Markup(json.dumps(zones_data))

        # Full (unfiltered) type list for the cascading Vehicle Category filter:
        # the widget rebuilds the <option>s client-side, so it needs every type
        # and its category, not just the ones the server rendered.
        vehicle_types_json = Markup(json.dumps([{
            'id': vt.id,
            'name': vt.name,
            'category_id': vt.category_id.id or False,
        } for vt in vehicle_types]))

        # Initialize context — no results by default; user must search
        ctx = {
            'datetime': datetime,
            'zones': zones,
            'zones_json': zones_json,
            'vehicle_types': vehicle_types,
            'vehicle_categories': vehicle_categories,
            'vehicle_types_json': vehicle_types_json,
            'show_results': False,
            'results': [],
            'search_params': {},
            'is_filtered_search': False,
        }

        # Always populate search_params from kwargs so the form retains values
        try:
            zone_from_id = int(kwargs.get('zone_from_id', 0) or 0)
            zone_to_id = int(kwargs.get('zone_to_id', 0) or 0)
            vehicle_type_id = int(kwargs.get('vehicle_type_id') or 0)
            vehicle_category_id = int(kwargs.get('vehicle_category_id') or 0)
        except (TypeError, ValueError):
            zone_from_id = zone_to_id = vehicle_type_id = vehicle_category_id = 0
        pickup_date = kwargs.get('pickup_date', '')

        # Narrow the rendered type dropdown to the chosen category so the page is
        # still correct with JavaScript disabled; the widget does the same live.
        if vehicle_category_id:
            ctx['vehicle_types'] = vehicle_types.filtered(
                lambda vt: vt.category_id.id == vehicle_category_id
            )

        # Dropoff timeframe is auto-calculated on the booking details page
        dropoff_timeframe = kwargs.get('dropoff_timeframe', '')

        # Address texts from kwargs or session
        pickup_address_text = kwargs.get('pickup_address_text')
        if pickup_address_text is None:
            pickup_address_text = request.session.get('logspace_pickup_address_text', '')
        else:
            request.session['logspace_pickup_address_text'] = pickup_address_text

        dropoff_address_text = kwargs.get('dropoff_address_text')
        if dropoff_address_text is None:
            dropoff_address_text = request.session.get('logspace_dropoff_address_text', '')
        else:
            request.session['logspace_dropoff_address_text'] = dropoff_address_text

        # If IDs are provided but text is not, resolve it using helper
        if zone_from_id and not pickup_address_text:
            zone_from = request.env['logspace.zone'].sudo().browse(zone_from_id)
            if zone_from.exists():
                pickup_address_text = self._get_zone_hierarchical_address(zone_from)
                request.session['logspace_pickup_address_text'] = pickup_address_text

        if zone_to_id and not dropoff_address_text:
            zone_to = request.env['logspace.zone'].sudo().browse(zone_to_id)
            if zone_to.exists():
                dropoff_address_text = self._get_zone_hierarchical_address(zone_to)
                request.session['logspace_dropoff_address_text'] = dropoff_address_text

        ctx['search_params'] = {
            'zone_from_id': zone_from_id,
            'zone_to_id': zone_to_id,
            'pickup_address_text': pickup_address_text,
            'dropoff_address_text': dropoff_address_text,
            'vehicle_category_id': vehicle_category_id,
            'vehicle_type_id': vehicle_type_id,
            'pickup_date': pickup_date,
            'dropoff_timeframe': '',  # auto-calculated on the booking details page
        }

        # Check if this is a filtered search (user clicked search button)
        is_filtered = request.httprequest.method == 'POST' or kwargs.get('zone_from_id')

        if is_filtered:
            ctx['is_filtered_search'] = True

            # Reset booking session data on new search (POST only, not GET pagination)
            if request.httprequest.method == 'POST':
                for key in ('logspace_booking', 'logspace_order_id', 'logspace_tx_id',
                            'logspace_guest_email', 'logspace_guest_phone'):
                    request.session.pop(key, None)
                if hasattr(request.session, 'should_save'):
                    request.session.should_save = True

            # The pickup date is mandatory: without it availability cannot be
            # guaranteed (the date picker enforces this in the browser; this
            # guard covers non-JS / crafted submissions). Old GET links without
            # a date keep working - only the explicit search submit is blocked.
            if request.httprequest.method == 'POST' and not pickup_date:
                ctx['search_error'] = _(
                    'Please choose a pickup date before searching.'
                )

            # Only search if zone params provided (vehicle_type_id is optional - empty means "all")
            if zone_from_id and zone_to_id and not ctx.get('search_error'):
                results = []

                # Read config: show all vehicles per provider or just 1
                show_all_vehicles = request.env['ir.config_parameter'].sudo().get_param(
                    'logspace.search_show_all_vehicles', 'True'
                ) == 'True'

                # Expand zones bidirectionally: ancestors (UP) + descendants (DOWN)
                # - District search finds parent city prices/vehicles
                # - City search finds child district prices/vehicles
                zone_from_obj = request.env['logspace.zone'].sudo().browse(zone_from_id)
                zone_to_obj = request.env['logspace.zone'].sudo().browse(zone_to_id)

                zone_from_ids = zone_from_obj._get_zone_hierarchy_ids()
                zone_to_ids = zone_to_obj._get_zone_hierarchy_ids()

                # Step 1: Find price matrices for this route
                # When vehicle_type_id is set, filter by type; otherwise show all types
                matrix_domain = [
                    ('zone_from_id', 'in', zone_from_ids),
                    ('zone_to_id', 'in', zone_to_ids),
                    ('is_active', '=', True),
                    ('provider_id.is_provider', '=', True),
                    ('provider_id.state', '=', 'approved'),
                ]
                if vehicle_type_id:
                    matrix_domain.append(('vehicle_type_id', '=', vehicle_type_id))
                elif vehicle_category_id:
                    # No specific type chosen, but a category was: still narrow the
                    # results, otherwise picking a category and searching returns
                    # everything and the filter looks broken.
                    matrix_domain.append(('vehicle_type_id.category_id', '=', vehicle_category_id))

                price_matrices = request.env['logspace.price.matrix'].sudo().search(matrix_domain)

                # Dedup: track (provider, vehicle_type) to avoid duplicate results
                # when multiple price matrices cover the same route+type combination
                seen_combos = set()

                for matrix in price_matrices:
                    provider = matrix.provider_id
                    current_vehicle_type_id = matrix.vehicle_type_id.id

                    # Skip if we already processed this provider+type combo
                    combo_key = (provider.id, current_vehicle_type_id)
                    if combo_key in seen_combos:
                        continue
                    seen_combos.add(combo_key)

                    # Step 2: Get vehicles available for this provider/type/zones on the requested date
                    vehicles = request.env['logspace.vehicle'].sudo().get_available_vehicles(
                        provider_id=provider.id,
                        vehicle_type_id=current_vehicle_type_id,
                        zone_from_id=zone_from_id,
                        zone_to_id=zone_to_id,
                        date_str=pickup_date or None,
                    )

                    if not vehicles:
                        continue  # Skip if no vehicles available (zone mismatch, date conflict, or non-working day)

                    # Limit to 1 vehicle per provider if config says so
                    if not show_all_vehicles:
                        vehicles = vehicles[:1]

                    # Step 3: Get available timeframes for this provider + vehicle type
                    timeframes = provider.time_frame_ids.filtered(
                        lambda t: t.vehicle_type_id.id == current_vehicle_type_id
                    )

                    # Step 4: Get special instructions for this provider + vehicle type
                    special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
                        ('partner_id', '=', provider.id),
                        ('vehicle_type_id', '=', current_vehicle_type_id),
                        ('is_active', '=', True),
                    ], limit=1)

                    # Get fleet count
                    fleet_summary = provider.fleet_summary_ids.filtered(
                        lambda f: f.vehicle_type_id.id == current_vehicle_type_id
                    )
                    fleet_count = sum(fs.fleet_count for fs in fleet_summary) or len(vehicles)

                    # Get vehicle type details
                    vehicle_type = request.env['logspace.vehicle.type'].sudo().browse(current_vehicle_type_id)

                    # Build result for each available vehicle
                    for vehicle in vehicles:
                        results.append({
                            'price_matrix_id': matrix.id,
                            'provider_id': provider.id,
                            'provider_name': provider.name,
                            'vehicle_type_id': current_vehicle_type_id,
                            'vehicle_type_name': vehicle_type.name,
                            'vehicle_type_image': vehicle_type.image_url or '/appness_logspace/static/src/img/truck_flatbed.jpg',
                            'vehicle_id': vehicle.id,
                            'vehicle_name': vehicle.name,
                            'price': matrix.customer_price,
                            'formatted_price': (matrix.currency_id or request.env.company.currency_id).format(matrix.customer_price),
                            'currency_symbol': (matrix.currency_id or request.env.company.currency_id).symbol or '',
                            'provider_price': matrix.provider_price,
                            'platform_fee': matrix.platform_fee,
                            'rating': provider.logspace_rating or 0.0,
                            'reviews': provider.logspace_review_count or 0,
                            'zone_from': matrix.zone_from_id.name,
                            'zone_to': matrix.zone_to_id.name,
                            'zone_from_id': zone_from_id,
                            'zone_to_id': zone_to_id,
                            'timeframes': timeframes,
                            'fleet_count': fleet_count,
                            'special_instructions': special_instruction.instructions if special_instruction else '',
                            'special_instruction_id': special_instruction.id if special_instruction else False,
                            # For booking link - point to vehicle info page, which then leads to booking
                            'vehicle_info_url': '/logspace/vendor/vehicle/%d?provider_id=%d&vehicle_type_id=%d&zone_from_id=%d&zone_to_id=%d&matrix_id=%d%s' % (
                                vehicle.id,
                                provider.id, current_vehicle_type_id, zone_from_id, zone_to_id, matrix.id,
                                '&pickup_date=%s' % pickup_date if pickup_date else '',
                            ),
                        })

                ctx['results'] = results
                ctx['show_results'] = True

        # Pagination
        all_results = ctx.get('results', [])
        per_page = 9
        total_results = len(all_results)
        total_pages = (total_results + per_page - 1) // per_page if total_results > 0 else 0

        try:
            page = max(1, int(kwargs.get('page', 1)))
        except (ValueError, TypeError):
            page = 1

        if page > total_pages and total_pages > 0:
            page = total_pages

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_results = all_results[start_idx:end_idx]

        # Build page range for pagination display
        if total_pages <= 5:
            page_range = list(range(1, total_pages + 1))
        elif page <= 3:
            page_range = list(range(1, 6))
        elif page >= total_pages - 2:
            page_range = list(range(total_pages - 4, total_pages + 1))
        else:
            page_range = list(range(page - 2, page + 3))

        # Build pagination URLs preserving search params
        search_params = ctx.get('search_params', {})
        base_params = {}
        for k in ['zone_from_id', 'zone_to_id', 'vehicle_category_id', 'vehicle_type_id',
                  'pickup_date', 'pickup_address_text', 'dropoff_address_text']:
            v = search_params.get(k, '')
            if v:
                base_params[k] = v

        page_urls = {}
        for p in range(1, total_pages + 1):
            params = dict(base_params, page=p)
            page_urls[p] = '/logspace/search?' + urlencode(params)

        ctx.update({
            'page_results': page_results,
            'current_page': page,
            'total_pages': total_pages,
            'total_results': total_results,
            'page_range': page_range,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'page_urls': page_urls,
        })

        return request.render('appness_logspace.logspace_search_page', self._get_page_context(ctx))

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

        try:
            selection = request.env['logspace.price.matrix'].sudo()._validate_booking_selection(
                matrix_id=int(kwargs.get('matrix_id', 0) or 0),
                provider_id=int(kwargs.get('provider_id', 0) or 0),
                vehicle_type_id=int(kwargs.get('vehicle_type_id', 0) or 0),
                zone_from_id=int(kwargs.get('zone_from_id', 0) or 0),
                zone_to_id=int(kwargs.get('zone_to_id', 0) or 0),
                vehicle_id=vehicle_id,
                pickup_date=kwargs.get('pickup_date'),
            )
        except (TypeError, ValueError, ValidationError):
            return request.redirect('/logspace/search')

        provider = selection['provider']
        vehicle_type = selection['vehicle_type']
        zone = vehicle.zone_id

        # Build booking URL with all params passed through from search
        booking_params = [
            ('provider_id', provider.id),
            ('vehicle_type_id', vehicle_type.id),
            ('zone_from_id', selection['zone_from'].id),
            ('zone_to_id', selection['zone_to'].id),
            ('matrix_id', selection['matrix'].id),
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
        # Flatten to unique set of time slots
        available_slots = request.env['logspace.time.slot']
        for tf in timeframes:
            available_slots |= tf.time_slot_ids

        # Get special instructions
        special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
            ('partner_id', '=', provider.id),
            ('vehicle_type_id', '=', vehicle_type.id),
            ('is_active', '=', True),
        ], limit=1)

        # Get required documents for this vehicle type
        required_documents = vehicle_type.required_document_ids.filtered(lambda d: d.is_active)

        # Get provider-specific addons for this vehicle type
        provider_addon_model = request.env[
            'logspace.provider.vehicle.type.addon'
        ].sudo()
        provider_domain = [
            ('provider_id', '=', provider.id),
            ('vehicle_type_id', '=', vehicle_type.id),
            ('is_active', '=', True),
        ]
        provider_addons_configured = bool(
            provider_addon_model.search_count(provider_domain, limit=1)
        )
        provider_addons = provider_addon_model.search(provider_domain + [
            ('addon_id.active', '=', True),
            ('currency_id', '=', selection['currency'].id),
            ('provider_price', '>=', 0),
        ])
        addons_list = []
        for pa in provider_addons:
            addons_list.append({
                'id': pa.addon_id.id,
                'name': pa.addon_id.name,
                'description': pa.addon_id.description,
                'price': pa.provider_price,
                'icon': pa.addon_id.icon or 'fa-plus',
            })
        if not addons_list and not provider_addons_configured:
            master_addons = request.env['logspace.addon'].sudo().search([
                ('active', '=', True),
                ('currency_id', '=', selection['currency'].id),
                ('price', '>=', 0),
            ])
            for addon in master_addons:
                addons_list.append({
                    'id': addon.id,
                    'name': addon.name,
                    'description': addon.description,
                    'price': addon.price,
                    'icon': addon.icon or 'fa-plus',
                })

        return request.render('appness_logspace.logspace_vehicle_info_page',
                              self._get_page_context({
                                  'vehicle': vehicle,
                                  'provider': provider,
                                  'vehicle_type': vehicle_type,
                                  'zone': zone,
                                  'timeframes': available_slots,
                                  'special_instruction': special_instruction,
                                  'required_documents': required_documents,
                                  'addons': addons_list,
                                  'booking_data': {
                                      'dropoff_timeframe': kwargs.get('dropoff_timeframe', ''),
                                  } if kwargs.get('dropoff_timeframe') else {},
                                  'booking_url': booking_url,
                                  'price': selection['price'],
                                  'pickup_date': kwargs.get('pickup_date'),
                                  'zone_from_id': kwargs.get('zone_from_id'),
                                  'zone_to_id': kwargs.get('zone_to_id'),
                              }))
