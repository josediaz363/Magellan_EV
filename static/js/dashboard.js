// Dashboard JavaScript

// Chart.js initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if they exist on the page
    initializeCharts();
    
    // Initialize project selector
    const projectSelector = document.querySelector('.navbar select');
    if (projectSelector) {
        projectSelector.addEventListener('change', function() {
            if (this.value) {
                loadProjectData(this.value);
            }
        });
    }
    
    // Initialize settings button if it exists
    const settingsBtn = document.getElementById('dashboard-settings-btn');
    if (settingsBtn) {
        settingsBtn.addEventListener('click', function() {
            window.location.href = '/settings';
        });
    }
    
    // Initialize update planned progress button if it exists
    const updatePlanBtn = document.getElementById('update-plan-btn');
    if (updatePlanBtn) {
        updatePlanBtn.addEventListener('click', function() {
            showUpdatePlanModal();
        });
    }
});

// Initialize all charts
function initializeCharts() {
    // Get dashboard settings from localStorage
    const dashboardSettings = getDashboardSettings();
    
    // Only initialize charts that are enabled in settings
    if (dashboardSettings.showOverallProgress) {
        initializeOverallProgressChart();
    }
    
    if (dashboardSettings.showQuantityDistribution) {
        initializeQuantityDistributionChart();
    }
    
    if (dashboardSettings.showProgressHistogram) {
        initializeProgressHistogramChart();
    }
    
    if (dashboardSettings.showSPI) {
        initializeSPIChart();
    }
    
    if (dashboardSettings.showManpowerDistribution) {
        initializeManpowerDistributionChart();
    }
    
    if (dashboardSettings.showBudgetByPhase) {
        initializeBudgetByPhaseChart();
    }
}

// Get dashboard settings from localStorage with defaults
function getDashboardSettings() {
    const defaultSettings = {
        showOverallProgress: true,
        showQuantityDistribution: true,
        showProgressHistogram: true,
        showSPI: true,
        showManpowerDistribution: true,
        showBudgetByPhase: true,
        plannedCompleteInterval: 'weekly' // daily, weekly, monthly
    };
    
    const savedSettings = localStorage.getItem('dashboardSettings');
    return savedSettings ? JSON.parse(savedSettings) : defaultSettings;
}

// Load project data via AJAX
function loadProjectData(projectId) {
    fetch(`/api/project/${projectId}/dashboard`)
        .then(response => response.json())
        .then(data => {
            updateDashboardMetrics(data);
            updateCharts(data);
        })
        .catch(error => {
            console.error('Error loading project data:', error);
        });
}

// Update dashboard metrics
function updateDashboardMetrics(data) {
    // Update actual progress
    const actualProgressElement = document.getElementById('actual-progress');
    if (actualProgressElement) {
        actualProgressElement.textContent = `${data.actualProgress.toFixed(1)}%`;
    }
    
    // Update planned progress
    const plannedProgressElement = document.getElementById('planned-progress');
    if (plannedProgressElement) {
        plannedProgressElement.textContent = `${data.plannedProgress.toFixed(1)}%`;
    }
    
    // Update weekly actual progress
    const weeklyActualElement = document.getElementById('weekly-actual');
    if (weeklyActualElement) {
        weeklyActualElement.textContent = `${data.weeklyActual.toFixed(1)}%`;
    }
    
    // Update weekly planned progress
    const weeklyPlannedElement = document.getElementById('weekly-planned');
    if (weeklyPlannedElement) {
        weeklyPlannedElement.textContent = `${data.weeklyPlanned.toFixed(1)}%`;
    }
}

// Update all charts with new data
function updateCharts(data) {
    // Get dashboard settings
    const dashboardSettings = getDashboardSettings();
    
    // Update each chart if it's enabled in settings
    if (dashboardSettings.showOverallProgress) {
        updateOverallProgressChart(data.overallProgress);
    }
    
    if (dashboardSettings.showQuantityDistribution) {
        updateQuantityDistributionChart(data.quantityDistribution);
    }
    
    if (dashboardSettings.showProgressHistogram) {
        updateProgressHistogramChart(data.progressHistogram);
    }
    
    if (dashboardSettings.showSPI) {
        updateSPIChart(data.spiData);
    }
    
    if (dashboardSettings.showManpowerDistribution) {
        updateManpowerDistributionChart(data.manpowerDistribution);
    }
    
    if (dashboardSettings.showBudgetByPhase) {
        updateBudgetByPhaseChart(data.budgetByPhase);
    }
}

