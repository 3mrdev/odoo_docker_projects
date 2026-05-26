import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";

patch(OrderSummary.prototype, {

    /**
     * @override
     */
    _setValue(val) {
        const order = this.pos.get_order();
        this.pos.syncAllOrders({ orders: [order], throw: true });
        return super._setValue(val);
    },

});
