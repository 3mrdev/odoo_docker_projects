/** @odoo-module **/

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

const { DateTime } = luxon;

patch(TicketScreen.prototype, {
    async onDoRefund() {
        const order = this.getSelectedOrder();
        if (order && this.pos.config.return_limit_days > 0) {
            const dateOrder = order.date_order; // luxon DateTime object
            const limitDays = this.pos.config.return_limit_days;
            // Calculate deadline: date_order + limitDays
            // We want to check if today > deadline
            // Or simpler: diff between today and dateOrder > limitDays

            const today = DateTime.now();
            const diffInDays = today.diff(dateOrder, 'days').days;

            if (diffInDays > limitDays) {
                this.dialog.add(AlertDialog, {
                    title: _t("Return Policy Restriction"),
                    body: _t("This order can't be returned due to our policy of not returning products after %s amount of days", limitDays),
                });
                return;
            }
        }
        return super.onDoRefund(...arguments);
    }
});
