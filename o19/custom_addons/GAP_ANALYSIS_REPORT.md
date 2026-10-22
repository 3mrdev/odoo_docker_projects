# Prompt

We are working in this module "custom_addons/appness_logspace" please understand everything related to the updates before doing them .. i want you to make surgical updates only .. don't do anything else .. you are a odoo expert so act acordingly

1: in this .docx file "custom_addons/appness_logspace/TECH SHORT (LogSpace SRS v1.2 ).docx" we have the full project requirements i want you to read all of it understand the requirements along with the pictures and read the module and understand it .. make a full report about what has already been implemented and what wasent implemented and needs more work focus on the customizations part .. anything that is already in odoo standard we don't wabt to focus on right now 


# LogSpace SRS v1.2 — Full Implementation Gap Analysis Report

## Context
This report compares the LogSpace SRS v1.2 requirements (including all wireframe diagrams) against the current `appness_logspace` module codebase to identify what is implemented, what is partially done, and what still needs work. **Focus is on customizations only** — standard Odoo features are excluded unless custom logic has been built on top.

---

## ✅ FULLY IMPLEMENTED (Customizations Complete)

### 1. Customer Booking Flow (Screens 1-8)
| Screen | Status | Details |
|--------|--------|---------|
| Screen 1: Pickup/Dropoff Search | ✅ | Zone hierarchy, date/time selection, vehicle type filtering |
| Screen 2: Search Results | ✅ | Vendor cards with price breakdown, pagination |
| Screen 3: Vendor Details | ✅ | Vehicle info, provider details, special instructions |
| Screen 4: Add-ons Selection | ✅ | Provider-specific addons with pricing |
| Screen 5: Item Details | ✅ | Goods notes, pickup/dropoff contacts, document upload |
| Screen 6: Checkout Review | ✅ | Order summary, tax calculation, guest email/phone |
| Screen 7: Payment | ✅ | Odoo payment provider integration |
| Screen 8: Booking Complete | ✅ | Confirmation with pickup verification code |

### 2. Customer Profile (Screens 9-19)
| Screen | Status | Details |
|--------|--------|---------|
| Screen 9/10: Login/Signup | ✅ | Simple auth (no OTP) |
| My Account Dashboard | ✅ | Dashboard cards with order counts |
| Profile Edit | ✅ | Name, email, phone, address, timezone |
| Orders List | ✅ | Status tabs (active/completed/cancelled) |
| Order Tracking | ✅ | Full timeline with verification codes |
| Rate Driver | ✅ | 1-5 stars + comment |
| Refund Request | ✅ | 7 reason types, attachment upload |
| Support Tickets | ✅ | Create/list/view tickets per order |
| Notifications | ✅ | List with mark-as-read |
| Saved Addresses | ✅ | Via partner address book |

### 3. Provider Registration (5-Step Flow)
| Step | Status | Details |
|------|--------|---------|
| Step 1: Basic Info | ✅ | Logo, company name, CR number, tax ID, years in business |
| Step 2: Admin Contacts | ✅ | Contact roles, number of users |
| Step 3: Fleet Summary | ✅ | Vehicle types, fleet count, capacity |
| Step 4: Documents | ✅ | Upload CR, insurance, other docs |
| Step 5: Review & Submit | ✅ | Summary review, submit for approval |

### 4. Provider Dashboard
| Feature | Status | Details |
|---------|--------|---------|
| Vehicle Management | ✅ | List/form with plate, capacity, driver, docs |
| Pricing by Zone | ✅ | Price matrix with zone pair × vehicle type |
| Order Management | ✅ | Assigned orders with status updates |
| Fleet Summary | ✅ | Fleet counts by vehicle type |
| Availability Toggle | ✅ | Active/inactive per vehicle |

### 5. Master Data Models
| Model | Status | Details |
|-------|--------|---------|
| `logspace.zone` | ✅ | 36 zones, hierarchy, coordinates |
| `logspace.zone.distance` | ✅ | Symmetric, hierarchical fallback |
| `logspace.vehicle.type` | ✅ | 6 types with images, categories |
| `logspace.addon` | ✅ | 7 addons with pricing |
| `logspace.time.slot` | ✅ | Morning/afternoon/evening |

### 6. Admin Backend
| Feature | Status | Details |
|---------|--------|---------|
| Provider Approval Workflow | ✅ | Submit→Approve/Reject→Suspend |
| Zone Setup Wizard | ✅ | Bulk price matrix generation |
| Order Management | ✅ | 11-state workflow |
| Menu Structure | ✅ | Logspace root + submenus |
| Security Rules | ✅ | 30+ record rules, 67 access rights |
| Demo Data | ✅ | 12 providers, 54 vehicles |

