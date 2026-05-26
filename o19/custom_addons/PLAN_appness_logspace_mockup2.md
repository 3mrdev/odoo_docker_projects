# Logspace Mockup2 - Implementation Plan

## Overview
A new Odoo 19 module `appness_logspace_mockup2` that creates an interconnected mockup website with 17 screens showing a complete customer journey for a logistics/truck booking application.

## Key Design Principles
1. **Follow Odoo Standards**: Reuse existing patterns from `/my/account` and portal pages
2. **Use Odoo Theme Colors**: Primary (#714B67), Secondary (#0180A2), Success (#28A745), etc.
3. **Minimal Code**: Reuse existing portal templates where possible
4. **Interconnected Navigation**: All screens linked in a logical flow
5. **Dummy Data**: Controllers return static/mock data, no database queries needed

---

## Module Structure

```
appness_logspace_mockup2/
├── __init__.py
├── __manifest__.py
├── controllers/
│   └── main.py              # 17 routes with dummy data
├── views/
│   ├── mockup_layout_templates.xml     # Base layout
│   ├── mockup_search_templates.xml     # Screen 1-2: Search/List
│   ├── mockup_vendor_templates.xml     # Screen 3: Vendor/Item
│   ├── mockup_booking_templates.xml    # Screen 4-8: Booking stepper
│   ├── mockup_auth_templates.xml       # Screen 9-10: Login/Signup
│   └── mockup_portal_templates.xml     # Screen 11-17: Portal/My Account
├── static/
│   ├── src/
│   │   ├── scss/
│   │   │   └── mockup2.scss   # Custom styles, Odoo colors
│   │   └── js/
│   │       └── mockup2.js     # Minimal interactivity
│   └── description/
│       └── icon.png
└── data/
    └── demo_data.xml        # Optional demo records
```

---

## Screen-by-Screen Implementation Plan

### Customer Journey Flow
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PUBLIC FLOW                     │  AUTHENTICATED PORTAL FLOW               │
│                                  │                                          │
│  1. Search ──► 2. Results Grid ──► 3. Vendor/Item Page                    │
│                      │                    │                                 │
│                      ▼                    ▼                                 │
│  9. Login ◄──────── 4. Add-ons ◄─────── Book Now                          │
│      │                    │                                                 │
│      ▼                    ▼                                               │
│  10. SignUp ──► 11. Profile    5. Details ──► 6. Checkout                   │
│      │           (can skip)          │            │                        │
│      │               │               ▼            ▼                         │
│      └───────────────┘           7. Payment ──► 8. Confirmation            │
│                                      │            │                         │
│                                      ▼            ▼                         │
│                              16. Refund ◄── 12. My Orders ──► 13. Tracking│
│                                  │      │            │                      │
│                                  ▼      └────────► 15. Rating               │
│                              17. Ticket/Help                                 │
│                                      │                                      │
│                                      ▼                                      │
│                              14. Notifications                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Screen Specifications

### Screen 1 & 2: Search & List/Grid View
**Route**: `/mockup2/search`
**Template**: `mockup2_search_page`

**Features**:
- Hero search section with service type, pickup/dropoff, date
- Grid/List toggle for results display
- 6 dummy truck listings with images, ratings, prices
- Filter sidebar (optional)

**Odoo Standards**:
- Use `website.layout` with breadcrumb
- Reuse card styles from `/web/static/src/scss/bootstrap_overridden.scss`
- FontAwesome icons

**Navigation**:
- Search button → Results display (same page)
- Truck card click → Screen 3 (Vendor)
- Login link in header → Screen 9

**Dummy Data**:
```python
trucks = [
    {'id': 1, 'name': 'Flatbed Truck 3T', 'vendor': 'ABC Logistics', 
     'price': 150, 'rating': 4.5, 'reviews': 128, 'image': 'truck1.png',
     'features': ['GPS Tracking', 'Insurance Included']},
    # ... 5 more trucks
]
```

---

### Screen 3: Vendor/Item Page
**Route**: `/mockup2/vendor/<int:vendor_id>`
**Template**: `mockup2_vendor_page`

**Features**:
- Large vehicle image gallery
- Vendor info (name, rating, completed trips)
- Price breakdown
- "Book Now" CTA button
- Back to search link

**Odoo Standards**:
- Use Odoo `bg-o-color-1` for primary headers
- Card layout similar to portal document cards

**Navigation**:
- Book Now → Screen 4 (Add-ons)
- Back → Screen 1 (Search)

**Dummy Data**:
```python
vendor = {
    'id': 1, 'name': 'ABC Logistics', 'rating': 4.7,
    'trips_completed': 1250, 'member_since': '2021',
    'description': 'Professional logistics company...',
    'features': ['GPS Tracked', '24/7 Support', 'Insured'],
    'images': ['/img1.jpg', '/img2.jpg', '/img3.jpg']
}
```

---

### Screen 4: Add-ons
**Route**: `/mockup2/addons`
**Template**: `mockup2_addons_page`

**Features**:
- Stepper showing step 1 of 4
- Checkbox list of add-ons with prices
- Order summary sidebar

**Odoo Standards**:
- Stepper using `progress-bar` component
- Form check styles from Bootstrap 5 (Odoo default)

**Navigation**:
- Next → Screen 5 (Details)
- Cancel → Screen 3 (Vendor)

**Dummy Data**:
```python
addons = [
    {'id': 1, 'name': 'Loading Service', 'price': 25, 'description': 'Professional loading'},
    {'id': 2, 'name': 'Insurance Premium', 'price': 15, 'description': 'Full coverage'},
    {'id': 3, 'name': 'Priority Delivery', 'price': 30, 'description': 'Same day delivery'},
]
```

---

### Screen 5: Order Details/Setup
**Route**: `/mockup2/details`
**Template**: `mockup2_details_page`

**Features**:
- Stepper showing step 2 of 4
- Form fields: item description, weight, dimensions
- Pickup/Delivery time selection
- Special instructions textarea

**Odoo Standards**:
- Use `form-control` and `form-label` classes
- Grid layout using Odoo's grid system

**Navigation**:
- Next → Screen 6 (Checkout)
- Back → Screen 4 (Add-ons)

---

### Screen 6: Checkout/Summary
**Route**: `/mockup2/checkout`
**Template**: `mockup2_checkout_page`

**Features**:
- Stepper showing step 3 of 4
- Full order summary (route, vehicle, add-ons, total)
- Editable sections that expand
- Total calculation display

**Odoo Standards**:
- Summary card like portal order view
- Use `text-primary` for prices

**Navigation**:
- Proceed to Payment → Screen 7
- Edit Details → Screen 5
- Cancel → Screen 1

---

### Screen 7: Payment Screen
**Route**: `/mockup2/payment`
**Template**: `mockup2_payment_page`

**Features**:
- Stepper showing step 4 of 4
- Payment method selection (Credit Card, Apple Pay, Wallet)
- Card form (if credit card selected)
- Promo code field

**Odoo Standards**:
- Use toggle button groups like Odoo backend
- Form validation styling

**Navigation**:
- Pay Now → Screen 8 (Confirmation)
- Back → Screen 6

---

### Screen 8: Done/Confirmation
**Route**: `/mockup2/done`
**Template**: `mockup2_done_page`

**Features**:
- Success icon and message
- Order number display
- Quick action buttons (Track, Share, Home)
- Timeline preview (optional)

**Odoo Standards**:
- Success alert styling `alert-success`
- Use `fa-check-circle` icon

**Navigation**:
- Track Order → Screen 13 (Tracking)
- View Orders → Screen 12 (My Orders)
- Book Another → Screen 1 (Search)

**Dummy Data**:
```python
order = {
    'number': 'ORD-2024-0001',
    'status': 'confirmed',
    'truck': 'Flatbed Truck 3T',
    'total': 205.00,
    'eta': '2 hours'
}
```

---

### Screen 9: Login
**Route**: `/mockup2/login`
**Template**: `mockup2_login_page`

**Features**:
- Phone/Email input
- Password input
- "Remember me" checkbox
- Forgot password link
- Sign up link

**Odoo Standards**:
- **REUSE**: `web.login` template layout
- Same form structure as Odoo login
- Use `web.login_layout` if possible

**Navigation**:
- Sign In → Screen 11 (Profile) or Screen 12 (Orders) depending on intent
- Sign Up link → Screen 10

---

### Screen 10: SignUp
**Route**: `/mockup2/signup`
**Template**: `mockup2_signup_page`

**Features**:
- Full name input
- Phone input with country code
- Email input
- Password + Confirm password
- Terms checkbox

**Odoo Standards**:
- **REUSE**: `auth_signup.signup` template patterns
- Same validation structure

**Navigation**:
- Create Account → Screen 11 (Profile)
- Already have account → Screen 9

---

### Screen 11: My Profile
**Route**: `/mockup2/my/profile`
**Template**: `mockup2_profile_page`

**Features**:
- Left sidebar navigation (like portal)
- Profile picture upload placeholder
- Personal info form
- Password change section
- Notification preferences

**Odoo Standards**:
- **REUSE**: `portal.portal_my_home` sidebar pattern
- Use `o_portal_sidebar` classes
- Form layout like `/my/account`

**Navigation** (Sidebar):
- My Orders → Screen 12
- Notifications → Screen 14
- Help/Ticket → Screen 17
- Logout → Screen 1 (Search)

---

### Screen 12: My Orders List
**Route**: `/mockup2/my/orders`
**Template**: `mockup2_orders_page`

**Features**:
- Tab navigation: Active | Completed | Cancelled
- Order cards with:
  - Order number, date
  - Status badge (colored)
  - Truck image thumbnail
  - Price
  - Quick actions (Track, Reorder)
- Empty state for new users

**Odoo Standards**:
- **REUSE**: `portal.portal_my_orders` list patterns
- Use `o_portal_my_home` card styling
- Status badges like `badge bg-success`

**Navigation**:
- Order card click → Screen 13 (Tracking)
- Track button → Screen 13
- Rate button (if completed) → Screen 15
- Reorder → Screen 4 (Add-ons)

**Dummy Data**:
```python
orders = [
    {
        'id': 'ORD-2024-0001', 'date': '2024-01-15', 
        'status': 'in_transit', 'status_label': 'In Transit',
        'truck': 'Flatbed 3T', 'total': 205.00,
        'from': 'Riyadh', 'to': 'Jeddah'
    },
    {
        'id': 'ORD-2024-0002', 'date': '2024-01-10',
        'status': 'delivered', 'status_label': 'Delivered',
        'truck': 'Refrigerated', 'total': 350.00,
        'from': 'Dammam', 'to': 'Riyadh'
    },
]
```

---

### Screen 13: Order Tracking (Map/Timeline)
**Route**: `/mockup2/my/orders/track?order_id=xxx`
**Template**: `mockup2_track_page`

**Features**:
- Map placeholder (static image or styled div)
- Driver info card (photo, name, rating, phone)
- Live timeline with current status highlighted
- ETA display

**Odoo Standards**:
- Timeline using `border-start` with circles
- Card layout from portal

**Navigation**:
- Back to Orders → Screen 12
- Rate Driver (if delivered) → Screen 15
- Request Refund → Screen 16
- Report Issue → Screen 17

**Dummy Data**:
```python
timeline = [
    {'status': 'confirmed', 'label': 'Order Confirmed', 'time': 'Jan 15, 09:00', 'done': True},
    {'status': 'picked', 'label': 'Item Picked Up', 'time': 'Jan 15, 10:30', 'done': True},
    {'status': 'in_transit', 'label': 'In Transit', 'time': 'Jan 15, 11:00', 'done': True, 'current': True},
    {'status': 'delivered', 'label': 'Delivered', 'time': 'Expected 14:00', 'done': False},
]
```

---

### Screen 14: Notifications
**Route**: `/mockup2/my/notifications`
**Template**: `mockup2_notifications_page`

**Features**:
- Notification list with icons
- Read/Unread indicators
- Timestamp
- Mark all as read button
- Empty state

**Odoo Standards**:
- List group styling `list-group-item`
- Icon colors matching notification type

**Navigation**:
- Notification click → Relevant screen (Order, Profile, etc.)

**Dummy Data**:
```python
notifications = [
    {'id': 1, 'type': 'order', 'title': 'Driver Assigned', 'message': 'Your driver Ahmed is on the way', 'time': '10 mins ago', 'read': False},
    {'id': 2, 'type': 'payment', 'title': 'Payment Successful', 'message': 'Order ORD-2024-0001 confirmed', 'time': '2 hours ago', 'read': True},
    {'id': 3, 'type': 'promo', 'title': '20% Off!', 'message': 'Get 20% off your next booking', 'time': '1 day ago', 'read': True},
]
```

---

### Screen 15: Rating Screen
**Route**: `/mockup2/rate?order_id=xxx`
**Template**: `mockup2_rate_page`

**Features**:
- Star rating input (1-5)
- Category ratings (Driver, Vehicle, Timeliness)
- Comment textarea
- Driver profile summary

**Odoo Standards**:
- Form styling consistent with portal
- Use `fa-star` for rating icons

**Navigation**:
- Submit Review → Screen 12 (Orders) with success message
- Skip → Screen 12

---

### Screen 16: Refund Screen
**Route**: `/mockup2/refund?order_id=xxx`
**Template**: `mockup2_refund_page`

**Features**:
- Order reference (readonly)
- Refund reason dropdown
- Details textarea
- File upload placeholder (optional)
- Refund policy link

**Odoo Standards**:
- Form structure like portal forms
- Alert for policy information

**Navigation**:
- Submit Request → Screen 12 with confirmation
- Cancel → Screen 13 (Tracking)

---

### Screen 17: Ticket/Help Screen
**Route**: `/mockup2/ticket`
**Template**: `mockup2_ticket_page`

**Features**:
- Subject dropdown (Order Issue, Payment, General)
- Related order selection (if applicable)
- Description textarea
- Priority selection
- File attachment placeholder

**Odoo Standards**:
- **REUSE**: Similar to helpdesk ticket form if available
- Use standard form controls

**Navigation**:
- Submit Ticket → Screen 11 (Profile) with confirmation
- Cancel → Previous page

---

## SCSS Styling Guidelines

### Color Palette (Odoo Theme)
```scss
// Primary Colors
$o-color-palette: (
    'o-color-1': #714B67,  // Odoo Purple (Primary)
    'o-color-2': #0180A2,  // Teal (Secondary)
    'o-color-3': #E4E4E4,  // Light Gray
    'o-color-4': #FFFFFF,  // White
    'o-color-5': #282828,  // Dark Gray
);

// Semantic Colors
$o-success: #28A745;
$o-info: #17A2B8;
$o-warning: #FFC107;
$o-danger: #DC3545;
```

### Key Custom Styles
```scss
// mockup2.scss

// Stepper customization
.mockup2-stepper {
    .step-circle {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;

        &.active {
            background-color: $o-brand-primary;
            color: white;
        }

        &.completed {
            background-color: $o-success;
            color: white;
        }
    }
}

// Order status badges
.order-badge {
    &.in_transit { @extend .bg-info; }
    &.delivered { @extend .bg-success; }
    &.cancelled { @extend .bg-danger; }
    &.pending { @extend .bg-warning; }
}

// Card hover effects
.truck-card {
    transition: transform 0.2s, box-shadow 0.2s;

    &:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
}
```

---

## Controller Structure

```python
# controllers/main.py
from odoo import http
from odoo.http import request

class LogspaceMockup2(http.Controller):

    def _get_mock_context(self, extra=None):
        """Base context helper with is_mockup flag"""
        ctx = {'is_mockup': True}
        if extra:
            ctx.update(extra)
        return ctx

    # ========== PUBLIC FLOW ==========

    @http.route(['/mockup2/search'], type='http', auth='public', website=True)
    def mockup_search(self, **kwargs):
        trucks = [...]  # Dummy data
        return request.render('appness_logspace_mockup2.mockup2_search_page', 
                              self._get_mock_context({'trucks': trucks}))

    @http.route(['/mockup2/vendor/<int:vendor_id>'], type='http', auth='public', website=True)
    def mockup_vendor(self, vendor_id, **kwargs):
        vendor = {...}  # Dummy based on vendor_id
        return request.render('appness_logspace_mockup2.mockup2_vendor_page',
                              self._get_mock_context({'vendor': vendor}))

    # ... (all 17 routes)
```

---

## Template Inheritance Strategy

### Base Layout
```xml
<!-- Base layout extending website.layout -->
<template id="mockup2_layout" name="Mockup2 Layout">
    <t t-call="website.layout">
        <div id="wrap" class="oe_structure oe_empty">
            <!-- Breadcrumb -->
            <nav aria-label="breadcrumb" class="bg-light py-2">
                <div class="container">
                    <ol class="breadcrumb mb-0">
                        <li class="breadcrumb-item"><a href="/mockup2/search">Home</a></li>
                        <!-- Dynamic breadcrumb items per page -->
                    </ol>
                </div>
            </nav>
            <t t-out="0"/>
        </div>
    </t>
</template>
```

### Portal Layout
```xml
<!-- Portal-style layout with sidebar -->
<template id="mockup2_portal_layout" name="Mockup2 Portal Layout">
    <t t-call="appness_logspace_mockup2.mockup2_layout">
        <div class="container py-4">
            <div class="row">
                <div class="col-lg-3">
                    <!-- Sidebar Navigation -->
                    <div class="list-group shadow-sm">
                        <a href="/mockup2/my/profile" 
                           t-attf-class="list-group-item #{page == 'profile' and 'active'}">
                            <i class="fa fa-user me-2"></i> Profile
                        </a>
                        <!-- ... other links -->
                    </div>
                </div>
                <div class="col-lg-9">
                    <t t-out="0"/>
                </div>
            </div>
        </div>
    </t>
</template>
```

---

## JavaScript (Minimal)

```javascript
// static/src/js/mockup2.js
publicWidget.registry.Mockup2Interactions = publicWidget.Widget.extend({
    selector: '.o_mockup2_wrapper',
    events: {
        'click .js_grid_view': '_onGridViewClick',
        'click .js_list_view': '_onListViewClick',
        'change .js_addon_check': '_onAddonChange',
        'click .js_star_rating': '_onStarClick',
    },

    _onGridViewClick: function() {
        $('.results-container').removeClass('list-view').addClass('grid-view');
    },

    _onListViewClick: function() {
        $('.results-container').removeClass('grid-view').addClass('list-view');
    },

    _onAddonChange: function(ev) {
        // Update total price based on selected addons
        this._calculateTotal();
    },

    _calculateTotal: function() {
        let total = this.basePrice || 150;
        $('.js_addon_check:checked').each(function() {
            total += parseFloat($(this).data('price'));
        });
        $('.js_total_price').text('$' + total);
    },

    _onStarClick: function(ev) {
        const rating = $(ev.currentTarget).data('rating');
        $('.js_star_rating').removeClass('fa-star').addClass('fa-star-o');
        $('.js_star_rating').each(function(index) {
            if (index < rating) {
                $(this).removeClass('fa-star-o').addClass('fa-star');
            }
        });
        $('input[name="rating"]').val(rating);
    },
});
```

---

## Dependencies

```python
# __manifest__.py
{
    'name': 'Logspace Mockup 2',
    'version': '1.0',
    'category': 'Website',
    'depends': [
        'website',           # Base website
        'portal',            # Portal patterns
        'web',               # Login templates
        'auth_signup',       # Signup templates
        # Note: Optional dependency on appness_logspace for shared assets
    ],
    'data': [
        'views/mockup_layout_templates.xml',
        'views/mockup_search_templates.xml',
        'views/mockup_vendor_templates.xml',
        'views/mockup_booking_templates.xml',
        'views/mockup_auth_templates.xml',
        'views/mockup_portal_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'appness_logspace_mockup2/static/src/scss/mockup2.scss',
            'appness_logspace_mockup2/static/src/js/mockup2.js',
        ],
    },
}
```

---

## Reuse Strategy Summary

| Component | Reuse From | Modifications |
|-----------|------------|---------------|
| Login Page | `web.login_layout` | Add phone-based UI |
| Signup Page | `auth_signup.signup` | Add logistics-specific fields |
| Portal Sidebar | `portal.portal_layout` | Custom navigation items |
| Form Styling | `web._form.scss` | None - use as-is |
| Cards | `portal.o_portal_docs` | Adjust colors |
| Stepper | Custom | Inspired by Odoo wizards |
| Breadcrumbs | `o_portal_submenu` | Standard usage |

---

## Implementation Phases

### Phase 1: Foundation
1. Create module structure
2. Base layout templates
3. SCSS variables and base styles

### Phase 2: Public Flow (Screens 1-8)
1. Search + Results (Screen 1-2)
2. Vendor page (Screen 3)
3. Booking stepper (Screens 4-8)

### Phase 3: Auth Flow (Screens 9-10)
1. Login (reuse Odoo login patterns)
2. Signup (reuse signup patterns)

### Phase 4: Portal Flow (Screens 11-17)
1. Portal layout with sidebar
2. Profile, Orders, Tracking
3. Notifications, Rating, Refund, Ticket

### Phase 5: Polish
1. Navigation links between all screens
2. Mobile responsiveness
3. Final styling review

---

## Questions for Review

1. **Authentication**: Should login/signup reuse the existing `appness_logspace_portal` OTP flow or create simplified mockup versions?

2. **Portal Sidebar**: Should we copy the existing portal sidebar style or use the lighter mockup2 version?

3. **Data Complexity**: How detailed should the dummy data be? Simple static values or more realistic nested structures?

4. **Mobile**: Should mobile have a different layout (e.g., bottom nav instead of sidebar) or stick to responsive only?

5. **Tracking Map**: Static placeholder image, CSS-based map visualization, or embedded map iframe?

---

## Next Steps After Approval

1. Create module folder structure
2. Implement controllers with all dummy data
3. Create templates following Odoo standards
4. Add SCSS with Odoo theme colors
5. Test navigation flow between all 17 screens
6. Mobile responsiveness testing

Please review this plan and let me know:
- Any changes to the flow or screen features?
- Preference on reusing vs. creating new templates?
- Any specific design elements you'd like added or removed?

Once approved, I'll proceed with implementation.
