// Main JavaScript file for Grad Café Analysis Dashboard

// Global variables
let statusPollingInterval = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Check if we need to start status polling
    checkInitialStatus();
});

function checkInitialStatus() {
    // This function can be used to check status on page load
    // Currently handled by server-side template logic
}

// Utility function to show notifications
function showNotification(message, type = 'info') {
    // Create a simple notification
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Utility function to format numbers
function formatNumber(num) {
    if (typeof num === 'number') {
        return num.toLocaleString();
    }
    return num;
}

// Utility function to handle API errors
function handleApiError(error, defaultMessage = 'An error occurred') {
    console.error('API Error:', error);
    showNotification(defaultMessage, 'danger');
}

// Export functions for global use
window.showNotification = showNotification;
window.formatNumber = formatNumber;
window.handleApiError = handleApiError;
