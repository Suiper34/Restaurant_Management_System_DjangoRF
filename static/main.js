const SELECTORS = {
    navToggle: '[data-nav-toggle]',
    navMenu: '[data-nav]',
    managerTable: '#manager-users',
    toastContainer: '#app-toast',
    dailySales: '#manager-daily-sales',
    stockAlerts: '#manager-stock-alerts',
};

const MANAGER_ENDPOINTS = {
    listUsers: '/managers/users/',
    assignUser: (id) => `/managers/users/${id}/assign/`,
    removeUser: (id) => `/managers/users/${id}/remove/`,
    dailySales: '/managers/reports/daily-sales/',
    stockAlerts: '/managers/reports/stock-alerts/',
};

document.addEventListener('DOMContentLoaded', () => {
    setupNavigation();
    const page = (document.body.dataset.page || '').toLowerCase();
    if (page === 'managers') {
        initManagerDashboard().catch((error) => {
            console.error(error);
            showToast('Failed to initialise the managers dashboard.', 'error');
        });
    }
});

/**
 * Set up mobile navigation toggling.
 */
function setupNavigation() {
    const toggle = document.querySelector(SELECTORS.navToggle);
    const menu = document.querySelector(SELECTORS.navMenu);
    if (!toggle || !menu) {
        return;
    }

    toggle.addEventListener('click', () => {
        const isOpen = menu.getAttribute('data-open') === 'true';
        menu.setAttribute('data-open', String(!isOpen));
        toggle.setAttribute('aria-expanded', String(!isOpen));
    });
}

/**
 * Initialise the managers dashboard widgets.
 */
async function initManagerDashboard() {
    attachUserActions();
    await Promise.all([loadUsers(), loadDailySales(), loadStockAlerts()]);
}

/**
 * Return the CSRF token from cookies or meta tags.
 */
function getCSRFToken() {
    const cookie = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='));
    if (cookie) {
        return decodeURIComponent(cookie.split('=')[1]);
    }

    const metaTag = document.querySelector('meta[name=\'csrf-token\']');
    return metaTag ? metaTag.getAttribute('content') : '';
}

/**
 * Perform a JSON fetch request with sensible defaults and error handling.
 */
async function fetchJSON(url, options = {}) {
    const headers = {
        Accept: 'application/json',
        ...(options.headers || {}),
    };

    const config = {
        credentials: 'same-origin',
        ...options,
        headers,
    };

    const method = (config.method || 'GET').toUpperCase();
    if (
        method !== 'GET' &&
        !Object.prototype.hasOwnProperty.call(headers, 'X-CSRFToken')
    ) {
        const csrfToken = getCSRFToken();
        if (!csrfToken) {
            throw new Error('CSRF token not found. Refresh and try again.');
        }
        headers['X-CSRFToken'] = csrfToken;
    }

    if (config.body && typeof config.body !== 'string') {
        headers['Content-Type'] =
            headers['Content-Type'] || 'application/json';
        config.body = JSON.stringify(config.body);
    }

    const response = await fetch(url, config);
    const contentType = response.headers.get('Content-Type') || '';
    const isJson = contentType.includes('application/json');

    let payload;
    if (isJson) {
        try {
            payload = await response.json();
        } catch {
            payload = null;
        }
    } else {
        payload = await response.text();
    }

    if (!response.ok) {
        let message = response.statusText || 'Unable to complete the request.';
        if (isJson && payload && typeof payload === 'object') {
            if (typeof payload.message === 'string') {
                message = payload.message;
            } else if (typeof payload.detail === 'string') {
                message = payload.detail;
            } else if (typeof payload.error === 'string') {
                message = payload.error;
            }
        }
        throw new Error(message);
    }

    return payload;
}

/**
 * Render the users table inside the managers dashboard.
 */
function renderUsers(users) {
    const container = document.querySelector(SELECTORS.managerTable);
    if (!container) {
        return;
    }

    if (!users.length) {
        container.innerHTML =
            '<p class=\'card\'>No users found yet. Invite teammates to collaborate.</p>';
        return;
    }

    const rows = users
        .map(
            (user) => `
            <tr>
                <td>${user.username}</td>
                <td>${user.email || '—'}</td>
                <td>${user.is_staff ? 'Staff' : 'Member'}</td>
                <td>
                    <span class='badge ${user.is_manager ? 'badge-success' : 'badge-muted'
                }'>
                        ${user.is_manager ? 'Manager' : 'Employee'}
                    </span>
                </td>
                <td>
                    <button
                        class='button button-outline'
                        data-action='${user.is_manager ? 'remove' : 'assign'}'
                        data-user-id='${user.id}'
                    >
                        ${user.is_manager ? 'Remove manager' : 'Make manager'}
                    </button>
                </td>
            </tr>`
        )
        .join('');

    container.innerHTML = `
        <div class='table-responsive'>
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        </div>`;
}

/**
 * Fetch and render all users for the dashboard table.
 */
