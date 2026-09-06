# -*- coding: utf-8 -*-
import base64
import datetime
import logging

from odoo import http, fields
from odoo.http import request
from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

from .common import LogspaceController

_logger = logging.getLogger(__name__)


class LogspaceBooking(LogspaceController):
    """Booking flow routes: details, add-ons, checkout, payment, confirmation."""

    @http.route(['/logspace/booking/addons'], type='http', auth='public', website=True, csrf=False)
    def logspace_addons(self, **kwargs):
        """Screen 4: Booking Step 2 - Add-ons with session storage"""
        # Check if we have booking data in session
        booking_data = request.session.get('logspace_booking')
        if not booking_data:
            return request.redirect('/logspace/booking/details')


        # Handle POST - save selected addons to session
        if request.httprequest.method == 'POST':
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

        # Calculate selected addon prices for sidebar display
        selected_addons_summary = []
        addons_total = 0
        addon_ids = booking_data.get('addon_ids', [])
        if addon_ids and booking_data.get('provider_id'):
            provider_addons = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', 'in', addon_ids),
            ])
            provider_addon_map = {pa.addon_id.id: pa for pa in provider_addons}
            master_addons = request.env['logspace.addon'].sudo().browse(addon_ids)
            master_addon_map = {ma.id: ma for ma in master_addons}

            for addon_id in addon_ids:
                provider_addon = provider_addon_map.get(addon_id)
                if provider_addon:
                    addons_total += provider_addon.provider_price
                    selected_addons_summary.append({
                        'name': provider_addon.addon_id.name,
                        'price': provider_addon.provider_price,
                    })
                else:
                    master_addon = master_addon_map.get(addon_id)
                    if master_addon:
                        addons_total += master_addon.price
                        selected_addons_summary.append({
                            'name': master_addon.name,
                            'price': master_addon.price,
                        })

        truck_price = float(booking_data.get('price', 0) or 0)
        addons_subtotal = truck_price + addons_total

        # Calculate tax for sidebar display
        addons_tax = 0.0
        currency = request.env.company.currency_id
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref(
            'appness_logspace.product_logspace_service_product_template',
            raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search(
                [('default_code', '=', 'LOGSPACE-SVC')], limit=1)
        if service_product_tmpl and service_product_tmpl.exists() and service_product_tmpl.taxes_id:
            taxes = service_product_tmpl.taxes_id.compute_all(
                truck_price, currency=currency, quantity=1,
                product=service_product_tmpl)
            addons_tax += taxes['total_included'] - taxes['total_excluded']
        for sa in selected_addons_summary:
            addon_id_val = addon_ids[selected_addons_summary.index(sa)]
            provider_addon = provider_addon_map.get(addon_id_val) if addon_ids else None
            master_addon = master_addon_map.get(addon_id_val) if addon_ids else None
            prod_tmpl = None
            if provider_addon and provider_addon.addon_id.product_tmpl_id:
                prod_tmpl = provider_addon.addon_id.product_tmpl_id
            elif master_addon and master_addon.product_tmpl_id:
                prod_tmpl = master_addon.product_tmpl_id
            if prod_tmpl and prod_tmpl.exists() and prod_tmpl.taxes_id:
                ataxes = prod_tmpl.taxes_id.compute_all(
                    sa['price'], currency=currency, quantity=1,
                    product=prod_tmpl)
                addons_tax += ataxes['total_included'] - ataxes['total_excluded']

        return request.render('appness_logspace.logspace_addons_page',
                              self._get_page_context({
                                  'addons': available_addons,
                                  'current_step': 2,
                                  'total_steps': 4,
                                  'steps': ['Details', 'Add-ons', 'Checkout', 'Payment'],
                                  'booking_data': booking_data,
                                  'selected_addons_summary': selected_addons_summary,
                                  'addons_total': addons_total,
                                  'addons_subtotal': addons_subtotal,
                                  'addons_tax': addons_tax,
                                  'addons_grand_total': addons_subtotal + addons_tax,
                              }))

    # Screen 5: Booking Details (Now Step 1) - With Session Storage
    @http.route(['/logspace/booking/details'], type='http', auth='public', website=True, csrf=False)
    def logspace_details(self, **kwargs):
        """Screen 5: Booking Step 1 - Item Details with session storage"""

        # Handle POST - save to session and redirect to add-ons
        if request.httprequest.method == 'POST':
            zone_from_id_val = int(kwargs.get('zone_from_id', 0))
            zone_to_id_val = int(kwargs.get('zone_to_id', 0))
            pickup_tf = kwargs.get('pickup_timeframe', '')
            # Auto-calculate dropoff timeframe using helper
            auto_dropoff = self._calculate_dropoff_timeframe(
                zone_from_id_val, zone_to_id_val, pickup_tf
            )

            # Preserve addon_ids and uploaded_document_ids from existing session
            existing_booking = request.session.get('logspace_booking', {})
            preserved_addon_ids = existing_booking.get('addon_ids', [])
            preserved_doc_attachments = dict(existing_booking.get('uploaded_document_ids', {}))

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
            request.session['logspace_booking'] = {
                'provider_id': int(kwargs.get('provider_id', 0)),
                'vehicle_type_id': int(kwargs.get('vehicle_type_id', 0)),
                'vehicle_id': int(kwargs.get('vehicle_id', 0)),
                'zone_from_id': zone_from_id_val,
                'zone_to_id': zone_to_id_val,
                'price_matrix_id': int(kwargs.get('price_matrix_id', 0)),
                'price': float(kwargs.get('price', 0)),
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
            if hasattr(request.session, 'should_save'):
                request.session.should_save = True
            return request.redirect('/logspace/booking/addons')

        # GET request - show form with initial data from query params or session
        booking_data = request.session.get('logspace_booking', {})

        # Get provider special instructions and required documents
        # Fall back to session if kwargs are empty (user navigating back)
        provider_id = int(kwargs.get('provider_id', 0)) or booking_data.get('provider_id', 0)
        vehicle_type_id = int(kwargs.get('vehicle_type_id') or 0) or booking_data.get('vehicle_type_id', 0)
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
                SLOT_HOURS = {'morning': 6, 'afternoon': 12, 'evening': 18}
                start_h = SLOT_HOURS.get(booking_data.get('pickup_timeframe', 'morning'), 6)
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
                    'error': 'Email is required for guest checkout.',
                    'booking_data': booking_data,
                })

            is_public = not request.env.user or request.env.user._is_public()

            # Check for existing order in session
            existing_order_id = request.session.get('logspace_order_id')
            existing_order = None
            if existing_order_id:
                existing_order = request.env['sale.order'].sudo().browse(existing_order_id)
                if not existing_order.exists() or not existing_order.is_logspace_order:
                    existing_order = None

            # Duplicate email check for guest users
            if is_public and guest_email:
                existing_partner = request.env['res.partner'].sudo().search(
                    [('email', '=ilike', guest_email)], limit=1)
                if existing_partner:
                    # Check if this email belongs to a different customer
                    if existing_order and existing_order.partner_id.id != existing_partner.id:
                        # Email belongs to another customer - block it
                        return request.render('appness_logspace.logspace_checkout_page', {
                            'error': 'This email address is already registered to another customer. Please use a different email or sign in.',
                            'booking_data': booking_data,
                            'guest_email_prefill': guest_email,
                            'guest_phone_prefill': guest_phone,
                        })
                    elif not existing_order and existing_partner.user_ids:
                        # No current order but email belongs to a registered user - block it
                        return request.render('appness_logspace.logspace_checkout_page', {
                            'error': 'This email address is already registered. Please sign in or use a different email.',
                            'booking_data': booking_data,
                            'guest_email_prefill': guest_email,
                            'guest_phone_prefill': guest_phone,
                        })

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
                    [('email', '=ilike', guest_email)], limit=1)
                if existing:
                    partner = existing
                    # Update partner phone if changed
                    if partner.phone != guest_phone:
                        partner.write({'phone': guest_phone})
                else:
                    partner = request.env['res.partner'].sudo().create({
                        'name': booking_data.get('pickup_contact_name') or guest_email.split('@')[0],
                        'email': guest_email.lower(),
                        'phone': guest_phone,
                        'type': 'contact',
                    })

            # Reuse existing order or create new one
            if existing_order:
                # Update existing order with new guest info
                existing_order.write({
                    'guest_email': guest_email.lower() if is_public else False,
                    'guest_phone': guest_phone if is_public else False,
                    'partner_id': partner.id,
                })
                order = existing_order
            else:
                order = self._create_logspace_sale_order(booking_data, partner)
                request.session['logspace_order_id'] = order.id

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

        # Calculate totals from session data
        truck_price = float(booking_data.get('price', 0) or 0)
        addon_total = 0
        selected_addons = []

        # Batch fetch all provider-specific addons at once
        addon_ids = booking_data.get('addon_ids', [])
        if addon_ids:
            provider_addons = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', 'in', addon_ids),
            ])
            # Build lookup dict: addon_id -> provider_addon record
            provider_addon_map = {pa.addon_id.id: pa for pa in provider_addons}

            # Batch fetch master addons for fallback
            master_addons = request.env['logspace.addon'].sudo().browse(addon_ids)
            master_addon_map = {ma.id: ma for ma in master_addons}

            for addon_id in addon_ids:
                provider_addon = provider_addon_map.get(addon_id)
                if provider_addon:
                    addon_price = provider_addon.provider_price
                    addon_name = provider_addon.addon_id.name
                    addon_product_tmpl = provider_addon.addon_id.product_tmpl_id
                else:
                    master_addon = master_addon_map.get(addon_id)
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
        service_product_tmpl = ProductTmpl.env.ref('appness_logspace.product_logspace_service_product_template', raise_if_not_found=False)
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

    # =========================================================================
    # Payment Calculation Helper
    # =========================================================================
    def _calculate_booking_total(self, booking_data):
        """Calculate total, tax, and breakdown from booking session data."""
        truck_price = float(booking_data.get('price', 0) or 0)
        addon_total = 0
        addon_lines_data = []

        # Batch fetch all provider-specific addons at once
        addon_ids = booking_data.get('addon_ids', [])
        if addon_ids:
            provider_addons = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', 'in', addon_ids),
            ])
            provider_addon_map = {pa.addon_id.id: pa for pa in provider_addons}

            # Batch fetch master addons for fallback
            master_addons = request.env['logspace.addon'].sudo().browse(addon_ids)
            master_addon_map = {ma.id: ma for ma in master_addons}

            for addon_id in addon_ids:
                provider_addon = provider_addon_map.get(addon_id)
                if provider_addon:
                    addon_total += provider_addon.provider_price
                    addon_lines_data.append({
                        'product_tmpl_id': provider_addon.addon_id.product_tmpl_id.id if provider_addon.addon_id.product_tmpl_id else False,
                        'price': provider_addon.provider_price,
                        'name': provider_addon.addon_id.name,
                    })
                else:
                    master_addon = master_addon_map.get(addon_id)
                    if master_addon:
                        addon_total += master_addon.price
                        addon_lines_data.append({
                            'product_tmpl_id': master_addon.product_tmpl_id.id if master_addon.product_tmpl_id else False,
                            'price': master_addon.price,
                            'name': master_addon.name,
                        })

        subtotal = truck_price + addon_total
        ProductTmpl = request.env['product.template'].sudo()
        service_product_tmpl = ProductTmpl.env.ref('appness_logspace.product_logspace_service_product_template', raise_if_not_found=False)
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
            'appness_logspace.product_logspace_service_product_template',
            raise_if_not_found=False)
        if not service_product_tmpl:
            service_product_tmpl = ProductTmpl.search(
                [('default_code', '=', 'LOGSPACE-SVC')], limit=1)
        service_product = False
        if service_product_tmpl:
            service_product = request.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', service_product_tmpl.id)], limit=1)

        # Batch fetch all provider-specific addons at once
        addon_ids = booking_data.get('addon_ids', [])
        if addon_ids:
            provider_addons = request.env['logspace.provider.vehicle.type.addon'].sudo().search([
                ('provider_id', '=', booking_data['provider_id']),
                ('addon_id', 'in', addon_ids),
            ])
            provider_addon_map = {pa.addon_id.id: pa for pa in provider_addons}

            # Batch fetch master addons for fallback
            master_addons = request.env['logspace.addon'].sudo().browse(addon_ids)
            master_addon_map = {ma.id: ma for ma in master_addons}

            for addon_id in addon_ids:
                provider_addon = provider_addon_map.get(addon_id)
                if provider_addon:
                    addon_price = provider_addon.provider_price
                    addon_name = provider_addon.addon_id.name
                    addon_total += addon_price
                    addon_product = request.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', provider_addon.addon_id.product_tmpl_id.id)],
                        limit=1) if provider_addon.addon_id.product_tmpl_id else False
                    addon_lines_data.append({'product': addon_product, 'price': addon_price, 'name': addon_name})
                else:
                    master_addon = master_addon_map.get(addon_id)
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
    def logspace_payment(self, **kwargs):
        """Screen 7: Payment — shows Odoo payment providers."""
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

        return request.render('appness_logspace.logspace_payment_page',
                              self._get_page_context({
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
    @http.route('/logspace/booking/payment/transaction', type='jsonrpc', auth='public')
    def logspace_payment_transaction(self, provider_id, payment_method_id, **kwargs):
        """Create a payment.transaction for the logspace booking.
        Uses Odoo's standard redirect flow: creates tx with online_redirect,
        monitors it, and returns processing values with redirect_form_html.
        """
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
    def logspace_booking_done(self, **kwargs):
        """Screen 8: Booking Complete — confirm the order created at checkout."""
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
                    'appness_logspace.email_template_booking_confirmation')
                if template:
                    template.send_mail(order.id, force_send=True)
            except Exception:
                pass

        # Clear session
        request.session.pop('logspace_booking', None)
        request.session.pop('logspace_order_id', None)
        request.session.pop('logspace_tx_id', None)

        is_public = not request.env.user or request.env.user._is_public()

        return request.render('appness_logspace.logspace_done_page',
                              self._get_page_context({
                                  'order_number': order.name,
                                  'order_id': order.id,
                                  'tracking_url': '/logspace/my/orders/track/%s' % order.name,
                                  'is_guest': is_public,
                                  'guest_email': order.guest_email or '',
                              }))

