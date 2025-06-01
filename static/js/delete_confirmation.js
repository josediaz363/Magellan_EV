/**
 * Unified delete confirmation functionality for Magellan EV Tracker v1.20
 * 
 * This script provides a consistent delete confirmation popup across all pages
 * replacing the previous modal/card-based confirmations with a unified approach.
 */

// Function to handle delete button clicks and show confirmation popup
function setupDeleteConfirmations() {
    // Find all delete buttons across the application
    const deleteButtons = document.querySelectorAll('[data-delete-action]');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const deleteUrl = this.getAttribute('data-delete-action');
            const itemType = this.getAttribute('data-item-type') || 'item';
            const confirmMessage = `Are you sure you want to delete this ${itemType}? It cannot be undone if work items are using it.`;
            
            // Show the confirmation dialog
            if (confirm(confirmMessage)) {
                // If confirmed, create and submit a form to the delete URL
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = deleteUrl;
                document.body.appendChild(form);
                form.submit();
            }
        });
    });
}

// Initialize when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    setupDeleteConfirmations();
});
