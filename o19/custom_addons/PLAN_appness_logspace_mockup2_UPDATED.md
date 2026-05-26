# Logspace Mockup2 - Updated Implementation Plan

## Overview
A new Odoo 19 module `appness_logspace_mockup2` that creates an interconnected mockup website with:
- **17 Customer screens** (Screens 1-17) - for truck booking/customer journey
- **6 Provider screens** (Screens 18-23) - for service provider/driver registration
- Total: **23 interconnected mockup screens**

## Key Design Principles (Per Your Requirements)
1. **NO OTP** - Build simple designs for customer signup/login (no OTP complexity)
2. **Odoo Portal Sidebar** - Use existing style from Odoo portal parameters for consistent branding
3. **No Map for Tracking** - Order info like Sales module portal + status timeline (like Screen 13)
4. **Mobile Responsive** - All designs must be mobile responsive
5. **Standard Odoo Navbar** - Use website navbar, insert links via menu model
6. **Maximum Reuse** - Inherit from Odoo templates (`portal.portal_layout`, `web.login_layout`, etc.)
7. **Provider Button** - Add "Become a Provider" button in website navbar

---

## Module Structure

```
appness_logspace_mockup2/
├── __init__.py
├── __manifest__.py
├── controllers/
│   └── main.py              # 23 routes (17 customer + 6 provider)
├── views/
│   ├── mockup_layout_templates.xml      # Base layout
│   ├── mockup_search_templates.xml      # Screens 1-2: Search/List
│   ├── mockup_vendor_templates.xml      # Screen 3: Vendor/Item
│   ├── mockup_booking_templates.xml     # Screens 4-8: Booking stepper
│   ├── mockup_auth_templates.xml      # Screens 9-10: Login/Signup
│   ├── mockup_portal_templates.xml      # Screens 11-17: Customer Portal
│   └── mockup_provider_templates.xml    # Screens 18-23: Provider Registration
├── data/
│   └── website_menu.xml       # Navbar menu items (including Provider button)
├── static/
│   ├── src/
│   │   ├── scss/
│   │   │   └── mockup2.scss   # Odoo theme colors, minimal custom styles
│   │   └── js/
│   │       └── mockup2.js     # Minimal interactivity
│   └── description/
│       └── icon.png
```

---

## Screen-by-Screen Implementation

### CUSTOMER JOURNEY (17 Screens)

#### Screen 1 & 2: Search & List/Grid View
**Route**: `/mockup2/search`
**Template**: `mockup2_search_page`

**Features**:
- Hero search section with service type, pickup/dropoff, date
- Grid/List toggle for results
- 6 dummy truck listings with images, ratings, prices

**Navigation**:
- Search button → Results display (same page)
- Truck card → Screen 3 (Vendor)
- Login link → Screen 9

**Reuse**: `website.layout` with standard cards

---

#### Screen 3: Vendor/Item Page
**Route**: `/mockup2/vendor/<int:vendor_id>`
**Template**: `mockup2_vendor_page`

**Features**:
- Large vehicle image gallery (placeholder)
- Vendor info (name, rating, completed trips)
- Price breakdown
- "Book Now" CTA

**Navigation**: Book Now → Screen 4 (Add-ons)

---

#### Screens 4-8: Booking Stepper (5 screens)
**Routes**:
- `/mockup2/addons` (Screen 4)
- `/mockup2/details` (Screen 5)
- `/mockup2/checkout` (Screen 6)
- `/mockup2/payment` (Screen 7)
- `/mockup2/done` (Screen 8)

**Templates**: `mockup2_addons_page`, `mockup2_details_page`, etc.

**Stepper Component**: Reusable template showing progress (1→2→3→4)

**Features per step**:
- Step 1 (Addons): Checkbox list with prices
- Step 2 (Details): Item description, weight, dimensions form
- Step 3 (Checkout): Full order summary, editable sections
- Step 4 (Payment): Payment methods (Card, Apple Pay, Wallet)
- Step 5 (Done): Success message, order number, tracking link

