/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

publicWidget.registry.LogspaceBirthday = publicWidget.Widget.extend({
    selector: "#signup_form",
    events: {
        "change .logspace_v_city > .form-select": "_onChangeHandelCity",
        "change .logspace_v_state > .form-select": "_onChangeHandelState",
        "change .logspace_v_country > .form-select": "_onChangeHandelCountry",
        "click .toggle_current_documents": "_toggleCurrentDocuments",
    },
    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);
        // logspace_v_birthday change
        var input_birth = this.$el.find('.logspace_v_birthday > .form-control');
        input_birth.on('change', this._onChangeHandel.bind(this));
        input_birth.on('keyup', this._onChangeHandel.bind(this));
        // set max date to today
        input_birth.attr('max', new Date().toISOString().split('T')[0]);

        var input_number = this.$el.find('.logspace_v_number > .form-control');
        input_number.on('change', this._onChangeHandelNumber.bind(this));
        input_number.on('keyup', this._onChangeHandelNumber.bind(this));

        var input_civil_number = this.$el.find('.logspace_v_civil_number > .form-control');
        input_civil_number.on('change', this._onChangeHandelCivilNumber.bind(this));
        input_civil_number.on('keyup', this._onChangeHandelCivilNumber.bind(this));

        this._onChangeHandelCountry();

        var current_url = window.location.href;
        current_url.split("/");

        return def;
    },
    _toggleCurrentDocuments: function (ev) {
        var current_documents = this.$el.find('.current_documents');
        current_documents.toggle();
    },
    _onChangeHandel: function (ev) {
        //validate birthday to not be in the future
        var validation_error = this.$el.find('.logspace_v_birthday > .validation_error');
        var $input = $(ev.target);
        var value = $input.val();
        var isValid = this.validateBirthDate(value);
        if (!isValid) {
            $input.addClass('is-invalid');
            validation_error.text(_t("Birthday cannot be in the future"));
        } else {
            $input.removeClass('is-invalid');
            validation_error.text("");
        }
    },
    _onChangeHandelNumber: function (ev) {
        //validate number to be a number
        var validation_error = this.$el.find('.logspace_v_number > .validation_error');
        var $input = $(ev.target);
        var value = $input.val();
        var isValid = this.validateNumber(value);
        if (!isValid) {
            $input.addClass('is-invalid');
            validation_error.text(_t("Please enter a valid number"));
        } else {
            $input.removeClass('is-invalid');
            validation_error.text("");
        }
    },
    _onChangeHandelCivilNumber: async function (ev) {
        //validate civil number to be a number
        var validation_error = this.$el.find('.logspace_v_civil_number > .validation_error');
        var $input = $(ev.target);
        var value = $input.val();
        var isValid = this.validateNumber(value);
        if (!isValid) {
            $input.addClass('is-invalid');
            validation_error.text(_t("Please enter a valid civil number"));
            validation_error.removeClass('d-none');
        } else {
            // $input.removeClass('is-invalid');
            // validation_error.text("");
            // validation_error.addClass('d-none');

            //civil number must be unique
            const data = await rpc(`/logspace/check_civil_number/${value}`, {});
            if (data.exists) {
                $input.addClass('is-invalid');
                validation_error.text(_t("Civil number already exists"));
                validation_error.removeClass('d-none');
            } else {
                $input.removeClass('is-invalid');
                validation_error.text("");
                validation_error.addClass('d-none');
            }
        }

    },
    _changeOption(selectElement, choices, current, type) {
        // empty existing options, only keep the placeholder.
        if (selectElement != null) {
            selectElement.options.length = 1;
            if (choices.length) {
                choices.forEach((item) => {
                    let option = new Option(item[1], item[0]);
                    option.setAttribute('data-code', item[2]);
                    selectElement.appendChild(option);
                });
                if (current != false) {
                    selectElement.value = current;
                }
                if (type == 'state') {
                    this._onChangeHandelState();
                }
                if (type == 'city') {
                    this._onChangeHandelCity();
                }
            }
        }
    },
    _onChangeHandelCountry: async function (ev) {
        // when country changes, state, city and area should filtered to show only related to the country
        const $countrySelect = this.$el.find('.logspace_v_country > .form-select');
        const countryId = $countrySelect.val();
        let choices = [];
        let current = false;
        if (countryId && countryId != "" && countryId != "0" && countryId != null && countryId != undefined && countryId != "undefined" && countryId != "“”") {
            const data = await rpc(`/logspace/states/${countryId}`, {});
            choices = data.states;
            current = data.current_state;
        }
        const stateSelect = this.el.querySelector('.logspace_v_state > .form-select');
        this._changeOption(stateSelect, choices, current, 'state');
    },
    _onChangeHandelState: async function (ev) {
        // when state changes, city and area should filtered to show only related to the state
        const $stateSelect = this.$el.find('.logspace_v_state > .form-select');
        const stateId = $stateSelect.val();
        let choices = [];
        let current = false;
        if (stateId && stateId != "" && stateId != "0" && stateId != null && stateId != undefined && stateId != "undefined" && stateId != "“”") {
            const data = await rpc(`/logspace/cities/${stateId}`, {});
            choices = data.cities;
            current = data.current_city;
        }
        const citySelect = this.el.querySelector('.logspace_v_city > .form-select');
        this._changeOption(citySelect, choices, current, 'city');
    },
    _onChangeHandelCity: async function (ev) {
        // when city changes, area should filtered to show only related to the city
        const $citySelect = this.$el.find('.logspace_v_city > .form-select');
        const cityId = $citySelect.val();
        let current = false;
        let choices = [];
        if (cityId && cityId != "" && cityId != "0" && cityId != null && cityId != undefined && cityId != "undefined" && cityId != "“”") {
            const data = await rpc(`/logspace/areas/${cityId}`, {});
            choices = data.areas;
            current = data.current_area;
        }
        const areaSelect = this.el.querySelector('.logspace_v_area > .form-select');
        this._changeOption(areaSelect, choices, current, 'none');
    },
    validateNumber: function (inputNumber) {
        const regex = /^[0-9]+$/;
        return regex.test(inputNumber);
    },
    validateBirthDate: function (inputDate) {
        const currentDate = new Date();
        const userDate = new Date(inputDate);

        // Check if userDate is a valid date and is not in the future
        if (isNaN(userDate) || userDate > currentDate) {
            return false;
        }

        return true;
    }
});