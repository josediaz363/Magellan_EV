/**
 * Magellan EV Tracker v2.0
 * Core application module
 */

const App = (function() {
    // Private variables
    let config = {
        debug: false,
        apiBasePath: '/api'
    };
    
    let state = {
        currentProject: null,
        currentSubJob: null,
        visualizationsLoaded: false
    };
    
    // Private methods
    function initEventListeners() {
        // Project selector
        const projectSelector = document.getElementById('project-selector');
        if (projectSelector) {
            projectSelector.addEventListener('change', function() {
                const projectId = this.value;
                if (projectId) {
                    state.currentProject = projectId;
                    loadProjectData(projectId);
                }
            });
        }
        
        // Initialize delete confirmation dialogs
        initDeleteConfirmations();
    }
    
    function initDeleteConfirmations() {
        // This functionality will be moved to a separate module in the future
        const deleteButtons = document.querySelectorAll('[data-delete-target]');
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const target = this.getAttribute('data-delete-target');
                const confirmMessage = this.getAttribute('data-confirm-message') || 'Are you sure you want to delete this item?';
                
                if (confirm(confirmMessage)) {
                    document.getElementById(target).submit();
                }
            });
        });
    }
    
    function loadProjectData(projectId) {
        if (!projectId) return;
        
        // Load project metrics
        updateProjectMetrics(projectId);
        
        // Load visualizations if they exist
        if (state.visualizationsLoaded) {
            updateVisualizations(projectId);
        } else {
            loadVisualizations(projectId);
        }
    }
    
    function updateProjectMetrics(projectId) {
        // This will be implemented to update metrics cards
        if (config.debug) console.log(`Updating metrics for project ${projectId}`);
    }
    
    function loadVisualizations(projectId) {
        // This will be implemented to load visualizations
        if (config.debug) console.log(`Loading visualizations for project ${projectId}`);
        
        // Check if visualization container exists
        const container = document.getElementById('visualization-container');
        if (!container) return;
        
        // Initialize visualizations based on data-type attributes
        const visualizationElements = container.querySelectorAll('[data-visualization-type]');
        visualizationElements.forEach(element => {
            const type = element.getAttribute('data-visualization-type');
            initVisualization(element, type, projectId);
        });
        
        state.visualizationsLoaded = true;
    }
    
    function updateVisualizations(projectId) {
        // This will be implemented to update existing visualizations
        if (config.debug) console.log(`Updating visualizations for project ${projectId}`);
        
        // Dispatch update event for visualizations
        const event = new CustomEvent('visualization:update', { 
            detail: { projectId: projectId } 
        });
        document.dispatchEvent(event);
    }
    
    function initVisualization(element, type, projectId) {
        // Initialize specific visualization types
        if (config.debug) console.log(`Initializing ${type} visualization`);
        
        switch (type) {
            case 'donut':
                // Initialize donut chart
                if (typeof DonutChart !== 'undefined') {
                    DonutChart.create(element, {
                        projectId: projectId,
                        size: 200,
                        thickness: 30,
                        colors: {
                            primary: '#4e73df',
                            secondary: '#eaecf4',
                            text: '#5a5c69'
                        }
                    }).loadData(projectId);
                } else {
                    console.error('DonutChart module not loaded');
                }
                break;
            case 'histogram':
                // Will be implemented when VisualizationFactory is created
                break;
            case 'scurve':
                // Will be implemented when VisualizationFactory is created
                break;
            case 'quantity':
                // Will be implemented when VisualizationFactory is created
                break;
            case 'spi':
                // Will be implemented when VisualizationFactory is created
                break;
            default:
                console.warn(`Unknown visualization type: ${type}`);
        }
    }
    
    // Public API
    return {
        init: function(options = {}) {
            // Merge options with default config
            config = { ...config, ...options };
            
            if (config.debug) console.log('Initializing Magellan EV Tracker App');
            
            // Initialize event listeners
            initEventListeners();
            
            // Check if we have a pre-selected project
            const projectSelector = document.getElementById('project-selector');
            if (projectSelector && projectSelector.value) {
                state.currentProject = projectSelector.value;
                loadProjectData(state.currentProject);
            }
            
            return this;
        },
        
        setDebug: function(debug) {
            config.debug = debug;
            return this;
        },
        
        getCurrentProject: function() {
            return state.currentProject;
        }
    };
})();