async function loadUsers() {
    const container = document.querySelector(SELECTORS.managerTable);
    if (!container) {
        return;
    }

    container.innerHTML = `<p class='card'>Loading users…</p>`;
    try {
        const users = await fetchJSON(MANAGER_ENDPOINTS.listUsers);
        renderUsers(users);
    } catch (error) {
        console.error(error);
        container.innerHTML =
            '<p class=\'card\'>Unable to load users. Please try again later.</p>';
        showToast(error.message, 'error');
    }
}

/**
 * Attach handlers for promote/demote actions.
 */
function attachUserActions() {
    const container = document.querySelector(SELECTORS.managerTable);
    if (!container) {
        return;
    }

    container.addEventListener('click', async (event) => {
        const button = event.target.closest('button[data-action]');
        if (!button) {
            return;
        }

        const action = button.dataset.action;
        const userId = button.dataset.userId;
        if (!action || !userId) {
            return;
        }

        button.disabled = true;
        const endpoint =
            action === 'assign'
                ? MANAGER_ENDPOINTS.assignUser(userId)
                : MANAGER_ENDPOINTS.removeUser(userId);

        try {
            const result = await fetchJSON(endpoint, { method: 'POST', body: {} });
            const message =
                result && typeof result.message === 'string'
                    ? result.message
                    : 'Action completed.';
            showToast(message, 'success');
            await loadUsers();
        } catch (error) {
            console.error(error);
            showToast(error.message, 'error');
            button.disabled = false;
        }
    });
}

/**
 * Load the daily sales widget.
 */
async function loadDailySales() {
    const container = document.querySelector(SELECTORS.dailySales);
    if (!container) {
        return;
    }

    container.innerHTML = '<p>Loading sales data…</p>';

    try {
        const data = await fetchJSON(MANAGER_ENDPOINTS.dailySales);
        renderDailySales(container, data ? data.summary : null, data ? data.generated_at : null);
    } catch (error) {
        console.error(error);
        container.innerHTML =
            '<p>Unable to load daily sales data.</p>';
        showToast(error.message, 'error');
    }
}

/**
 * Render the daily sales summary.
 */
function renderDailySales(container, summary, generatedAt) {
    if (!summary) {
        container.innerHTML = '<p>No sales recorded for the selected day yet.</p>';
        return;
    }

    container.innerHTML = `
        <ul>
            <li><strong>Date:</strong> ${summary.date}</li>
            <li><strong>Total orders:</strong> ${summary.total_orders}</li>
            <li><strong>Completed orders:</strong> ${summary.completed_orders}</li>
            <li><strong>Pending orders:</strong> ${summary.pending_orders}</li>
            <li><strong>Gross revenue:</strong> ${formatCurrency(summary.gross_revenue)}</li>
            <li><strong>Average order value:</strong> ${formatCurrency(summary.average_order_value)}</li>
        </ul>
        <small>Generated at ${formatTimestamp(generatedAt)}</small>
    `;
}

/**
 * Load inventory stock alerts.
 */
async function loadStockAlerts() {
    const container = document.querySelector(SELECTORS.stockAlerts);
    if (!container) {
        return;
    }

    container.innerHTML = '<p>Loading stock alerts…</p>';

    try {
        const data = await fetchJSON(MANAGER_ENDPOINTS.stockAlerts);
        renderStockAlerts(container, data ? data.alerts : [], data ? data.generated_at : null);
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p>Unable to load stock alerts.</p>';
        showToast(error.message, 'error');
    }
}

/**
 * Render the stock alert list.
 */
function renderStockAlerts(container, alerts = [], generatedAt) {
    if (!alerts.length) {
        container.innerHTML = '<p>All inventory levels look healthy.</p>';
        return;
    }

    const items = alerts
        .map((alert) => {
            const statusText =
                alert.deficit > 0
                    ? `Short by ${alert.deficit}`
                    : 'Near threshold';
            return `<li><strong>${alert.menu_item}</strong> — Qty: ${alert.quantity} / Threshold: ${alert.threshold} (${statusText})</li>`;
        })
        .join('');

    container.innerHTML = `
        <ul>
            ${items}
        </ul>
        <small>Generated at ${formatTimestamp(generatedAt)}</small>
    `;
}

/**
 * Helper to format currency-like strings.
 */
function formatCurrency(value) {
    const amount = Number(value);
    if (Number.isNaN(amount)) {
        return value;
    }
    return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2,
    }).format(amount);
}

/**
 * Format an ISO timestamp into a readable string.
 */
function formatTimestamp(value) {
    if (!value) {
        return '—';
    }
    try {
        return new Date(value).toLocaleString();
    } catch {
        return value;
    }
}

/**
 * Display toast notifications in the UI.
 */
function showToast(message, type = 'success') {
    const container = document.querySelector(SELECTORS.toastContainer);
    if (!container) {
        return;
    }

    const toast = document.createElement('div');
    toast.classList.add('toast', `toast--${type}`);
    toast.setAttribute('role', 'alert');
    toast.textContent = message;

    container.appendChild(toast);

    window.setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        toast.addEventListener(
            'transitionend',
            () => toast.remove(),
            { once: true }
        );
    }, 3200);
}