**Navigation**: Next/Back buttons between steps

---

#### Screens 9-10: Customer Auth (Simplified)
**Routes**:
- `/mockup2/login` (Screen 9)
- `/mockup2/signup` (Screen 10)

**Templates**: `mockup2_login_page`, `mockup2_signup_page`

**Features** (Simple designs, no OTP):
- **Login**: Email/Phone + Password, "Remember me", Forgot password link
- **Signup**: Full name, Phone, Email, Password + Confirm, Terms checkbox

**Reuse**: Inherit from `web.login_layout` and `auth_signup.signup`

**Navigation**:
- Login → Screen 11 (Profile) or Screen 12 (Orders)
- Signup → Screen 11 (Profile completion)

---

#### Screens 11-17: Customer Portal
All use **Odoo Portal Sidebar** layout (`portal.portal_layout`)

| Screen | Route | Template | Features |
|--------|-------|----------|----------|
| 11 | `/mockup2/my/profile` | `mockup2_profile_page` | Personal info, password change |
| 12 | `/mockup2/my/orders` | `mockup2_orders_page` | Tabbed list (Active/Completed/Cancelled) |
| 13 | `/mockup2/my/orders/track` | `mockup2_track_page` | Order timeline (NO MAP), status steps |
| 14 | `/mockup2/my/notifications` | `mockup2_notifications_page` | Notification list with icons |
| 15 | `/mockup2/rate` | `mockup2_rate_page` | Star rating, categories, comment |
| 16 | `/mockup2/refund` | `mockup2_refund_page` | Reason dropdown, details textarea |
| 17 | `/mockup2/ticket` | `mockup2_ticket_page` | Helpdesk form |

**Navigation**: Sidebar links between all portal screens

**Reuse**: `portal.portal_layout`, `portal.portal_my_home` cards

---

### PROVIDER JOURNEY (6 Screens)

Provider screens accessible via **"Become a Provider"** button in website navbar (added via `website.menu` record).

| Screen | Route | Template | Step | Features |
|--------|-------|----------|------|----------|
| 18 | `/mockup2/provider/register/1` | `mockup2_provider_step1` | Step 1 | Basic info (Name, Phone, Email) |
| 19 | `/mockup2/provider/register/2` | `mockup2_provider_step2` | Step 2 | Business details (Company name, Type) |
| 20 | `/mockup2/provider/register/3` | `mockup2_provider_step3` | Step 3 | Vehicle info (Type, Capacity, License) |
| 21 | `/mockup2/provider/register/4` | `mockup2_provider_step4` | Step 4 | Documents upload (ID, License, Insurance) |
| 22 | `/mockup2/provider/register/5` | `mockup2_provider_step5` | Step 5 | Service areas (Regions, Cities) |
| 23 | `/mockup2/provider/register/6` | `mockup2_provider_step6` | Step 6 | Review & Submit |

**Stepper**: Reuse same stepper component from customer booking (1→2→3→4→5→6)

**Features**:
- Each step has form fields relevant to that step
- Back/Next navigation
- Step 6 shows summary of all entered data
- Submit shows success message with "Pending Approval" status

**Reuse**: `website.layout` (public) with custom stepper

---

## Template Inheritance Strategy

### Base Layout
```xml
<!-- All pages extend this -->
<template id="mockup2_layout" name="Mockup2 Base">
    <t t-call="website.layout">
        <!-- Breadcrumb optional -->
        <div id="wrap" class="oe_structure">
            <t t-out="0"/>
        </div>
    </t>
</template>
```

