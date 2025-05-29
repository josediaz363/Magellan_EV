/**
 * Magellan EV Tracker v2.0
 * Visualization Base Component - Enhanced Debug Version
 * 
 * This is the base component for all visualizations with enhanced debugging.
 */

const VisualizationBase = (function() {
    // Base visualization constructor
    function BaseVisualization(element, options = {}) {
        // Store element and create container
        this.element = element;
        this.container = element;
        this.options = options;
        this.data = null;
        
        // Debug mode
        this.debug = options.debug || true;
        
        // Log function for debugging
        this.log = function(message, data) {
            if (this.debug) {
                console.log(`[Visualization] ${message}`, data || '');
            }
        };
        
        // Initialize the visualization
        this.init = function() {
            this.log('Initializing visualization', this.options);
            
            // Create loading and error elements
            this._createHelperElements();
            
            // Load data if project ID is provided
            if (this.options.projectId) {
                this.log('Project ID provided, loading data', this.options.projectId);
                this.loadData(this.options.projectId);
            } else {
                this.log('No project ID provided, skipping data load');
            }
            
            // Add event listeners
            this._addEventListeners();
            
            return this;
        };
        
        // Create helper elements for loading and error states
        this._createHelperElements = function() {
            this.log('Creating helper elements');
            
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
            this.log('Adding event listeners');
            
            // Listen for project selection changes
            const projectSelector = document.getElementById('project-selector');
            if (projectSelector) {
                this.log('Project selector found, adding change listener');
                projectSelector.addEventListener('change', (event) => {
                    const projectId = event.target.value;
                    this.log('Project selection changed', projectId);
                    if (projectId) {
                        this.loadData(projectId);
                    } else {
                        this.clear();
                    }
                });
            } else {
                this.log('Project selector not found');
            }
            
            // Listen for window resize
            window.addEventListener('resize', () => {
                this.log('Window resized, updating visualization');
                this.resize();
            });
            
            // Listen for visualization update events
            document.addEventListener('visualization:update', (event) => {
                const projectId = event.detail.projectId;
                this.log('Visualization update event received', projectId);
                if (projectId) {
                    this.loadData(projectId);
                }
            });
            
            return this;
        };
        
        // Show loading state
        this._showLoading = function() {
            this.log('Showing loading state');
            this.loadingElement.style.display = 'flex';
            this.errorElement.style.display = 'none';
            return this;
        };
        
        // Hide loading state
        this._hideLoading = function() {
            this.log('Hiding loading state');
            this.loadingElement.style.display = 'none';
            return this;
        };
        
        // Show error message
        this._showError = function(message) {
            this.log('Showing error', message);
            this.errorElement.textContent = message;
            this.errorElement.style.display = 'flex';
            this.loadingElement.style.display = 'none';
            return this;
        };
        
        // Load data - to be overridden by child classes
        this.loadData = function(projectId) {
            this.log('Base loadData called, should be overridden', projectId);
            this._showLoading();
            // This method should be overridden by child classes
            console.warn('loadData method not implemented');
            this._hideLoading();
            return Promise.resolve(null);
        };
        
        // Render visualization - to be overridden by child classes
        this.render = function() {
            this.log('Base render called, should be overridden');
            // This method should be overridden by child classes
            console.warn('render method not implemented');
            return this;
        };
        
        // Resize visualization - to be overridden by child classes
        this.resize = function() {
            this.log('Base resize called, should be overridden');
            // This method should be overridden by child classes
            return this;
        };
        
        // Clear visualization
        this.clear = function() {
            this.log('Clearing visualization');
            this.container.innerHTML = '';
            this._createHelperElements();
            return this;
        };
        
        // Destroy visualization
        this.destroy = function() {
            this.log('Destroying visualization');
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
            console.log('[VisualizationBase] Creating new visualization', options);
            return new BaseVisualization(element, options);
        }
    };
})();
