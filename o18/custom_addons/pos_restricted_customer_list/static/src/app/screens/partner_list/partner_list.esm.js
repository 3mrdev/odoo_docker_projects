import {PartnerList} from "@point_of_sale/app/screens/partner_list/partner_list";
import {patch} from "@web/core/utils/patch";

patch(PartnerList.prototype, {
    async getNewPartners() {
        const config = this.pos.config;
        if (!config.available_in_pos_restricted) {
            return super.getNewPartners(...arguments);
        }
        const domain = [["available_in_pos", "=", true]];
        if (config.pos_partner_category && config.raw.partner_category_id) {
            domain.push(["category_id", "in", [config.raw.partner_category_id]]);
        }
        const query = (this.state.query || "").trim();
        if (query) {
            const searchFields = [
                "name",
                "parent_name",
                ...this.getPhoneSearchTerms(),
                "email",
                "barcode",
                "street",
                "zip",
                "city",
                "state_id",
                "country_id",
                "vat",
            ];
            const searchDomain = [
                ...Array(searchFields.length - 1).fill("|"),
                ...searchFields.map((field) => [field, "ilike", query + "%"]),
            ];
            domain.push(...searchDomain);
        }
        const limit = 30;
        const result = await this.pos.data.searchRead("res.partner", domain, [], {
            limit: limit,
            offset: this.state.currentOffset,
        });
        return result;
    },
});
