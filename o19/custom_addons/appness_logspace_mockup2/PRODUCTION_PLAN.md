# Logspace Production Implementation Plan

## Implementation Status

### ✅ Week 1: Foundation - COMPLETED
**Date:** 2026-05-24

### 🔧 Surgical Updates Applied (2026-06-10)

The following surgical updates have been applied:

1. **Removed Duplicate logspace.provider Model** - The `logspace.provider` model has been removed in favor of using `res.partner` with `is_provider=True`. This avoids duplicate models and consolidates provider management.
   - Removed from `models/__init__.py`
   - Removed from `__manifest__.py` (logspace_provider_views.xml commented out)
   - All existing models already point to `res.partner` for provider references

2. **Updated logspace_state Field States** - The `logspace_state` field in `sale.order` has been updated with proper 10-step workflow states:
   - `order_received` → `pickup_started` → `vendor_arrived_pickup` → `pickup_addons` → `pickup_completed` → `pre_dropoff_addons` → `arrived_destination` → `dropoff_completed` → `grace_period` → `order_completed`

3. **Updated Action Methods** - All action methods in `sale_order.py` have been updated to match the new state workflow:
   - `action_logspace_confirm()` - Sets state to `order_received`
   - `action_start_pickup()` - Sets state to `pickup_started`
   - `action_vendor_arrived_pickup()` - Sets state to `vendor_arrived_pickup`
   - `action_pickup_addons()` - Sets state to `pickup_addons`
   - `action_pickup_completed()` - Sets state to `pickup_completed`
   - `action_pre_dropoff_addons()` - Sets state to `pre_dropoff_addons`
   - `action_arrived_destination()` - Sets state to `arrived_destination`
   - `action_dropoff_completed()` - Sets state to `dropoff_completed`
   - `action_start_grace_period()` - Sets state to `grace_period`
   - `action_complete_order()` - Sets state to `order_completed`
   - `action_cancel_logspace()` - Sets state to `cancelled`

4. **Fixed Guest Booking User Registration** - Updated `/logspace/booking/done` controller:
   - If user is not logged in: checks if email already has an account
   - If account exists: uses existing account for the order
   - If no account: creates new partner + portal user, sends invitation email
   - If user is logged in: uses current user's account

5. **Fixed My Orders Route** - Updated `/logspace/my/orders` and `/my/orders` routes:
   - Fixed `env.user` → `request.env.user` bugs throughout the file
   - Updated `_get_real_orders()` to use new logspace_state values
   - Updated `_get_logspace_order_counts()` with correct state mappings
   - Added parent company lookup for partners (handles contacts of companies)
   - Updated `_get_real_order_timeline()` with new state mappings
   - Fixed verification code visibility logic for new states

6. **Updated Timeline Model** - Updated `logspace.order.timeline` event types to match new states.

---

#### Completed Tasks:
1. **Updated Dependencies** - Added `hr` and `helpdesk` modules to manifest
2. **Created/Updated Models:**
   - `models/res_partner.py` - Provider fields on res.partner (is_provider, state, fleet_summary_ids, time_frame_ids, special_instruction_ids)
   - `models/hr_job.py` - show_in_portal boolean for contact roles
   - `models/logspace_provider_fleet_summary.py` - Fleet capacity per vehicle type
   - `models/logspace_provider_time_frame.py` - Time slots per vehicle type
   - `models/logspace_provider_special_instruction.py` - Provider instructions per vehicle type
   - `models/logspace_vehicle_type.py` - Added image and image_url fields
   - `models/sale_order.py` - Full Logspace order fields (provider, zones, contacts, verification codes, states)
   - `models/helpdesk_ticket.py` - Logspace ticket integration fields
3. **Updated Model Imports** - `models/__init__.py`
4. **Created Backend Views:**
   - `views/backend/res_partner_views.xml` - Provider form with 6 notebook pages (Business Info, Fleet Summary, Time Frames, Special Instructions, Vehicles, Price Matrix)
   - `views/backend/hr_job_views.xml` - Contact roles configuration
   - `views/backend/sale_order_views.xml` - Order form with 6 notebook pages
   - `views/backend/helpdesk_ticket_views.xml` - Ticket integration
   - `views/backend/logspace_vehicle_views.xml` - Vehicle management
   - Updated all existing views: replaced `tree` with `list` for Odoo 19 compatibility
