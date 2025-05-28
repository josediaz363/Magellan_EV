// Dashboard JavaScript

// Chart initialization functions
function initializeOverallProgress(percentage) {
    // Create circular progress indicator
    const progressCircle = document.getElementById('overall-progress-circle');
    if (!progressCircle) return;
    
    const radius = 80;
    const circumference = 2 * Math.PI * radius;
    
    // Calculate stroke-dasharray and stroke-dashoffset
    const dashOffset = circumference - (percentage / 100) * circumference;
    
    // Set circle properties
    progressCircle.style.strokeDasharray = circumference;
    progressCircle.style.strokeDashoffset = dashOffset;
    
    // Update percentage text
    const percentageText = document.getElementById('overall-progress-percentage');
    if (percentageText) {
        percentageText.textContent = `${Math.round(percentage)}%`;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get project selector
    const projectSelector = document.getElementById('project-selector');
    if (!projectSelector) return;
    
    // Initialize with default values
    initializeOverallProgress(0);
    
    // Add event listener for project selection
    projectSelector.addEventListener('change', function() {
        const projectId = this.value;
        if (!projectId) {
            // Reset dashboard if no project selected
            initializeOverallProgress(0);
            return;
        }
        
        // Fetch project data
        fetch(`/api/project/${projectId}/dashboard`)
            .then(response => response.json())
            .then(data => {
                // Update overall progress
                initializeOverallProgress(data.overallProgress || 0);
            })
            .catch(error => {
                console.error('Error fetching dashboard data:', error);
            });
    });
});