// Initialize Overall Progress Chart (circle)
function initializeOverallProgressChart() {
    const ctx = document.getElementById('overall-progress-chart');
    if (!ctx) return;
    
    window.overallProgressChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [75, 25],
                backgroundColor: [
                    '#00a67e',
                    '#2c3e50'
                ],
                borderWidth: 0,
                cutout: '80%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: {
                    enabled: false
                },
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Add center text
    const centerText = {
        id: 'centerText',
        afterDraw: function(chart) {
            const width = chart.width;
            const height = chart.height;
            const ctx = chart.ctx;
            
            ctx.restore();
            const fontSize = (height / 114).toFixed(2);
            ctx.font = fontSize + 'em sans-serif';
            ctx.textBaseline = 'middle';
            
            const text = '75%';
            const textX = Math.round((width - ctx.measureText(text).width) / 2);
            const textY = height / 2;
            
            ctx.fillStyle = '#ffffff';
            ctx.fillText(text, textX, textY);
            ctx.save();
        }
    };
    
    Chart.register(centerText);
}

// Update Overall Progress Chart
function updateOverallProgressChart(progress) {
    if (!window.overallProgressChart) return;
    
    window.overallProgressChart.data.datasets[0].data = [progress, 100 - progress];
    window.overallProgressChart.update();
    
    // Update center text
    const centerText = {
        id: 'centerText',
        afterDraw: function(chart) {
            const width = chart.width;
            const height = chart.height;
            const ctx = chart.ctx;
            
            ctx.restore();
            const fontSize = (height / 114).toFixed(2);
            ctx.font = fontSize + 'em sans-serif';
            ctx.textBaseline = 'middle';
            
            const text = `${progress.toFixed(1)}%`;
            const textX = Math.round((width - ctx.measureText(text).width) / 2);
            const textY = height / 2;
            
            ctx.fillStyle = '#ffffff';
            ctx.fillText(text, textX, textY);
            ctx.save();
        }
    };
    
    Chart.register(centerText);
}

