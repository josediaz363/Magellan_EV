/**
 * Magellan EV Tracker v2.0
 * API Client module
 */

const ApiClient = (function() {
    // Private variables
    let config = {
        basePath: '/api',
        defaultHeaders: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    };
    
    // Private methods
    async function fetchJSON(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...config.defaultHeaders,
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`API request failed: ${response.status} ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request error:', error);
            throw error;
        }
    }
    
    function buildUrl(endpoint) {
        // Ensure endpoint starts with a slash
        if (!endpoint.startsWith('/')) {
            endpoint = '/' + endpoint;
        }
        
        return `${config.basePath}${endpoint}`;
    }
    
    // Public API
    return {
        init: function(options = {}) {
            // Merge options with default config
            config = { ...config, ...options };
            return this;
        },
        
        // Visualization data endpoints
        getVisualizationData: function(type, projectId) {
            return fetchJSON(buildUrl(`/visualizations/${type}/${projectId}`));
        },
        
        // Existing API endpoints
        getSubJobs: function(projectId) {
            return fetchJSON(buildUrl(`/get_subjobs/${projectId}`));
        },
        
        getCostCodes: function(projectId) {
            return fetchJSON(buildUrl(`/get_cost_codes/${projectId}`));
        },
        
        getRuleSteps: function(ruleId) {
            return fetchJSON(buildUrl(`/get_rule_steps/${ruleId}`));
        },
        
        // Generic methods
        get: function(endpoint) {
            return fetchJSON(buildUrl(endpoint));
        },
        
        post: function(endpoint, data) {
            return fetchJSON(buildUrl(endpoint), {
                method: 'POST',
                body: JSON.stringify(data)
            });
        },
        
        put: function(endpoint, data) {
            return fetchJSON(buildUrl(endpoint), {
                method: 'PUT',
                body: JSON.stringify(data)
            });
        },
        
        delete: function(endpoint) {
            return fetchJSON(buildUrl(endpoint), {
                method: 'DELETE'
            });
        }
    };
})();
