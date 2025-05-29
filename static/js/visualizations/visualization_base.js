/**
 * Magellan EV Tracker v2.0
 * Visualization Base Component
 * 
 * This is the base component for all visualizations.
 */

const VisualizationBase = (function() {
    // Base visualization constructor
    function BaseVisualization(element, options = {}) {
        // Store element and create container
        this.element = element;
        this.container = element;
        this.options = options;
        this.data = null;
        
        // Initialize the visualization
        this.init = function() {
            // Create loading and error elements
            this._createHelperElements();
            
            // Load data if project ID is provided
            if (this.options.projectId) {
                this.loadData(this.options.projectId);
            }
            
            // Add event listeners
            this._addEventListeners();
            
            return this;
        };
        
        // Create helper elements for loading and error states
        this._createHelperElements = function() {
            // Create loading element
            this.loadingElement = document.createElement('div');
            this.loadingElement.className = 'visualization-loading';
            this.loadingElement.textContent = 'Loading...';
            this.loadingElement.style.display = 'none';
            this.container.appendChild(this.loadingElement);
            
            // Create error element
            this.errorElement = document.createElement('div');
            this.errorElement.className = 'visualization-error';
            this.errorElement.style.display = 'none';
            this.container.appendChild(this.errorElement);
            
            return this;
        };
        
        // Add event listeners
        this._addEventListeners = function() {
            // Listen for project selection changes
            const projectSelector = document.getElementById('project-selector');
            if (projectSelector) {
                projectSelector.addEventListener('change', (event) => {
                    const projectId = event.target.value;
                    if (projectId) {
                        this.loadData(projectId);
                    } else {
                        this.clear();
                    }
                });
            }
            
            // Listen for window resize
            window.addEventListener('resize', () => {
                this.resize();
            });
            
            return this;
        };
        
        // Show loading state
        this._showLoading = function() {
            this.loadingElement.style.display = 'flex';
            this.errorElement.style.display = 'none';
            return this;
        };
        
        // Hide loading state
        this._hideLoading = function() {
            this.loadingElement.style.display = 'none';
            return this;
        };
        
        // Show error message
        this._showError = function(message) {
            this.errorElement.textContent = message;
            this.errorElement.style.display = 'flex';
            this.loadingElement.style.display = 'none';
            return this;
        };
        
        // Load data - to be overridden by child classes
        this.loadData = function(projectId) {
            this._showLoading();
            // This method should be overridden by child classes
            console.warn('loadData method not implemented');
            this._hideLoading();
            return Promise.resolve(null);
        };
        
        // Render visualization - to be overridden by child classes
        this.render = function() {
            // This method should be overridden by child classes
            console.warn('render method not implemented');
            return this;
        };
        
        // Resize visualization - to be overridden by child classes
        this.resize = function() {
            // This method should be overridden by child classes
            return this;
        };
        
        // Clear visualization
        this.clear = function() {
            this.container.innerHTML = '';
            this._createHelperElements();
            return this;
        };
        
        // Destroy visualization
        this.destroy = function() {
            // Remove event listeners
            window.removeEventListener('resize', this.resize);
            
            // Clear container
            this.container.innerHTML = '';
            
            return this;
        };
        
        return this;
    }
    
    // Factory function to create new instances
    return {
        create: function(element, options) {
            return new BaseVisualization(element, options);
        }
    };
})();
