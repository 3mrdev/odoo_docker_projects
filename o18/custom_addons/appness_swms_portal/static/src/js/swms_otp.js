/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.SWMSOTP = publicWidget.Widget.extend({
    selector: "#otp_container",
    events: {
       'keyup .otp_input': '_onChangeHandel',
    },
    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        // console.log("OTP widget started");
        return def;
    },
    _onChangeHandel: function(ev){
        // This code gets the current input element and stores it in the currentInput variable
        // This code gets the next sibling element of the current input element and stores it in the nextInput variable
        // This code gets the previous sibling element of the current input element and stores it in the prevInput variable
        var input = ev.target;

        const currentInput = input,
        nextInput = input.nextElementSibling,
        prevInput = input.previousElementSibling;

        // if the value has more than one character then clear it
        if (currentInput.value.length > 1) {
            currentInput.value = "";
            return;
        }
        // if the next input is disabled and the current value is not empty
        //  enable the next input and focus on it
        if (nextInput && currentInput.value !== "") {
            nextInput.focus();
        }

        // if the backspace key is pressed
        if (ev.key === "Backspace") {
            // iterate over all inputs again
            if (prevInput) {
                prevInput.focus();
            }
        }
    },
});