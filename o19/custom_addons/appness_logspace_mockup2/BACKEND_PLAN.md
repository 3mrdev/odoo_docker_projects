# Logspace Backend Module Plan (Complete)

## Overview
This document outlines the complete backend implementation plan for the Logspace module, including both admin/provider management AND all customer-facing features (ratings, refunds, tickets, notifications, addons). Following Odoo standards and reusing existing models where possible.

## Module Structure
```
appness_logspace_mockup2/
├── models/
│   ├── __init__.py
│   ├── logspace_provider.py          # Provider with approval workflow
│   ├── logspace_vehicle.py           # Vehicles (trucks)
│   ├── logspace_service_area.py      # Zone/service area mappings
│   ├── logspace_price_matrix.py      # Pricing by zone + vehicle type
│   ├── logspace_addon.py             # Booking add-ons (loading assistance, etc.)
│   ├── logspace_zone.py              # Master data: zones
│   ├── logspace_vehicle_type.py      # Master data: vehicle types
│   ├── logspace_rating.py            # Customer ratings/reviews
│   ├── logspace_refund.py            # Refund requests
│   ├── logspace_ticket.py            # Support tickets
│   ├── logspace_notification.py      # User notifications
│   └── logspace_order.py              # Extends sales.order for Logspace
├── views/
│   ├── logspace_provider_views.xml
│   ├── logspace_vehicle_views.xml
│   ├── logspace_price_matrix_views.xml
│   ├── logspace_addon_views.xml
│   ├── logspace_zone_views.xml
│   ├── logspace_vehicle_type_views.xml
│   ├── logspace_rating_views.xml
│   ├── logspace_refund_views.xml
│   ├── logspace_ticket_views.xml
│   ├── logspace_notification_views.xml
│   ├── logspace_order_views.xml
│   └── logspace_menus.xml
├── security/
│   └── ir.model.access.csv
└── data/
    └── logspace_demo_data.xml
```

---

## 1. MASTER DATA MODELS

### 1.1 logspace.zone
**Fields:**
- `name` (Char, required) - e.g., "Downtown", "Airport Zone"
- `code` (Char, required, unique) - uppercase, e.g., "DOWNTOWN"
- `city` (Char)
- `region` (Char) - state/province
- `country_id` (Many2one → res.country)
- `active` (Boolean) - default True

### 1.2 logspace.vehicle.type
**Fields:**
- `name` (Char, required) - "Flatbed 3T"
- `code` (Char, required, unique) - "flatbed_3t"
- `icon` (Char) - FontAwesome class, e.g., "fa-truck"
- `default_capacity_kg` (Integer)
- `default_capacity_cbm` (Float)
- `category` (Selection): light, medium, heavy, special
- `description` (Text)
- `active` (Boolean) - default True

### 1.3 logspace.addon (Service Add-ons)
**Fields:**
- `name` (Char, required) - e.g., "Loading Assistance"
- `code` (Char, unique) - "loading_assist"
- `description` (Text) - shown in vendor page
- `price` (Float) - base price
- `price_type` (Selection): fixed, per_km, per_hour, per_item
- `is_active` (Boolean)
- `icon` (Char) - FontAwesome class
- `sequence` (Integer) - for ordering

---

## 2. PROVIDER MANAGEMENT MODELS

### 2.1 logspace.provider (Main Provider Model)
**Inherits:** `res.partner` (using delegation inheritance or related partner)

**Fields:**
- `partner_id` (Many2one → res.partner) - linked contact
- `state` (Selection, required): draft, pending, approved, rejected, suspended
- `tax_id` (Char) - Tax/EIN registration
- `website` (Char)
- `years_experience` (Selection): less_1, 1_2, 3_5, 5_10, more_10
- `is_verified` (Boolean)
- `approval_date` (Date)
- `rejection_reason` (Text)
- `suspension_reason` (Text)

**Computed Fields:**
- `vehicle_count` (Integer) - count of related vehicles
- `active_order_count` (Integer) - from sales.order
- `rating` (Float) - average customer rating (from logspace.rating)
- `review_count` (Integer) - count of ratings

