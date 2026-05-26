# Implementation Plan: Liquidity Transfer via Account Payments

## Summary
This module has been updated to create `account.payment` records instead of direct `account.move` records for liquidity transfers. This ensures proper integration with Odoo's accounting dashboard and enables payment receipt printing.

## Changes Made

### 1. Base Module Updates (`approvals_custom_base`)
**File: `models/approval_request.py`**
- Added `payment_note` field (Text) - for payment memo/reference
- Added `payment_ids` field (One2many to `account.payment`) - tracks related payments
- Added `payments_count` computed field - for smart button display
- Added `action_open_payments()` method - opens related payments list
- Added `_compute_payments_count()` method - computes payment count

**File: `views/approval_request_views.xml`**
- Added smart button for "Payments" (appears when payments_count > 0)
- Maintains existing "Journal Entries" smart button

### 2. Account Payment Extension
**New File: `models/account_payment.py`**
- Added `approval_request_id` field (Many2one to `approval.request`)
- Enables reverse relation from payments back to approval requests

**Updated: `models/__init__.py`**
- Added import for new `account_payment` module

### 3. Liquidity Transfer Logic Update
**File: `models/approval_request.py`**
- Renamed `_action_create_journal_entries_liquidity_transfer()` to `_action_create_payments_liquidity_transfer()`
- Creates 2 payments:
  1. **Source Payment (Outbound)**: Sends money from source journal
  2. **Destination Payment (Inbound)**: Receives money to destination journal
- Both payments use the company `transfer_account_id` as the destination account
- Both payments include `payment_note` in the memo field
- After posting payments, their generated journal entries are linked back to the approval request

**Updated: `action_create_custom_by_type()`**
- Now calls `_action_create_payments_liquidity_transfer()`

### 4. Views Update
**File: `views/approval_request_views.xml`**
- Changed button label from "Create Journal Entries" to "Create Payments"
- Updated invisible condition to check `payments_count` instead of `journal_entries_count`
- Added `payment_note` field below amount field (visible only for liquidity_transfer type)

## How It Works

### Payment Creation Flow
1. User creates approval request with type = `liquidity_transfer`
2. User fills: amount, date, payment_note, source journal, destination journal
3. User approves the request
4. User clicks "Create Payments" button
5. System creates 2 payments:
   - Source payment (outbound from source journal)
   - Destination payment (inbound to destination journal)
6. Both payments are auto-posted, generating journal entries
7. The journal entries are linked to the approval request for tracking

### Account Configuration Required
- **Transfer Account**: Must be configured in Accounting Settings (company.transfer_account_id)
- **Journal Accounts**: Source and destination journals must have default accounts configured

## Technical Notes

### Destination Account Handling
The `destination_account_id` field has a UI domain restricting to receivable/payable accounts, but we bypass this by setting the value directly in Python code. The transfer account (asset_current type) is used as the counterparty account.

### Outstanding Account Computation
The `_get_outstanding_account()` method in Odoo's account module handles this automatically:
1. Checks journal's payment method outstanding accounts
2. Falls back to company's transfer account if needed

### Journal Entries Linking
After payments are posted, we link their generated journal entries back to the approval request via the `approval_request_id` field on `account.move`. This allows the existing "Journal Entries" smart button to display all related moves.

## Benefits

1. ✅ **Dashboard Balance Accuracy**: Journal dashboard properly counts payment-based transactions
2. ✅ **Payment Receipt Printing**: Users can print payment receipts (PDF) from payment forms
3. ✅ **Bank Reconciliation Ready**: Future bank statement reconciliation works seamlessly
4. ✅ **Proper Move Generation**: Payments respect journal outstanding account configuration
5. ✅ **Tracking**: Both payments and their journal entries are linked to the approval request

## Verification Checklist

After implementing, verify:
- [ ] Create approval request with type = liquidity_transfer
- [ ] Fill required fields: amount, date, source/destination journals
- [ ] Optional: Add payment_note for reference
- [ ] Approve the request
- [ ] Click "Create Payments" button
- [ ] Verify "Payments" smart button shows "2"
- [ ] Click payments button to view both payments (outbound + inbound)
- [ ] Verify "Journal Entries" smart button shows "2"
- [ ] Click journal entries button to view the generated moves
- [ ] Verify source journal dashboard reflects the transfer
- [ ] Verify destination journal dashboard reflects the transfer
- [ ] Verify transfer account is used as counterparty in both payments' moves
- [ ] Verify payment receipts can be printed from payment form
