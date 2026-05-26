import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { FlavorSelectorPopup } from "../components/flavor_selector_popup/flavor_selector_popup";

patch(PosStore.prototype, {
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const product = vals.product_id;

        // custom flavor mix logic
        if (product.is_flavor_mix && configure) {
            const payload = await makeAwaitable(this.dialog, FlavorSelectorPopup, {
                product
            });
            console.log("FlavorSelectorPopup payload", payload);

            if (!payload) return;

            console.log("FlavorSelectorPopup attribute_value_ids", payload.attribute_value_ids);
            // Inject attribute values from flavor popup to bypass default popup
            vals.attribute_value_ids = payload.attribute_value_ids.map((id) => [
                "link",
                this.data.models["product.template.attribute.value"].get(id),
            ]);
            
            // These field names must match what's on pos_order.py _load_pos_data_fields
            vals.flavor_mix_selections = payload.attribute_value_ids;
            vals.flavor_quantities = payload.flavor_quantities;
            
            vals.price_extra = payload.price_extra;
            vals.qty = payload.quantity;

            // prevent default ProductConfiguratorPopup
            configure = false;
            console.log("FlavorSelectorPopup payload.label", payload.label);
            console.log("FlavorSelectorPopup full name", product.display_name, payload.label);

            const line = await super.addLineToCurrentOrder(vals, opts, false);
            line.set_customer_note(`(${payload.label})`);
            return line;
        }

        return await super.addLineToCurrentOrder(vals, opts, configure);
    },
});