### 2.2 logspace.vehicle (Provider Fleet)
**Fields:**
- `provider_id` (Many2one → logspace.provider, required, ondelete=cascade)
- `name` (Char) - e.g., "Truck #1"
- `vehicle_type_id` (Many2one → logspace.vehicle.type, required)
- `plate_number` (Char, required) - unique across system
- `is_active` (Boolean) - default True
- `registration_doc_id` (Many2one → ir.attachment)
- `insurance_doc_id` (Many2one → ir.attachment)

### 2.3 logspace.service.area (Provider Coverage)
**Fields:**
- `provider_id` (Many2one → logspace.provider, required)
- `region` (Char) - region/state
- `city` (Char, required) - specific city/area
- `zone_id` (Many2one → logspace.zone) - linked zone
- `coverage_radius_km` (Integer) - 10 to 500 km
- `service_days` (Selection): weekdays, weekends, all_days, by_request
- `is_active` (Boolean)

### 2.4 logspace.price.matrix (Pricing Configuration)
**Fields:**
- `provider_id` (Many2one → logspace.provider, required)
- `vehicle_type_id` (Many2one → logspace.vehicle.type, required)
- `zone_from_id` (Many2one → logspace.zone, required)
- `zone_to_id` (Many2one → logspace.zone, required)
- `distance_km` (Float) - distance between zones
- `provider_price` (Float) - what provider charges
- `platform_fee` (Float) - Logspace commission (default from config)
- `customer_price` (Float, computed, stored) - provider_price + platform_fee
- `is_active` (Boolean)
- `currency_id` (Many2one → res.currency, default company)

---

## 3. ORDER & BOOKING MODELS

### 3.1 logspace.order (Extends sales.order)
**Inherits/Extends:** `sale.order`

**New Fields:**
- `logspace_provider_id` (Many2one → logspace.provider)
- `logspace_vehicle_id` (Many2one → logspace.vehicle)
- `driver_id` (Many2one → res.partner) - driver contact
- `driver_phone` (Char)
- `pickup_address` (Text)
- `pickup_zone_id` (Many2one → logspace.zone)
- `dropoff_address` (Text)
- `dropoff_zone_id` (Many2one → logspace.zone)
- `scheduled_date` (Datetime) - pickup date/time
- `delivery_date` (Datetime) - actual delivery
- `estimated_distance_km` (Float)
- `item_description` (Text)
- `estimated_weight_kg` (Integer)
- `item_quantity` (Integer)
- `item_length_cm` (Integer)
- `item_width_cm` (Integer)
- `item_height_cm` (Integer)
- `special_instructions` (Text)
- `logspace_state` (Selection): pending, confirmed, driver_assigned, in_transit, delivered, cancelled
- `tracking_timeline` (One2many → logspace.order.timeline)
- `addons_ids` (Many2many → logspace.addon) - selected add-ons

**Methods:**
- `action_confirm_booking()` - moves to confirmed
- `action_assign_driver()` - assigns driver
- `action_start_transit()` - moves to in_transit
- `action_mark_delivered()` - moves to delivered

### 3.2 logspace.order.timeline (Order Tracking Events)
**Fields:**
- `order_id` (Many2one → sale.order, required)
- `event_type` (Selection): booked, confirmed, driver_assigned, pickup, in_transit, delivered, cancelled
- `event_time` (Datetime, default now)
- `description` (Char)
- `location` (Char)
- `is_current` (Boolean) - current status
- `sequence` (Integer) - for ordering

---

## 4. CUSTOMER SUPPORT & INTERACTION MODELS

### 4.1 logspace.rating (Customer Reviews)
**Fields:**
- `order_id` (Many2one → sale.order, required)
- `provider_id` (Many2one → logspace.provider, related)
- `customer_id` (Many2one → res.partner) - customer who rated
- `overall_rating` (Integer, required) - 1-5 stars
- `timeliness_rating` (Selection): excellent, good, average, poor
- `driver_behavior_rating` (Selection): excellent, good, average, poor
- `vehicle_condition_rating` (Selection): excellent, good, average, poor
- `comments` (Text)
- `is_published` (Boolean) - show on provider profile
- `create_date` (Datetime) - rating date