5. **Updated Menus** - `logspace_menus.xml` with new actions
6. **Security & Access Rights:**
   - `security/ir.model.access.csv` - All model permissions
   - `security/logspace_security.xml` - Record rules for portal/public access
7. **Updated Manifest** - Added all new files and dependencies

#### Installation Verified On: `o19_db_3`

#### Known Issues (Non-Critical):
- Duplicate field labels (Payment Method, Driver) - cosmetic
- Missing not-null constraints on address fields - expected (optional fields)

---

### 🔧 Week 1 Fixes Applied (2026-05-24)

The following issues have been fixed:

1. **Fixed Provider Model References** - Updated all models that referenced the deprecated `logspace.provider` model to use `res.partner` with `is_provider=True` domain:
   - `models/logspace_order.py` - `logspace_provider_id` now points to `res.partner`
   - `models/logspace_ticket.py` - `provider_id` now points to `res.partner`
   - `models/logspace_vehicle.py` - `provider_id` now points to `res.partner`
   - `models/logspace_price_matrix.py` - `provider_id` now points to `res.partner`
   - `models/logspace_rating.py` - `provider_id` now points to `res.partner`
   - `models/logspace_refund.py` - `provider_id` now points to `res.partner`
   - `models/logspace_provider_vtype_addon.py` - `provider_id` now points to `res.partner`

2. **Fixed Notebook Pages Inline Editing** - Updated `res_partner_views.xml` to use `<list editable="bottom">` with proper field definitions for:
   - Fleet Summary page
   - Time Frames page
   - Special Instructions page
   - Vehicles page
   - Price Matrix page

3. **Fixed View Domains** - Added `domain="[('is_provider', '=', True)]"` to provider_id fields in:
   - `views/backend/logspace_vehicle_views.xml`
   - `views/backend/logspace_price_matrix_views.xml`
   - `views/backend/logspace_provider_vtype_addon_views.xml`

4. **Fixed Helpdesk Ticket Error** - The `logspace_provider_id` field in `helpdesk_ticket.py` was already correctly configured as a related field to `res.partner` through `sale.order`.

---

## ✅ Week 4: Provider Registration - COMPLETED (2026-05-31)

### Tasks Completed:
1. **5-Step Provider Registration with Session**
   - Step 1: Business Info (name, email, phone, tax_id, cr_number, years_experience, address)
   - Step 2: Contacts (name, role, phone, email) - stored in session
   - Step 3: Fleet (vehicle type, fleet count, capacity, dimensions) - stored in session
   - Step 4: Documents (vehicles_doc, company_doc, bank_statement) - stored in session
   - Step 5: Review page with dynamic data from session

2. **Provider Creation on Submit** (`/logspace/provider/done`)
   - Creates `res.partner` with `is_provider=True`
   - Sets state to 'pending'
   - Stores business details (tax_id, cr_number, years_experience)

3. **Contacts Creation**
   - Creates child partners for each contact
   - Links to `hr.job` for role mapping

4. **Fleet Summary Creation**
   - Creates `logspace.provider.fleet.summary` records
   - Links to actual vehicle types

5. **Session Management**
   - Data persisted across steps using `request.session`
   - Can navigate back and edit previous steps
   - Cleared on successful submission

### Files Modified:
- `controllers/main.py` - Provider registration methods now use real data
- `views/mockup_provider_templates.xml` - Forms updated with POST/CSRF, dynamic data display

---

## ✅ Week 2: Search & Booking Flow - COMPLETED

### Tasks Completed:
1. **Search Controller** (`/logspace/search`)
   - Zone-to-zone search via price matrix
   - Vehicle zone verification (pickup OR dropoff zone match)
   - Time frame availability check
   - Special instructions display

