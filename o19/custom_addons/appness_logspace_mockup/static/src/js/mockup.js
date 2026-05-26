odoo.define('appness_logspace_mockup.mockup_search', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.MockupSearch = publicWidget.Widget.extend({
        selector: '.container:has(#results-container)',
        events: {
            'click #btn-grid': '_onBtnGrid',
            'click #btn-list': '_onBtnList',
        },

        start: function () {
            this.$resultsContainer = this.$('#results-container');
            return this._super.apply(this, arguments);
        },

        _onBtnGrid: function (ev) {
            ev.preventDefault();
            this.$('#btn-grid').addClass('active');
            this.$('#btn-list').removeClass('active');
            
            this.$resultsContainer.attr('data-view', 'grid');
            this.$('.truck-card-wrapper').removeClass('col-12').addClass('col-md-4');
            this.$('.truck-card').removeClass('flex-row').addClass('flex-column');
            this.$('.truck-card .card-img-top').css({'height': '200px', 'width': 'auto', 'border-radius': '0.25rem 0.25rem 0 0'});
        },

        _onBtnList: function (ev) {
            ev.preventDefault();
            this.$('#btn-list').addClass('active');
            this.$('#btn-grid').removeClass('active');

            this.$resultsContainer.attr('data-view', 'list');
            this.$('.truck-card-wrapper').removeClass('col-md-4').addClass('col-12');
            this.$('.truck-card').removeClass('flex-column').addClass('flex-row');
            // Adjust image for list view
            this.$('.truck-card .card-img-top').css({'height': 'auto', 'width': '30%', 'border-radius': '0.25rem 0 0 0.25rem'});
        },
    });
});