**Computed:**
- `average_rating` (Float) - computed from the 4 ratings

### 4.2 logspace.refund (Refund Requests)
**Fields:**
- `name` (Char, required) - "REF-0001" sequence
- `order_id` (Many2one → sale.order, required)
- `customer_id` (Many2one → res.partner, related)
- `provider_id` (Many2one → logspace.provider, related)
- `amount` (Float) - refund amount
- `currency_id` (Many2one → res.currency)
- `reason` (Selection, required):
  - service_not_provided
  - late_delivery
  - damaged_goods
  - wrong_vehicle
  - overcharged
  - cancelled_by_provider
  - other
- `details` (Text, required)
- `attachments` (Many2many → ir.attachment)
- `state` (Selection): draft, submitted, under_review, approved, rejected, processed
- `submitted_date` (Datetime)
- `processed_date` (Datetime)
- `processed_by_id` (Many2one → res.users)
- `rejection_reason` (Text)
- `refund_method` (Selection): original_payment, credit, bank_transfer

### 4.3 logspace.ticket (Support Tickets)
**Fields:**
- `name` (Char, required) - "TICK-0001" sequence
- `category` (Selection, required):
  - booking_issue
  - payment_problem
  - driver_complaint
  - vehicle_issue
  - refund_request
  - technical_support
  - general_inquiry
- `subject` (Char, required)
- `description` (Text, required)
- `order_id` (Many2one → sale.order) - optional linked order
- `customer_id` (Many2one → res.partner) - who submitted
- `provider_id` (Many2one → logspace.provider) - if provider-related
- `attachments` (Many2many → ir.attachment)
- `state` (Selection): new, assigned, in_progress, waiting_customer, resolved, closed, escalated
- `priority` (Selection): low, medium, high, urgent
- `assigned_to_id` (Many2one → res.users)
- `create_date` (Datetime)
- `resolved_date` (Datetime)
- `resolution_notes` (Text)