2. **Booking Flow Controllers**
   - Session-based multi-step booking
   - Step 1: Item Details → Session storage
   - Step 2: Add-ons → Session storage
   - Step 3: Checkout → Calculate totals
   - Step 4: Payment (placeholder for Paymob)
   - Step 5: Order creation with auto-user registration

3. **Guest Checkout**
   - Create res.partner from guest data
   - Create res.users with portal access
   - Send invitation email
   - Link order to new user

---

## ✅ Week 3: Customer Portal - COMPLETED (2026-05-31)

### Tasks Completed:
1. **My Orders List** (`/logspace/my/orders`)
   - Query actual `sale.order` records for logged-in user
   - Filter by status tabs (all, active, completed, cancelled)
   - Real-time counts for each status
   - Order details with provider, vehicle type, dates

2. **Order Tracking** (`/logspace/my/orders/track/<order_id>`)
   - Real order timeline from `logspace.order.timeline`
   - Conditional verification codes display (pickup/dropoff)
   - Driver information from order

3. **Rating System** (`/logspace/my/orders/<order_id>/rate`)
   - Create `logspace.rating` records
   - Overall rating (1-5 stars) + category ratings
   - Prevents rating non-delivered orders
   - Creates notification on submit

4. **Refund Requests** (`/logspace/my/orders/<order_id>/refunds`)
   - Create `logspace.refund` records
   - Full workflow: draft → submitted → review → approved/rejected
   - List refunds with status for each order
   - Creates notification on submit

5. **Helpdesk Tickets** (`/logspace/my/orders/<order_id>/tickets`)
   - Create `helpdesk.ticket` records linked to orders
   - Logspace ticket type categorization
   - List tickets with status (open/resolved)

6. **Notifications** (`/logspace/my/notifications`)
   - Real `logspace.notification` records
   - Mark individual/all as read
   - Time-ago formatting
   - Created on booking confirmation, rating, refund, ticket events

### Files Modified:
- `controllers/main.py` - Portal methods now use real data
- `views/mockup_portal_templates.xml` - Forms updated with proper POST/CSRF

---

## Original Architecture & Implementation Details

### Dependencies
```python
# __manifest__.py
'depends': [
    'website',
    'portal',
    'web',
    'auth_signup',
    'sale',
    'mail',
    'hr',           # For job positions (contact roles)
    'helpdesk',     # For support tickets
],
```

---

## Dependencies (Updated)

```python
# __manifest__.py
'depends': [
    'website',
    'portal',
    'web',
    'auth_signup',
    'sale',
    'mail',
    'hr',           # For job positions (contact roles)
    'helpdesk',     # For support tickets
],
```

---

## Architecture Overview

### Provider Management (res.partner Extension)
```
res.partner (extended)
├── is_provider: Boolean
├── is_approved_provider: Boolean
├── state: draft/pending/approved/rejected/suspended
├── Provider Fields (visible if is_provider=True)
│   ├── tax_id, cr_number, years_experience
│   ├── platform_fee_percentage
│   ├── approval_date, rejection_reason, suspension_reason
├── Contacts (child_ids - standard Odoo)
│   └── function: hr.job (with show_in_portal boolean)
├── Fleet Summary (logspace.provider.fleet.summary)
├── Time Frames (logspace.provider.time.frame)
├── Special Instructions (logspace.provider.special.instruction)  # NEW
└── Documents (ir.attachment with res_model='res.partner')
```

---

## Model Definitions (Final)

### 1. Extend: res.partner (Provider Fields)
**File**: `models/res_partner.py`

