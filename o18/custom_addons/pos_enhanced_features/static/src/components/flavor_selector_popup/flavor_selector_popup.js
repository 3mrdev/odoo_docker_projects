import { Component, onMounted, useRef, useState, useSubEnv } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Dialog } from "@web/core/dialog/dialog";

export class FlavorSelectorPopup extends Component {
    static template = "pos_enhanced_features.FlavorSelectorPopup";
    static components = { Dialog };
    static props = ["product", "getPayload", "close"];
    
    setup() {
        super.setup();
        this.pos = usePos();
        this.product = this.props.product;

        // Feature flags from pos.config
        this.featureFlags = {
            valueLimitEnabled: this.pos.config.flavor_value_limit_enabled || false,
            clickableCardEnabled: this.pos.config.flavor_clickable_card_enabled || false,
            multiAttributeEnabled: this.pos.config.flavor_multi_attribute_enabled || false,
        };

        // Group flavors by their attribute line
        let attributeLines = this.product.attribute_line_ids.filter(al => al.mix_is_active && al.mix_max_qty > 0);
        
        // Multi-attribute gating: if disabled, only show the first active attribute group
        if (!this.featureFlags.multiAttributeEnabled) {
            attributeLines = attributeLines.slice(0, 1);
        }

        this.attributeGroups = attributeLines.map(al => {
            const flavors = al.product_template_value_ids || [];
            return {
                id: al.id,
                name: al.attribute_id.name,
                maxQty: al.mix_max_qty,
                flavors: JSON.parse(JSON.stringify(flavors.map(f => ({
                    id: f.id,
                    name: f.name,
                    price_extra: f.price_extra,
                    mix_max_value_qty: this.featureFlags.valueLimitEnabled ? (f.mix_max_value_qty || 0) : 0,
                    image_url: f.image,
                    product_image_url: this.product.image_128,
                    attribute_id: al.id
                }))))
            };
        });

        // Initialize state
        // selected: { attrLineId: { ptavId: count } }
        // totals: { attrLineId: totalCount }
        const selected = {};
        const totals = {};
        for (const group of this.attributeGroups) {
            selected[group.id] = {};
            totals[group.id] = 0;
        }

        this.state = useState({
            selected,
            totals,
            quantity: 1, // Outer quantity (number of mix portions)
        });
    }

    incrementQuantity() {
        if (this.state.quantity >= 100) return;
        this.state.quantity += 1;
    }

    decrementQuantity() {
        if (this.state.quantity < 2) return;
        this.state.quantity -= 1;
    }

    incrementFlavor(ev) {
        const ptavId = parseInt(ev.currentTarget.dataset.id);
        const attrLineId = parseInt(ev.currentTarget.dataset.attrId);
        const group = this.attributeGroups.find(g => g.id === attrLineId);
        
        if (!group || this.state.totals[attrLineId] >= group.maxQty) return;
        
        // Per-value limit check
        const flavor = group.flavors.find(f => f.id === ptavId);
        const currentCount = this.state.selected[attrLineId][ptavId] || 0;
        if (flavor && flavor.mix_max_value_qty > 0 && currentCount >= flavor.mix_max_value_qty) return;
        
        this.state.selected[attrLineId][ptavId] = currentCount + 1;
        this.state.totals[attrLineId] += 1;
    }
    
    decrementFlavor(ev) {
        const ptavId = parseInt(ev.currentTarget.dataset.id);
        const attrLineId = parseInt(ev.currentTarget.dataset.attrId);

        if (!this.state.selected[attrLineId] || !this.state.selected[attrLineId][ptavId]) return;
        
        this.state.selected[attrLineId][ptavId] -= 1;
        this.state.totals[attrLineId] -= 1;
        if (this.state.selected[attrLineId][ptavId] === 0) {
            delete this.state.selected[attrLineId][ptavId];
        }
    }

    onCardClick(ev) {
        if (!this.featureFlags.clickableCardEnabled) return;
        const card = ev.currentTarget;
        const ptavId = card.dataset.id;
        const attrId = card.dataset.attrId;
        if (!ptavId || !attrId) return;
        // Reuse incrementFlavor logic
        this.incrementFlavor({ currentTarget: { dataset: { id: ptavId, attrId: attrId } } });
    }

    isFlavorMaxed(group, flavor) {
        if (!this.featureFlags.valueLimitEnabled || !flavor.mix_max_value_qty || flavor.mix_max_value_qty <= 0) {
            return false;
        }
        const currentCount = this.state.selected[group.id][flavor.id] || 0;
        return currentCount >= flavor.mix_max_value_qty;
    }

    getFlavorRemaining(group, flavor) {
        if (!flavor.mix_max_value_qty || flavor.mix_max_value_qty <= 0) return 0;
        const currentCount = this.state.selected[group.id][flavor.id] || 0;
        return flavor.mix_max_value_qty - currentCount;
    }

    get isValid() {
        // Form is valid if ALL groups have reached exactly their maxQty limit
        for (const group of this.attributeGroups) {
            if (this.state.totals[group.id] !== group.maxQty) {
                return false;
            }
        }
        return true;
    }

    computePayload() {
        const attribute_value_ids = [];
        const flavor_quantities = {};
        let price_extra = 0;
        let quantity = this.state.quantity;
        const groupLabels = [];

        for (const group of this.attributeGroups) {
            const attrSelections = this.state.selected[group.id];
            const flavorCounts = [];
            
            for (const [idStr, count] of Object.entries(attrSelections)) {
                if (count <= 0) continue;
                
                const ptavId = parseInt(idStr);
                const flavor = group.flavors.find(f => f.id === ptavId);
                if (!flavor) continue;
        
                // Add to standard attributes (for display/configurator bypass)
                for (let i = 0; i < count; i++) {
                    attribute_value_ids.push(ptavId);
                }
                
                // Add to JSON dict for backend BOM explosion override
                flavor_quantities[ptavId] = count;
        
                price_extra += flavor.price_extra * count;
                flavorCounts.push(`${flavor.name}${count > 1 ? ` ×${count}` : ""}`);
            }
            if (flavorCounts.length > 0) {
                groupLabels.push(flavorCounts.join(", "));
            }
        }
    
        const label = groupLabels.join(" | ");
    
        return {
            attribute_value_ids,
            flavor_quantities: JSON.stringify(flavor_quantities),
            attribute_custom_values: {},
            price_extra,
            label,
            quantity,
        };
    }
    
    confirm() {
        if (!this.isValid) return;
        this.props.getPayload(this.computePayload());
        this.props.close();
    }

    close() {
        this.props.close();
    }
}