### Portal Layout (Customer Screens 11-17)
```xml
<!-- Inherit from Odoo portal -->
<template id="mockup2_portal_layout" name="Mockup2 Portal">
    <t t-call="portal.portal_layout">
        <div class="container py-4">
            <div class="row">
                <!-- Sidebar: Reuse Odoo's portal sidebar -->
                <div class="col-lg-3">
                    <div class="o_portal_sidebar">
                        <t t-call="mockup2_portal_menu"/>
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

### Auth Layout (Screens 9-10)
```xml
<!-- Reuse Odoo login/signup -->
<template id="mockup2_login_page" name="Mockup2 Login">
    <t t-call="web.login_layout">
        <!-- Custom form fields -->
        <form class="oe_login_form">
            <!-- Email/Phone -->
            <!-- Password -->
            <!-- Remember me -->
            <!-- Submit -->
        </form>
    </t>
</template>
```

### Stepper Component (Reusable)
```xml
<template id="mockup2_stepper" name="Stepper">
    <div class="row mb-4">
        <div class="col-12">
            <div class="progress" style="height: 4px;">
                <div class="progress-bar bg-primary" 
                     t-attf-style="width: #{(current_step - 1) / (total_steps - 1) * 100}%"/>
            </div>
            <div class="d-flex justify-content-between mt-2">
                <t t-foreach="steps" t-as="step">
                    <div t-attf-class="step #{step_index + 1 == current_step and 'active' or ''}
                                        #{step_index + 1 &lt; current_step and 'completed' or ''}">
                        <span t-esc="step"/>
                    </div>
                </t>
            </div>
        </div>
    </div>
</template>
```

---

## SCSS Styling (Minimal & Odoo-Compliant)

```scss
// static/src/scss/mockup2.scss

// Use Odoo's existing variables where possible
// Only add minimal custom styles

// Stepper customization
.mockup2-stepper {
    .step {
        text-align: center;
        color: $text-muted;
        
        &.active {
            color: $o-brand-primary;
            font-weight: bold;
        }
        
        &.completed {
            color: $success;
        }
    }
}

// Order status badges
.order-status {
    &.in_transit { @extend .bg-info; }
    &.delivered { @extend .bg-success; }
    &.cancelled { @extend .bg-danger; }
    &.pending { @extend .bg-warning; }
}

// Provider registration specific
.provider-stepper {
    // Same as customer stepper
}

// Mobile responsive adjustments
@media (max-width: 768px) {
    .o_portal_sidebar {
        // Mobile-friendly sidebar (collapsible)
    }
}
```

---

## Website Navbar Integration

### Menu Item (data/website_menu.xml)
```xml
<record id="menu_provider_signup" model="website.menu">
    <field name="name">Become a Provider</field>
    <field name="url">/mockup2/provider/register/1</field>
    <field name="parent_id" ref="website.main_menu"/>
    <field name="sequence">50</field>
</record>
```

---

## Controller Structure (simplified)

```python
# controllers/main.py
from odoo import http
from odoo.http import request

class LogspaceMockup2(http.Controller):

    def _get_mock_context(self, extra=None):
        ctx = {'is_mockup': True}
        if extra:
            ctx.update(extra)
        return ctx

    # ========== CUSTOMER SCREENS ==========
    
    @http.route(['/mockup2/search'], type='http', auth='public', website=True)
    def mockup_search(self, **kwargs):
        trucks = [...]  # Dummy data
        return request.render('appness_logspace_mockup2.mockup2_search_page',
                              self._get_mock_context({'trucks': trucks}))

    @http.route(['/mockup2/vendor/<int:vendor_id>'], ...)
    def mockup_vendor(self, vendor_id, **kwargs):
        vendor = {...}  # Dummy based on ID
        return request.render('appness_logspace_mockup2.mockup2_vendor_page',
                              self._get_mock_context({'vendor': vendor}))

    # ... (booking stepper routes 4-8)

    @http.route(['/mockup2/login'], ...)
    def mockup_login(self, **kwargs):
        return request.render('appness_logspace_mockup2.mockup2_login_page')

    @http.route(['/mockup2/signup'], ...)
    def mockup_signup(self, **kwargs):
        return request.render('appness_logspace_mockup2.mockup2_signup_page')

    # Portal routes (11-17)
    @http.route(['/mockup2/my/profile'], ...)
    def mockup_profile(self, **kwargs):
        return request.render('appness_logspace_mockup2.mockup2_profile_page')

    # ... (other portal routes)

    # ========== PROVIDER SCREENS ==========
    
    @http.route(['/mockup2/provider/register/<int:step>'], ...)
    def mockup_provider_register(self, step, **kwargs):
        templates = {
            1: 'appness_logspace_mockup2.mockup2_provider_step1',
            2: 'appness_logspace_mockup2.mockup2_provider_step2',
            # ... etc
        }
        return request.render(templates.get(step, templates[1]))
