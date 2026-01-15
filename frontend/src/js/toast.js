/**
 * Toast Notification System
 * Provides non-blocking notifications for user feedback
 */

/**
 * Initialize toast container
 */
function initToastContainer() {
    // Check if container exists in DOM (not just cached reference)
    let container = document.getElementById('toast-container');
    if (container) return container;

    container = document.createElement('div');
    container.id = 'toast-container';
    container.setAttribute('role', 'alert');
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);

    return container;
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {object} options - Configuration options
 * @param {string} options.type - 'success' | 'error' | 'warning' | 'info' (default: 'info')
 * @param {number} options.duration - Duration in ms (default: 4000)
 * @param {boolean} options.dismissible - Show close button (default: true)
 */
function showToast(message, options = {}) {
    const {
        type = 'info',
        duration = 4000,
        dismissible = true
    } = options;

    const container = initToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Icon based on type
    const icons = {
        success: '\u2713',
        error: '\u2717',
        warning: '\u26A0',
        info: '\u2139'
    };

    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${escapeHtml(message)}</span>
        ${dismissible ? '<button class="toast-close" aria-label="Dismiss">\u00D7</button>' : ''}
    `;

    // Add to container
    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('toast-show');
    });

    // Auto-dismiss
    let timeoutId;
    if (duration > 0) {
        timeoutId = setTimeout(() => dismissToast(toast), duration);
    }

    // Manual dismiss
    if (dismissible) {
        toast.querySelector('.toast-close').addEventListener('click', () => {
            clearTimeout(timeoutId);
            dismissToast(toast);
        });
    }

    return toast;
}

/**
 * Dismiss a toast
 */
function dismissToast(toast) {
    toast.classList.remove('toast-show');
    toast.classList.add('toast-hide');

    // Remove after animation
    toast.addEventListener('animationend', () => {
        toast.remove();
    });
}

/**
 * Convenience methods
 */
function showSuccess(message, options = {}) {
    return showToast(message, { ...options, type: 'success' });
}

function showError(message, options = {}) {
    return showToast(message, { ...options, type: 'error', duration: 6000 });
}

function showWarning(message, options = {}) {
    return showToast(message, { ...options, type: 'warning' });
}

function showInfo(message, options = {}) {
    return showToast(message, { ...options, type: 'info' });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for ES modules
export { showToast, showSuccess, showError, showWarning, showInfo, dismissToast };
