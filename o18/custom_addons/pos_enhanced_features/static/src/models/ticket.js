/** Extend POS Order Model */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";

patch(TicketScreen.prototype, {
    /**
     * Hide the delete button if one of the payments is a 'done' electronic payment.
     */
    shouldHideDeleteButton(order) {
        // const orders = this.pos.models["pos.order"].filter((o) => !o.finalized);
        // return (
        //     (orders.length === 1 && orders[0].lines.length === 0) ||
        //     (this.ui.isSmall && order != this.state.selectedOrder) ||
        //     this.isDefaultOrderEmpty(order) ||
        //     order.finalized ||
        //     order.payment_ids.some(
        //         (payment) => payment.is_electronic() && payment.get_payment_status() === "done"
        //     ) ||
        //     order.finalized
        // );
        return true;
    },
});
