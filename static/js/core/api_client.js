/**
 * Magellan EV Tracker v2.0
 * API Client Module
 * 
 * This module handles all API requests to the backend.
 */

const ApiClient = (function() {
    // Private variables
    let config = {
        baseUrl: '',
        debug: false
    };
    
    // Private methods
    function handleResponse(response) {
        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }
        return response.json();
    }
    
    function logRequest(endpoint, method, data) {
        if (config.debug) {
            console.log(`API ${method} request to ${endpoint}`, data || '');
        }
    }
    
    function logResponse(endpoint, data) {
        if (config.debug) {
            console.log(`API response from ${endpoint}`, data);
        }
    }
    
    // Public API
    return {
        init: function(options = {}) {
            // Merge options with default config
            config = { ...config, ...options };
            
            // Set base URL if not provided
            if (!config.baseUrl) {
                config.baseUrl = window.location.origin;
            }
            
            if (config.debug) {
                console.log('API Client initialized with config:', config);
            }
            
            return this;
        },
        
        /**
         * Get data for a visualization
         * @param {string} type - Visualization type (donut, histogram, etc.)
         * @param {number} projectId - Project ID
         * @returns {Promise} Promise resolving to visualization data
         */
        getVisualizationData: function(type, projectId) {
            if (!projectId) {
                return Promise.resolve({
                    success: false,
                    error: 'No project selected',
                    data: {
                        percentage: 0,
                        earned: 0,
                        budgeted: 0
                    }
                });
            }
            
            const endpoint = `/api/visualizations/${type}/${projectId}`;
            logRequest(endpoint, 'GET');
            
            return fetch(endpoint)
                .then(handleResponse)
                .then(data => {
                    logResponse(endpoint, data);
                    return data;
                })
                .catch(error => {
                    console.error(`Error fetching ${type} data:`, error);
                    // Return default data structure to prevent UI errors
                    return {
                        success: false,
                        error: error.message,
                        data: {
                            percentage: 0,
                            earned: 0,
                            budgeted: 0
                        }
                    };
                });
        },
        
        /**
         * Get sub jobs for a project
         * @param {number} projectId - Project ID
         * @returns {Promise} Promise resolving to sub jobs array
         */
        getSubJobs: function(projectId) {
            const endpoint = `/api/get_subjobs/${projectId}`;
            logRequest(endpoint, 'GET');
            
            return fetch(endpoint)
                .then(handleResponse)
                .then(data => {
                    logResponse(endpoint, data);
                    return data;
                })
                .catch(error => {
                    console.error('Error fetching sub jobs:', error);
                    return [];
                });
        },
        
        /**
         * Get cost codes for a project
         * @param {number} projectId - Project ID
         * @returns {Promise} Promise resolving to cost codes array
         */
        getCostCodes: function(projectId) {
            const endpoint = `/api/get_cost_codes/${projectId}`;
            logRequest(endpoint, 'GET');
            
            return fetch(endpoint)
                .then(handleResponse)
                .then(data => {
                    logResponse(endpoint, data);
                    return data;
                })
                .catch(error => {
                    console.error('Error fetching cost codes:', error);
                    return [];
                });
        },
        
        /**
         * Get steps for a rule of credit
         * @param {number} ruleId - Rule of Credit ID
         * @returns {Promise} Promise resolving to steps array
         */
        getRuleSteps: function(ruleId) {
            const endpoint = `/api/get_rule_steps/${ruleId}`;
            logRequest(endpoint, 'GET');
            
            return fetch(endpoint)
                .then(handleResponse)
                .then(data => {
                    logResponse(endpoint, data);
                    return data;
                })
                .catch(error => {
                    console.error('Error fetching rule steps:', error);
                    return [];
                });
        },
        
        /**
         * Update work item progress
         * @param {number} workItemId - Work Item ID
         * @param {string} stepName - Step name
         * @param {number} completionPercentage - Completion percentage
         * @returns {Promise} Promise resolving to update result
         */
        updateWorkItemProgress: function(workItemId, stepName, completionPercentage) {
            const endpoint = `/update_work_item_progress/${workItemId}`;
            const data = {
                step_name: stepName,
                completion_percentage: completionPercentage
            };
            
            logRequest(endpoint, 'POST', data);
            
            return fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            })
                .then(handleResponse)
                .then(data => {
                    logResponse(endpoint, data);
                    return data;
                })
                .catch(error => {
                    console.error('Error updating work item progress:', error);
                    return {
                        success: false,
                        error: error.message
                    };
                });
        }
    };
})();
