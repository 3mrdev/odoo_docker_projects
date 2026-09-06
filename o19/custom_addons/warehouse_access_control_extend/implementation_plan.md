# Extend Warehouse Access Control to Orderpoints & Routes

## Background

The existing `sttl_warehouse_access_control` module restricts warehouse-related models (locations, quants, moves, pickings, etc.) based on `allowed_location_ids` configured per user. It uses a **boolean-flag bypass pattern**: each model gets a boolean field (always `False`), and the record rule domain uses `['|', (location_check), ('boolean_flag', '=', user.check_location)]`. When the user has **no** allowed locations, `check_location` is `False`, the flag is also `False`, so the `|` evaluates to `True` → the user sees all records. When the user **has** allowed locations, `check_location` is `True`, the flag is `False`, so only the location check matters.

We need to extend this to two additional models in a **new module** `warehouse_access_control_extend`.

---

## Resolved Decisions (from review)

### 1. `_compute_allowed_location_ids` override with `sudo()` ✅

Approved. We will override this method to use `sudo()` for the warehouse/location search to prevent the `stock.location` record rule from breaking the computation, then intersect with the user's allowed locations.

### 2. `allowed_location_ids` caching concern — ADDRESSED

> *User concern:* "is the `allowed_location_ids` field user-based? Because if it's not, this will make a problem for manager users who can see more fields, and this field is computed and won't be recomputed for each user's allowed locations because it doesn't depend on the user — it's only dependent on the warehouse."

**This is safe.** Here's why:

- The `allowed_location_ids` field on `stock.warehouse.orderpoint` is a **non-stored** computed field (`store=False` by default). This means it is **never written to the database** — it is computed fresh on every read request.
- Odoo's field cache is **per-Environment**, and the `Environment` is keyed by `(cursor, user_id, context)`. Different users → different `Environment` → different cache → the field computes independently for each user.
- Our override uses `self.env.user.allowed_location_ids`, which returns different results per user.
- The `@api.depends('warehouse_id')` decorator only controls **cache invalidation** (recompute when `warehouse_id` changes), not cross-user sharing.

**Result:** User A (restricted) sees filtered locations; User B (manager) sees all locations — correctly, without interference.

### 3. Routes — No user field needed ✅

The user confirmed: **no new field on `res.users`** for routes. The `stock.route` record rule will dynamically filter routes based on whether their `rule_ids` contain `location_src_id` or `location_dest_id` matching the user's `allowed_location_ids`. This also automatically filters the `route_id` dropdown on the orderpoint form.

---

## Proposed Changes

### Module Structure

```
custom_addons/warehouse_access_control_extend/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── stock_warehouse_orderpoint.py
│   └── stock_route.py
└── security/
    └── access_control_rules.xml
```

---

### Module Manifest & Init

#### [NEW] [\_\_manifest\_\_.py](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/__manifest__.py)

```python
{
    'name': 'Warehouse Access Control - Extend',
    'version': '18.0.1.0',
    'depends': ['sttl_warehouse_access_control'],
    'description': 'Extends warehouse access control to replenishments and routes.',
    'data': [
        'security/access_control_rules.xml',
    ],
    'category': 'Warehouse',
    'installable': True,
    'application': False,
}
```

#### [NEW] [\_\_init\_\_.py](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/__init__.py)

```python
from . import models
```

#### [NEW] [models/\_\_init\_\_.py](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/models/__init__.py)

```python
from . import stock_warehouse_orderpoint
from . import stock_route
```

---

### Model: `stock.warehouse.orderpoint`

#### [NEW] [stock_warehouse_orderpoint.py](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/models/stock_warehouse_orderpoint.py)

Two changes:

1. **Add `boolean_orderpoint_flag`** — the bypass flag field (always `False`, matching the base module pattern).

2. **Override `_compute_allowed_location_ids`** — use `sudo()` for warehouse/location search to avoid the `stock.location` record rule breaking the computation. Then intersect with `self.env.user.allowed_location_ids` when the user has restrictions.

```python
from odoo import api, fields, models
from odoo.osv import expression


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    boolean_orderpoint_flag = fields.Boolean(
        string='Orderpoint Flag', default=False)

    @api.depends('warehouse_id')
    def _compute_allowed_location_ids(self):
        """Override to use sudo() for the warehouse/location search to avoid
        conflicts with the stock.location record rule, then intersect with
        the user's allowed locations.
        
        Note: This is a non-stored computed field. Odoo's cache is keyed per
        Environment (cr, uid, context), so different users get independent
        computation results — no cross-user cache contamination.
        """
        user = self.env.user
        user_allowed_locations = user.allowed_location_ids
        has_restrictions = bool(user_allowed_locations)

        for orderpoint in self:
            # Use sudo to get the full location set for the warehouse
            # (bypassing the stock.location record rule)
            loc_domain = [('usage', 'in', ('internal', 'view'))]
            other_warehouses = self.env['stock.warehouse'].sudo().search(
                [('id', '!=', orderpoint.warehouse_id.id)])
            for view_location_id in other_warehouses.mapped('view_location_id'):
                loc_domain = expression.AND([
                    loc_domain,
                    ['!', ('id', 'child_of', view_location_id.id)]
                ])
                loc_domain = expression.AND([
                    loc_domain,
                    ['|', ('company_id', '=', False),
                          ('company_id', '=', orderpoint.company_id.id)]
                ])
            all_locations = self.env['stock.location'].sudo().search(loc_domain)

            # If user has location restrictions, intersect with their allowed set
            if has_restrictions:
                orderpoint.allowed_location_ids = (
                    all_locations & user_allowed_locations)
            else:
                # No restrictions → show all valid locations for the warehouse
                orderpoint.allowed_location_ids = all_locations
```