### 7. Core Customizations
| Feature | Status | Details |
|---------|--------|---------|
| Order Verification Codes | ✅ | 4-digit pickup + dropoff codes |
| Order Timeline | ✅ | 13 event types with estimated times |
| Email Templates | ✅ | 5 templates (booking, driver, approval, application, delivery) |
| Refund Workflow | ✅ | 6-state workflow with reason types |
| Helpdesk Integration | ✅ | Tickets linked to orders |
| Payment Integration | ✅ | `payment.transaction` extension |
| Guest Booking | ✅ | Auto account creation after payment |
| International Phone Widget | ✅ | `intl-tel-input` library |

---

## ⚠️ PARTIALLY IMPLEMENTED / NEEDS WORK

### 1. Add-on Execution Time (FR-05) — **MISSING**
**Requirement:** Each add-on has an execution time field — "before pickup" or "after drop-off". This is visible in the SRS wireframe Screen 4 where addons are grouped.
**Current state:** `logspace.addon` model has `price_type` but **NO field for execution timing** (before_pickup / after_dropoff).
**What's needed:**
- Add `execution_time` selection field to `logspace.addon` (before_pickup / after_dropoff / both)
- Update add-on views (form, list)
- Update frontend add-on selection to group/display by execution time
- Update `logspace.provider.vehicle.type.addon` if needed

### 2. Booking Fee (Non-Refundable) (FR-11) — **MISSING**
**Requirement (from SRS Screen 7):** Payment method selection shows a "Booking Fee" line item. The SRS states: "Fixed booking fee (not refundable) required for confirmation of future orders."
**Current state:** No dedicated booking fee field or logic. Payment is handled as a single transaction. The checkout shows tax calculation but no separate booking fee.
**What's needed:**
- Add booking fee configuration (ir.config_parameter or model field)
- Add booking fee line to checkout summary
- Split payment logic: booking fee at confirmation + remaining before order starts
- Mark booking fee as non-refundable in refund calculations

### 3. Refund Percentage Rules (FR-12) — **MISSING**
**Requirement (from SRS Screen 12):**
- **100% refund** at booking stage (before pickup started)
- **50% refund** at started stage (after pickup started)
- **0% refund** at pickup stage (after pickup completed)

**Current state:** `logspace.refund` model exists with manual approval workflow, but **no automatic percentage calculation** based on order state. The refund amount is manually entered.
**What's needed:**
- Add auto-calculation of refund amount based on `logspace_state` of the order
- Pre-fill refund amount on form creation based on current order state
- Show refund eligibility percentage to customer before submission
- Possibly add a config model for refund percentages per state

### 4. Provider Earnings & Reporting (FR-16) — **MISSING**
**Requirement (from SRS Provider Dashboard):**
- Earnings summary card showing completed order revenue
- Withdrawal history
- Payout processing by management

**Current state:** NO earnings model, NO earnings views, NO payout tracking. The `sale.order` has provider assignment and amounts but no provider-facing financial summary.
**What's needed:**
- Create `logspace.provider.earning` or computed fields on `res.partner`
- Provider dashboard: total earnings, pending payout, payout history
- Admin view for processing provider payouts
- Earnings = sum of completed orders × (1 - platform_fee_percentage) - penalties

### 5. Penalty System (FR-13) — **MISSING**
**Requirement:** System applies provider penalties for no-show and delay based on predefined business rules.
**Current state:** Completely missing — no model, no views, no automation.
**What's needed:**
- Create `logspace.penalty` model (provider, order, type, amount, reason, state)
- Admin UI for viewing/applying penalties
- Integration with provider earnings (deduct penalties from payouts)
- Possibly auto-detect penalties based on order timeline vs expected times

### 6. Failed Payment Continuation Link (FR-11) — **MISSING**
**Requirement:** "If payment fails, order remains saved. Continuation link sent by email."
**Current state:** Payment failure updates `payment_status` to 'failed' but **no email template or logic** for sending continuation links.
**What's needed:**
- Create email template for payment continuation
- Add logic to send email when payment fails (override `_post_process`)
- Generate unique continuation URL pointing back to checkout
- Handle guest users receiving the link

### 7. Automated Document Workflow (System Workflow) — **MISSING**
**Requirement (from SRS):**
1. Auto-create **Draft SO** on search/booking → ✅ (done in checkout)
2. Auto-create **Invoice** for customer on payment → ❌ NOT done
3. Auto-create **Purchase Order** to vendor on payment → ❌ NOT done
4. Auto-create **Vendor Bill** on order completion → ❌ NOT done

**Current state:** SO is created during checkout. But the downstream document chain (Invoice + PO → Bill) is not automated.
**What's needed:**
- Override payment confirmation to auto-create customer invoice + vendor PO
- Override order completion (`action_complete_order`) to auto-create vendor bill
- Link these documents together via references

### 8. Zone Activation by Radius (FR-07) — **PARTIAL**
**Requirement:** "Provider activates zones by selecting operation zone + km radius → zones within 100km activated automatically"
**Current state:** The zone setup wizard exists for bulk price matrix generation (select zones + vehicle types → generate prices). But there's no explicit "zone activation" by km radius feature.
**What's needed:**
- Add zone activation logic to provider workflow (separate from or extending the wizard)
- Auto-activate zones within 100km of selected operation zone using distance matrix
- Visual indicator of activated zones in provider dashboard

