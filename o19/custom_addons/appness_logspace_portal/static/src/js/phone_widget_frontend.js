/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.LogspacePhoneWidget = publicWidget.Widget.extend({
    selector: "#logspace_intl_tel_widget",
    events: {
        'change .intl_tel_widget': '_onChangeHandel',
        'keyup .intl_tel_widget': '_onChangeHandel',
    },
    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        // var input = this.$el.find('.intl_tel_widget');
        var input = this.el.querySelector('.intl_tel_widget');
        this.iti = window.intlTelInput(input, {
            initialCountry: "auto",
            separateDialCode: true,
            placeholderNumberType: 'MOBILE',
            geoIpLookup: callback => {
                fetch("https://ipapi.co/json")
                    .then(res => res.json())
                    .then(data => callback(data.country_code))
                    .catch(() => callback("om"));
            },
            onlyCountries: ["om"],
            loadUtils: () => import("https://cdn.jsdelivr.net/npm/intl-tel-input@25.3.0/build/js/utils.js"),
        });

        return def;
    },
    _onChangeHandel: function (ev) {
        var phone_output = this.el.querySelector('.phone_output');
        var phone_value = this.el.querySelector('.phone_value');

        // phone_value.value = (iti.isValidNumber()) ? iti.getNumber() : "Please enter a valid number";
        if (this.iti.isValidNumber()) {
            var text = "Correct: " + this.iti.getNumber();
            phone_value.value = this.iti.getNumber();
            phone_output.innerHTML = text;
            phone_output.classList.remove("alert-danger")
            phone_output.classList.add("alert-success")
        } else {
            if (this.iti.getNumber() == '') {
                phone_output.classList.add("d-none")
            } else {
                phone_output.innerHTML = "Please enter a valid number ";
                phone_value.value = '';
                phone_output.classList.add("alert-danger")
                phone_output.classList.remove("alert-success")
                phone_output.classList.remove("d-none")
            }
        }

    },
});