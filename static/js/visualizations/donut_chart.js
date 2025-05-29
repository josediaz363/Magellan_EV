/**
 * Magellan EV Tracker v2.0
 * Donut Chart Visualization Component - Enhanced Debug Version
 * 
 * This component renders a donut chart showing overall progress.
 */

const DonutChart = (function() {
    // Extend the base visualization
    function DonutVisualization(element, options = {}) {
        // Call the parent constructor
        const base = VisualizationBase.create(element, options);
        
        // Debug mode
        const debug = options.debug || true;
        
        // Log function for debugging
        function log(message, data) {
            if (debug) {
                console.log(`[DonutChart] ${message}`, data || '');
            }
        }
        
        log('Creating donut chart', options);
        
        // Merge with default options
        const donutOptions = {
            size: 200,
            thickness: 30,
            colors: {
                primary: '#4CAF50',
                secondary: '#E0E0E0',
                text: '#333333'
            },
            animation: true,
            animationDuration: 1000,
            ...options
        };
        
        log('Donut options', donutOptions);
        
        // Private properties
        let chart = null;
        let svg = null;
        
        // Override loadData method
        base.loadData = function(projectId) {
            log('Loading data for project', projectId);
            
            if (!projectId) {
                log('No project ID provided, showing empty chart');
                base.data = {
                    success: true,
                    data: {
                        percentage: 0,
                        earned: 0,
                        budgeted: 0
                    }
                };
                base.render();
                return Promise.resolve(base.data);
            }
            
            base._showLoading();
            
            // Add a console message to help with debugging
            console.log(`[DonutChart] Fetching data from API for project ${projectId}`);
            
            return ApiClient.getVisualizationData('donut', projectId)
                .then(data => {
                    log('Data received from API', data);
                    base.data = data;
                    base._hideLoading();
                    base.render();
                    return data;
                })
                .catch(error => {
                    log('Error loading data', error);
                    base._showError(`Failed to load data: ${error.message}`);
                    console.error('Error loading donut chart data:', error);
                    
                    // Render empty chart as fallback
                    base.data = {
                        success: false,
                        error: error.message,
                        data: {
                            percentage: 0,
                            earned: 0,
                            budgeted: 0
                        }
                    };
                    base.render();
                    
                    return null;
                });
        };
        
        // Override render method
        base.render = function() {
            log('Rendering chart', base.data);
            
            if (!base.data) {
                log('No data available, showing empty chart');
                base.data = {
                    success: true,
                    data: {
                        percentage: 0,
                        earned: 0,
                        budgeted: 0
                    }
                };
            }
            
            // Clear previous chart
            base.container.innerHTML = '';
            
            // Create SVG element
            const width = donutOptions.size;
            const height = donutOptions.size;
            const radius = Math.min(width, height) / 2;
            const innerRadius = radius - donutOptions.thickness;
            
            log('Creating SVG element', { width, height, radius });
            
            svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('width', width);
            svg.setAttribute('height', height);
            svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
            svg.setAttribute('class', 'donut-chart');
            
            // Create group for centering
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('transform', `translate(${width / 2}, ${height / 2})`);
            
            // Create background circle
            const backgroundCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            backgroundCircle.setAttribute('cx', 0);
            backgroundCircle.setAttribute('cy', 0);
            backgroundCircle.setAttribute('r', radius - donutOptions.thickness / 2);
            backgroundCircle.setAttribute('fill', 'none');
            backgroundCircle.setAttribute('stroke', donutOptions.colors.secondary);
            backgroundCircle.setAttribute('stroke-width', donutOptions.thickness);
            
            // Create progress arc
            const percentage = base.data.data ? (base.data.data.percentage || 0) : 0;
            log('Progress percentage', percentage);
            
            const circumference = 2 * Math.PI * (radius - donutOptions.thickness / 2);
            const progressLength = (percentage / 100) * circumference;
            const remainingLength = circumference - progressLength;
            
            const progressArc = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            progressArc.setAttribute('cx', 0);
            progressArc.setAttribute('cy', 0);
            progressArc.setAttribute('r', radius - donutOptions.thickness / 2);
            progressArc.setAttribute('fill', 'none');
            progressArc.setAttribute('stroke', donutOptions.colors.primary);
            progressArc.setAttribute('stroke-width', donutOptions.thickness);
            progressArc.setAttribute('stroke-dasharray', `${progressLength} ${remainingLength}`);
            progressArc.setAttribute('stroke-dashoffset', circumference / 4); // Start from top
            
            // Create percentage text
            const percentageText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            percentageText.setAttribute('x', 0);
            percentageText.setAttribute('y', 0);
            percentageText.setAttribute('text-anchor', 'middle');
            percentageText.setAttribute('dominant-baseline', 'middle');
            percentageText.setAttribute('font-size', '40px');
            percentageText.setAttribute('font-weight', 'bold');
            percentageText.setAttribute('fill', donutOptions.colors.text);
            percentageText.textContent = `${Math.round(percentage)}%`;
            
            // Create label text
            const labelText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            labelText.setAttribute('x', 0);
            labelText.setAttribute('y', 30);
            labelText.setAttribute('text-anchor', 'middle');
            labelText.setAttribute('dominant-baseline', 'middle');
            labelText.setAttribute('font-size', '14px');
            labelText.setAttribute('fill', donutOptions.colors.text);
            labelText.textContent = 'Complete';
            
            // Add elements to SVG
            g.appendChild(backgroundCircle);
            g.appendChild(progressArc);
            g.appendChild(percentageText);
            g.appendChild(labelText);
            svg.appendChild(g);
            
            // Add SVG to container
            base.container.appendChild(svg);
            
            // Add details below chart
            const earned = base.data.data ? (base.data.data.earned || 0) : 0;
            const budgeted = base.data.data ? (base.data.data.budgeted || 0) : 0;
            
            log('Chart details', { earned, budgeted });
            
            const details = document.createElement('div');
            details.className = 'donut-chart-details';
            details.innerHTML = `
                <div class="detail-item">
                    <span class="detail-label">Earned Hours:</span>
                    <span class="detail-value">${earned.toLocaleString()}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Budgeted Hours:</span>
                    <span class="detail-value">${budgeted.toLocaleString()}</span>
                </div>
            `;
            base.container.appendChild(details);
            
            // Add animation if enabled
            if (donutOptions.animation) {
                progressArc.style.transition = `stroke-dasharray ${donutOptions.animationDuration}ms ease-in-out`;
                setTimeout(() => {
                    progressArc.setAttribute('stroke-dasharray', `${progressLength} ${remainingLength}`);
                }, 100);
            }
            
            log('Chart rendered successfully');
            return base;
        };
        
        // Override resize method
        base.resize = function() {
            if (!svg) {
                return base;
            }
            
            // Get container size
            const containerWidth = base.element.clientWidth;
            const size = Math.min(containerWidth, donutOptions.size);
            
            log('Resizing chart', { containerWidth, size });
            
            // Update SVG size
            svg.setAttribute('width', size);
            svg.setAttribute('height', size);
            
            return base;
        };
        
        // Initialize the chart
        log('Initializing chart');
        base.init();
        
        return base;
    }
    
    // Factory function to create new instances
    return {
        create: function(element, options) {
            console.log('[DonutChart] Creating new donut chart', options);
            return new DonutVisualization(element, options);
        }
    };
})();
