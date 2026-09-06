/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.Logspace = publicWidget.Widget.extend({
    selector: '.logspace-page, .logspace-rate-page',
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
        this._initStarRatings();
        return Promise.resolve();
    },

    /**
     * Initialize stepper animation
     */
    _initStepper: function () {
        const stepper = document.querySelector('.logspace-stepper');
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
     * Initialize star ratings - fill stars based on current rating value
     */
    _initStarRatings: function () {
        const containers = document.querySelectorAll('.rating-stars');
        containers.forEach(container => {
            const currentRating = parseInt(container.getAttribute('data-current-rating') || '0', 10);
            if (currentRating > 0) {
                const hiddenInput = container.querySelector('input[name="overall_rating"]');
                if (hiddenInput) {
                    hiddenInput.value = currentRating;
                }
                const stars = container.querySelectorAll('.js-star-rating');
                stars.forEach(star => {
                    const starValue = parseInt(star.getAttribute('data-rating'), 10);
                    if (starValue <= currentRating) {
                        star.classList.remove('fa-star-o');
                        star.classList.add('fa-star');
                    } else {
                        star.classList.remove('fa-star');
                        star.classList.add('fa-star-o');
                    }
                });
            }
        });
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
            const ratingInput = container.querySelector('input[name="overall_rating"]');
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

/**
 * Offline Autocomplete for Zone Fields
 */
publicWidget.registry.LogspaceZoneAutocomplete = publicWidget.Widget.extend({
    selector: '.zone-autocomplete-wrapper',
    events: {
        'input .zone-autocomplete-input': '_onInput',
        'focus .zone-autocomplete-input': '_onFocus',
        'keydown .zone-autocomplete-input': '_onKeyDown',
        'click .autocomplete-item': '_onItemClick',
    },

    start: function () {
        this._super.apply(this, arguments);

        // Find inputs
        this.input = this.el.querySelector('.zone-autocomplete-input');
        this.hiddenId = this.el.querySelector('input[type="hidden"][name^="zone_"]');
        this.hiddenText = this.el.querySelector('input[type="hidden"][name$="_address_text"]');

        if (!this.input) return Promise.resolve();

        // Create dropdown element and append to body for proper z-index stacking
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'zone-autocomplete-dropdown d-none';
        document.body.appendChild(this.dropdown);

        this.activeIndex = -1;
        this.suggestions = [];
        this.zones = [];

        // Parse zones data if not already done
        const zonesDataEl = document.getElementById('logspace-zones-data');
        try {
            this.zones = zonesDataEl ? JSON.parse(zonesDataEl.textContent || '[]') : [];
        } catch (e) {
            console.error("Failed to parse logspace zones JSON data", e);
            this.zones = [];
        }

        // Handle click outside to close dropdown
        this._onDocumentClick = this._onDocumentClick.bind(this);
        document.addEventListener('click', this._onDocumentClick);

        // Handle scroll to reposition dropdown
        this._repositionDropdown = this._repositionDropdown.bind(this);
        window.addEventListener('scroll', this._repositionDropdown, true);

        // Bind click handler directly on dropdown since it's on body (outside widget's event delegation)
        this._onDropdownClick = this._onDropdownClick.bind(this);
        this.dropdown.addEventListener('click', this._onDropdownClick);

        return Promise.resolve();
    },

    destroy: function () {
        document.removeEventListener('click', this._onDocumentClick);
        window.removeEventListener('scroll', this._repositionDropdown, true);
        if (this.dropdown && this.dropdown.parentNode) {
            this.dropdown.parentNode.removeChild(this.dropdown);
        }
        this._super.apply(this, arguments);
    },

    _onInput: function (ev) {
        const query = this.input.value.trim().toLowerCase();

        // If query is empty, clear hidden fields and close dropdown
        if (!query) {
            if (this.hiddenId) this.hiddenId.value = '';
            if (this.hiddenText) this.hiddenText.value = '';
            this._closeDropdown();
            return;
        }

        // Filter zones client-side by name or full hierarchical address
        const matchedZones = this.zones.filter(zone => {
            return (zone.full_address && zone.full_address.toLowerCase().includes(query)) ||
                   (zone.name && zone.name.toLowerCase().includes(query));
        });

        this.suggestions = matchedZones.slice(0, 8); // limit to 8 results
        this.activeIndex = -1;
        this._renderDropdown();
    },

    _onFocus: function (ev) {
        const query = this.input.value.trim().toLowerCase();
        if (query) {
            this._onInput(ev);
        }
    },

    _renderDropdown: function () {
        if (this.suggestions.length === 0) {
            this.dropdown.innerHTML = '<div class="autocomplete-no-results p-2 text-muted small">No matches found</div>';
            this.dropdown.classList.remove('d-none');
            return;
        }

        let html = '';
        this.suggestions.forEach((zone, index) => {
            const isActive = index === this.activeIndex ? 'active' : '';
            const query = this.input.value.trim();
            let displayAddress = zone.full_address;
            
            if (query) {
                const regex = new RegExp(`(${this._escapeRegExp(query)})`, 'gi');
                displayAddress = zone.full_address.replace(regex, '<span class="highlight">$1</span>');
            }

            const zoneTypeLabel = zone.zone_type ? zone.zone_type.toUpperCase() : 'ZONE';

            html += `
                <div class="autocomplete-item ${isActive} d-flex align-items-center p-2" data-index="${index}">
                    <i class="fa fa-map-marker text-muted me-2"></i>
                    <div class="address-text-wrapper flex-grow-1">
                        <span class="address-main text-dark font-weight-bold">${displayAddress}</span>
                    </div>
                    <span class="badge bg-light text-secondary small ms-2">${zoneTypeLabel}</span>
                </div>
            `;
        });

        this.dropdown.innerHTML = html;
        this.dropdown.classList.remove('d-none');
        this._repositionDropdown();
    },

    _selectSuggestion: function (index) {
        if (index >= 0 && index < this.suggestions.length) {
            const suggestion = this.suggestions[index];
            this.input.value = suggestion.full_address;
            if (this.hiddenId) this.hiddenId.value = suggestion.id;
            if (this.hiddenText) this.hiddenText.value = suggestion.full_address;
            this._closeDropdown();
        }
    },

    _closeDropdown: function () {
        this.dropdown.classList.add('d-none');
        this.activeIndex = -1;
    },

    _repositionDropdown: function () {
        if (this.dropdown.classList.contains('d-none') || !this.input) return;
        const rect = this.input.getBoundingClientRect();
        this.dropdown.style.left = rect.left + 'px';
        this.dropdown.style.top = rect.bottom + 'px';
        this.dropdown.style.width = rect.width + 'px';
    },

    _onDropdownClick: function (ev) {
        const item = ev.target.closest('.autocomplete-item');
        if (!item) return;
        const index = parseInt(item.dataset.index, 10);
        this._selectSuggestion(index);
    },

    _onItemClick: function (ev) {
        const item = ev.currentTarget;
        const index = parseInt(item.dataset.index, 10);
        this._selectSuggestion(index);
    },

    _onDocumentClick: function (ev) {
        if (!this.el.contains(ev.target)) {
            this._closeDropdown();
            // Clear if input text doesn't match a selected zone
            if (this.hiddenId && !this.hiddenId.value) {
                this.input.value = '';
                if (this.hiddenText) this.hiddenText.value = '';
            }
        }
    },

    _onKeyDown: function (ev) {
        if (this.dropdown.classList.contains('d-none')) {
            if (ev.key === 'ArrowDown') {
                const query = this.input.value.trim();
                if (query) {
                    this._onInput(ev);
                    ev.preventDefault();
                }
            }
            return;
        }

        switch (ev.key) {
            case 'ArrowDown':
                ev.preventDefault();
                this.activeIndex = (this.activeIndex + 1) % this.suggestions.length;
                this._renderDropdown();
                break;
            case 'ArrowUp':
                ev.preventDefault();
                this.activeIndex = (this.activeIndex - 1 + this.suggestions.length) % this.suggestions.length;
                this._renderDropdown();
                break;
            case 'Enter':
                ev.preventDefault();
                if (this.activeIndex >= 0 && this.activeIndex < this.suggestions.length) {
                    this._selectSuggestion(this.activeIndex);
                } else if (this.suggestions.length > 0) {
                    this._selectSuggestion(0);
                }
                break;
            case 'Escape':
                ev.preventDefault();
                this._closeDropdown();
                break;
            case 'Tab':
                if (this.suggestions.length > 0) {
                    if (this.activeIndex === -1) {
                        this._selectSuggestion(0);
                    } else {
                        this._selectSuggestion(this.activeIndex);
                    }
                }
                break;
        }
    },

    _escapeRegExp: function (string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    },
});

export default {
    Logspace: publicWidget.registry.Logspace,
    LogspacePortalSidebar: publicWidget.registry.LogspacePortalSidebar,
    LogspaceSearch: publicWidget.registry.LogspaceSearch,
    LogspaceResultsView: publicWidget.registry.LogspaceResultsView,
    LogspaceZoneAutocomplete: publicWidget.registry.LogspaceZoneAutocomplete,
};
