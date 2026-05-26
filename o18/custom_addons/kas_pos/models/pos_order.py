from odoo import models, fields,api
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class PosOrder(models.Model):
    _inherit = 'pos.order'

    deleted_lines = fields.Boolean(string='Deleted Lines', default=False)

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        # Log the created line
        for line in res:
            body= "[POS_CREATE] "
            body += "User: " + self.env.user.name + " \n"
            body += "Cashier: " + line.order_id.cashier + " \n"
            body += "Product: " + line.product_id.name + " \n"
            body += "Quantity: " + str(line.qty) + " \n"
            body += "Price: " + str(line.price_unit) + " \n"
            body += "Total: " + str(line.price_subtotal) + " \n"
            line.order_id.message_post(
                body=body,
                message_type='notification'
            )
            _logger.info(body)
        return res

    def write(self, vals):
        for line in self:

            is_advanced_employee = False
            for advanced_employee_id in line.order_id.session_id.config_id.advanced_employee_ids:
                if advanced_employee_id.id == line.order_id.employee_id.id:
                    is_advanced_employee = True

            # if not is_advanced_employee:
            #     raise AccessError("You cannot update a product line please contact your manager")

            current_user = self.env.user
            # Log the updated of the line
            body = "[POS_UPDATE] Product: " + line.product_id.name + " \n"
            if current_user:
                body += "User: " + current_user.name + " \n"
            if line.order_id.cashier:
                body += "Cashier: " + line.order_id.cashier + " \n"
            if 'product_id' in vals and line.product_id:
                body += "Product: " + line.product_id.name + " -> " + str(vals['product_id']) + "\n"
            if 'qty' in vals and line.qty != vals['qty']:
                body += "Quantity: " + str(line.qty) + " -> " + str(vals['qty']) + "\n"
            if 'price_unit' in vals and line.price_unit != vals['price_unit']:
                body += "Price: " + str(line.price_unit) + " -> " + str(vals['price_unit']) + "\n"
            if 'price_subtotal' in vals and line.price_subtotal != vals['price_subtotal']:
                body += "Total: " + str(line.price_subtotal) + " -> " + str(vals['price_subtotal']) + "\n"
            
            if body:
                line.order_id.message_post(
                    body=body,
                    message_type='notification'
                )
                _logger.info(body)

        return super().write(vals)
    
    def unlink(self):
        for line in self:
            line.order_id.deleted_lines = True

            is_advanced_employee = False
            for advanced_employee_id in line.order_id.session_id.config_id.advanced_employee_ids:
                if advanced_employee_id.id == line.order_id.employee_id.id:
                    is_advanced_employee = True

            # if not is_advanced_employee:
            #     raise AccessError("You cannot delete a product line please contact your manager")

            current_user = self.env.user

            body = "[POS_DELETE] "
            body += "User: " + current_user.name + " \n"
            body += "Cashier: " + line.order_id.cashier + " \n"
            body += "Product: " + line.product_id.name + " \n"
            body += "Quantity: " + str(line.qty) + " \n"
            body += "Price: " + str(line.price_unit) + " \n"
            body += "Total: " + str(line.price_subtotal) + " \n"
            # Log the delete of the line
            line.order_id.message_post(
                body=body,
                message_type='notification'
            )
            _logger.info(body)
        return super().unlink()