---

### Model: `stock.route`

#### [NEW] [stock_route.py](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/models/stock_route.py)

Add the bypass flag field only. No computed field override needed — the record rule handles filtering via `rule_ids` traversal.

```python
from odoo import fields, models


class StockRoute(models.Model):
    _inherit = 'stock.route'

    boolean_route_flag = fields.Boolean(
        string='Route Flag', default=False)
```

---

### Security: Record Rules

#### [NEW] [access_control_rules.xml](file:///Users/firebits/odoo/docker/o18/custom_addons/warehouse_access_control_extend/security/access_control_rules.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>

    <!-- ============================================================ -->
    <!-- INTERNAL USER RULES (base.group_user)                        -->
    <!-- ============================================================ -->

    <!-- stock.warehouse.orderpoint: internal user sees only orderpoints
         whose location_id is in their allowed locations.
         Bypass: if user has no allowed locations, sees all. -->
    <record id="rule_orderpoint_allowed_user" model="ir.rule">
        <field name="name">Orderpoint Allowed User</field>
        <field name="model_id" ref="stock.model_stock_warehouse_orderpoint"/>
        <field name="domain_force">
            ['|',
                ('location_id', 'in', user.allowed_location_ids.ids),
                ('boolean_orderpoint_flag', '=', user.check_location)]
        </field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <!-- stock.route: internal user sees only routes whose rules
         have source OR destination in their allowed locations.
         Bypass: if user has no allowed locations, sees all. -->
    <record id="rule_route_allowed_user" model="ir.rule">
        <field name="name">Route Allowed User</field>
        <field name="model_id" ref="stock.model_stock_route"/>
        <field name="domain_force">
            ['|', '|',
                ('rule_ids.location_src_id', 'in', user.allowed_location_ids.ids),
                ('rule_ids.location_dest_id', 'in', user.allowed_location_ids.ids),
                ('boolean_route_flag', '=', user.check_location)]
        </field>
        <field name="groups" eval="[(4, ref('base.group_user'))]"/>
    </record>

    <!-- ============================================================ -->
    <!-- MANAGER RULES (group_warehouse_manager)                      -->
    <!-- ============================================================ -->

    <!-- stock.warehouse.orderpoint: manager sees all -->
    <record id="rule_orderpoint_manager" model="ir.rule">
        <field name="name">Orderpoint Manager</field>
        <field name="model_id" ref="stock.model_stock_warehouse_orderpoint"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="groups" eval="[(4, ref('sttl_warehouse_access_control.group_warehouse_manager'))]"/>
    </record>

    <!-- stock.route: manager sees all -->
    <record id="rule_route_manager" model="ir.rule">
        <field name="name">Route Manager</field>
        <field name="model_id" ref="stock.model_stock_route"/>
        <field name="domain_force">[(1, '=', 1)]</field>
        <field name="groups" eval="[(4, ref('sttl_warehouse_access_control.group_warehouse_manager'))]"/>
    </record>

</odoo>
```

---

## How Record Rules Combine (no conflicts)

| Rule Layer | Domain | Scope |
|---|---|---|
| **Odoo global** (stock_security.xml) | `[('company_id', 'in', company_ids)]` | No group → applies to ALL users |
| **Our internal user** rule | `['|', (location_check), (bypass)]` | `base.group_user` |
| **Our manager** rule | `[(1, '=', 1)]` | `group_warehouse_manager` |

- **Global rules** (no group) are AND-ed with group-specific rules.
- **Group rules** for the same model are OR-ed across groups the user belongs to.
- A manager has both `base.group_user` AND `group_warehouse_manager`, so their rules OR → `(location_filter) OR (1=1)` → sees everything ✅
- An internal user only has `base.group_user` → gets the location filter ✅
- Both are AND-ed with the company rule → always company-scoped ✅

---

## Verification Plan

### Automated Tests
```bash
# Install the module
docker compose exec web odoo -d odoo -i warehouse_access_control_extend --stop-after-init

# Verify module updates cleanly
docker compose exec web odoo -d odoo -u warehouse_access_control_extend --stop-after-init
```

### Manual Verification
1. **Internal user with allowed locations**:
   - Set allowed locations on the user
   - Verify Replenishments shows only orderpoints for those locations
   - Verify the `route_id` dropdown on orderpoints shows only matching routes
   - Verify Configuration → Routes shows only routes with matching rule locations

2. **Internal user without allowed locations**:
   - Clear allowed locations → verify ALL orderpoints and routes are visible

3. **Warehouse Manager**:
   - Assign the Warehouse Manager group
   - Verify ALL orderpoints and routes are visible regardless of allowed locations

4. **Orderpoint form — location dropdown**:
   - As a restricted user, edit an orderpoint
   - Verify the location dropdown shows only the user's allowed locations (intersected with warehouse-valid locations)