// Initialize Quantity Distribution Chart
function initializeQuantityDistributionChart() {
    const ctx = document.getElementById('quantity-distribution-chart');
    if (!ctx) return;
    
    window.quantityDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Electrical', 'Mechanical', 'Civil', 'Instrumentation'],
            datasets: [{
                label: 'Budgeted Quantity',
                data: [1200, 800, 500, 300],
                backgroundColor: '#3498db'
            }, {
                label: 'Earned Quantity',
                data: [900, 600, 300, 150],
                backgroundColor: '#00a67e'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

// Update Quantity Distribution Chart
function updateQuantityDistributionChart(data) {
    if (!window.quantityDistributionChart) return;
    
    window.quantityDistributionChart.data.labels = data.labels;
    window.quantityDistributionChart.data.datasets[0].data = data.budgeted;
    window.quantityDistributionChart.data.datasets[1].data = data.earned;
    window.quantityDistributionChart.update();
}

// Initialize Progress Histogram Chart
function initializeProgressHistogramChart() {
    const ctx = document.getElementById('progress-histogram-chart');
    if (!ctx) return;
    
    window.progressHistogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['0-10%', '11-20%', '21-30%', '31-40%', '41-50%', '51-60%', '61-70%', '71-80%', '81-90%', '91-100%'],
            datasets: [{
                label: 'Work Items',
                data: [5, 8, 12, 15, 20, 18, 15, 10, 8, 5],
                backgroundColor: '#00a67e'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

// Update Progress Histogram Chart
function updateProgressHistogramChart(data) {
    if (!window.progressHistogramChart) return;
    
    window.progressHistogramChart.data.datasets[0].data = data;
    window.progressHistogramChart.update();
}

// Initialize SPI Chart
function initializeSPIChart() {
    const ctx = document.getElementById('spi-chart');
    if (!ctx) return;
    
    window.spiChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            datasets: [{
                label: 'SPI',
                data: [0.95, 0.98, 1.02, 1.05, 1.03, 1.01],
                borderColor: '#00a67e',
                backgroundColor: 'rgba(0, 166, 126, 0.1)',
                fill: true,
                tension: 0.4
            }, {
                label: 'Target',
                data: [1, 1, 1, 1, 1, 1],
                borderColor: '#e74c3c',
                borderDash: [5, 5],
                fill: false,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#ffffff'
                    },
                    suggestedMin: 0.8,
                    suggestedMax: 1.2
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

// Update SPI Chart
function updateSPIChart(data) {
    if (!window.spiChart) return;
    
    window.spiChart.data.labels = data.labels;
    window.spiChart.data.datasets[0].data = data.values;
    
    // Update target line to match the number of data points
    const targetData = Array(data.labels.length).fill(1);
    window.spiChart.data.datasets[1].data = targetData;
    
    window.spiChart.update();
}

// Initialize Manpower Distribution Chart
function initializeManpowerDistributionChart() {
    const ctx = document.getElementById('manpower-distribution-chart');
    if (!ctx) return;
    
    window.manpowerDistributionChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Electrical', 'Mechanical', 'Civil', 'Instrumentation'],
            datasets: [{
                data: [30, 25, 20, 25],
                backgroundColor: [
                    '#3498db',
                    '#e74c3c',
                    '#f1c40f',
                    '#9b59b6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

// Update Manpower Distribution Chart
function updateManpowerDistributionChart(data) {
    if (!window.manpowerDistributionChart) return;
    
    window.manpowerDistributionChart.data.labels = data.labels;
    window.manpowerDistributionChart.data.datasets[0].data = data.values;
    window.manpowerDistributionChart.update();
}

// Initialize Budget by Phase Chart
function initializeBudgetByPhaseChart() {
    const ctx = document.getElementById('budget-by-phase-chart');
    if (!ctx) return;
    
    window.budgetByPhaseChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Engineering', 'Procurement', 'Construction', 'Commissioning'],
            datasets: [{
                data: [15, 25, 45, 15],
                backgroundColor: [
                    '#3498db',
                    '#e74c3c',
                    '#f1c40f',
                    '#9b59b6'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        }
    });
}

// Update Budget by Phase Chart
function updateBudgetByPhaseChart(data) {
    if (!window.budgetByPhaseChart) return;
    
    window.budgetByPhaseChart.data.labels = data.labels;
    window.budgetByPhaseChart.data.datasets[0].data = data.values;
    window.budgetByPhaseChart.update();
}

// Show modal for updating planned progress
function showUpdatePlanModal() {
    // Get the current settings
    const settings = getDashboardSettings();
    const intervalType = settings.plannedCompleteInterval;
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal fade" id="updatePlanModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Update Planned % Complete</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <p>Update the ${intervalType} planned % complete:</p>
                        <div class="mb-3">
                            <label for="plannedPercentage" class="form-label">Planned % Complete</label>
                            <input type="number" class="form-control" id="plannedPercentage" min="0" max="100" step="0.1">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="savePlannedProgress">Save</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to body
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHTML;
    document.body.appendChild(modalContainer);
    
    // Initialize modal
    const modal = new bootstrap.Modal(document.getElementById('updatePlanModal'));
    modal.show();
    
    // Add event listener to save button
    document.getElementById('savePlannedProgress').addEventListener('click', function() {
        const plannedPercentage = document.getElementById('plannedPercentage').value;
        if (plannedPercentage) {
            savePlannedProgress(parseFloat(plannedPercentage));
            modal.hide();
            
            // Remove modal from DOM after hiding
            document.getElementById('updatePlanModal').addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modalContainer);
            });
        }
    });
}

// Save planned progress
function savePlannedProgress(percentage) {
    // Get the current project ID
    const projectSelector = document.querySelector('.navbar select');
    const projectId = projectSelector ? projectSelector.value : null;
    
    if (!projectId) {
        alert('Please select a project first');
        return;
    }
    
    // Get the current settings
    const settings = getDashboardSettings();
    
    // Save to server
    fetch(`/api/project/${projectId}/planned-progress`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            percentage: percentage,
            intervalType: settings.plannedCompleteInterval
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI
            const plannedProgressElement = document.getElementById('planned-progress');
            if (plannedProgressElement) {
                plannedProgressElement.textContent = `${percentage.toFixed(1)}%`;
            }
        } else {
            alert('Error saving planned progress: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving planned progress:', error);
        alert('Error saving planned progress');
    });
}
