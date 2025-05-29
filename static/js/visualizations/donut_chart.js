/**
 * Magellan EV Tracker v2.0
 * Donut Chart Visualization Component
 * 
 * This component renders a donut chart showing overall progress.
 */

const DonutChart = (function() {
    // Extend the base visualization
    function DonutVisualization(element, options = {}) {
        // Call the parent constructor
        const base = VisualizationBase.create(element, options);
        
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
        
        // Private properties
        let chart = null;
        let svg = null;
        
        // Override loadData method
        base.loadData = function(projectId) {
            base._showLoading();
            
            return ApiClient.getVisualizationData('donut', projectId)
                .then(data => {
                    base.data = data;
                    base._hideLoading();
                    base.render();
                    return data;
                })
                .catch(error => {
                    base._showError(`Failed to load data: ${error.message}`);
                    console.error('Error loading donut chart data:', error);
                    return null;
                });
        };
        
        // Override render method
        base.render = function() {
            if (!base.data) {
                return base;
            }
            
            // Clear previous chart
            base.container.innerHTML = '';
            
            // Create SVG element
            const width = donutOptions.size;
            const height = donutOptions.size;
            const radius = Math.min(width, height) / 2;
            const innerRadius = radius - donutOptions.thickness;
            
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
            const percentage = base.data.data.percentage || 0;
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
            const details = document.createElement('div');
            details.className = 'donut-chart-details';
            details.innerHTML = `
                <div class="detail-item">
                    <span class="detail-label">Earned Hours:</span>
                    <span class="detail-value">${base.data.data.earned.toLocaleString()}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Budgeted Hours:</span>
                    <span class="detail-value">${base.data.data.budgeted.toLocaleString()}</span>
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
            
            return base;
        };
        
        // Override resize method
        base.resize = function() {
            if (!base.data || !svg) {
                return base;
            }
            
            // Get container size
            const containerWidth = base.element.clientWidth;
            const size = Math.min(containerWidth, donutOptions.size);
            
            // Update SVG size
            svg.setAttribute('width', size);
            svg.setAttribute('height', size);
            
            return base;
        };
        
        return base;
    }
    
    // Factory function to create new instances
    return {
        create: function(element, options) {
            return new DonutVisualization(element, options);
        }
    };
})();