```python
class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Provider Identification
    is_provider = fields.Boolean('Is Logspace Provider', default=False)
    is_approved_provider = fields.Boolean('Approved Provider', default=False)

    # Provider State Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('suspended', 'Suspended'),
    ], string='Provider Status', default='draft', tracking=True)

    # Business Information (visible if is_provider)
    tax_id = fields.Char(string='Tax ID / EIN', tracking=True)
    cr_number = fields.Char(string='CR Number', help='Commercial Registration Number')
    years_experience = fields.Selection([
        ('less_1', 'Less than 1 year'),
        ('1_2', '1-2 years'),
        ('3_5', '3-5 years'),
        ('5_10', '5-10 years'),
        ('more_10', 'More than 10 years'),
    ], string='Years of Experience', default='3_5')

    # Financial & Workflow
    platform_fee_percentage = fields.Float(string='Platform Fee (%)', default=0.1)
    approval_date = fields.Date(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    suspension_reason = fields.Text(string='Suspension Reason')

    # Related Records
    vehicle_ids = fields.One2many('logspace.vehicle', 'provider_id', string='Vehicles')
    price_matrix_ids = fields.One2many('logspace.price.matrix', 'provider_id', string='Price Matrix')
    fleet_summary_ids = fields.One2many('logspace.provider.fleet.summary', 'partner_id', string='Fleet Summary')
    time_frame_ids = fields.One2many('logspace.provider.time.frame', 'partner_id', string='Available Time Frames')
    special_instruction_ids = fields.One2many('logspace.provider.special.instruction', 'partner_id', string='Special Instructions by Vehicle Type')

    # Computed Fields
    vehicle_count = fields.Integer(compute='_compute_vehicle_count', store=True)
    rating = fields.Float(compute='_compute_rating', store=True, digits=(2, 1))
    review_count = fields.Integer(compute='_compute_rating', store=True)
```

### 2. Extend: hr.job (Job Position)
**File**: `models/hr_job.py`

```python
class HrJob(models.Model):
    _inherit = 'hr.job'

    show_in_portal = fields.Boolean('Show in Portal', default=False,
        help='If checked, contacts with this job position will be visible to customers')
```

### 3. New Model: Provider Fleet Summary
**File**: `models/logspace_provider_fleet_summary.py`

```python
class LogspaceProviderFleetSummary(models.Model):
    _name = 'logspace.provider.fleet.summary'
    _description = 'Provider Fleet Summary by Vehicle Type'
    _rec_name = 'vehicle_type_id'

    partner_id = fields.Many2one('res.partner', string='Provider',
        required=True, domain=[('is_provider', '=', True)], ondelete='cascade')
    vehicle_type_id = fields.Many2one('logspace.vehicle.type',
        string='Vehicle Type', required=True)
    fleet_count = fields.Integer(string='Fleet Count', required=True, default=1)
    capacity_tons = fields.Float(string='Capacity (Tons)')
    dimensions = fields.Char(string='Dimensions', help='e.g., 300x200x150 cm')

    _sql_constraints = [
        ('unique_provider_vehicle_type', 'unique(partner_id, vehicle_type_id)',
         'Fleet summary for this vehicle type already exists!')
    ]
```

### 4. New Model: Provider Time Frame (Simplified)
**File**: `models/logspace_provider_time_frame.py`

```python
class LogspaceProviderTimeFrame(models.Model):
    _name = 'logspace.provider.time.frame'
    _description = 'Provider Available Time Frames'
    _rec_name = 'name'

    partner_id = fields.Many2one('res.partner', string='Provider',
        required=True, domain=[('is_provider', '=', True)], ondelete='cascade')
    vehicle_type_id = fields.Many2one('logspace.vehicle.type',
        string='Vehicle Type', required=True)

    # Simple time ranges (e.g., "08:00-10:00" stored as 8.0-10.0)
    time_start = fields.Float(string='Start Time', required=True,
        help='Time in hours (e.g., 8.0 = 8:00 AM, 13.5 = 1:30 PM)')
    time_end = fields.Float(string='End Time', required=True)

    # Type of service
    is_pickup = fields.Boolean('Available for Pickup', default=True)
    is_dropoff = fields.Boolean('Available for Dropoff', default=True)

    # Display label (computed)
    name = fields.Char(string='Time Frame', compute='_compute_name', store=True)

    @api.depends('time_start', 'time_end')
    def _compute_name(self):
        for tf in self:
            start_hours = int(tf.time_start)
            start_mins = int((tf.time_start % 1) * 60)
            end_hours = int(tf.time_end)
            end_mins = int((tf.time_end % 1) * 60)
            tf.name = f"{start_hours:02d}:{start_mins:02d} - {end_hours:02d}:{end_mins:02d}"

    _sql_constraints = [
        ('unique_timeframe', 'unique(partner_id, vehicle_type_id, time_start, time_end)',
         'This time frame already exists for this vehicle type!')
    ]
```

