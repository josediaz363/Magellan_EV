/**
 * Magellan EV Tracker v2.0
 * Base Visualization Component
 * 
 * This is the base class for all visualization components.
 * It provides common functionality for data loading, rendering, and responsiveness.
 */

const VisualizationBase = (function() {
    // Private constructor function
    function Visualization(element, options = {}) {
        this.element = element;
        this.options = {
            responsive: true,
            projectId: null,
            ...options
        };
        this.data = null;
        this.isLoading = false;
        this.error = null;
        this.initialized = false;
    }
    
    // Prototype methods
    Visualization.prototype = {
        /**
         * Initialize the visualization
         * @returns {Visualization} this instance for chaining
         */
        init: function() {
            if (this.initialized) return this;
            
            // Create container elements
            this._createElements();
            
            // Set up event listeners
            this._setupEventListeners();
            
            // Mark as initialized
            this.initialized = true;
            
            // Load data if project ID is provided
            if (this.options.projectId) {
                this.loadData(this.options.projectId);
            }
            
            return this;
        },
        
        /**
         * Create container elements
         * @private
         */
        _createElements: function() {
            // Create loading indicator
            this.loadingElement = document.createElement('div');
            this.loadingElement.className = 'visualization-loading';
            this.loadingElement.textContent = 'Loading...';
            this.loadingElement.style.display = 'none';
            
            // Create error message element
            this.errorElement = document.createElement('div');
            this.errorElement.className = 'visualization-error';
            this.errorElement.style.display = 'none';
            
            // Create container for the actual visualization
            this.container = document.createElement('div');
            this.container.className = 'visualization-container';
            
            // Append elements to the main element
            this.element.appendChild(this.loadingElement);
            this.element.appendChild(this.errorElement);
            this.element.appendChild(this.container);
        },
        
        /**
         * Set up event listeners
         * @private
         */
        _setupEventListeners: function() {
            // Listen for project changes
            document.addEventListener('visualization:update', (event) => {
                if (event.detail && event.detail.projectId) {
                    this.loadData(event.detail.projectId);
                }
            });
            
            // Listen for window resize events if responsive
            if (this.options.responsive) {
                window.addEventListener('resize', this._debounce(() => {
                    this.resize();
                }, 250));
            }
        },
        
        /**
         * Debounce function to limit the rate at which a function can fire
         * @private
         */
        _debounce: function(func, wait) {
            let timeout;
            return function() {
                const context = this;
                const args = arguments;
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    func.apply(context, args);
                }, wait);
            };
        },
        
        /**
         * Load data for the visualization
         * @param {number|string} projectId - Project ID
         * @returns {Promise} Promise that resolves when data is loaded
         */
        loadData: function(projectId) {
            // Show loading indicator
            this._showLoading();
            
            // Store project ID
            this.options.projectId = projectId;
            
            // This method should be overridden by subclasses
            console.warn('loadData method not implemented');
            
            // Hide loading indicator
            this._hideLoading();
            
            return Promise.resolve(null);
        },
        
        /**
         * Render the visualization
         * @returns {Visualization} this instance for chaining
         */
        render: function() {
            // This method should be overridden by subclasses
            console.warn('render method not implemented');
            return this;
        },
        
        /**
         * Update the visualization with new data
         * @param {Object} data - New data
         * @returns {Visualization} this instance for chaining
         */
        update: function(data) {
            this.data = data;
            return this.render();
        },
        
        /**
         * Resize the visualization
         * @returns {Visualization} this instance for chaining
         */
        resize: function() {
            // This method should be overridden by subclasses
            console.warn('resize method not implemented');
            return this;
        },
        
        /**
         * Show loading indicator
         * @private
         */
        _showLoading: function() {
            this.isLoading = true;
            this.loadingElement.style.display = 'block';
            this.errorElement.style.display = 'none';
        },
        
        /**
         * Hide loading indicator
         * @private
         */
        _hideLoading: function() {
            this.isLoading = false;
            this.loadingElement.style.display = 'none';
        },
        
        /**
         * Show error message
         * @param {string} message - Error message
         * @private
         */
        _showError: function(message) {
            this.error = message;
            this.errorElement.textContent = message;
            this.errorElement.style.display = 'block';
            this._hideLoading();
        },
        
        /**
         * Destroy the visualization and clean up resources
         */
        destroy: function() {
            // Remove event listeners
            window.removeEventListener('resize', this.resize);
            
            // Clear the element
            this.element.innerHTML = '';
            
            // Reset properties
            this.data = null;
            this.isLoading = false;
            this.error = null;
            this.initialized = false;
        }
    };
    
    // Factory function to create new instances
    return {
        create: function(element, options) {
            return new Visualization(element, options);
        }
    };
})();
