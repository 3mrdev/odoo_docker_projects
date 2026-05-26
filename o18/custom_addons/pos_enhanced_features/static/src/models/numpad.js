import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Numpad, enhancedButtons } from "@point_of_sale/app/generic_components/numpad/numpad";

patch(Numpad.prototype, {
    setup() {
        super.setup?.();

        this.pos = useService("pos");
        this.dialog = useService("dialog");
        const numberBuffer = this.numberBuffer || useService("number_buffer");

        this.onClick = async (buttonValue) => {
            console.log("buttonValue:", buttonValue);

            if (buttonValue === "Backspace" || buttonValue === "Delete" || buttonValue === "1" || buttonValue === "2" || buttonValue === "3" || buttonValue === "4" || buttonValue === "5" || buttonValue === "6" || buttonValue === "7" || buttonValue === "8" || buttonValue === "9" || buttonValue === "0" || buttonValue === "." || buttonValue === "-") {
                const order = this.pos.get_order();
                const line = order?.get_selected_orderline();
                const is_manager = this.pos.get_cashier()?._role === "manager";
                const is_sent = typeof line?.id === "number";  // ✅ safe check

                console.log("Cashier:", this.pos.get_cashier()?._role);
                console.log("Line ID:", line?.id, "→ is_sent:", is_sent);
                //await this.pos.syncAllOrders({ orders: [order], throw: true });

                if (line && is_sent && !is_manager) {
                    // alert("You cannot remove or modify a product already sent to the kitchen.");
                    this.dialog.add(AlertDialog, {
                        title: _t("Unauthorized"),
                        body: _t(
                            "You cannot remove or modify a product already sent to the kitchen."
                        ),
                    });
                    // ev.preventDefault();
                    return;
                }
            }

            (this.numberBuffer || numberBuffer).sendKey(buttonValue);
        };

        document.addEventListener("keydown", async (ev) => {
            console.log("key:", ev.key);
            if (ev.key === "Backspace" || ev.key === "Delete" || ev.key === "1" || ev.key === "2" || ev.key === "3" || ev.key === "4" || ev.key === "5" || ev.key === "6" || ev.key === "7" || ev.key === "8" || ev.key === "9" || ev.key === "0" || ev.key === "." || ev.key === "-") {
                const order = this.pos.get_order();
                const line = order?.get_selected_orderline();
                const is_manager = this.pos.get_cashier()?._role === "manager";
                const is_sent = typeof line?.id === "number";  // ✅ safe check

                console.log("Cashier:", this.pos.get_cashier()?._role);
                console.log("Line ID:", line?.id, "→ is_sent:", is_sent);
                //await this.pos.syncAllOrders({ orders: [order], throw: true });

                if (line && is_sent && !is_manager) {
                    // ev.preventDefault();
                    this.dialog.add(AlertDialog, {
                        title: _t("Unauthorized"),
                        body: _t(
                            "You cannot remove or modify a product already sent to the kitchen."
                        ),
                    });
                    alert("You cannot remove or modify a product already sent to the kitchen.");
                    ev.preventDefault();
                    return;
                }
            }
        });
    },
});