**One2many:**
- `message_ids` (using Odoo's mail.thread for replies)

### 4.4 logspace.notification (User Notifications)
**Fields:**
- `user_id` (Many2one → res.users, required) - recipient
- `partner_id` (Many2one → res.partner) - alternative recipient
- `type` (Selection): success, info, warning, error
- `title` (Char, required)
- `message` (Text, required)
- `is_read` (Boolean) - default False
- `read_date` (Datetime)
- `action_link` (Char) - URL to redirect when clicked
- `action_model` (Char) - e.g., "sale.order"
- `action_res_id` (Integer) - record ID
- `icon` (Char) - FontAwesome class
- `create_date` (Datetime)

**Methods:**
- `action_mark_read()`
- `action_mark_all_read()` (class method)

---

## 5. WORKFLOWS

### 5.1 Provider Approval Workflow
**States:** draft → pending → approved → rejected/suspended

**Transitions:**
- draft → pending: `action_submit()` button (provider)
- pending → approved: `action_approve()` (manager)
- pending → rejected: `action_reject(reason)` (manager)
- rejected → draft: `action_resubmit()` (provider)
- approved → suspended: `action_suspend(reason)` (manager)
- suspended → approved: `action_reactivate()` (manager)

### 5.2 Order Workflow (Logspace States)
**States:** pending → confirmed → driver_assigned → in_transit → delivered

**Events Timeline:**
1. Booked (create)
2. Confirmed (payment received)
3. Driver Assigned
4. Pickup (start)
5. In Transit
6. Delivered

### 5.3 Refund Workflow
**States:** draft → submitted → under_review → approved/rejected → processed

### 5.4 Ticket Workflow
**States:** new → assigned → in_progress → resolved → closed
              ↓ waiting_customer ↓ escalated

---

## 6. MENU STRUCTURE

```
Logspace (main menu)
├── Dashboard
│   └── My Dashboard (kanban with stats)
├── Providers
│   ├── Providers (kanban/tree/form with tabs: General, Vehicles, Service Areas, Documents, Pricing, Orders)
│   ├── Vehicles (tree by provider)
│   └── Service Areas (tree/matrix)
├── Sales
│   ├── Quotations (sale.order - draft)
│   ├── Orders (sale.order - confirmed/delivered)
│   ├── Customers (res.partner - customers)
│   └── Price Matrix (tree for pricing)
├── Customer Support
│   ├── Tickets (kanban/tree/form)
│   ├── Ratings & Reviews (tree/form)
│   └── Refund Requests (tree/form)
├── Services
│   ├── Add-ons (logspace.addon tree/form)
│   ├── Zones (logspace.zone tree/form)
│   └── Vehicle Types (logspace.vehicle.type tree/form)
├── Invoicing
│   ├── Invoices (account.move)
│   └── Payments (account.payment)
└── Configuration
    ├── Notification Templates
    └── Settings (res.config.settings)
```

---

## 7. VIEWS DESIGN

### 7.1 Provider Views
**Kanban:**
- Card with provider logo/name
- State badge (colored)
- Vehicle count, Rating stars
- Quick approve/reject buttons for pending

**List:**
- Name | State | License | Business Type | Vehicles | Rating | Phone | City

**Form (Tabs):**
- **General:** Basic info from res.partner + Business Type, Years Experience, License, Tax ID, Website
- **Vehicles:** One2many tree (editable inline) - Type, Plate, Capacity, Year, Active
- **Service Areas:** One2many tree - Region, City, Zone, Radius, Service Days
- **Documents:** Attachment widgets for License, Registration, Insurance, Profile Photo
- **Pricing:** Smart button → Price Matrix filtered by provider
- **Orders:** Smart button → Orders filtered by provider
- **Settings:** GPS, A/C, Operating Hours, Emergency, Max Distance

### 7.2 Order (Sales) Views
**List:**
- Order # | Date | Customer | Provider | Vehicle | Pickup | Status | Total

**Form (Additional Logspace Tab):**
- Pickup/Dropoff addresses with zone selection
- Provider & Driver assignment
- Item details (description, weight, quantity, dimensions)
- Special instructions
- Add-ons selected
- Timeline (readonly list of tracking events)

### 7.3 Rating Views
**List:**
- Order | Provider | Customer | Overall | Timeliness | Driver | Vehicle | Date | Published

**Form:**
- Order link
- All rating fields
- Comments
- Published checkbox

### 7.4 Refund Views
**Kanban:**
- By state columns
- Card with amount, reason, order, customer

**List:**
- Refund # | Order | Amount | Reason | State | Date

**Form:**
- All fields + State buttons (Approve/Reject/Process)
- Attachments list

### 7.5 Ticket Views
**Kanban:**
- By state columns
- Priority indicator
- Assigned user avatar

**List:**
- Ticket # | Category | Subject | Customer | Priority | State | Assigned To | Created

**Form:**
- Header: Category, Priority, Subject, State
- Customer info, Order link (if any)
- Description
- Attachments
- Thread for replies (mail.thread)
- Resolution notes (visible on resolved)

### 7.6 Notification Views
**List:**
- Type (icon) | Title | Message | User | Read Status | Date

**Form:**
- Basic fields, readonly

### 7.7 Master Data Views
**Addons Tree:**
- Name | Code | Price | Type | Active

**Zones Tree:**
- Code | Name | City | Region | Country | Active

**Vehicle Types Tree:**
- Icon | Name | Code | Category | Capacity | Active

---

## 8. SECURITY

**ir.model.access.csv:**

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_logspace_provider_user,Provider User,model_logspace_provider,base.group_user,1,0,0,0
access_logspace_provider_manager,Provider Manager,model_logspace_provider,base.group_system,1,1,1,1
access_logspace_vehicle_user,Vehicle User,model_logspace_vehicle,base.group_user,1,1,1,1
access_logspace_zone_manager,Zone Manager,model_logspace_zone,base.group_system,1,1,1,1
access_logspace_vehicle_type_manager,Vehicle Type Manager,model_logspace_vehicle_type,base.group_system,1,1,1,1
access_logspace_addon_manager,Addon Manager,model_logspace_addon,base.group_system,1,1,1,1
access_logspace_price_matrix_user,Price Matrix User,model_logspace_price_matrix,base.group_user,1,1,1,1
access_logspace_rating_user,Rating User,model_logspace_rating,base.group_user,1,0,1,0
access_logspace_rating_manager,Rating Manager,model_logspace_rating,base.group_system,1,1,1,1
access_logspace_refund_user,Refund User,model_logspace_refund,base.group_user,1,0,1,0
access_logspace_refund_manager,Refund Manager,model_logspace_refund,base.group_system,1,1,1,1
access_logspace_ticket_user,Ticket User,model_logspace_ticket,base.group_user,1,1,1,0
access_logspace_ticket_manager,Ticket Manager,model_logspace_ticket,base.group_system,1,1,1,1
access_logspace_notification_user,Notification User,model_logspace_notification,base.group_user,1,1,1,0
access_logspace_notification_manager,Notification Manager,model_logspace_notification,base.group_system,1,1,1,1
access_logspace_order_timeline_user,Order Timeline User,model_logspace_order_timeline,base.group_user,1,1,1,1
```

**Record Rules:**
- Notifications: Users see only their own notifications (`[('user_id', '=', user.id)]`)
- Ratings: All users can read published ratings, managers see all
- Refunds: Customers see own refunds, managers see all
- Tickets: Customers see own tickets, managers see all

---

## 9. DUMMY DATA

Create `data/logspace_demo_data.xml`:

**Vehicle Types (4):**
- Flatbed 3T, Flatbed 5T, Covered 3T, Van

**Zones (10):**
- Downtown, Airport Zone, Port Area, Industrial North, Business District, Residential East, Suburb West, Metro Central, Northern Hub, Coastal Area

**Addons (6):**
- Loading Assistance ($25), Unloading Assistance ($25), Express Delivery ($50), Extra Helper ($40), Furniture Protection ($15), GPS Tracking ($10)

**Providers (5):**
1. ABC Logistics (approved, 2 vehicles, 4.5 rating)
2. Fast Truck Co (approved, 1 vehicle, 4.8 rating)
3. City Movers (pending approval)
4. New Provider LLC (draft)
5. Suspended Trucking (suspended)

**Vehicles (8):**
- Distributed among approved providers

**Price Matrix (15 entries):**
- Covering popular zone pairs

**Demo Orders (5):**
1. Pending confirmation
2. Confirmed, driver assigned
3. In transit (active)
4. Delivered (completed)
5. Cancelled (for refund demo)

**Demo Ratings (3):**
- For completed orders

**Demo Refunds (1):**
- For cancelled order

**Demo Tickets (2):**
- One new, one resolved

**Demo Notifications (4):**
- Mix of read/unread for demo user

---

## 10. IMPLEMENTATION PHASES

### Phase 1: Master Data & Provider
1. Create all master data models (zone, vehicle.type, addon)
2. Create provider model with workflow
3. Create vehicle model
4. Create service.area model
5. Create price.matrix model
6. Security rules for above

### Phase 2: Order Management
1. Extend sale.order with logspace fields
2. Create order.timeline model
3. Views for order management

### Phase 3: Customer Support
1. Create rating model
2. Create refund model with workflow
3. Create ticket model with mail.thread
4. Create notification model
5. Security rules for above
6. All views for support models

### Phase 4: Demo Data & Polish
1. Create comprehensive demo data XML
2. Test all workflows
3. Add dashboard statistics

---

## 11. ODOO STANDARDS

- **Inheritance:** Use _inherit for extending sale.order
- **Naming:** logspace.* for all new models
- **Views:** logspace_view_*_tree/kanban/form
- **Sequences:** Use ir.sequence for REF-, TICK- prefixes
- **Mail Thread:** Inherit mail.thread for ticket messaging
- **Attachments:** Use ir.attachment with res_model/res_id
- **Translations:** All user-facing strings wrapped with _()
