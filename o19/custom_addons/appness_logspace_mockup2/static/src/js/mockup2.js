/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.LogspaceMockup2 = publicWidget.Widget.extend({
    selector: '.logspace-mockup',
    events: {
        'click .js-addons-toggle': '_onAddonsToggle',
        'click .js-star-rating': '_onStarRating',
        'click .js-booking-next': '_onBookingNext',
        'click .js-booking-back': '_onBookingBack',
        'change .js-file-upload': '_onFileUpload',
    },

    /**
     * Initialize the widget
     */
    start: function () {
        this._super.apply(this, arguments);
        this._initStepper();
        return Promise.resolve();
    },

    /**
     * Initialize stepper animation
     */
    _initStepper: function () {
        const stepper = document.querySelector('.mockup2-stepper');
        if (stepper) {
            // Add subtle animation to progress bar
            const progressBar = stepper.querySelector('.progress-bar');
            if (progressBar) {
                setTimeout(() => {
                    progressBar.style.transition = 'width 0.5s ease-in-out';
                }, 100);
            }
        }
    },

    /**
     * Handle add-ons checkbox toggle
     */
    _onAddonsToggle: function (ev) {
        const checkbox = ev.currentTarget;
        const card = checkbox.closest('.addon-card');
        if (card) {
            card.classList.toggle('selected', checkbox.checked);
            this._updateTotal();
        }
    },

    /**
     * Update total price when add-ons change
     */
    _updateTotal: function () {
        const basePrice = parseFloat(document.querySelector('[data-base-price]')?.dataset.basePrice || 0);
        let addonsTotal = 0;

        document.querySelectorAll('.js-addon-checkbox:checked').forEach((checkbox) => {
            addonsTotal += parseFloat(checkbox.dataset.price || 0);
        });

        const total = basePrice + addonsTotal;
        const totalElement = document.querySelector('.js-total-price');
        if (totalElement) {
            totalElement.textContent = '$' + total.toFixed(2);
        }
    },

    /**
     * Handle star rating selection
     */
    _onStarRating: function (ev) {
        ev.preventDefault();
        const star = ev.currentTarget;
        const rating = parseInt(star.dataset.rating, 10);
        const container = star.closest('.rating-stars');

        if (container) {
            container.querySelectorAll('.star').forEach((s, index) => {
                if (index < rating) {
                    s.classList.remove('empty');
                    s.querySelector('i')?.classList.replace('fa-star-o', 'fa-star');
                } else {
                    s.classList.add('empty');
                    s.querySelector('i')?.classList.replace('fa-star', 'fa-star-o');
                }
            });

            // Update hidden input for form submission
            const ratingInput = container.querySelector('input[name="rating"]');
            if (ratingInput) {
                ratingInput.value = rating;
            }
        }
    },

    /**
     * Handle booking step navigation - Next
     */
    _onBookingNext: function (ev) {
        ev.preventDefault();
        const form = ev.currentTarget.closest('form');
        if (form && this._validateForm(form)) {
            const nextUrl = ev.currentTarget.dataset.nextUrl;
            if (nextUrl) {
                window.location.href = nextUrl;
            }
        }
    },

    /**
     * Handle booking step navigation - Back
     */
    _onBookingBack: function (ev) {
        ev.preventDefault();
        const backUrl = ev.currentTarget.dataset.backUrl;
        if (backUrl) {
            window.location.href = backUrl;
        }
    },

    /**
     * Simple form validation
     */
    _validateForm: function (form) {
        let isValid = true;
        form.querySelectorAll('[required]').forEach((field) => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('is-invalid');
            } else {
                field.classList.remove('is-invalid');
            }
        });
        return isValid;
    },

    /**
     * Handle file upload preview
     */
    _onFileUpload: function (ev) {
        const input = ev.currentTarget;
        const files = input.files;
        const previewContainer = document.querySelector(input.dataset.previewTarget);

        if (previewContainer && files.length > 0) {
            previewContainer.innerHTML = '';
            Array.from(files).forEach((file) => {
                const fileBadge = document.createElement('span');
                fileBadge.className = 'badge bg-light text-dark me-2 mb-2';
                fileBadge.innerHTML = `<i class="fa fa-file-o me-1"></i>${file.name}`;
                previewContainer.appendChild(fileBadge);
            });
        }
    },
});

/**
 * Mobile sidebar toggle for portal
 */
publicWidget.registry.LogspacePortalSidebar = publicWidget.Widget.extend({
    selector: '.o_portal_sidebar',
    events: {
        'click .js-toggle-sidebar': '_onToggleSidebar',
    },

    _onToggleSidebar: function (ev) {
        ev.preventDefault();
        const sidebar = this.el;
        sidebar.classList.toggle('d-none');
        sidebar.classList.toggle('d-block');
    },
});

/**
 * Search form enhancements
 */
publicWidget.registry.LogspaceSearch = publicWidget.Widget.extend({
    selector: '.search-hero form',
    events: {
        'submit': '_onSearchSubmit',
    },

    _onSearchSubmit: function (ev) {
        // Add loading state to button
        const submitBtn = ev.currentTarget.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
        }
    },
});

/**
 * Search results view toggle (Grid/List)
 */
publicWidget.registry.LogspaceResultsView = publicWidget.Widget.extend({
    selector: '.logspace-results',

    events: {
        'click .js-view-grid': '_onViewGrid',
        'click .js-view-list': '_onViewList',
    },

    start: function () {
        this._super.apply(this, arguments);
        console.log('[LogspaceResultsView] Widget starting...');
        // Initialize elements after the DOM is ready
        this.gridView = this.el.querySelector('#grid-view');
        this.listView = this.el.querySelector('#list-view');
        this.gridBtn = this.el.querySelector('.js-view-grid');
        this.listBtn = this.el.querySelector('.js-view-list');
        console.log('[LogspaceResultsView] Elements found:', {
            gridView: !!this.gridView,
            listView: !!this.listView,
            gridBtn: !!this.gridBtn,
            listBtn: !!this.listBtn
        });
        return Promise.resolve();
    },

    _onViewGrid: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        console.log('[LogspaceResultsView] Grid button clicked');
        if (this.gridView && this.listView && this.gridBtn && this.listBtn) {
            this.gridView.classList.remove('d-none');
            this.listView.classList.add('d-none');
            this.gridBtn.classList.add('active');
            this.listBtn.classList.remove('active');
            console.log('[LogspaceResultsView] Switched to grid view');
        } else {
            console.warn('[LogspaceResultsView] Elements not found, cannot switch view');
        }
    },

    _onViewList: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        console.log('[LogspaceResultsView] List button clicked');
        if (this.gridView && this.listView && this.gridBtn && this.listBtn) {
            this.gridView.classList.add('d-none');
            this.listView.classList.remove('d-none');
            this.gridBtn.classList.remove('active');
            this.listBtn.classList.add('active');
            console.log('[LogspaceResultsView] Switched to list view');
        } else {
            console.warn('[LogspaceResultsView] Elements not found, cannot switch view');
        }
    },
});

export default {
    LogspaceMockup2: publicWidget.registry.LogspaceMockup2,
    LogspacePortalSidebar: publicWidget.registry.LogspacePortalSidebar,
    LogspaceSearch: publicWidget.registry.LogspaceSearch,
    LogspaceResultsView: publicWidget.registry.LogspaceResultsView,
};
