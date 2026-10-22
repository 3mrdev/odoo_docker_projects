from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = ['maintenance.equipment', 'analytic.mixin']

    expense_account_id = fields.Many2one(
        'account.account', string='Maintenance Expense Account',
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable'))]",
        help="Expense account used to debit the value of the spare parts consumed "
             "for this equipment when they are sent to an inventory loss location. "
             "Falls back to the equipment category's account if not set.")

    def _get_maintenance_expense_account(self):
        self.ensure_one()
        return self.expense_account_id or self.category_id.expense_account_id


class MaintenanceEquipmentCategory(models.Model):
    _inherit = 'maintenance.equipment.category'

    expense_account_id = fields.Many2one(
        'account.account', string='Maintenance Expense Account',
        check_company=True,
        domain="[('account_type', 'not in', ('asset_receivable', 'liability_payable'))]",
        help="Fallback expense account used for the spare parts consumed by the "
             "equipments of this category when they don't define their own account.")
