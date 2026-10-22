/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

/**
 * Driver delivery actions.
 *
 * Drives the buttons rendered by `logspace_driver_track_page`. Each button
 * posts one whitelisted transition to /logspace/driver/orders/action; the two
 * code-gated ones first open a modal so the driver can type in the 4-digit
 * code they read aloud from the customer.
 *
 * The server never returns the expected code - only ok/error - so a failure is
 * shown inline and the driver can retry without losing the page.
 */
publicWidget.registry.LogspaceDriver = publicWidget.Widget.extend({
    selector: ".logspace-driver-page",
    events: {
        "click .logspace-driver-action": "_onActionClick",
        "click .logspace-driver-code-submit": "_onCodeSubmit",
        "input .logspace-driver-code-input": "_onCodeInput",
        "keyup .logspace-driver-code-input": "_onCodeKeyup",
        "shown.bs.modal": "_onModalShown",
        "hidden.bs.modal": "_onModalHidden",
    },

    /**
     * @override
     */
    start() {
        this._super(...arguments);
        this.orderName = this.el.dataset.orderName || "";
        this.busy = false;
        this.pendingAction = null;
        this.feedbackEl = this.el.querySelector(".logspace-driver-feedback");
        this.modalEl = this.el.querySelector("#logspaceDriverCodeModal");
        // Bootstrap 5 ships as a global in web.assets_frontend.
        this.modal = this.modalEl && window.Modal
            ? window.Modal.getOrCreateInstance(this.modalEl)
            : null;
        return Promise.resolve();
    },

    // -------------------------------------------------------------------------
    // Handlers
    // -------------------------------------------------------------------------

    _onActionClick(ev) {
        const button = ev.currentTarget;
        if (this.busy) {
            return;
        }
        const action = button.dataset.action;
        if (!action) {
            return;
        }
        if (button.dataset.needsCode) {
            this._openCodeModal(action, button.dataset.codeType, button.dataset.label);
        } else {
            this._callAction(action, null, button);
        }
    },

    _onCodeSubmit() {
        if (this.busy || !this.pendingAction) {
            return;
        }
        const code = this._getCode();
        if (code.length !== 4) {
            this._showModalError(_t("Enter the 4-digit code exactly as the customer reads it."));
            return;
        }
        this._callAction(this.pendingAction.key, code, this.pendingAction.button);
    },

    _onCodeInput(ev) {
        // Keep the field numeric; the server compares digits only.
        const cleaned = ev.currentTarget.value.replace(/\D/g, "").slice(0, 4);
        if (cleaned !== ev.currentTarget.value) {
            ev.currentTarget.value = cleaned;
        }
        this._hideModalError();
    },

    _onCodeKeyup(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this._onCodeSubmit();
        }
    },

    /**
     * Focus the code input once the modal is fully shown.
     *
     * Bootstrap's Modal activates a focus trap at the end of its show
     * transition, and that trap focuses the modal root. A `setTimeout` here
     * races the trap and loses, which leaves the field unfocused: on a phone
     * the driver has to tap it before the keypad appears. Waiting for
     * `shown.bs.modal` means we always focus after the trap has settled.
     */
    _onModalShown() {
        const input = this._getInput();
        if (input) {
            input.focus();
        }
    },

    _onModalHidden() {
        this.pendingAction = null;
        this._hideModalError();
        const input = this._getInput();
        if (input) {
            input.value = "";
        }
    },

    // -------------------------------------------------------------------------
    // Code modal
    // -------------------------------------------------------------------------

    _openCodeModal(key, codeType, label) {
        this.pendingAction = { key, codeType, label: label || key, button: null };
        const actionButton = this.el.querySelector(
            `.logspace-driver-action[data-action="${CSS.escape(key)}"]`
        );
        this.pendingAction.button = actionButton;

        const intro = this.el.querySelector(".logspace-driver-code-intro");
        if (intro) {
            intro.textContent = codeType === "dropoff"
                ? _t("Ask the customer for the 4-digit drop-off verification code and enter it below.")
                : _t("Ask the customer for the 4-digit pickup verification code and enter it below.");
        }
        this._hideModalError();
        this._setSubmitBusy(false);

        if (!this.modal) {
            // No Bootstrap available - fall back to a plain prompt-free inline flow.
            this._showFeedback("danger", _t("The verification dialog could not be opened. Reload the page and try again."));
            return;
        }
        this.modal.show();
        const input = this._getInput();
        if (input) {
            input.value = "";
        }
    },

    _getInput() {
        return this.el.querySelector(".logspace-driver-code-input");
    },

    _getCode() {
        const input = this._getInput();
        return input ? input.value.replace(/\D/g, "").slice(0, 4) : "";
    },

    _showModalError(message) {
        const errorEl = this.el.querySelector(".logspace-driver-code-error");
        if (!errorEl) {
            return;
        }
        errorEl.textContent = message;
        errorEl.classList.remove("d-none");
        const input = this._getInput();
        if (input) {
            input.classList.add("is-invalid");
            input.select();
        }
    },

    _hideModalError() {
        const errorEl = this.el.querySelector(".logspace-driver-code-error");
        if (errorEl) {
            errorEl.textContent = "";
            errorEl.classList.add("d-none");
        }
        const input = this._getInput();
        if (input) {
            input.classList.remove("is-invalid");
        }
    },

    _setSubmitBusy(busy) {
        const submit = this.el.querySelector(".logspace-driver-code-submit");
        if (!submit) {
            return;
        }
        submit.disabled = busy;
        const label = submit.querySelector(".logspace-driver-code-submit-label");
        if (label) {
            label.textContent = busy ? _t("Verifying...") : _t("Confirm");
        }
    },

    // -------------------------------------------------------------------------
    // RPC
    // -------------------------------------------------------------------------

    async _callAction(action, code, button) {
        if (this.busy) {
            return;
        }
        const fromModal = Boolean(code);
        this.busy = true;
        this._setButtonsEnabled(false);
        this._setButtonSpinner(button, true);
        if (fromModal) {
            this._setSubmitBusy(true);
            this._hideModalError();
        } else {
            this._clearFeedback();
        }

        let result = null;
        let transportError = null;
        try {
            result = await rpc("/logspace/driver/orders/action", {
                order_name: this.orderName,
                action: action,
                code: code,
            });
        } catch (error) {
            transportError = error;
        }

        this._setButtonSpinner(button, false);
        this.busy = false;

        if (result && result.ok) {
            this._setButtonsEnabled(false);
            if (this.modal && this.modalEl && this.modalEl.classList.contains("show")) {
                this.modal.hide();
            }
            this._showFeedback(
                "success",
                _t('Status updated to "%s". Reloading...', result.label || result.state)
            );
            // Brief pause so the driver sees the confirmation before the reload.
            setTimeout(() => window.location.reload(), 900);
            return;
        }

        const message =
            (result && result.error) ||
            (transportError && transportError.data && transportError.data.message) ||
            _t("The status could not be updated. Please try again.");

        if (fromModal) {
            this._setSubmitBusy(false);
            this._setButtonsEnabled(true);
            this._showModalError(message);
        } else {
            this._setButtonsEnabled(true);
            this._showFeedback("danger", message);
        }
    },

    // -------------------------------------------------------------------------
    // UI helpers
    // -------------------------------------------------------------------------

    _setButtonsEnabled(enabled) {
        this.el.querySelectorAll(".logspace-driver-action").forEach((btn) => {
            btn.disabled = !enabled;
            btn.classList.toggle("disabled", !enabled);
        });
    },

    _setButtonSpinner(button, show) {
        if (!button) {
            return;
        }
        let spinner = button.querySelector(".logspace-driver-action-spinner");
        if (show && !spinner) {
            spinner = document.createElement("i");
            spinner.className = "fa fa-spinner fa-spin ms-2 logspace-driver-action-spinner";
            button.appendChild(spinner);
        } else if (!show && spinner) {
            spinner.remove();
        }
    },

    _showFeedback(type, message) {
        if (!this.feedbackEl) {
            return;
        }
        this.feedbackEl.className = `logspace-driver-feedback mt-3 alert alert-${type}`;
        this.feedbackEl.setAttribute("role", "alert");
        this.feedbackEl.textContent = message;
        this.feedbackEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    },

    _clearFeedback() {
        if (!this.feedbackEl) {
            return;
        }
        this.feedbackEl.className = "logspace-driver-feedback mt-3";
        this.feedbackEl.textContent = "";
    },
});

export default publicWidget.registry.LogspaceDriver;
