# -*- coding: utf-8 -*-
import base64
import datetime
import urllib.parse

from odoo import _, http
from odoo.exceptions import ValidationError
from odoo.http import request

from .common import LogspaceController

class LogspaceBooking(LogspaceController):
    """Booking flow routes: details, add-ons, checkout, payment, confirmation."""

    @http.route(['/logspace/booking/addons'], type='http', auth='public', website=True, csrf=True)
    def logspace_addons(self, **kwargs):
        """Screen 4: Booking Step 2 - Add-ons with session storage"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        session_order_id = request.session.get('logspace_order_id')
        session_order = request.env['sale.order'].sudo().browse(session_order_id).exists()
        if session_order and session_order.is_logspace_order and (
            session_order.state not in ('draft', 'sent')
            or session_order._get_blocking_logspace_transactions()
        ):
            access_token = session_order._portal_ensure_token()
            query = urllib.parse.urlencode({'access_token': access_token})
            return request.redirect(
                f'/logspace/booking/payment/result/{session_order.id}?{query}'
            )

        try:
            booking_data, _selection, _addon_values = self._get_validated_booking_data(
                booking_data
            )
        except ValidationError:
            return request.redirect('/logspace/search')
        request.session['logspace_booking'] = booking_data

        # Handle POST - save selected addons to session
        if request.httprequest.method == 'POST':
            addon_ids = []
            try:
                for key, value in kwargs.items():
                    if key.startswith('addon_') and value:
                        addon_ids.append(int(key.replace('addon_', '')))
            except ValueError:
                return request.redirect('/logspace/booking/addons')
            # Create a new dict copy so request.session registers the modification
            booking_data = dict(booking_data, addon_ids=addon_ids)
            try:
                booking_data, _selection, _addon_values = self._get_validated_booking_data(
                    booking_data
                )
            except ValidationError:
                return request.redirect('/logspace/booking/addons')
            request.session['logspace_booking'] = booking_data
            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/checkout')

        # Get available addons for the provider and vehicle type
        available_addons = []
        provider_addons_configured = False
        if booking_data.get('provider_id') and booking_data.get('vehicle_type_id'):
            # Get provider-specific addons for this vehicle type
            provider_addon_model = request.env[
                'logspace.provider.vehicle.type.addon'
            ].sudo()
            provider_domain = [
                ('provider_id', '=', booking_data['provider_id']),
                ('vehicle_type_id', '=', booking_data['vehicle_type_id']),
                ('is_active', '=', True),
            ]
            provider_addons_configured = bool(
                provider_addon_model.search_count(provider_domain, limit=1)
            )
            provider_addons = provider_addon_model.search(provider_domain + [
                ('addon_id.active', '=', True),
                ('currency_id', '=', _selection['currency'].id),
                ('provider_price', '>=', 0),
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
        if not available_addons and not provider_addons_configured:
            master_addons = request.env['logspace.addon'].sudo().search([
                ('active', '=', True),
                ('currency_id', '=', _selection['currency'].id),
                ('price', '>=', 0),
            ])
            for addon in master_addons:
                available_addons.append({
                    'id': addon.id,
                    'name': addon.name,
                    'description': addon.description,
                    'price': addon.price,
                    'icon': addon.icon or 'fa-plus',
                })

        totals = self._calculate_booking_total(booking_data)
        selected_addons_summary = [{
            'name': line['name'],
            'price': line['price'],
        } for line in totals['addon_lines']]

        return request.render('appness_logspace.logspace_addons_page',
                              self._get_page_context({
                                  'addons': available_addons,
                                  'current_step': 2,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'selected_addons_summary': selected_addons_summary,
                                  'addons_total': totals['addon_total'],
                                  'addons_subtotal': totals['subtotal'],
                                  'addons_tax': totals['tax'],
                                  'addons_grand_total': totals['total'],
                              }))

    # Screen 5: Booking Details (Now Step 1) - With Session Storage
    @http.route(['/logspace/booking/details'], type='http', auth='public', website=True, csrf=True)
    def logspace_details(self, **kwargs):
        """Screen 5: Booking Step 1 - Item Details with session storage"""

        # Handle POST - save to session and redirect to add-ons
        if request.httprequest.method == 'POST':
            try:
                zone_from_id_val = int(kwargs.get('zone_from_id', 0) or 0)
                zone_to_id_val = int(kwargs.get('zone_to_id', 0) or 0)
                provider_id_val = int(kwargs.get('provider_id', 0) or 0)
                vehicle_type_id_val = int(kwargs.get('vehicle_type_id', 0) or 0)
                vehicle_id_val = int(kwargs.get('vehicle_id', 0) or 0)
                matrix_id_val = int(kwargs.get('price_matrix_id', 0) or 0)
            except (TypeError, ValueError):
                return request.redirect('/logspace/search')
            pickup_tf = kwargs.get('pickup_timeframe', '')
            # Auto-calculate dropoff timeframe using helper
            auto_dropoff = self._calculate_dropoff_timeframe(
                zone_from_id_val, zone_to_id_val, pickup_tf
            )

            # Preserve uploaded documents, but reset add-ons when the selected route changes.
            existing_booking = request.session.get('logspace_booking', {})
            same_matrix = matrix_id_val == existing_booking.get('price_matrix_id')
            preserved_addon_ids = existing_booking.get('addon_ids', []) if same_matrix else []
            preserved_doc_attachments = dict(existing_booking.get('uploaded_document_ids', {}))

            candidate_booking = {
                'provider_id': provider_id_val,
                'vehicle_type_id': vehicle_type_id_val,
                'vehicle_id': vehicle_id_val,
                'zone_from_id': zone_from_id_val,
                'zone_to_id': zone_to_id_val,
                'price_matrix_id': matrix_id_val,
                'pickup_date': kwargs.get('pickup_date'),
                'pickup_timeframe': pickup_tf,
                'dropoff_timeframe': auto_dropoff,
                'pickup_address': kwargs.get('pickup_address'),
                'dropoff_address': kwargs.get('dropoff_address'),
                'pickup_contact_name': kwargs.get('pickup_contact_name'),
                'pickup_contact_phone': kwargs.get('pickup_contact_phone'),
                'dropoff_contact_name': kwargs.get('dropoff_contact_name'),
                'dropoff_contact_phone': kwargs.get('dropoff_contact_phone'),
                'item_description': kwargs.get('item_description'),
                'addon_ids': preserved_addon_ids,
                'uploaded_document_ids': preserved_doc_attachments,
            }
            try:
                candidate_booking, _selection, _addon_values = self._get_validated_booking_data(
                    candidate_booking
                )
            except ValidationError:
                return request.redirect('/logspace/search')

            # Handle document uploads - create ir.attachment records immediately
            for key, storage in request.httprequest.files.items():
                if key.startswith('document_') and storage and storage.filename:
                    doc_id = int(key.replace('document_', ''))
                    # Remove old attachment if replacing
                    old_att_id = preserved_doc_attachments.get(doc_id)
                    if old_att_id:
                        request.env['ir.attachment'].sudo().browse(old_att_id).unlink()
                    # Create new attachment (temporary, no order link yet)
                    attachment = request.env['ir.attachment'].sudo().create({
                        'name': storage.filename,
                        'type': 'binary',
                        'datas': base64.b64encode(storage.read()).decode('ascii'),
                    })
                    preserved_doc_attachments[doc_id] = attachment.id

            # Store booking data in session (attachment IDs only, not binary data)
            candidate_booking['uploaded_document_ids'] = preserved_doc_attachments
            request.session['logspace_booking'] = candidate_booking
            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/addons')

        # GET request - show form with initial data from query params or session
        booking_data = request.session.get('logspace_booking', {})

        # Get provider special instructions and required documents
        # Fall back to session if kwargs are empty (user navigating back)
        try:
            provider_id = int(kwargs.get('provider_id', 0) or 0) or booking_data.get('provider_id', 0)
            vehicle_type_id = int(kwargs.get('vehicle_type_id') or 0) or booking_data.get('vehicle_type_id', 0)
        except (TypeError, ValueError):
            return request.redirect('/logspace/search')
        provider_special_instructions = ''
        required_documents = request.env['logspace.vehicle.type.document']
        if provider_id and vehicle_type_id:
            special_instruction = request.env['logspace.provider.special.instruction'].sudo().search([
                ('partner_id', '=', provider_id),
                ('vehicle_type_id', '=', vehicle_type_id),
            ], limit=1)
            provider_special_instructions = special_instruction.instructions if special_instruction else ''
            vehicle_type = request.env['logspace.vehicle.type'].sudo().browse(vehicle_type_id)
            required_documents = vehicle_type.required_document_ids.filtered(lambda d: d.is_active)

        # Build attachment name lookup from stored attachment IDs (for display in template)
        attachment_names = {}
        for doc_id, att_id in booking_data.get('uploaded_document_ids', {}).items():
            att = request.env['ir.attachment'].sudo().browse(int(att_id))
            if att.exists():
                attachment_names[int(doc_id)] = att.name

        # Allow URL params to override session data (for new searches)
        try:
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
            if kwargs.get('matrix_id'):
                booking_data['price_matrix_id'] = int(kwargs.get('matrix_id'))
        except (TypeError, ValueError):
            return request.redirect('/logspace/search')
        if kwargs.get('pickup_date'):
            booking_data['pickup_date'] = kwargs.get('pickup_date')
        if kwargs.get('pickup_timeframe'):
            booking_data['pickup_timeframe'] = kwargs.get('pickup_timeframe')

        if booking_data.get('price_matrix_id'):
            try:
                booking_data, _selection, _addon_values = self._get_validated_booking_data(
                    booking_data
                )
            except ValidationError:
                return request.redirect('/logspace/search')
            request.session['logspace_booking'] = booking_data

        # Auto-calculate dropoff timeframe from distance + delay if not already in session
        if kwargs.get('dropoff_timeframe'):
            booking_data['dropoff_timeframe'] = kwargs.get('dropoff_timeframe')
        elif booking_data.get('zone_from_id') and booking_data.get('zone_to_id') and booking_data.get('pickup_timeframe'):
            dist_rec = request.env['logspace.zone.distance'].sudo().search([
                ('zone_from_id', '=', booking_data['zone_from_id']),
                ('zone_to_id', '=', booking_data['zone_to_id']),
            ], limit=1)
            if dist_rec:
                extra_delay = int(request.env['ir.config_parameter'].sudo().get_param(
                    'appness_logspace.dropoff_delay_minutes', 30
                ))
                total_min = dist_rec.estimated_minutes + extra_delay
                start_h = request.env['logspace.time.slot']._start_hour_by_code().get(
                    booking_data.get('pickup_timeframe', 'morning'), 6)
                drop_h = start_h + (total_min / 60)
                if drop_h < 12:
                    booking_data['dropoff_timeframe'] = 'morning'
                elif drop_h < 18:
                    booking_data['dropoff_timeframe'] = 'afternoon'
                else:
                    booking_data['dropoff_timeframe'] = 'evening'

        # Fallback to session address texts if not already set
        # if not booking_data.get('pickup_address'):
        #     booking_data['pickup_address'] = request.session.get('logspace_pickup_address_text', '')
        # if not booking_data.get('dropoff_address'):
        #     booking_data['dropoff_address'] = request.session.get('logspace_dropoff_address_text', '')

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

        # The customer picks the pickup timeframe HERE now (it was removed from
        # the search bar). timeframes is a provider.time.frame recordset whose
        # display name is a joined "Morning, Afternoon" - flatten it to the
        # actual slot records, the same way search.py does for its result cards.
        # Falls back to every master slot when the provider declared none, so
        # the customer is never left with an empty dropdown.
        TimeSlot = request.env['logspace.time.slot'].sudo()
        available_slots = TimeSlot
        for tf in timeframes:
            available_slots |= tf.time_slot_ids
        if not available_slots:
            available_slots = TimeSlot.search([])
        available_slots = available_slots.sorted('sequence')

        # Code -> customer-facing label ("Morning (6:00 am - 11:59 am)") for the
        # read-only dropoff display, instead of the hardcoded dict that used to
        # live in the template.
        timeframe_labels = TimeSlot._get_labels_by_code()

        # Get selected zone names for display
        zone_from_name = ''
        zone_to_name = ''
        if booking_data.get('zone_from_id'):
            zone_from = request.env['logspace.zone'].sudo().browse(booking_data['zone_from_id'])
            zone_from_name = self._get_zone_hierarchical_address(zone_from)
            # zone_from_name = zone_from.name if zone_from.exists() else ''
        if booking_data.get('zone_to_id'):
            zone_to = request.env['logspace.zone'].sudo().browse(booking_data['zone_to_id'])
            zone_to_name = self._get_zone_hierarchical_address(zone_to)
            # zone_to_name = zone_to.name if zone_to.exists() else ''

        return request.render('appness_logspace.logspace_details_page',
                              self._get_page_context({
                                  'current_step': 1,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'zones': zones,
                                  'vehicle_types': vehicle_types,
                                  'timeframes': timeframes,
                                  'available_slots': available_slots,
                                  'timeframe_labels': timeframe_labels,
                                  'zone_from_name': zone_from_name,
                                  'zone_to_name': zone_to_name,
                                  'provider_special_instructions': provider_special_instructions,
                                  'required_documents': required_documents,
                                  'attachment_names': attachment_names,
                              }))

    # Screen 6: Checkout - Calculate totals from session
    @http.route(['/logspace/booking/checkout'], type='http', auth='public', website=True, csrf=True)
    def logspace_checkout(self, **kwargs):
        """Screen 6: Booking Step 3 - Checkout with calculated totals from session"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')

        session_order_id = request.session.get('logspace_order_id')
        session_order = request.env['sale.order'].sudo().browse(session_order_id).exists()
        if session_order and session_order.is_logspace_order and (
            session_order.state not in ('draft', 'sent')
            or session_order._get_blocking_logspace_transactions()
        ):
            access_token = session_order._portal_ensure_token()
            query = urllib.parse.urlencode({'access_token': access_token})
            return request.redirect(
                f'/logspace/booking/payment/result/{session_order.id}?{query}'
            )

        try:
            booking_data, _selection, _addon_values = self._get_validated_booking_data(
                booking_data
            )
        except ValidationError:
            return request.redirect('/logspace/search')
        request.session['logspace_booking'] = booking_data

        # Prefill guest email/phone from existing order (returning from payment)
        prefill_email = ''
        prefill_phone = ''
        _existing_order_id = request.session.get('logspace_order_id')
        if _existing_order_id:
            _existing_order = request.env['sale.order'].sudo().browse(_existing_order_id)
            if _existing_order.exists() and _existing_order.is_logspace_order:
                prefill_email = _existing_order.guest_email or ''
                prefill_phone = _existing_order.guest_phone or ''

        # Handle POST - save guest info, create/update order, and go to payment
        if request.httprequest.method == 'POST':
            # Get and validate guest email
            guest_email = kwargs.get('guest_email', '').strip()
            guest_phone = kwargs.get('guest_phone', '').strip()

            if not guest_email and (not request.env.user or request.env.user._is_public()):
                return request.render('appness_logspace.logspace_checkout_page', {
                    'error': _('Email is required for guest checkout.'),
                    'booking_data': booking_data,
                })

            is_public = not request.env.user or request.env.user._is_public()

            # Check for existing order in session
            existing_order_id = request.session.get('logspace_order_id')
            existing_order = None
            if existing_order_id:
                existing_order = request.env['sale.order'].sudo().browse(existing_order_id)
                if (
                    not existing_order.exists()
                    or not existing_order.is_logspace_order
                    or existing_order.state not in ('draft', 'sent')
                ):
                    existing_order = None
                    request.session.pop('logspace_order_id', None)
                elif existing_order._get_blocking_logspace_transactions():
                    access_token = existing_order._portal_ensure_token()
                    query = urllib.parse.urlencode({'access_token': access_token})
                    return request.redirect(
                        f'/logspace/booking/payment/result/{existing_order.id}?{query}'
                    )

            # Create a new dict copy so request.session registers the modification
            booking_data = dict(booking_data,
                                guest_email=guest_email.lower() if guest_email else '',
                                guest_phone=guest_phone,
                                is_guest=is_public)
            request.session['logspace_booking'] = booking_data
            request.session['logspace_guest_email'] = guest_email.lower() if guest_email else ''
            request.session['logspace_guest_phone'] = guest_phone

            # Resolve the order partner without treating an email address as proof of identity.
            if not is_public:
                partner = request.env.user.partner_id
            elif existing_order and existing_order.is_guest_order:
                # The server-side session already owns this draft guest order. Reuse only the
                # isolated guest contact that was created for this order.
                partner = existing_order.partner_id
                partner.write({
                    'name': booking_data.get('pickup_contact_name') or guest_email.split('@')[0],
                    'email': guest_email.lower(),
                    'phone': guest_phone,
                })
            else:
                # Always isolate a new anonymous checkout from pre-existing contacts. This avoids
                # exposing saved payment tokens or mutating another customer's partner record.
                partner = request.env['res.partner'].sudo().create({
                    'name': booking_data.get('pickup_contact_name') or guest_email.split('@')[0],
                    'email': guest_email.lower(),
                    'phone': guest_phone,
                    'type': 'contact',
                })

            # Recompute the complete draft from server-side booking data on every checkout visit.
            # This keeps the persisted order total authoritative after a customer changes add-ons.
            try:
                order = self._create_logspace_sale_order(
                    booking_data, partner, order=existing_order,
                )
            except ValidationError:
                return request.redirect('/logspace/search')
            if not existing_order:
                request.session['logspace_order_id'] = order.id
                if is_public and order.guest_email:
                    self._send_guest_payment_recovery_email(order)

            # Attach documents uploaded in details step (link temp attachments to order)
            for doc_id, att_id in booking_data.get('uploaded_document_ids', {}).items():
                att = request.env['ir.attachment'].sudo().browse(int(att_id))
                if att.exists():
                    att.write({
                        'res_model': 'sale.order',
                        'res_id': order.id,
                    })

            # Clear uploaded document IDs from session after linking
            if 'uploaded_document_ids' in booking_data:
                booking_data['uploaded_document_ids'] = {}
                request.session['logspace_booking'] = booking_data

            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/payment')

        totals = self._calculate_booking_total(booking_data)
        selected_addons = [{
            'id': addon_id,
            'name': line['name'],
            'price': line['price'],
            'product_tmpl_id': line['product_tmpl_id'],
        } for addon_id, line in zip(booking_data.get('addon_ids', []), totals['addon_lines'])]

        # Get provider and vehicle type info for display
        provider = request.env['res.partner'].sudo().browse(booking_data.get('provider_id'))
        vehicle_type = request.env['logspace.vehicle.type'].sudo().browse(booking_data.get('vehicle_type_id'))

        # Get zones
        zone_from = request.env['logspace.zone'].sudo().browse(booking_data.get('zone_from_id'))
        zone_to = request.env['logspace.zone'].sudo().browse(booking_data.get('zone_to_id'))

        checkout_data = {
            'truck_price': totals['truck_price'],
            'selected_addons': selected_addons,
            'addon_total': totals['addon_total'],
            'subtotal': totals['subtotal'],
            'tax': totals['tax'],
            'total': totals['total'],
            'provider_name': provider.name if provider else 'Unknown',
            'vehicle_type_name': vehicle_type.name if vehicle_type else 'Unknown',
            'zone_from_name': self._get_zone_hierarchical_address(zone_from) if zone_from else 'Unknown',
            'zone_to_name': self._get_zone_hierarchical_address(zone_to) if zone_to else 'Unknown',
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
            'guest_email_prefill': prefill_email,
            'guest_phone_prefill': prefill_phone,
        }

        return request.render('appness_logspace.logspace_checkout_page',
                              self._get_page_context(checkout_data))

    def _send_guest_payment_recovery_email(self, order):
        """Email guests a personal payment link so an accidentally closed
        payment screen never strands an unpaid booking."""
        order.sudo()._portal_ensure_token()
        template = request.env.ref(
            'appness_logspace.email_template_guest_payment_recovery',
            raise_if_not_found=False,
        )
        if not template:
            return
        try:
            template.sudo().send_mail(order.id, force_send=True)
        except Exception as error:  # never block checkout on mail failure
            import logging
            logging.getLogger(__name__).warning(
                "Guest payment recovery email failed for %s: %s", order.name, error,
            )