**Time Options** (matching frontend):
- 8:00-10:00 (8.0 - 10.0)
- 10:00-12:00 (10.0 - 12.0)
- 12:00-14:00 (12.0 - 14.0)
- 14:00-16:00 (14.0 - 16.0)
- 16:00-18:00 (16.0 - 18.0)
- 18:00-20:00 (18.0 - 20.0)

### 5. NEW MODEL: Provider Special Instruction
**File**: `models/logspace_provider_special_instruction.py`

```python
class LogspaceProviderSpecialInstruction(models.Model):
    _name = 'logspace.provider.special.instruction'
    _description = 'Provider Special Instructions by Vehicle Type'
    _rec_name = 'vehicle_type_id'

    partner_id = fields.Many2one('res.partner', string='Provider',
        required=True, domain=[('is_provider', '=', True)], ondelete='cascade')
    vehicle_type_id = fields.Many2one('logspace.vehicle.type',
        string='Vehicle Type', required=True)
    instructions = fields.Html(string='Special Instructions',
        help='Instructions shown to customers for this vehicle type (e.g., handling requirements, equipment included, etc.)')

    # Whether to show in frontend
    is_active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('unique_instruction_vehicle', 'unique(partner_id, vehicle_type_id)',
         'Special instructions for this vehicle type already exist!')
    ]
```

**Usage**: When displaying provider/vehicle in search results or vendor detail page, fetch the special instruction for that provider + vehicle type combination.

### 6. Extend: Vehicle Type (Add Image)
**File**: `models/logspace_vehicle_type.py`

```python
class LogspaceVehicleType(models.Model):
    _inherit = 'logspace.vehicle.type'

    image = fields.Binary(string='Vehicle Image', attachment=True)
    image_url = fields.Char(string='Image URL', compute='_compute_image_url')

    def _compute_image_url(self):
        for vt in self:
            if vt.image:
                vt.image_url = f'/web/image/logspace.vehicle.type/{vt.id}/image'
            else:
                # Default image based on code or category
                default_images = {
                    'flatbed': '/appness_logspace_mockup2/static/src/img/truck_flatbed.jpg',
                    'box': '/appness_logspace_mockup2/static/src/img/truck_box.jpg',
                    'mini': '/appness_logspace_mockup2/static/src/img/truck_mini.jpg',
                    'pickup': '/appness_logspace_mockup2/static/src/img/truck_pickup.jpg',
                    'heavy': '/appness_logspace_mockup2/static/src/img/truck_heavy.jpg',
                    'refrigerated': '/appness_logspace_mockup2/static/src/img/truck_reefer.jpg',
                }
                # Try to match by code, fallback to default
                for key, img in default_images.items():
                    if key in (vt.code or '').lower():
                        vt.image_url = img
                        break
                else:
                    vt.image_url = '/appness_logspace_mockup2/static/src/img/truck_default.jpg'
```