```

---

## Dummy Data Examples

### Trucks (Screen 1-2)
```python
trucks = [
    {
        'id': 1,
        'name': 'Flatbed Truck 3T',
        'vendor': 'ABC Logistics',
        'price': 150.0,
        'rating': 4.5,
        'reviews': 128,
        'features': ['GPS Tracking', 'Insurance Included']
    },
    # ... 5 more
]
```

### Order Timeline (Screen 13 - NO MAP)
```python
timeline = [
    {'status': 'confirmed', 'label': 'Order Confirmed', 
     'time': 'Jan 15, 09:00', 'done': True, 'current': False},
    {'status': 'picked', 'label': 'Item Picked Up', 
     'time': 'Jan 15, 10:30', 'done': True, 'current': False},
    {'status': 'in_transit', 'label': 'In Transit', 
     'time': 'Jan 15, 11:00', 'done': True, 'current': True},
    {'status': 'delivered', 'label': 'Delivered', 
     'time': 'Expected 14:00', 'done': False, 'current': False},
]
```

---

## Reuse Summary

| Component | Reuse From | Notes |
|-----------|------------|-------|
| Login Page | `web.login_layout` | Simplified form |
| Signup Page | `auth_signup.signup` | Simplified form |
| Portal Layout | `portal.portal_layout` | With sidebar |
| Portal Sidebar | Odoo's `o_portal_sidebar` | Consistent branding |
| Form Styling | Bootstrap 5 / Odoo's `_form.scss` | No custom needed |
| Cards | `o_portal_docs` | Portal cards |
| Stepper | Custom (inspired by Odoo wizards) | Minimal custom |
| Navbar | `website.menu` records | Add provider button |

---

## Mobile Responsive Approach

- Use Bootstrap 5 classes (already in Odoo)
- Sidebar collapses to hamburger menu on mobile
- Forms stack vertically on small screens
- Tables convert to cards on mobile (if needed)
- Touch-friendly buttons and inputs

---

## Implementation Phases

### Phase 1: Foundation
- Module structure, manifest
- Base layout templates
- Website menu (including Provider button)
- Minimal SCSS

### Phase 2: Customer Public Flow
- Screens 1-3: Search, List, Vendor
- Screens 4-8: Booking stepper
- Screens 9-10: Simplified auth

### Phase 3: Customer Portal
- Portal layout with sidebar
- Screens 11-17

### Phase 4: Provider Flow
- Screens 18-23: Provider registration stepper

### Phase 5: Polish
- Mobile responsiveness testing
- Navigation links verification
- Final styling review

---

## Files to Create

```
appness_logspace_mockup2/
├── __init__.py
├── __manifest__.py
├── data/
│   └── website_menu.xml
├── controllers/
│   ├── __init__.py
│   └── main.py
├── views/
│   ├── mockup_layout_templates.xml
│   ├── mockup_search_templates.xml
│   ├── mockup_vendor_templates.xml
│   ├── mockup_booking_templates.xml
│   ├── mockup_auth_templates.xml
│   ├── mockup_portal_templates.xml
│   └── mockup_provider_templates.xml
├── static/
│   └── src/
│       ├── scss/mockup2.scss
│       └── js/mockup2.js
└── static/description/icon.png
```

---

Ready for implementation upon approval.
