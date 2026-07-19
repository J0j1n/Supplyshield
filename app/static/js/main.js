document.addEventListener("DOMContentLoaded", function() {
    console.log("SupplyShield v0.1.0 initialized");

    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-messages .alert');
    flashMessages.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

/**
 * Initialize D3.js dependency graph (Placeholder)
 * TODO: Implement graph rendering logic
 */
function initDependencyGraph(containerId, graphData) {
    console.log(`Initializing dependency graph in #${containerId}`);
    // D3 logic goes here
}

/**
 * Format Trust Score to HTML badge
 */
function formatTrustScore(score) {
    const s = score.toUpperCase();
    if (s === 'A') return '<span class="badge trust-badge trust-badge-enterprise">Enterprise</span>';
    if (s === 'B') return '<span class="badge trust-badge trust-badge-trusted">Trusted</span>';
    if (s === 'C') return '<span class="badge trust-badge trust-badge-moderate">Moderate</span>';
    if (s === 'D') return '<span class="badge trust-badge trust-badge-high-risk">High Risk</span>';
    if (s === 'F') return '<span class="badge trust-badge trust-badge-critical">Critical</span>';
    return '<span class="badge bg-secondary">Unknown</span>';
}

/**
 * Poll scan status
 */
function refreshScanStatus(scanId) {
    const interval = setInterval(() => {
        fetch(`/scan/status/${scanId}`)
            .then(res => res.json())
            .then(data => {
                console.log("Status:", data.status);
                if (data.status === 'completed' || data.status === 'failed') {
                    clearInterval(interval);
                    window.location.reload();
                }
            })
            .catch(err => console.error("Error fetching status:", err));
    }, 3000);
}

/**
 * Show Bootstrap toast notification
 */
function showNotification(message, type = 'info') {
    // Create toast element dynamically
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();
    
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastEl.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}
