/** Extend POS Order Model */
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    can_be_removed() {
        console.log('can_be_removed', this);
        // Check if the order is sent to the kitchen
        const is_manager = this.pos.get_cashier()?._role === 'manager';
        console.log('is_manager', is_manager);
        const is_sent = this.is_sent_to_kitchen;
        console.log('is_sent', is_sent);

        if (is_sent && !is_manager) {
            console.log('Order cannot be removed');
            return false;
        }
        console.log('Order can be removed');
        return true; // fallback to default
    },

    export_for_printing() {
        const data = super.export_for_printing(...arguments);
        data.order_type = this.table_id?.floor_id?.name || " ";
        return data;
    },
});
