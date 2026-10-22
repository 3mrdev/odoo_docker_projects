# -*- coding: utf-8 -*-
import base64
import logging

from odoo import _, http
from odoo.http import request

from .common import LogspaceController

_logger = logging.getLogger(__name__)

# Registration document slots: (form field, human label). The slot key is the
# deterministic identity of a provider's registration upload - the human label
# is display text only.
_DOC_TYPES = [
    ('vehicles_doc', 'Vehicles Documents'),
    ('company_doc', 'Company Registration'),
    ('bank_statement', 'Bank Statement'),
]
# Server-side upload guards; the template's `accept=` promises pdf/jpeg/png.
MAX_DOCUMENT_BYTES = 20 * 1024 * 1024
ALLOWED_DOCUMENT_MIMETYPES = {'application/pdf', 'image/jpeg', 'image/png'}


class LogspaceProvider(LogspaceController):
    """Provider registration and management routes."""

    @http.route(['/logspace/provider/register', '/logspace/provider/register/<int:step>'], type='http', auth='public', website=True, csrf=True)
    def logspace_provider_register(self, step=1, **kwargs):
        """Screens 18-22: Provider registration stepper - creates draft partner at step 1"""
        pass

        templates = {
            1: 'appness_logspace.logspace_provider_step1',
            2: 'appness_logspace.logspace_provider_step2',
            3: 'appness_logspace.logspace_provider_step3',
            4: 'appness_logspace.logspace_provider_step4',
            5: 'appness_logspace.logspace_provider_step5',
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
                provider_email = kwargs.get('email', '').strip().lower()

                # Check for duplicate email across all partners (including child contacts)
                existing_partner = request.env['res.partner'].sudo().search(
                    [('email', '=', provider_email)], limit=1)
                if existing_partner and (not draft_provider or existing_partner.id != draft_provider.id):
                    # Email already exists - re-render step 1 with error
                    return request.render('appness_logspace.logspace_provider_step1', {
                        'email_error': _('This email is already registered. Please use a different email address or contact support if you already have a provider account.'),
                        'provider_data': {'business': {k: kwargs.get(k, '') for k in ['email', 'phone', 'business_name', 'tax_id', 'cr_number', 'years_experience', 'address']}},
                    })

                years_map = {
                    'Less than 1 year': 'less_1',
                    '1-2 years': '1_2',
                    '3-5 years': '3_5',
                    '5-10 years': '5_10',
                    'More than 10 years': 'more_10',
                }

                partner_vals = {
                    'name': kwargs.get('business_name', 'Draft Provider'),
                    'email': provider_email,
                    'phone': kwargs.get('phone'),
                    'street': kwargs.get('address'),
                    'company_type': 'company',
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
                        'email': provider_email,
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
                doc_types = _DOC_TYPES

                # Serialize concurrent uploads for the same draft provider: the
                # second POST waits here for the first to commit, then sees its
                # attachments and takes the replace path instead of duplicating
                # them (two transactions no longer run unlink+create blind).
                if draft_provider_id:
                    request.env.cr.execute(
                        'SELECT pg_advisory_xact_lock(%s)', (int(draft_provider_id),))

                # Validate sizes and mimetypes before touching the database
                oversized_docs, invalid_docs = [], []
                for field_name, doc_name in doc_types:
                    uploaded_file = kwargs.get(field_name)
                    if not (uploaded_file and hasattr(uploaded_file, 'read')
                            and hasattr(uploaded_file, 'filename') and uploaded_file.filename):
                        continue
                    data = uploaded_file.read()
                    uploaded_file.seek(0)
                    if len(data) > MAX_DOCUMENT_BYTES:
                        oversized_docs.append(doc_name)
                    elif (uploaded_file.mimetype or '') not in ALLOWED_DOCUMENT_MIMETYPES:
                        invalid_docs.append(doc_name)

                # Check that all required documents are uploaded
                missing_docs = []
                for field_name, doc_name in doc_types:
                    uploaded_file = kwargs.get(field_name)
                    has_new_file = (uploaded_file and hasattr(uploaded_file, 'read')
                                    and hasattr(uploaded_file, 'filename') and uploaded_file.filename)
                    if not has_new_file:
                        # Check if already uploaded in DB (slot-keyed identity)
                        already_uploaded = False
                        if draft_provider_id:
                            already_uploaded = request.env['documents.document'].sudo().search_count([
                                ('partner_id', '=', int(draft_provider_id)),
                                ('logspace_doc_slot', '=', field_name),
                            ]) > 0
                        if not already_uploaded:
                            missing_docs.append(doc_name)

                if missing_docs or oversized_docs or invalid_docs:
                    ctx = {
                        'current_step': step,
                        'total_steps': 5,
                        'steps': ['Business', 'Contacts', 'Fleet', 'Documents', 'Review'],
                        'vehicle_types': [(vt.code or str(vt.id), vt.name) for vt in
                                          request.env['logspace.vehicle.type'].sudo().search([('active', '=', True)])],
                        'provider_data': provider_data,
                        'document_error': True,
                        'missing_documents': missing_docs,
                        'oversized_documents': oversized_docs,
                        'invalid_documents': invalid_docs,
                        'from_review': provider_data.get('from_review', False),
                    }
                    template = 'appness_logspace.logspace_provider_step4'
                    return request.render(template, self._get_page_context(ctx))

                if draft_provider_id:
                    draft_provider = request.env['res.partner'].sudo().browse(draft_provider_id)
                    if draft_provider.exists():
                        for field_name, doc_name in doc_types:
                            uploaded_file = kwargs.get(field_name)
                            if uploaded_file and hasattr(uploaded_file, 'read') and hasattr(uploaded_file, 'filename'):
                                # Replace by slot, not by name match: unlinking the
                                # previous document for this slot also removes its
                                # access rows and the underlying attachment.
                                old_doc = request.env['documents.document'].sudo().search([
                                    ('partner_id', '=', draft_provider.id),
                                    ('logspace_doc_slot', '=', field_name),
                                ], limit=1)
                                if old_doc:
                                    old_doc.unlink()

                                attachment_vals = {
                                    'name': '%s - %s' % (doc_name, uploaded_file.filename),
                                    'type': 'binary',
                                    'datas': base64.b64encode(uploaded_file.read()).decode('utf-8'),
                                    'res_model': 'res.partner',
                                    'res_id': draft_provider.id,
                                    'mimetype': uploaded_file.mimetype or 'application/pdf',
                                }
                                attachment = request.env['ir.attachment'].sudo().create(attachment_vals)

                                # Also create a documents.document record linked to the provider
                                document = request.env['documents.document'].sudo().create({
                                    'attachment_id': attachment.id,
                                    'partner_id': draft_provider.id,
                                    'logspace_doc_slot': field_name,
                                    'access_internal': 'view',
                                })
                                # Grant provider view access via documents.access
                                request.env['documents.access'].sudo().create({
                                    'document_id': document.id,
                                    'partner_id': draft_provider.id,
                                    'role': 'view',
                                })

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
        # Persist from_review in session so it survives redirects
        if kwargs.get('from_review') == '1':
            provider_data['from_review'] = True
        from_review = provider_data.get('from_review', False)

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
            'from_review': from_review,
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
            elif step == 4:
                # Load document filenames from the slot-keyed documents
                if draft_provider_id:
                    documents_from_db = {}
                    for field_name, doc_name in _DOC_TYPES:
                        doc = request.env['documents.document'].sudo().search([
                            ('partner_id', '=', int(draft_provider_id)),
                            ('logspace_doc_slot', '=', field_name),
                        ], limit=1)
                        if doc and doc.attachment_id:
                            filename = doc.attachment_id.name.replace(doc_name + ' - ', '')
                            documents_from_db[field_name] = {'filename': filename}
                    if documents_from_db:
                        # Merge with session documents (new uploads take priority)
                        session_docs = provider_data.get('documents', {})
                        session_docs.update(documents_from_db)
                        provider_data['documents'] = session_docs

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

                # Documents from the slot-keyed documents
                documents = {}
                for field_name, doc_name in _DOC_TYPES:
                    doc = request.env['documents.document'].sudo().search([
                        ('partner_id', '=', draft_provider.id),
                        ('logspace_doc_slot', '=', field_name),
                    ], limit=1)
                    if doc and doc.attachment_id:
                        filename = doc.attachment_id.name.replace(doc_name + ' - ', '')
                        documents[field_name] = {'filename': filename}
                ctx['documents'] = documents

        return request.render(template, self._get_page_context(ctx))

    # Success page after provider submission - REAL DATA
    @http.route(['/logspace/provider/done'], type='http', auth='public', website=True, csrf=True)
    def logspace_provider_done(self, **kwargs):
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
            # Serialize racing double clicks: the transaction-level lock makes
            # the second POST wait for the first to commit, then see the state
            # it wrote instead of re-running the submission.
            request.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', (draft_provider_id,))

            # Clear the session BEFORE writing/emailing: a replayed POST finds
            # no session and bounces to step 1 instead of re-emailing.
            request.session.pop('logspace_provider_registration', None)

            # Submit only from draft: never re-email, and never flip an
            # already pending/approved/rejected provider back to pending.
            if provider.state == 'draft':
                provider.write({
                    'state': 'pending',
                })

                # Send application received email
                try:
                    template = request.env.ref('appness_logspace.email_template_provider_application_received')
                    if template:
                        template.send_mail(provider.id, force_send=True)
                except Exception:
                    pass  # Don't fail if email sending fails

            return request.render('appness_logspace.logspace_provider_done',
                                  self._get_page_context({
                                      'status': 'pending_approval',
                                      'provider_id': provider.id,
                                      'provider_name': provider.name,
                                  }))

        # GET request - show the done page with confirmation
        return request.render('appness_logspace.logspace_provider_done',
                              self._get_page_context({
                                  'status': 'pending_approval',
                                  'provider_id': provider.id,
                                  'provider_name': provider.name,
                              }))
    
    @http.route('/logspace/provider/<int:provider_id>/vehicles/export', type='http', auth='user', website=True)
    def download_vehicles_excel(self, provider_id):
        """Download vehicles as Excel file"""
        #return empty response
        return request.make_response(
            _('Excel file for provider %s is not implemented yet.', provider_id),
        )
