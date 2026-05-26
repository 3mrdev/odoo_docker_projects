# Subscription Penalty Inline Module

This module adds penalty charges as invoice lines for late subscription payments.

## Features
- Adds penalty lines directly to subscription invoices (not separate invoices)
- Yearly recurring penalties for unpaid invoices  
- Configurable penalty amount and product
- Automatic daily cron job
- Smart button showing penalty count on invoices
- Visual highlighting of penalty lines (yellow)

## How It Works
1. Subscription invoice becomes late (past deferred_end_date)
2. First penalty line is added to the invoice
3. Each year the invoice remains unpaid, another penalty line is added
4. When invoice is paid, no more penalties are added

## Configuration
Settings > Sales > Subscriptions > Late Payment Penalties (Inline)
- Set penalty amount
- Select penalty product (must be a service product)

## Testing
Manual cron execution in developer mode:
```python
env['sale.order']._cron_add_penalty_lines()
```
