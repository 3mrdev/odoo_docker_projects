/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    /**
     * Override setTableFromUi to auto-assign default customer from floor.
     * When a table is selected and the order has no partner, we check if
     * the floor has a default_customer configured and assign it.
     */
    async setTableFromUi(table, orderUuid = null) {
        await super.setTableFromUi(table, orderUuid);

        const order = this.get_order();
        if (!order) {
            return;
        }

        // Only set partner if order doesn't already have one
        if (order.get_partner()) {
            return;
        }

        // Get the floor from the table
        const floor = table.floor_id;
        if (!floor || !floor.default_customer) {
            return;
        }

        // Get the partner from loaded models
        const partnerId = floor.default_customer.id || floor.default_customer;
        const partner = this.models["res.partner"].get(partnerId);

        if (partner) {
            order.set_partner(partner);
        }
    },

    /**
     * Override pay() to auto-pay with Customer Account when customer has
     * use_pos_customer_account enabled. This prepares the order for auto-validation.
     */
    async pay() {
        const currentOrder = this.get_order();

        if (!currentOrder || !currentOrder.canPay()) {
            return;
        }

        const partner = currentOrder.get_partner();

        // Check if customer has auto-pay enabled
        if (partner && partner.use_pos_customer_account) {
            // Find Customer Account (pay_later) payment method from config
            const payLaterMethod = this.config.payment_method_ids.find(
                (pm) => pm.type === "pay_later"
            );

            if (payLaterMethod) {
                // Add payment line for the full amount due
                currentOrder.add_paymentline(payLaterMethod);

                // Mark this order for auto-validation
                currentOrder.uiState.autoValidateCustomerAccount = true;
            }
        }

        // Always go to payment screen - it will auto-validate if flag is set
        await super.pay();
    },
});
