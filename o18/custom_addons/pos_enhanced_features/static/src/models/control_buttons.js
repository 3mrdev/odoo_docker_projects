import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

patch(ControlButtons.prototype, {
    async clickPrintBill() {
 
        this.notification .add(_t("Order sent to the kitchen"), {
            type: "success",
            title: _t(`Order sent to the kitchen`),
        });

        // 1. Save order to server.
        let syncOrderResult = await this.pos.syncAllOrders({ throw: true });
        if (!syncOrderResult) {
            return;
        }

        // Proceed with original logic
        return await super.clickPrintBill();
    },
});