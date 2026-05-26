/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    /**
     * Override onMounted to auto-validate when customer has 
     * use_pos_customer_account enabled. The payment line was already 
     * added in PosStore.pay().
     */
    onMounted() {
        super.onMounted();

        // Check if this order should be auto-validated
        const order = this.currentOrder;
        if (order && order.uiState.autoValidateCustomerAccount) {
            // Clear the flag
            order.uiState.autoValidateCustomerAccount = false;

            // Trigger validation after a short delay to ensure UI is ready
            setTimeout(() => {
                if (order.is_paid()) {
                    this.validateOrder(false);
                }
            }, 100);
        }
    },
});
