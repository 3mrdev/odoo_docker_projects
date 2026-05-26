/** @odoo-module **/

import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { whenReady } from "@odoo/owl";

export const portalSessionTimeoutService = {
    TIMEOUT_MINUTES: 30,
    TIMEOUT_CHECK_INTERVAL_MS: 1000,

    start() {
        // Only run for portal users (not backend)
        if (
            odoo.session_info &&
            odoo.session_info.user_groups.includes("base.group_portal")
        ) {
            whenReady(() => {
                const TIMEOUT_MS = this.TIMEOUT_MINUTES * 60 * 1000;
                let logoutAt = Date.now() + TIMEOUT_MS;

                function resetTimer() {
                    logoutAt = Date.now() + TIMEOUT_MS;
                }

                function checkTimeout() {
                    console.log("Checking timeout...");
                    if (Date.now() >= logoutAt) {
                        console.log("Timeout reached. Logging out...");
                        window.location.href = "/web/session/logout?redirect=/";
                    }
                }

                // Reset timer on any user interaction
                const events = ["mousemove", "keypress", "click", "touchstart", "mousedown"];
                events.forEach((evt) =>
                    document.addEventListener(evt, resetTimer, { passive: true })
                );

                // Start checking every second
                setInterval(checkTimeout, this.TIMEOUT_CHECK_INTERVAL_MS);
            });
        }

        return {}; // You can return useful public API if needed
    },
};

registry.category("services").add("portal_session_timeout", portalSessionTimeoutService);
