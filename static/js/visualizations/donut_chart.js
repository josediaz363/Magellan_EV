/**
 * Magellan EV Tracker v2.0 - Donut Chart Visualization
 * This module handles the rendering and updating of the Overall Progress donut chart.
 */

const DonutChart = (function() {
    // Private variables
    let chart = null;
    let container = null;
    let projectId = null;
    let data = {
        percentage: 0,
        earned: 0,
        budgeted: 0
    };
    
    // DOM elements
    let percentageEl = null;
    let earnedEl = null;
    let budgetedEl = null;
    
    // Configuration
    const config = {
        size: 200,
        thickness: 30,
        colors: {
            fill: '#0d6efd',
            background: '#e9ecef',
            text: '#ffffff'
        },
        animationDuration: 1000
    };
    
    // Initialize the chart
    function init(containerId) {
        container = document.getElementById(containerId);
        if (!container) {
            console.error('Donut chart container not found:', containerId);
            return false;
        }
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', config.size);
        svg.setAttribute('height', config.size);
        svg.setAttribute('viewBox', `0 0 ${config.size} ${config.size}`);
        svg.setAttribute('class', 'donut-chart');
        
        // Create background circle
        const backgroundCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        backgroundCircle.setAttribute('cx', config.size / 2);
        backgroundCircle.setAttribute('cy', config.size / 2);
        backgroundCircle.setAttribute('r', (config.size / 2) - (config.thickness / 2));
        backgroundCircle.setAttribute('fill', 'none');
        backgroundCircle.setAttribute('stroke', config.colors.background);
        backgroundCircle.setAttribute('stroke-width', config.thickness);
        svg.appendChild(backgroundCircle);
        
        // Create progress circle
        const progressCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        progressCircle.setAttribute('cx', config.size / 2);
        progressCircle.setAttribute('cy', config.size / 2);
        progressCircle.setAttribute('r', (config.size / 2) - (config.thickness / 2));
        progressCircle.setAttribute('fill', 'none');
        progressCircle.setAttribute('stroke', config.colors.fill);
        progressCircle.setAttribute('stroke-width', config.thickness);
        progressCircle.setAttribute('stroke-dasharray', '0 1000');
        progressCircle.setAttribute('transform', `rotate(-90 ${config.size / 2} ${config.size / 2})`);
        svg.appendChild(progressCircle);
        
        // Add SVG to container
        container.appendChild(svg);
        
        // Create percentage display
        const percentageContainer = document.createElement('div');
        percentageContainer.className = 'donut-percentage';
        percentageEl = document.createElement('span');
        percentageEl.textContent = '0%';
        percentageContainer.appendChild(percentageEl);
        container.appendChild(percentageContainer);
        
        // Create info display
        const infoContainer = document.createElement('div');
        infoContainer.className = 'donut-info';
        
        const earnedContainer = document.createElement('div');
        earnedContainer.className = 'earned-hours';
        earnedContainer.innerHTML = '<span>Earned Hours:</span> ';
        earnedEl = document.createElement('span');
        earnedEl.textContent = '0';
        earnedContainer.appendChild(earnedEl);
        
        const budgetedContainer = document.createElement('div');
        budgetedContainer.className = 'budgeted-hours';
        budgetedContainer.innerHTML = '<span>Budgeted Hours:</span> ';
        budgetedEl = document.createElement('span');
        budgetedEl.textContent = '0';
        budgetedContainer.appendChild(budgetedEl);
        
        infoContainer.appendChild(earnedContainer);
        infoContainer.appendChild(budgetedContainer);
        container.appendChild(infoContainer);
        
        // Store reference to progress circle
        chart = progressCircle;
        
        return true;
    }
    
    // Update chart with new data
    function update(newData) {
        if (!chart) return false;
        
        data = newData;
        
        // Calculate circumference
        const radius = (config.size / 2) - (config.thickness / 2);
        const circumference = 2 * Math.PI * radius;
        
        // Calculate stroke dash array
        const dashArray = (data.percentage / 100) * circumference;
        
        // Animate the chart
        chart.style.transition = `stroke-dasharray ${config.animationDuration}ms ease-in-out`;
        chart.setAttribute('stroke-dasharray', `${dashArray} ${circumference}`);
        
        // Update text displays
        percentageEl.textContent = `${Math.round(data.percentage)}%`;
        earnedEl.textContent = data.earned.toFixed(1);
        budgetedEl.textContent = data.budgeted.toFixed(1);
        
        return true;
    }
    
    // Load data from API
    function loadData(projectId) {
        if (!projectId) {
            console.error('No project ID provided');
            return false;
        }
        
        // Store project ID
        this.projectId = projectId;
        
        // Show loading state
        if (percentageEl) percentageEl.textContent = 'Loading...';
        
        // Fetch data from API
        fetch(`/api/visualizations/donut/${projectId}`)
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    update(result.data);
                } else {
                    console.error('Error loading donut chart data:', result.error);
                    if (percentageEl) percentageEl.textContent = 'Error';
                }
            })
            .catch(error => {
                console.error('Error fetching donut chart data:', error);
                if (percentageEl) percentageEl.textContent = 'Error';
            });
            
        return true;
    }
    
    // Public API
    return {
        init: init,
        update: update,
        loadData: loadData
    };
})();

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the dashboard page
    const donutContainer = document.getElementById('donut-chart-container');
    if (donutContainer) {
        // Initialize the donut chart
        DonutChart.init('donut-chart-container');
        
        // Get project selector
        const projectSelector = document.getElementById('project-selector');
        if (projectSelector) {
            // Load data when project is selected
            projectSelector.addEventListener('change', function() {
                const projectId = this.value;
                if (projectId) {
                    DonutChart.loadData(projectId);
                }
            });
            
            // Load initial data if a project is already selected
            if (projectSelector.value) {
                DonutChart.loadData(projectSelector.value);
            }
        }
    }
});
