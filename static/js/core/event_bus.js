/**
 * Magellan EV Tracker v2.0
 * Event Bus module for component communication
 */

const EventBus = (function() {
    // Private variables
    let events = {};
    let config = {
        debug: false
    };
    
    // Public API
    return {
        init: function(options = {}) {
            // Merge options with default config
            config = { ...config, ...options };
            return this;
        },
        
        /**
         * Subscribe to an event
         * @param {string} event - Event name
         * @param {function} callback - Callback function
         * @returns {function} Unsubscribe function
         */
        on: function(event, callback) {
            if (!events[event]) {
                events[event] = [];
            }
            
            events[event].push(callback);
            
            if (config.debug) {
                console.log(`EventBus: Subscribed to ${event}`);
            }
            
            // Return unsubscribe function
            return () => {
                this.off(event, callback);
            };
        },
        
        /**
         * Unsubscribe from an event
         * @param {string} event - Event name
         * @param {function} callback - Callback function
         */
        off: function(event, callback) {
            if (!events[event]) return;
            
            events[event] = events[event].filter(cb => cb !== callback);
            
            if (config.debug) {
                console.log(`EventBus: Unsubscribed from ${event}`);
            }
        },
        
        /**
         * Emit an event
         * @param {string} event - Event name
         * @param {any} data - Event data
         */
        emit: function(event, data) {
            if (!events[event]) return;
            
            if (config.debug) {
                console.log(`EventBus: Emitting ${event}`, data);
            }
            
            events[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event handler for ${event}:`, error);
                }
            });
        },
        
        /**
         * Clear all event subscriptions
         */
        clear: function() {
            events = {};
            
            if (config.debug) {
                console.log('EventBus: Cleared all events');
            }
        }
    };
})();
