# Update Plan: Outstanding Account & Payment Method (Hybrid Approach)

## Overview
Hybrid approach combining transparency/user control with correct accounting:
- **Warnings**: Show alerts when payment methods lack outstanding accounts
- **User Control**: Boolean field to force journal entry creation
- **Correct Accounting**: Uses journal default account (not transfer account via force_payment_move)

---

## Problem 1: Outstanding Account Not Set → No Journal Entries

### Root Cause
In Odoo 19, `_generate_journal_entry()` filters:
```python
need_move = self.filtered(lambda p: not p.move_id and p.outstanding_account_id)
```
If `outstanding_account_id` is empty (payment method has no account), no move created.

### Solution: Hybrid Approach (Warnings + User-Controlled Fix)

#### Step 1: Computed Warning Fields
Show warnings in form view when payment methods lack outstanding accounts:

```python
# Computed warning flags
source_payment_method_warning = fields.Boolean(
    compute='_compute_payment_warnings',
    string='Source Payment Method Warning'
)
destination_payment_method_warning = fields.Boolean(
    compute='_compute_payment_warnings',
    string='Destination Payment Method Warning'
)

# User checkbox to force fix
force_journal_entries = fields.Boolean(
    string='Force Journal Entries',
    help='Check this if payment methods do not have outstanding accounts configured. '
         'The system will use the journal default accounts to create journal entries.'
)

@api.depends('payment_method_line_source_id', 'payment_method_line_destination_id')
def _compute_payment_warnings(self):
    for record in self:
        # Source warning
        if record.payment_method_line_source_id:
            record.source_payment_method_warning = not bool(
                record.payment_method_line_source_id.payment_account_id
            )
        else:
            # Check default method for source journal
            default_method = self.env['account.payment.method.line'].search([
                ('journal_id', '=', record.journal_source.id),
                ('payment_type', '=', 'outbound'),
            ], limit=1)
            record.source_payment_method_warning = default_method and not bool(
                default_method.payment_account_id
            )
        
        # Destination warning (similar logic)
        if record.payment_method_line_destination_id:
            record.destination_payment_method_warning = not bool(
                record.payment_method_line_destination_id.payment_account_id
            )
        else:
            default_method = self.env['account.payment.method.line'].search([
                ('journal_id', '=', record.journal_destination.id),
                ('payment_type', '=', 'inbound'),
            ], limit=1)
            record.destination_payment_method_warning = default_method and not bool(
                default_method.payment_account_id
            )
```

#### Step 2: Warning Banners in View
Show visual warnings in form view:

```xml
<!-- Warning banners above the sheet -->
<div class="alert alert-warning" role="alert" 
     invisible="approval_type != 'liquidity_transfer' or not source_payment_method_warning">
    <i class="fa fa-exclamation-triangle"/>
    Source journal's payment method has no outstanding account configured. 
    Check "Force Journal Entries" below to use the journal default account.
</div>

<div class="alert alert-warning" role="alert" 
     invisible="approval_type != 'liquidity_transfer' or not destination_payment_method_warning">
    <i class="fa fa-exclamation-triangle"/>
    Destination journal's payment method has no outstanding account configured. 
    Check "Force Journal Entries" below to use the journal default account.
</div>
```

#### Step 3: Force Checkbox in View
```xml
<field name="force_journal_entries" 
    invisible="approval_type != 'liquidity_transfer' or (not source_payment_method_warning and not destination_payment_method_warning)"
    readonly="request_status not in ['new','pending']" />
```

#### Step 4: Modified Payment Creation Logic
Check `force_journal_entries` boolean when determining outstanding account:

