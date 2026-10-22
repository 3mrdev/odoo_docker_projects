from odoo import models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_maintenance_equipment(self):
        """Resolve the maintenance equipment linked to this move, if any.

        Chain: stock move -> picking -> approval request -> maintenance
        request -> equipment. Returns an empty recordset when any link is
        missing so the accounting falls back to the core behavior.
        """
        self.ensure_one()
        return self.picking_id.approval_request_id.maintenance_request_id.equipment_id

    def _get_maintenance_expense_account(self):
        """Maintenance expense account driving the debit line, if any."""
        self.ensure_one()
        equipment = self._get_maintenance_equipment()
        return equipment and equipment._get_maintenance_expense_account()

    def _is_maintenance_consumption(self):
        """Whether this move consumes material for a maintenance request."""
        self.ensure_one()
        return (
            self.location_dest_id.usage == 'inventory'
            and bool(self._get_maintenance_equipment())
        )

    def _should_create_account_move(self):
        # Core only generates the stock journal entry when one of the
        # locations carries a valuation account. Maintenance consumptions
        # debit the equipment's maintenance expense account instead, so the
        # entry is generated even on plain loss locations.
        if self._is_maintenance_consumption() and self._get_maintenance_expense_account():
            return (
                self.product_id.is_storable
                and self.is_valued
                and self.product_id.valuation == 'real_time'
            )
        return super()._should_create_account_move()

    def _get_maintenance_analytic_distribution(self):
        """Equipment analytic distribution carried on the valuation entry."""
        self.ensure_one()
        if not self._is_maintenance_consumption():
            return None
        equipment = self._get_maintenance_equipment()
        return equipment.analytic_distribution or None

    def _get_account_move_line_vals(self):
        debit_acc = self._get_maintenance_expense_account()
        distribution = self._get_maintenance_analytic_distribution()
        if (
            debit_acc
            and not self.location_dest_id.valuation_account_id
            and not self.location_id.valuation_account_id
        ):
            # Plain loss location: core would crash building the debit line
            # from the (empty) destination valuation account. Build both
            # lines here, debiting the equipment's maintenance expense
            # account and crediting the stock valuation interim account.
            credit_acc = self.product_id._get_product_accounts()['stock_valuation']
            return [{
                'account_id': credit_acc.id,
                'name': self.reference,
                'debit': 0,
                'credit': self.value,
                'product_id': self.product_id.id,
            }, {
                'account_id': debit_acc.id,
                'name': self.reference,
                'debit': self.value,
                'credit': 0,
                'product_id': self.product_id.id,
                'analytic_distribution': distribution,
            }]
        vals = super()._get_account_move_line_vals()
        if self.location_dest_id.usage == 'inventory' and debit_acc:
            # vals[1] is the debit line: the equipment's expense account
            # takes precedence over the loss location's valuation account.
            vals[1]['account_id'] = debit_acc.id
            vals[1]['analytic_distribution'] = distribution
        return vals
