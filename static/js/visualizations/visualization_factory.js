/**
 * Magellan EV Tracker v2.0
 * Visualization Factory
 * 
 * This module creates and manages visualization components.
 */

const VisualizationFactory = (function() {
    // Private variables
    const visualizations = {};
    let config = {
        debug: false
    };
    
    // Private methods
    function createVisualization(type, element, options) {
        switch (type.toLowerCase()) {
            case 'donut':
                return DonutChart.create(element, options);
            case 'histogram':
                return ProgressHistogram.create(element, options);
            case 'scurve':
                return SCurve.create(element, options);
            case 'quantity':
                return QuantityDistribution.create(element, options);
            case 'spi':
                return SPIChart.create(element, options);
            default:
                if (config.debug) {
                    console.warn(`Unknown visualization type: ${type}`);
                }
                return null;
        }
    }
    
    // Public API
    return {
        init: function(options = {}) {
            // Merge options with default config
            config = { ...config, ...options };
            return this;
        },
        
        /**
         * Create a visualization component
         * @param {string} type - Visualization type
         * @param {HTMLElement} element - DOM element to render in
         * @param {Object} options - Visualization options
         * @returns {Object} Visualization instance
         */
        create: function(type, element, options = {}) {
            if (!element) {
                console.error('Element is required to create a visualization');
                return null;
            }
            
            const id = options.id || `${type}-${Date.now()}`;
            
            // Create the visualization
            const visualization = createVisualization(type, element, options);
            
            if (visualization) {
                // Store the visualization
                visualizations[id] = visualization;
                
                // Initialize the visualization
                visualization.init();
                
                if (config.debug) {
                    console.log(`Created ${type} visualization with ID ${id}`);
                }
            }
            
            return visualization;
        },
        
        /**
         * Get a visualization by ID
         * @param {string} id - Visualization ID
         * @returns {Object} Visualization instance
         */
        get: function(id) {
            return visualizations[id] || null;
        },
        
        /**
         * Remove a visualization
         * @param {string} id - Visualization ID
         */
        remove: function(id) {
            if (visualizations[id]) {
                visualizations[id].destroy();
                delete visualizations[id];
                
                if (config.debug) {
                    console.log(`Removed visualization with ID ${id}`);
                }
            }
        },
        
        /**
         * Initialize all visualizations in a container
         * @param {HTMLElement} container - Container element
         * @param {Object} options - Default options for all visualizations
         */
        initAll: function(container, options = {}) {
            if (!container) {
                console.error('Container is required to initialize visualizations');
                return;
            }
            
            const elements = container.querySelectorAll('[data-visualization-type]');
            
            elements.forEach(element => {
                const type = element.getAttribute('data-visualization-type');
                const id = element.getAttribute('data-visualization-id') || `${type}-${Date.now()}`;
                
                // Get element-specific options
                const elementOptions = {
                    ...options,
                    id: id
                };
                
                // Create the visualization
                this.create(type, element, elementOptions);
            });
            
            if (config.debug) {
                console.log(`Initialized ${elements.length} visualizations`);
            }
        }
    };
})();