### 9. Provider Registration — Insurance Details (FR-06) — **PARTIAL**
**Requirement (from SRS Step 1):** Registration includes insurance details (insurance provider, policy number, expiry date, coverage amount).
**Current state:** Provider registration has basic info (logo, name, CR number, tax ID, years) and document uploads, but specific **structured insurance fields** are not on `res.partner`. Insurance docs can be uploaded as files, but not structured data.
**What's needed:**
- Add insurance fields to provider partner: `insurance_provider`, `insurance_policy_number`, `insurance_expiry_date`, `insurance_coverage_amount`
- Update registration form step 1 to include these fields

### 10. SRS Screen 2: Price Breakdown Display — **NEEDS REVIEW**
**Requirement (from SRS Screen 2 wireframe):** Shows detailed price breakdown per vendor:
- Base fare
- Add-ons
- Distance fare
- VAT
- Booking fee
- Total

**Current state:** Search results show vendor cards with pricing. Need to verify if all breakdown elements (especially booking fee) are displayed.

---

## ❌ NOT IMPLEMENTED AT ALL

| # | Feature | SRS Reference |
|---|---------|---------------|
| 1 | Penalty model + logic | FR-13 |
| 2 | Provider earnings dashboard | FR-16 |
| 3 | Provider payout/withdrawal management | FR-16 |
| 4 | Auto Invoice creation on payment | System Workflow |
| 5 | Auto PO creation to vendor on payment | System Workflow |
| 6 | Auto Vendor Bill on order completion | System Workflow |
| 7 | Booking fee line item + logic | FR-11 |
| 8 | Automatic refund % calculation | FR-12 |
| 9 | Payment continuation email | FR-11 |
| 10 | Add-on execution time classification | FR-05 |
| 11 | Zone activation by km radius | FR-07 |

---

## 📋 PRIORITY SUMMARY

### HIGH PRIORITY (Core business logic gaps)
| # | Feature | Impact |
|---|---------|--------|
| 1 | Auto Invoice + PO + Bill creation chain | Financial workflow broken without this |
| 2 | Refund percentage auto-calculation | Customer-facing feature, SRS screen 12 |
| 3 | Booking fee (non-refundable) | Payment flow incomplete |
| 4 | Provider earnings dashboard | Provider retention, SRS dashboard |
| 5 | Penalty system | Admin enforcement tool |
| 6 | Failed payment continuation email | Revenue recovery |

### MEDIUM PRIORITY (Enhancement features)
| # | Feature | Impact |
|---|---------|--------|
| 7 | Add-on execution time classification | UX improvement for booking |
| 8 | Zone activation by radius | Provider convenience |
| 9 | Insurance structured fields | Data completeness |

### LOW PRIORITY (Nice-to-have)
| # | Feature | Impact |
|---|---------|--------|
| 10 | Price breakdown review (Screen 2) | UI polish |

---

## 📂 FILES LIKELY TO MODIFY

### For each missing feature:

**1. Auto Invoice + PO + Bill:**
- `models/sale_order.py` — override payment confirm + order complete
- `models/logspace_payment.py` — hook into `_post_process`
- Possibly `data/logspace_email_templates.xml` — add notification templates

**2. Refund % auto-calculation:**
- `models/logspace_refund.py` — add `default_amount` computation from order state
- `views/logspace_refund_views.xml` — show eligibility info
- `controllers/portal.py` — update refund creation route

**3. Booking fee:**
- `models/sale_order.py` — add `booking_fee` field
- `controllers/common.py` — update `_calculate_booking_total`
- `controllers/booking.py` — show booking fee in checkout
- `data/` — add config parameter for booking fee amount
- `views/logspace_booking_templates.xml` — update checkout template

**4. Provider earnings:**
- New model or computed fields on `res.partner`
- New views for provider dashboard
- Update `controllers/provider.py`

**5. Penalty system:**
- New model `logspace.penalty`
- New views, menu items, security rules
- Update `__init__.py`, `__manifest__.py`
- Integration with provider earnings

**6. Payment continuation email:**
- `data/logspace_email_templates.xml` — new template
- `models/logspace_payment.py` — send email on failure

**7. Add-on execution time:**
- `models/logspace_addon.py` — add field
- `views/logspace_addon_views.xml`
- `data/data_addons.xml` — set default values
- Frontend template for add-on selection

---

## ✅ VERIFICATION PLAN

After implementing each feature:
1. Run existing tests: `python -m pytest tests/`
2. Verify booking flow end-to-end (search → checkout → payment → tracking)
3. Verify provider flow (registration → approval → pricing → orders)
4. Verify admin flow (approval → zone setup → penalty → payout)
5. Check frontend templates render correctly with new fields
6. Verify email templates send correctly