```python
def _get_outstanding_account_for_payment(self, payment_method_line, journal, force_fix):
    """
    Determine outstanding account for payment.
    
    If payment method has account: use it (standard behavior)
    If no account and force_fix=True: use journal default
    If no account and force_fix=False: return None (let Odoo handle, may not create move)
    """
    if payment_method_line and payment_method_line.payment_account_id:
        # Payment method has outstanding account - standard behavior
        return None
    elif force_fix:
        # No outstanding account but user wants to force - use journal default
        return journal.default_account_id
    else:
        # No outstanding account, no force - let Odoo handle (may fail to create move)
        return None

def _action_create_payments_liquidity_transfer(self):
    # ... validation code ...
    
    # Determine payment method lines
    payment_method_source = self.payment_method_line_source_id or self.env['account.payment.method.line'].search([
        ('journal_id', '=', self.journal_source.id),
        ('payment_type', '=', 'outbound'),
    ], limit=1)
    
    payment_method_destination = self.payment_method_line_destination_id or self.env['account.payment.method.line'].search([
        ('journal_id', '=', self.journal_destination.id),
        ('payment_type', '=', 'inbound'),
    ], limit=1)
    
    # Get outstanding accounts based on warnings and force flag
    outstanding_account_source = self._get_outstanding_account_for_payment(
        payment_method_source, self.journal_source, self.force_journal_entries
    )
    outstanding_account_destination = self._get_outstanding_account_for_payment(
        payment_method_destination, self.journal_destination, self.force_journal_entries
    )
    
    # Create source payment
    payment_source_vals = {
        'approval_request_id': self.id,
        'payment_type': 'outbound',
        'journal_id': self.journal_source.id,
        'payment_method_line_id': payment_method_source.id,
        'amount': self.amount,
        'date': self.date,
        'memo': memo,
        'destination_account_id': liquidity_transfer_account.id,
    }
    if outstanding_account_source:
        payment_source_vals['outstanding_account_id'] = outstanding_account_source.id
    payment_source = self.env['account.payment'].create(payment_source_vals)
    
    # Create destination payment (similar pattern)
    payment_destination_vals = {
        'approval_request_id': self.id,
        'payment_type': 'inbound',
        'journal_id': self.journal_destination.id,
        'payment_method_line_id': payment_method_destination.id,
        'amount': self.amount,
        'date': self.date,
        'memo': memo,
        'destination_account_id': liquidity_transfer_account.id,
    }
    if outstanding_account_destination:
        payment_destination_vals['outstanding_account_id'] = outstanding_account_destination.id
    payment_destination = self.env['account.payment'].create(payment_destination_vals)
    
    # ... rest of code ...
```

---

## Problem 2: Payment Method Selection

### Fields
```python
# Source journal payment method
payment_method_line_source_id = fields.Many2one(
    'account.payment.method.line',
    string='Source Payment Method',
    domain="[('journal_id', '=', journal_source), ('payment_type', '=', 'outbound')]",
    check_company=True,
)

# Destination journal payment method
payment_method_line_destination_id = fields.Many2one(
    'account.payment.method.line',
    string='Destination Payment Method',
    domain="[('journal_id', '=', journal_destination), ('payment_type', '=', 'inbound')]",
    check_company=True,
)
```

### Onchanges
```python
@api.onchange('journal_source')
def _onchange_journal_source(self):
    if self.journal_source and self.approval_type == 'liquidity_transfer':
        method_line = self.env['account.payment.method.line'].search([
            ('journal_id', '=', self.journal_source.id),
            ('payment_type', '=', 'outbound'),
        ], limit=1)
        self.payment_method_line_source_id = method_line
        # Recompute warnings
        self._compute_payment_warnings()

@api.onchange('journal_destination')
def _onchange_journal_destination(self):
    if self.journal_destination and self.approval_type == 'liquidity_transfer':
        method_line = self.env['account.payment.method.line'].search([
            ('journal_id', '=', self.journal_destination.id),
            ('payment_type', '=', 'inbound'),
        ], limit=1)
        self.payment_method_line_destination_id = method_line
        # Recompute warnings
        self._compute_payment_warnings()

@api.onchange('payment_method_line_source_id', 'payment_method_line_destination_id')
def _onchange_payment_method_lines(self):
    # Recompute warnings when payment methods change
    self._compute_payment_warnings()
```

---

## Implementation Summary

### Files to Modify

#### 1. `models/approval_request.py`
**Add Fields:**
- `payment_method_line_source_id`
- `payment_method_line_destination_id`
- `source_payment_method_warning` (computed)
- `destination_payment_method_warning` (computed)
- `force_journal_entries`

**Add Methods:**
- `_compute_payment_warnings()`
- `_get_outstanding_account_for_payment()`
- `_onchange_journal_source()`
- `_onchange_journal_destination()`
- `_onchange_payment_method_lines()`

**Modify:**
- `_action_create_payments_liquidity_transfer()` to use new logic

#### 2. `views/approval_request_views.xml`
**Add:**
- Warning banners (alert divs) above form
- `payment_method_line_source_id` field after journal_source
- `payment_method_line_destination_id` field after journal_destination
- `force_journal_entries` checkbox (conditionally visible)

#### 3. `models/account_payment.py` (already created)
No changes needed - `approval_request_id` field already exists

---

## Benefits of Hybrid Approach

1. **Transparency**: User sees exactly when there might be an issue
2. **User Control**: User decides whether to force the fix
3. **Correct Accounting**: Uses journal default account (appropriate for internal transfers)
4. **Educational**: Users learn about payment method configuration
5. **Flexible**: Works whether or not payment methods are configured

---

## Verification Checklist

- [ ] Create approval without outstanding accounts → see warnings
- [ ] Warnings show correct message for source/destination
- [ ] Force checkbox appears only when needed
- [ ] Check force checkbox → journal entries created with default accounts
- [ ] Uncheck force → use standard behavior
- [ ] Journal dashboard shows correct balances
- [ ] Change payment method → warnings update dynamically
- [ ] Payment receipts print correctly
