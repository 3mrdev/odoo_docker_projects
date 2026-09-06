/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * LogspacePhoneWidget - Phone field with international telephone input validation.
 * Targets each .logspace_intl_tel_widget wrapper individually.
 *
 * Uses intl-tel-input v25.3.0 library for:
 * - Country flag + dial code selector
 * - E.164 phone number validation
 * - Visual feedback (valid/invalid)
 * - Hidden input carries the E.164 value for form submission
 *
 * Exposes window.initLogspacePhoneInput(wrapperEl) for dynamically added rows.
 */
publicWidget.registry.LogspacePhoneWidget = publicWidget.Widget.extend({
    selector: '.logspace_intl_tel_widget',
    events: {
        'change .intl_tel_widget': '_onChange',
        'keyup .intl_tel_widget': '_onChange',
    },

    start: function () {
        var def = this._super.apply(this, arguments);
        var input = this.el.querySelector('.intl_tel_widget');
        if (!input) return def;

        this.iti = window.intlTelInput(input, {
            initialCountry: "auto",
            separateDialCode: true,
            placeholderNumberType: 'MOBILE',
            geoIpLookup: function (callback) {
                fetch("https://ipapi.co/json")
                    .then(function (res) { return res.json(); })
                    .then(function (data) { callback(data.country_code); })
                    .catch(function () { callback("om"); });
            },
            onlyCountries: ["om"],
            loadUtils: function () {
                return import("https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/utils.js");
            },
        });

        // Pre-fill with stored phone number if data-value is set.
        // setNumber() accepts any format (E.164, national, with/without country code).
        // Wrapped in try-catch to handle invalid values like "Not set" gracefully.
        var prefill = (input.getAttribute('data-value') || '').trim();
        if (prefill && prefill !== 'Not set') {
            try {
                this.iti.setNumber(prefill);
            } catch (e) {
                // Invalid format - leave input empty, user will type manually
            }
        }

        // Trigger initial validation to set hidden value
        this._onChange();

        return def;
    },

    _onChange: function () {
        var phone_output = this.el.querySelector('.phone_output');
        var phone_value = this.el.querySelector('.phone_value');
        if (!this.iti) return;

        if (this.iti.isValidNumber()) {
            var number = this.iti.getNumber();
            if (phone_value) phone_value.value = number;
            if (phone_output) {
                phone_output.innerHTML = "Correct: " + number;
                phone_output.classList.remove("alert-danger", "d-none");
                phone_output.classList.add("alert-success");
            }
        } else {
            var raw = this.iti.getNumber();
            if (raw === '') {
                if (phone_value) phone_value.value = '';
                if (phone_output) {
                    phone_output.innerHTML = '';
                    phone_output.classList.add("d-none");
                    phone_output.classList.remove("alert-danger", "alert-success");
                }
            } else {
                if (phone_value) phone_value.value = '';
                if (phone_output) {
                    phone_output.innerHTML = "Please enter a valid number";
                    phone_output.classList.remove("d-none", "alert-success");
                    phone_output.classList.add("alert-danger");
                }
            }
        }
    },
});

/**
 * Global helper for initializing intl-tel-input on dynamically added phone wrappers.
 * Used by the addContactRow() function in provider step 2.
 * Cleans up any existing ITI markup from cloned elements before reinitializing.
 */
window.initLogspacePhoneInput = function (wrapperEl) {
    if (!wrapperEl || !window.intlTelInput) return;

    var input = wrapperEl.querySelector('.intl_tel_widget');
    if (!input) return;

    // Clean up intl-tel-input markup from cloning (ITI wraps input in .iti container)
    var existingIti = wrapperEl.querySelector('.iti');
    if (existingIti) {
        // Move the input back out of the .iti wrapper to its original position
        var parent = existingIti.parentNode;
        while (existingIti.firstChild) {
            parent.insertBefore(existingIti.firstChild, existingIti);
        }
        existingIti.remove();
    }

    // Re-find input after cleanup
    input = wrapperEl.querySelector('.intl_tel_widget');
    if (!input) return;

    var iti = window.intlTelInput(input, {
        initialCountry: "auto",
        separateDialCode: true,
        placeholderNumberType: 'MOBILE',
        geoIpLookup: function (callback) {
            fetch("https://ipapi.co/json")
                .then(function (res) { return res.json(); })
                .then(function (data) { callback(data.country_code); })
                .catch(function () { callback("om"); });
        },
        onlyCountries: ["om"],
        loadUtils: function () {
            return import("https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/utils.js");
        },
    });

    // Wire up event listeners for validation feedback
    var phone_output = wrapperEl.querySelector('.phone_output');
    var phone_value = wrapperEl.querySelector('.phone_value');

    function handleChange() {
        if (iti.isValidNumber()) {
            var number = iti.getNumber();
            if (phone_value) phone_value.value = number;
            if (phone_output) {
                phone_output.innerHTML = "Correct: " + number;
                phone_output.classList.remove("alert-danger", "d-none");
                phone_output.classList.add("alert-success");
            }
        } else {
            if (iti.getNumber() === '') {
                if (phone_value) phone_value.value = '';
                if (phone_output) {
                    phone_output.innerHTML = '';
                    phone_output.classList.add("d-none");
                    phone_output.classList.remove("alert-danger", "alert-success");
                }
            } else {
                if (phone_value) phone_value.value = '';
                if (phone_output) {
                    phone_output.innerHTML = "Please enter a valid number";
                    phone_output.classList.remove("d-none", "alert-success");
                    phone_output.classList.add("alert-danger");
                }
            }
        }
    }

    input.addEventListener('change', handleChange);
    input.addEventListener('keyup', handleChange);
    handleChange();
};

export default {
    LogspacePhoneWidget: publicWidget.registry.LogspacePhoneWidget,
};
