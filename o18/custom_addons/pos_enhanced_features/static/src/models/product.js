import { ProductProduct } from "@point_of_sale/app/models/product_product";
import { patch } from "@web/core/utils/patch";

patch(ProductProduct.prototype, {
    isFlavorMix() {
        // Now it's just based on is_flavor_mix, we removed max_flavor_count from the model
        return this.is_flavor_mix;
    }
});