### 7. Extend: Sale Order (Logspace Order)
**File**: `models/sale_order.py`

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Master flag
    is_logspace_order = fields.Boolean(string='Logspace Order', default=False)

    # Provider & Vehicle (visible if is_logspace_order)
    logspace_provider_id = fields.Many2one('res.partner',
        string='Logspace Provider', domain=[('is_provider', '=', True)])
    logspace_vehicle_id = fields.Many2one('logspace.vehicle', string='Assigned Vehicle')
    logspace_driver_id = fields.Many2one('res.partner', string='Driver')

    # Route Information
    pickup_zone_id = fields.Many2one('logspace.zone', string='Pickup Zone')
    dropoff_zone_id = fields.Many2one('logspace.zone', string='Dropoff Zone')
    pickup_address = fields.Text(string='Pickup Address')
    dropoff_address = fields.Text(string='Dropoff Address')

    # Contacts
    pickup_contact_name = fields.Char(string='Pickup Contact Name')
    pickup_contact_phone = fields.Char(string='Pickup Contact Phone')
    dropoff_contact_name = fields.Char(string='Dropoff Contact Name')
    dropoff_contact_phone = fields.Char(string='Dropoff Contact Phone')

    # Scheduling
    scheduled_date = fields.Date(string='Scheduled Date')
    pickup_timeframe = fields.Char(string='Pickup Time Frame')
    dropoff_timeframe = fields.Char(string='Dropoff Time Frame')

    # Item Details
    item_description = fields.Text(string='Item Description')
    special_instructions = fields.Text(string='Customer Special Instructions')

    # Addons
    logspace_addon_ids = fields.Many2many('logspace.addon', string='Add-ons')

    # Verification Codes
    verification_code_pickup = fields.Char(string='Pickup Verification Code', size=4)
    verification_code_dropoff = fields.Char(string='Dropoff Verification Code', size=4)

    # State
    logspace_state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('driver_assigned', 'Driver Assigned'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Logspace Status', default='pending', tracking=True)

    # Guest Order
    is_guest_order = fields.Boolean(string='Guest Order', default=False)
    guest_email = fields.Char(string='Guest Email')
    guest_phone = fields.Char(string='Guest Phone')
```

### 8. Extend: Helpdesk Ticket
**File**: `models/helpdesk_ticket.py`

```python
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    is_logspace_ticket = fields.Boolean(string='Logspace Ticket', default=False)
    logspace_order_id = fields.Many2one('sale.order', string='Related Order',
        domain=[('is_logspace_order', '=', True)])
    logspace_ticket_type = fields.Selection([
        ('booking', 'Booking Issue'),
        ('payment', 'Payment Issue'),
        ('delivery', 'Delivery Problem'),
        ('driver', 'Driver Complaint'),
        ('refund', 'Refund Request'),
        ('other', 'Other'),
    ], string='Ticket Category')
```

---

## Search Logic (Final - Alternative Approach with Zone Verification)

```python
@http.route(['/logspace', '/logspace/search'], type='http', auth='public', website=True)
def mockup_search(self, **kwargs):
    """Search: Zone to Zone via Price Matrix, verify Vehicle Zones"""

    zones = request.env['logspace.zone'].sudo().search([])
    vehicle_types = request.env['logspace.vehicle.type'].sudo().search([])

    if request.httprequest.method == 'POST':
        zone_from_id = int(kwargs.get('zone_from_id'))
        zone_to_id = int(kwargs.get('zone_to_id'))
        vehicle_type_id = int(kwargs.get('vehicle_type_id'))
        pickup_date = kwargs.get('pickup_date')
        requested_timeframe = kwargs.get('timeframe')  # e.g., "10:00-12:00"

        # Step 1: Find price matrices for this route with this vehicle type
        price_matrices = request.env['logspace.price.matrix'].sudo().search([
            ('vehicle_type_id', '=', vehicle_type_id),
            ('zone_from_id', '=', zone_from_id),
            ('zone_to_id', '=', zone_to_id),
            ('is_active', '=', True),
            ('provider_id.is_provider', '=', True),
            ('provider_id.state', '=', 'approved'),
        ])

        results = []
        for matrix in price_matrices:
            provider = matrix.provider_id

            # Step 2: Verify provider has vehicles of this type in pickup OR dropoff zone
            vehicles = request.env['logspace.vehicle'].sudo().search([
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
            if requested_timeframe:
                # Parse "10:00-12:00" to (10.0, 12.0)
                start_str, end_str = requested_timeframe.split('-')
                req_start = float(start_str.replace(':', '.'))
                req_end = float(end_str.replace(':', '.'))

                timeframe_available = any(
                    tf.time_start <= req_start and tf.time_end >= req_end
                    for tf in timeframes
                )

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
            fleet_count = sum(fleet_summary.mapped('fleet_count')) or len(vehicles)

            results.append({
                'price_matrix_id': matrix.id,
                'provider_id': provider.id,
                'provider_name': provider.name,
                'vehicle_type': matrix.vehicle_type_id.name,
                'vehicle_type_image': matrix.vehicle_type_id.image_url,
                'price': matrix.provider_price,
                'rating': provider.rating,
                'reviews': provider.review_count,
                'zone_from': matrix.zone_from_id.name,
                'zone_to': matrix.zone_to_id.name,
                'timeframes': timeframes,
                'timeframe_available': timeframe_available,
                'requested_timeframe': requested_timeframe,
                'fleet_count': fleet_count,
                'special_instructions': special_instruction.instructions if special_instruction else '',
                'special_instruction_id': special_instruction.id if special_instruction else False,
            })

        return request.render('appness_logspace_mockup2.mockup2_search_page', {
            'show_results': True,
            'results': results,
            'search_params': kwargs,
            'zones': zones,
            'vehicle_types': vehicle_types,
        })

    # GET request - show search form
    return request.render('appness_logspace_mockup2.mockup2_search_page', {
        'show_results': False,
        'zones': zones,
        'vehicle_types': vehicle_types,
    })
```

---

## View Updates (Visibility Rules)

### Provider Views (res.partner)

```xml
<!-- In provider form view -->
<field name="is_provider"/>
<field name="tax_id" invisible="not is_provider"/>
<field name="cr_number" invisible="not is_provider"/>
<field name="years_experience" invisible="not is_provider"/>
<field name="state" invisible="not is_provider"/>
<field name="platform_fee_percentage" invisible="not is_provider"/>

<field name="fleet_summary_ids" invisible="not is_provider">
    <tree editable="bottom">
        <field name="vehicle_type_id"/>
        <field name="fleet_count"/>
        <field name="capacity_tons"/>
        <field name="dimensions"/>
    </tree>
</field>

<field name="time_frame_ids" invisible="not is_provider">
    <tree editable="bottom">
        <field name="vehicle_type_id"/>
        <field name="time_start" widget="float_time"/>
        <field name="time_end" widget="float_time"/>
        <field name="is_pickup"/>
        <field name="is_dropoff"/>
    </tree>
</field>

<!-- NEW: Special Instructions -->
<field name="special_instruction_ids" invisible="not is_provider">
    <tree editable="bottom">
        <field name="vehicle_type_id"/>
        <field name="instructions" widget="html"/>
        <field name="is_active"/>
    </tree>
</field>

<field name="price_matrix_ids" invisible="not is_provider"/>
<field name="vehicle_ids" invisible="not is_provider"/>
```

### Sale Order Views

```xml
<field name="is_logspace_order"/>
<field name="logspace_provider_id" invisible="not is_logspace_order"/>
<field name="logspace_vehicle_id" invisible="not is_logspace_order"/>
<field name="logspace_driver_id" invisible="not is_logspace_order"/>
<field name="pickup_zone_id" invisible="not is_logspace_order"/>
<field name="dropoff_zone_id" invisible="not is_logspace_order"/>
<field name="pickup_address" invisible="not is_logspace_order"/>
<field name="dropoff_address" invisible="not is_logspace_order"/>
<field name="pickup_contact_name" invisible="not is_logspace_order"/>
<field name="pickup_contact_phone" invisible="not is_logspace_order"/>
<field name="dropoff_contact_name" invisible="not is_logspace_order"/>
<field name="dropoff_contact_phone" invisible="not is_logspace_order"/>
<field name="scheduled_date" invisible="not is_logspace_order"/>
<field name="pickup_timeframe" invisible="not is_logspace_order"/>
<field name="dropoff_timeframe" invisible="not is_logspace_order"/>
<field name="item_description" invisible="not is_logspace_order"/>
<field name="special_instructions" invisible="not is_logspace_order"/>
<field name="verification_code_pickup" invisible="not is_logspace_order"/>
<field name="verification_code_dropoff" invisible="not is_logspace_order"/>
<field name="logspace_state" invisible="not is_logspace_order"/>
<field name="logspace_addon_ids" invisible="not is_logspace_order"/>
```

---

## Implementation Timeline (Final)

### Week 1: Foundation
- [ ] Update `__manifest__.py` - add `hr` and `helpdesk` dependencies
- [ ] Extend `res.partner` with provider fields
- [ ] Extend `hr.job` with `show_in_portal`
- [ ] Create `logspace.provider.fleet.summary` model
- [ ] Create `logspace.provider.time.frame` model
- [ ] Create `logspace.provider.special.instruction` model (NEW)
- [ ] Extend `logspace.vehicle.type` with image field
- [ ] Extend `sale.order` with logspace fields
- [ ] Extend `helpdesk.ticket` with logspace fields
- [ ] Update all backend views with visibility rules
- [ ] Update security rules and access rights

### Week 2: Search & Booking Session
- [ ] Implement zone-to-zone search via price matrix (verify vehicle zones)
- [ ] Vehicle detail page with real data (including special instructions)
- [ ] Session-based booking flow (steps 1-4)
- [ ] Order creation with auto-user registration

### Week 3: Customer Portal - COMPLETED
- [x] My orders list (real data)
- [x] Order tracking with conditional verification codes
- [x] Rating creation
- [x] Refund request flow
- [x] Helpdesk ticket integration
- [x] Notifications

### Week 4: Provider Registration - COMPLETED (2026-05-31)
- [x] 5-step provider registration with session
- [x] Document upload handling
- [x] Provider creation on submit (res.partner with is_provider=True)
- [x] Contacts creation (child partners with hr.job roles)
- [x] Fleet summary creation
- [x] Review page with dynamic data

### Week 5: Polish & Testing - COMPLETED (2026-05-31)
- [x] Email templates created
  - Booking confirmation to customer
  - Driver assigned notification
  - Provider application received
  - Provider approval notification
  - Order delivered notification
- [x] Email sending hooks in controllers/models
- [x] Provider approval workflow with automatic portal user creation
- [x] Provider rejection workflow
- [x] Provider suspension workflow

---

## Implementation Summary

### All Weeks Completed!

| Week | Status | Key Deliverables |
|------|--------|------------------|
| Week 1 | ✅ Complete | Foundation - Models, Views, Security |
| Week 2 | ✅ Complete | Search & Booking Flow - Real data, Session-based |
| Week 3 | ✅ Complete | Customer Portal - Real orders, ratings, refunds, tickets |
| Week 4 | ✅ Complete | Provider Registration - Session-based, real creation |
| Week 5 | ✅ Complete | Email notifications, polish |

### Production Ready Features:
1. **Customer Booking Flow** - Full search, booking, payment, confirmation
2. **Guest Checkout** - Auto-creates portal user
3. **Customer Portal** - Orders, tracking, ratings, refunds, tickets
4. **Provider Registration** - 5-step wizard, real data
5. **Provider Management** - Approval workflow with user creation
6. **Email Notifications** - Booking confirmation, driver assignment, delivery, provider approval

### Next Steps (Optional):
- Paymob payment integration
- Real-time tracking updates (WebSockets)
- Mobile app API endpoints
- Advanced reporting

---

## Summary of Final Answers

| Question | Answer | Implementation |
|----------|--------|----------------|
| Q1: Vehicle Zone Logic | Current plan | Search price matrices first, verify vehicle zones match pickup OR dropoff |
| Q2: Driver Interface | Confirm skip | Driver gets codes via email only (no portal) |
| Q3: Helpdesk | Add dependency | Add `helpdesk` to manifest |
| Q4: HR Module | Add dependency | Add `hr` to manifest for job positions |
| Q5: Special Instructions | New model | `logspace.provider.special.instruction` with provider + vehicle type + instructions (html) |

---

## Ready to Start Implementation

**All requirements are finalized. The plan is ready for implementation.**

**Shall we begin Week 1 tasks?**

### Week 1 Task List (for confirmation):
1. Update manifest with `hr` and `helpdesk` dependencies
2. Create/update model files:
   - `models/res_partner.py`
   - `models/hr_job.py`
   - `models/logspace_provider_fleet_summary.py`
   - `models/logspace_provider_time_frame.py`
   - `models/logspace_provider_special_instruction.py` (NEW)
   - `models/logspace_vehicle_type.py`
   - `models/sale_order.py`
   - `models/helpdesk_ticket.py`
3. Create/update view files with visibility rules
4. Update security rules

**Confirm to begin Week 1 implementation.**
