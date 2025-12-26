/**
 * Form State Persistence Module
 *
 * Automatically saves and restores form data across page refreshes and tab switches
 * using browser sessionStorage. This ensures users don't lose their work when
 * navigating between different retirement phase tabs.
 */

(function() {
    'use strict';

    const FormPersistence = {
        // Storage key prefix
        STORAGE_PREFIX: 'retirementForm_',

        // Time to keep data in sessionStorage (24 hours in milliseconds)
        MAX_AGE: 24 * 60 * 60 * 1000,

        /**
         * Initialize form persistence for all forms with data-persist attribute
         */
        init: function() {
            const userId = this.getUserId();
            const forms = document.querySelectorAll('form[data-persist]');

            forms.forEach(form => {
                const formId = form.id || form.getAttribute('data-persist');
                if (!formId) {
                    console.warn('Form has data-persist but no id:', form);
                    return;
                }

                // Restore saved data on page load
                this.restoreFormData(form, formId, userId);

                // Save data on input change
                this.attachSaveHandlers(form, formId, userId);
            });

            // Clean up old data
            this.cleanupOldData();
        },

        /**
         * Get the current user ID from data attribute or use 'anonymous'
         */
        getUserId: function() {
            const userIdElement = document.querySelector('[data-user-id]');
            return userIdElement ? userIdElement.getAttribute('data-user-id') : 'anonymous';
        },

        /**
         * Generate storage key with user ID for security
         */
        getStorageKey: function(formId, userId) {
            return `${this.STORAGE_PREFIX}${userId}_${formId}`;
        },

        /**
         * Restore form data from sessionStorage
         */
        restoreFormData: function(form, formId, userId) {
            const key = this.getStorageKey(formId, userId);
            const savedData = sessionStorage.getItem(key);

            if (!savedData) return;

            try {
                const data = JSON.parse(savedData);

                // Check if data is too old
                if (data.timestamp && (Date.now() - data.timestamp > this.MAX_AGE)) {
                    sessionStorage.removeItem(key);
                    return;
                }

                // Restore form values
                if (data.values) {
                    Object.keys(data.values).forEach(name => {
                        const input = form.querySelector(`[name="${name}"]`);
                        if (input) {
                            if (input.type === 'checkbox' || input.type === 'radio') {
                                input.checked = data.values[name];
                            } else {
                                input.value = data.values[name];
                            }
                        }
                    });
                }
            } catch (e) {
                console.error('Error restoring form data:', e);
                sessionStorage.removeItem(key);
            }
        },

        /**
         * Attach event handlers to save form data on change
         */
        attachSaveHandlers: function(form, formId, userId) {
            const inputs = form.querySelectorAll('input, select, textarea');

            inputs.forEach(input => {
                // Save on input change with debouncing
                input.addEventListener('input', () => {
                    this.debouncedSave(form, formId, userId);
                });

                // Also save on change for selects and checkboxes
                input.addEventListener('change', () => {
                    this.saveFormData(form, formId, userId);
                });
            });
        },

        /**
         * Save form data to sessionStorage
         */
        saveFormData: function(form, formId, userId) {
            const key = this.getStorageKey(formId, userId);
            const formData = new FormData(form);
            const values = {};

            // Collect all form values
            for (let [name, value] of formData.entries()) {
                values[name] = value;
            }

            // Also handle checkboxes (which don't appear in FormData if unchecked)
            const checkboxes = form.querySelectorAll('input[type="checkbox"]');
            checkboxes.forEach(cb => {
                values[cb.name] = cb.checked;
            });

            const data = {
                values: values,
                timestamp: Date.now()
            };

            try {
                sessionStorage.setItem(key, JSON.stringify(data));
            } catch (e) {
                console.error('Error saving form data:', e);
                // SessionStorage might be full - try clearing old data
                this.cleanupOldData();
            }
        },

        /**
         * Debounced save to avoid excessive writes
         */
        debouncedSave: (function() {
            let timeout;
            return function(form, formId, userId) {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.saveFormData(form, formId, userId);
                }, 500); // Wait 500ms after last input
            };
        })(),

        /**
         * Clear saved data for a specific form
         */
        clearFormData: function(formId, userId) {
            const key = this.getStorageKey(formId, userId);
            sessionStorage.removeItem(key);
        },

        /**
         * Clear all saved form data for current user
         */
        clearAllFormData: function() {
            const userId = this.getUserId();
            const prefix = `${this.STORAGE_PREFIX}${userId}_`;

            // Find and remove all keys matching this user's prefix
            for (let i = sessionStorage.length - 1; i >= 0; i--) {
                const key = sessionStorage.key(i);
                if (key && key.startsWith(prefix)) {
                    sessionStorage.removeItem(key);
                }
            }
        },

        /**
         * Clean up old data from sessionStorage
         */
        cleanupOldData: function() {
            const now = Date.now();

            for (let i = sessionStorage.length - 1; i >= 0; i--) {
                const key = sessionStorage.key(i);
                if (key && key.startsWith(this.STORAGE_PREFIX)) {
                    try {
                        const data = JSON.parse(sessionStorage.getItem(key));
                        if (data.timestamp && (now - data.timestamp > this.MAX_AGE)) {
                            sessionStorage.removeItem(key);
                        }
                    } catch (e) {
                        // Invalid JSON, remove it
                        sessionStorage.removeItem(key);
                    }
                }
            }
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => FormPersistence.init());
    } else {
        FormPersistence.init();
    }

    // Expose globally for manual clearing
    window.FormPersistence = FormPersistence;

})();
