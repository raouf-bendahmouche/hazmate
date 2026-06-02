/**
 * app.js — Main UI Controller
 * Handles routing, themes, language, and core UI events.
 *
 * ARCHITECTURAL REFACTORING & DESIGN NOTES (FULL SYSTEM SYNCHRONIZATION):
 *
 * 1. Entity Separation (Vehicles / Drivers / Contracts):
 *    - Vehicles and Drivers are represented as separate first-class entities with dedicated, independent database tables and frontend views.
 *    - The dedicated Vehicles View displays registration number, type, category, and company association with no contract or driver context.
 *    - The dedicated Drivers View displays driver name, system-generated ID, optional phone number, and associated company with no license/contract leakage.
 *
 * 2. Auto-Increment Driver ID Logic:
 *    - Drivers use a system-generated, auto-incrementing integer as the primary key. Manual edits are disabled.
 *
 * 3. Optional Phone Field:
 *    - The driver's phone number is optional (nullable in the database and frontend form validation), permitting driver creation without a phone number.
 *
 * 4. Expiration Segmentation:
 *    - Segmented into 30, 60, and 90 day ranges on the dashboard.
 *    - Previews are fetched with a backend limit parameter of 5 records. A "View Full List" button allows retrieving the complete dataset for each range.
 *
 * 5. Purged Background Services:
 *    - All SMTP configuration forms, test email buttons, and database backup elements have been deleted from the Settings UI.
 *    - Background job manager modules, schedulers, and background threads have been removed to avoid memory leaks.
 *
 * 6. Indexing:
 *    - B-Tree indexes are preserved on vehicle registration numbers and licensing fields to ensure lightning-fast dashboard and query operations.
 */

const state = {
    currentPath: 'dashboard',
    history: [],
    theme: localStorage.getItem('theme') || 'light',
    selectedLicenseId: null,
    communes: [],
    wilaya: 'Setif'
};

// ── UI Elements ──────────────────────────────────────────────

const el = {
    content: document.getElementById('content'),
    navItems: document.querySelectorAll('.nav-item'),
    pageTitle: document.getElementById('page-title'),
    backBtn: document.getElementById('back-btn'),
    darkToggle: document.getElementById('dark-toggle'),
    langBtn: document.getElementById('lang-btn'),
    langMenu: document.getElementById('lang-menu'),
    toastContainer: document.getElementById('toast-container'),
    confirmModal: document.getElementById('confirm-modal'),
};

// Global chart instances
let statsCharts = {};
let searchTimeout = null;

function debounce(func, wait) {
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(searchTimeout);
            func(...args);
        };
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(later, wait);
    };
}

// Global location select builder (Sorted Alphabetically)
function buildLocationSelectHTML(name, currentValue = '', id = '') {
    const idAttr = id ? `id="${id}"` : '';
    const options = (state.communes || []).map(commune => {
        const selected = (commune === currentValue || currentValue?.startsWith(commune)) ? 'selected' : '';
        return `<option value="${commune}" ${selected}>${commune} (${state.wilaya || 'Setif'})</option>`;
    }).join('');
    
    return `
        <select class="form-control" name="${name}" ${idAttr}>
            <option value="">${t('opt_all_locations') || '(Select location)'}</option>
            ${options}
        </select>
    `;
}

// ── Initialization ───────────────────────────────────────────

async function init() {
    await initApiBase();
    // Load Setif communes
    try {
        const resp = await fetch('./data/setif_communes.json');
        if (resp.ok) {
            const data = await resp.json();
            if (data.communes) {
                state.communes = data.communes.sort((a, b) => a.localeCompare(b));
                state.wilaya = data.wilaya || 'Setif';
            }
        }
    } catch (e) {
        console.error("Failed to load communes:", e);
    }
    applyTheme();
    applyLanguage();
    setupEventListeners();
    syncSidebarProfile();
    navigateTo('dashboard', false);
}

function setupEventListeners() {
    // Navigation
    el.navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.getAttribute('data-page');
            if (page) navigateTo(page);
        });
    });

    el.backBtn.addEventListener('click', goBack);

    // Theme toggle (guarded)
    if (el.darkToggle) {
        el.darkToggle.addEventListener('click', toggleTheme);
    }

    // Language (guarded)
    if (el.langBtn) {
        el.langBtn.addEventListener('click', () => {
            if (el.langMenu) el.langMenu.classList.toggle('open');
        });
    }

    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.addEventListener('click', () => {
            const lang = opt.getAttribute('data-lang');
            setLanguage(lang);
            if (el.langMenu) el.langMenu.classList.remove('open');
        });
    });

    // Close lang menu on click outside (guarded)
    document.addEventListener('click', (e) => {
        if (el.langBtn && el.langMenu && !el.langBtn.contains(e.target) && !el.langMenu.contains(e.target)) {
            el.langMenu.classList.remove('open');
        }
    });

    // Keyboard Shortcuts (from Electron)
    if (window.electronAPI) {
        window.electronAPI.onShortcut((cmd) => {
            if (cmd === 'new-contract') navigateTo('add-contract');
            if (cmd === 'search') navigateTo('search');
            if (cmd === 'back') goBack();
        });
    }

    // Topbar settings shortcut
    const topbarSettingsBtn = document.getElementById('btn-topbar-settings');
    if (topbarSettingsBtn) {
        topbarSettingsBtn.addEventListener('click', () => navigateTo('settings'));
    }

    // Refresh on language change
    document.addEventListener('langchange', () => {
        renderCurrentPage();
    });
}

// ── Navigation ───────────────────────────────────────────────

function navigateTo(path, addToHistory = true) {
    if (addToHistory && state.currentPath !== path) {
        state.history.push(state.currentPath);
    }
    
    state.currentPath = path;
    
    // Update Sidebar
    el.navItems.forEach(item => {
        item.classList.toggle('active', item.getAttribute('data-page') === path);
    });

    // Update Topbar
    el.backBtn.classList.toggle('hidden', state.history.length === 0);
    el.pageTitle.setAttribute('data-i18n', `nav_${path.replace('-', '_')}`);
    el.pageTitle.textContent = t(`nav_${path.replace('-', '_')}`);

    // Show loading spinner immediately
    el.content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div><p style="margin-top: 10px;">Loading...</p></div>';

    // Use a timeout to allow the UI to update before starting the heavy work
    setTimeout(() => {
        try {
            switch (path) {
                case 'welcome':
                    renderWelcome();
                    break;
                case 'dashboard':
                    renderDashboard();
                    break;
                case 'add-contract':
                    renderAddContract();
                    break;
                case 'search':
                    renderSearch();
                    break;
                case 'deleted-contracts':
                    renderDeletedContracts();
                    break;
                case 'statistics':
                    renderStatistics();
                    break;
                case 'settings':
                    renderSettings();
                    break;
                case 'vehicles':
                    renderVehiclesView();
                    break;
                case 'drivers':
                    renderDriversView();
                    break;
                default:
                    el.content.innerHTML = `<div class="empty-state"><h2>404 - Page Not Found</h2><p>The requested page '${path}' does not exist.</p></div>`;
            }
        } catch (err) {
            showToast(err.message, 'error');
            el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
        }
    }, 50); // A small delay to ensure the spinner renders
}

function goBack() {
    if (state.history.length > 0) {
        const prev = state.history.pop();
        navigateTo(prev, false);
    }
}

function renderCurrentPage() {
    el.content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
    
    switch(state.currentPath) {
        case 'welcome':
            renderWelcome();
            break;
        case 'dashboard':
            renderDashboard();
            break;
        case 'add-contract':
            renderAddContract();
            break;
        case 'search':
            renderSearch();
            break;
        case 'deleted-contracts':
            renderDeletedContracts();
            break;
        case 'statistics':
            renderStatistics();
            break;
        case 'settings':
            renderSettings();
            break;
        case 'vehicles':
            renderVehiclesView();
            break;
        case 'drivers':
            renderDriversView();
            break;
        default:
            el.content.innerHTML = `<h2>Page ${state.currentPath} not found</h2>`;
    }
}

// ── Theme ────────────────────────────────────────────────────

function toggleTheme() {
    state.theme = state.theme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', state.theme);
    applyTheme();
}

function applyTheme() {
    document.documentElement.setAttribute('data-theme', state.theme);
    if (el.darkToggle) {
        el.darkToggle.textContent = state.theme === 'light' ? '🌙' : '☀️';
    }
}

// ── Toasts ───────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div class="toast-body">
            <div class="toast-title">${t('toast_' + type)}</div>
            <div class="toast-msg">${message}</div>
        </div>
    `;
    
    el.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 200);
    }, 4000);
}

// ── Confirmation Modal ──────────────────────────────────────

function confirmAction(title, message, onConfirm) {
    const modal = el.confirmModal;
    const titleEl = document.getElementById('confirm-title');
    const msgEl = document.getElementById('confirm-message');
    const okBtn = document.getElementById('confirm-ok');
    const cancelBtn = document.getElementById('confirm-cancel');
    const closeBtn = document.getElementById('confirm-close');

    titleEl.textContent = title;
    msgEl.textContent = message;
    
    modal.classList.remove('hidden');

    const hide = () => modal.classList.add('hidden');

    okBtn.onclick = () => { onConfirm(); hide(); };
    cancelBtn.onclick = hide;
    closeBtn.onclick = hide;
}

// ── Dashboard Rendering ──────────────────────────────────────

async function loadExpirySegment(days, isPreview = true) {
    const container = document.getElementById('expiry-table-container');
    if (!container) return;
    
    container.innerHTML = '<div class="text-center py-16"><div class="spinner"></div></div>';
    
    try {
        const data = await API.expiringLicenses(0, days, isPreview ? 5 : null);
        
        if (data.length > 0) {
            container.innerHTML = `
                <div class="table-wrapper">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>${t('col_license')}</th>
                                <th>${t('col_driver')}</th>
                                <th>${t('col_vehicle')}</th>
                                <th>${t('col_company')}</th>
                                <th>${t('col_expiry')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.map(ex => `
                                <tr>
                                    <td><strong>${ex.license_number}</strong></td>
                                    <td>${ex.driver_name || '-'}</td>
                                    <td>${ex.vehicle_reg || '-'}</td>
                                    <td>${ex.company_name || '-'}</td>
                                    <td><span class="badge badge-amber">${ex.expiration_date}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${isPreview ? `
                    <div class="d-flex justify-end mt-16">
                        <button class="btn btn-ghost" id="btn-load-full-expiry">${t('btn_view_full')}</button>
                    </div>
                ` : ''}
            `;
            
            if (isPreview) {
                const btn = document.getElementById('btn-load-full-expiry');
                if (btn) {
                    btn.onclick = () => loadExpirySegment(days, false);
                }
            }
        } else {
            container.innerHTML = `<div class="empty-state"><p>${t('no_expiring')}</p></div>`;
        }
    } catch (err) {
        showToast(err.message, 'error');
        container.innerHTML = `<div class="empty-state"><p>${err.message}</p></div>`;
    }
}

async function renderDashboard() {
    try {
        const stats = await API.stats();
        const advStats = await API.statsAdvanced();
        const forecast = advStats.activity?.forecast || [];

        let forecastHtml = `
            <div class="card mb-16">
                <div class="card-header"><h3 class="card-title">🔮 ${t('predictive_insights') || 'Predictive Insights: Expiry Forecast'}</h3></div>
                <div class="card-body">
                    <div class="stats-grid">
                        ${forecast.map((f, idx) => {
                            const days = (idx + 1) * 30;
                            return `
                                <div class="stat-card clickable-forecast-card" data-days="${days}" style="border-left: 4px solid var(--warning); cursor: pointer;">
                                    <div class="stat-icon yellow">🔮</div>
                                    <div class="stat-info">
                                        <div class="stat-value">${f.count}</div>
                                        <div class="stat-label">${t('expiring_' + days)}</div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                    <p class="text-muted mt-8 text-sm">Automated forecast based on current active contracts and their respective expiration dates.</p>
                </div>
            </div>
        `;

        el.content.innerHTML = `
            <div class="stats-grid mb-24">
                <div class="stat-card" id="card-active-licenses" style="border-top: 4px solid var(--accent); cursor: pointer;">
                    <div class="stat-icon purple">📄</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.active_licenses}</div>
                        <div class="stat-label">${t('stat_active')}</div>
                    </div>
                </div>
                <div class="stat-card" id="card-expired-licenses" style="border-top: 4px solid var(--danger); cursor: pointer;">
                    <div class="stat-icon red">⏰</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.expired_licenses}</div>
                        <div class="stat-label">${t('stat_expired')}</div>
                    </div>
                </div>
                <div class="stat-card" id="card-total-vehicles" style="border-top: 4px solid var(--info); cursor: pointer;">
                    <div class="stat-icon blue">🚚</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.total_vehicles}</div>
                        <div class="stat-label">${t('stat_vehicles')}</div>
                    </div>
                </div>
                <div class="stat-card" id="card-total-drivers" style="border-top: 4px solid var(--success); cursor: pointer;">
                    <div class="stat-icon green">👤</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.total_drivers}</div>
                        <div class="stat-label">${t('stat_drivers')}</div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-24">
                <div class="card-header d-flex justify-between align-center" style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 class="card-title">🛡️ ${t('expiring_preview_title')}</h3>
                    <div class="activity-tabs" id="expiry-tabs">
                        <button class="activity-tab active" data-days="30">${t('expiring_30')}</button>
                        <button class="activity-tab" data-days="60">${t('expiring_60')}</button>
                        <button class="activity-tab" data-days="90">${t('expiring_90')}</button>
                    </div>
                </div>
                <div class="card-body">
                    <div id="expiry-table-container">
                        <div class="text-center py-16"><div class="spinner"></div></div>
                    </div>
                </div>
            </div>

            <h2 class="mb-16 mt-24">📈 ${t('system_forecasting') || 'System Forecasting'}</h2>
            ${forecastHtml}
        `;

        const tabs = document.querySelectorAll('#expiry-tabs button');
        tabs.forEach(btn => {
            btn.onclick = () => {
                tabs.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const days = parseInt(btn.dataset.days, 10);
                loadExpirySegment(days, true);
            };
        });

        const cardActive = document.getElementById('card-active-licenses');
        const cardExpired = document.getElementById('card-expired-licenses');
        const cardVehicles = document.getElementById('card-total-vehicles');
        const cardDrivers = document.getElementById('card-total-drivers');

        if (cardActive) {
            cardActive.onclick = () => {
                searchParams.status = 'active';
                searchParams.search = '';
                searchParams.activity_location = '';
                searchParams.carrier = '';
                searchParams.page = 1;
                navigateTo('search');
            };
        }
        if (cardExpired) {
            cardExpired.onclick = () => {
                searchParams.status = 'expired';
                searchParams.search = '';
                searchParams.activity_location = '';
                searchParams.carrier = '';
                searchParams.page = 1;
                navigateTo('search');
            };
        }
        if (cardVehicles) {
            cardVehicles.onclick = () => {
                navigateTo('vehicles');
            };
        }
        if (cardDrivers) {
            cardDrivers.onclick = () => {
                navigateTo('drivers');
            };
        }

        document.querySelectorAll('.clickable-forecast-card').forEach(card => {
            card.onclick = () => {
                const days = card.dataset.days;
                const tab = document.querySelector(`#expiry-tabs button[data-days="${days}"]`);
                if (tab) {
                    tabs.forEach(b => b.classList.remove('active'));
                    tab.classList.add('active');
                    loadExpirySegment(parseInt(days, 10), true);
                    tab.scrollIntoView({ behavior: 'smooth' });
                }
            };
        });

        await loadExpirySegment(30, true);
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Settings Page ────────────────────────────────────────────

async function renderSettings() {
    try {
        const currentLang = localStorage.getItem('lang') || 'ar';
        const currentTheme = state.theme || 'light';
        const username = sessionStorage.getItem('auth_user') || 'admin';

        el.content.innerHTML = `
        <div class="settings-page">
            <div class="settings-grid">

                <!-- Account Info -->
                <div class="settings-card">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">👤</span>
                        <h3>${t('settings_account')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <div class="settings-info-row">
                            <span class="settings-label">${t('settings_username')}</span>
                            <span class="settings-value" id="settings-disp-username">${username}</span>
                        </div>
                        <div class="settings-info-row">
                            <span class="settings-label">${t('settings_role')}</span>
                            <span class="settings-value badge badge-green" style="font-size:12px; padding:2px 10px;">Admin</span>
                        </div>
                        <div class="settings-info-row">
                            <span class="settings-label">${t('settings_app_version')}</span>
                            <span class="settings-value">v2.0</span>
                        </div>
                    </div>
                </div>

                <!-- Change Username -->
                <div class="settings-card">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">👤</span>
                        <h3>${t('settings_change_username')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <form id="change-username-form" autocomplete="off">
                            <div class="form-group">
                                <label>${t('settings_new_username')}</label>
                                <input type="text" class="form-control" id="username-new" required value="${username}">
                            </div>
                            <div class="form-group">
                                <label>${t('settings_current_password')}</label>
                                <input type="password" class="form-control" id="username-pw-current" required>
                            </div>
                            <div class="field-error" id="username-error"></div>
                            <button type="submit" class="btn btn-primary mt-8" id="username-save-btn">${t('settings_save_username')}</button>
                        </form>
                    </div>
                </div>

                <!-- Change Password -->
                <div class="settings-card">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">🔑</span>
                        <h3>${t('settings_change_password')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <form id="change-pw-form" autocomplete="off">
                            <div class="form-group">
                                <label>${t('settings_current_password')}</label>
                                <input type="password" class="form-control" id="pw-current" required>
                            </div>
                            <div class="form-group">
                                <label>${t('settings_new_password')}</label>
                                <input type="password" class="form-control" id="pw-new" required minlength="6">
                            </div>
                            <div class="form-group">
                                <label>${t('settings_confirm_password')}</label>
                                <input type="password" class="form-control" id="pw-confirm" required>
                            </div>
                            <div class="field-error" id="pw-error"></div>
                            <button type="submit" class="btn btn-primary mt-8" id="pw-save-btn">${t('settings_save_password')}</button>
                        </form>
                    </div>
                </div>

                <!-- Theme -->
                <div class="settings-card">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">🎨</span>
                        <h3>${t('settings_theme')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <p class="settings-desc">${t('settings_theme_desc')}</p>
                        <div class="settings-toggle-group">
                            <button class="settings-toggle-btn ${currentTheme === 'light' ? 'active' : ''}" data-theme-val="light">
                                ☀️ ${t('settings_theme_light')}
                            </button>
                            <button class="settings-toggle-btn ${currentTheme === 'dark' ? 'active' : ''}" data-theme-val="dark">
                                🌙 ${t('settings_theme_dark')}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Language -->
                <div class="settings-card">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">🌐</span>
                        <h3>${t('settings_language')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <p class="settings-desc">${t('settings_language_desc')}</p>
                        <div class="settings-toggle-group settings-lang-group">
                            <button class="settings-toggle-btn ${currentLang === 'ar' ? 'active' : ''}" data-lang-val="ar">
                                🇩🇿 العربية
                            </button>
                            <button class="settings-toggle-btn ${currentLang === 'fr' ? 'active' : ''}" data-lang-val="fr">
                                🇫🇷 Français
                            </button>
                            <button class="settings-toggle-btn ${currentLang === 'en' ? 'active' : ''}" data-lang-val="en">
                                🇬🇧 English
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Logout -->
                <div class="settings-card settings-card-danger">
                    <div class="settings-card-header">
                        <span class="settings-card-icon">🚪</span>
                        <h3>${t('settings_logout')}</h3>
                    </div>
                    <div class="settings-card-body">
                        <p class="settings-desc">${t('settings_logout_desc')}</p>
                        <button class="btn btn-danger" id="settings-logout-btn">🚪 ${t('settings_logout_btn') || 'Logout'}</button>
                    </div>
                </div>

                <!-- Contact Us -->
                <div class="contact-card">
                    <div class="contact-header">
                        <span class="settings-card-icon">📬</span>
                        <h3 class="contact-title">${t('sect_contact_us')}</h3>
                    </div>
                    <div class="contact-body">
                        <p class="contact-devs">${t('contact_devs')}</p>
                        <h4 class="contact-authors">Bendahmouche Abde Raouf &amp; Hamzaoui Abderraouf</h4>
                        <p class="contact-univ">${t('contact_univ')}</p>
                        <p style="margin-top: 12px;">${t('contact_prompt')}</p>
                        <div class="contact-links">
                            <a href="mailto:hamzaouihamoudi73@gmail.com" class="contact-email-btn">
                                ✉️ hamzaouihamoudi73@gmail.com
                            </a>
                            <a href="mailto:abderaoufbendahmouche@gmail.com" class="contact-email-btn">
                                ✉️ abderaoufbendahmouche@gmail.com
                            </a>
                        </div>
                    </div>
                </div>

            </div>
        </div>
        `;

        // ── Change Username Handler ──
        document.getElementById('change-username-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errEl = document.getElementById('username-error');
            errEl.textContent = '';

            const newUsername = document.getElementById('username-new').value.trim();
            const password = document.getElementById('username-pw-current').value;

            if (!newUsername) {
                errEl.textContent = t('invalid_required');
                return;
            }

            const saveBtn = document.getElementById('username-save-btn');
            saveBtn.disabled = true;
            saveBtn.textContent = t('btn_saving') || 'Saving...';

            try {
                await API.changeUsername(username, newUsername, password);
                
                // Update session state
                sessionStorage.setItem('auth_user', newUsername);
                showToast(t('settings_username_success'), 'success');
                
                // Instant update
                syncSidebarProfile();
                
                // Re-render to reflect new settings state
                await renderSettings();
            } catch (err) {
                if (err.message.includes('401') || err.message.toLowerCase().includes('password')) {
                    errEl.textContent = t('settings_username_error') || 'Current password is incorrect.';
                } else if (err.message.includes('taken') || err.message.includes('400')) {
                    errEl.textContent = t('settings_username_taken') || 'New username is already taken.';
                } else {
                    errEl.textContent = err.message;
                }
                showToast(errEl.textContent, 'error');
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = t('settings_save_username');
            }
        });

        // ── Change Password Handler ──
        document.getElementById('change-pw-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const errEl = document.getElementById('pw-error');
            errEl.textContent = '';

            const currentPw = document.getElementById('pw-current').value;
            const newPw = document.getElementById('pw-new').value;
            const confirmPw = document.getElementById('pw-confirm').value;

            if (newPw.length < 6) {
                errEl.textContent = t('settings_pw_min_length');
                return;
            }
            if (newPw !== confirmPw) {
                errEl.textContent = t('settings_pw_mismatch');
                return;
            }

            const saveBtn = document.getElementById('pw-save-btn');
            saveBtn.disabled = true;
            saveBtn.textContent = t('btn_saving') || 'Saving...';

            try {
                await API.changePassword(username, currentPw, newPw);
                showToast(t('settings_pw_success'), 'success');
                document.getElementById('change-pw-form').reset();
            } catch (err) {
                errEl.textContent = err.message;
                showToast(err.message, 'error');
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = t('settings_save_password');
            }
        });

        // ── Theme Toggle ──
        document.querySelectorAll('[data-theme-val]').forEach(btn => {
            btn.addEventListener('click', () => {
                state.theme = btn.dataset.themeVal;
                localStorage.setItem('theme', state.theme);
                applyTheme();
                document.querySelectorAll('[data-theme-val]').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });

        // ── Language Selector ──
        document.querySelectorAll('[data-lang-val]').forEach(btn => {
            btn.addEventListener('click', () => {
                setLanguage(btn.dataset.langVal);
            });
        });

        // ── Logout ──
        document.getElementById('settings-logout-btn').addEventListener('click', async () => {
            try {
                const token = sessionStorage.getItem('auth_token');
                if (token) {
                    await fetch((window._API_BASE || API_BASE) + '/auth/logout', {
                        method: 'POST',
                        headers: { Authorization: 'Bearer ' + token }
                    });
                }
            } catch (_) { /* best-effort */ }
            sessionStorage.clear();
            window.location.replace('pages/login.html');
        });

    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Search Page ──────────────────────────────────────────────

let searchParams = { page: 1, limit: 50, search: '', status: '', carrier: '', activity_location: '' };
let deletedSearchParams = { page: 1, limit: 50, search: '', status: '', activity_location: '', contract_type: '' };

async function renderSearch() {
    el.content.innerHTML = `
        <div class="card mb-16">
            <div class="card-body">
                <div class="search-bar">
                    <div class="search-input-wrap">
                        <span class="search-icon">🔍</span>
                        <input type="text" class="form-control" id="search-input" placeholder="${t('search_ph')}" value="${searchParams.search}">
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_status')}</label>
                        <select class="form-control" id="filter-status">
                            <option value="">${t('opt_all')}</option>
                            <option value="active" ${searchParams.status === 'active' ? 'selected' : ''}>${t('opt_active')}</option>
                            <option value="expired" ${searchParams.status === 'expired' ? 'selected' : ''}>${t('opt_expired')}</option>
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('carrier_type') || 'Carrier Type'}</label>
                        <select class="form-control" id="filter-carrier">
                            <option value="">${t('opt_all')}</option>
                            <option value="Public" ${searchParams.carrier === 'Public' ? 'selected' : ''}>${t('opt_public') || 'Public'}</option>
                            <option value="Private" ${searchParams.carrier === 'Private' ? 'selected' : ''}>${t('opt_private') || 'Private'}</option>
                        </select>
                    </div>
                    <div style="width: 180px">
                        <label>${t('lbl_location')}</label>
                        ${buildLocationSelectHTML('filter-location', searchParams.activity_location, 'filter-location')}
                    </div>
                    <div class="d-flex align-center gap-8 mt-16">
                        <button class="btn btn-primary" id="btn-search">${t('btn_search')}</button>
                        <button class="btn btn-ghost" id="btn-reset">${t('btn_reset')}</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="action-toolbar">
            <button class="btn btn-success" id="btn-add-contract">➕ ${t('btn_add_contract')}</button>
            <button class="btn btn-primary" id="btn-edit-contract">✏️ ${t('btn_edit_selected_contract')}</button>
        </div>

        <div class="table-wrapper card">
            <table id="results-table">
                <thead>
                    <tr>
                        <th>${t('col_record')}</th>
                        <th>${t('col_license')}</th>
                        <th>${t('col_driver')}</th>
                        <th>${t('col_vehicle')}</th>
                        <th>${t('col_company')}</th>
                        <th>${t('col_location')}</th>
                        <th>${t('col_expiry')}</th>
                        <th>${t('col_status')}</th>
                        <th>${t('col_actions')}</th>
                    </tr>
                </thead>
                <tbody id="results-body">
                    <tr><td colspan="9" class="text-center"><div class="spinner"></div></td></tr>
                </tbody>
            </table>
        </div>
        <div id="pagination" class="pagination"></div>
    `;

    const searchInput = document.getElementById('search-input');
    const filterStatus = document.getElementById('filter-status');
    const filterLocation = document.getElementById('filter-location');
    const filterCarrier = document.getElementById('filter-carrier');

    const triggerSearch = debounce(() => {
        searchParams.search = searchInput.value;
        searchParams.status = filterStatus.value;
        searchParams.activity_location = filterLocation.value;
        searchParams.carrier = filterCarrier.value;
        searchParams.page = 1;
        loadSearchResults();
    }, 400);

    searchInput.oninput = triggerSearch;
    filterStatus.onchange = triggerSearch;
    filterLocation.onchange = triggerSearch;
    filterCarrier.onchange = triggerSearch;

    document.getElementById('btn-search').onclick = triggerSearch;

    document.getElementById('btn-add-contract').onclick = () => navigateTo('add-contract');

    document.getElementById('btn-edit-contract').onclick = () => {
        if (state.selectedLicenseId) {
            openEditModal(state.selectedLicenseId);
        } else {
            showToast(t('select_contract_first'), 'warning');
        }
    };

    document.getElementById('btn-reset').onclick = () => {
        searchParams = { page: 1, limit: 50, search: '', status: '', carrier: '', activity_location: '' };
        state.selectedLicenseId = null;
        renderSearch();
    };

    loadSearchResults();
}

async function loadSearchResults() {
    const tbody = document.getElementById('results-body');
    const pagination = document.getElementById('pagination');
    
    try {
        const result = await API.getLicenses(searchParams);
        
        if (result.records.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="9">
                        <div class="empty-state">
                            <div class="empty-icon">📂</div>
                            <h3>${t('no_records') || 'No records found'}</h3>
                            <p>${t('try_adjust_filter') || 'Try adjusting your filters or search terms'}</p>
                            <button class="btn btn-primary mt-16" onclick="navigateTo('add-contract')">${t('btn_add_new') || 'Add New Contract'}</button>
                        </div>
                    </td>
                </tr>
            `;
            pagination.innerHTML = '';
            return;
        }

        tbody.innerHTML = result.records.map(r => `
            <tr class="clickable-row ${state.selectedLicenseId == r.id ? 'selected-row' : ''}" data-id="${r.id}">
                <td>${r.record_number}</td>
                <td>${r.license_number}</td>
                <td>${r.driver_name}</td>
                <td>${r.vehicle_reg}</td>
                <td>${r.company_name}</td>
                <td>${r.activity_location || '-'}</td>
                <td>${r.expiration_date}</td>
                <td><span class="badge ${r.status === 'active' ? 'badge-green' : 'badge-red'}">${t('opt_' + r.status)}</span></td>
                <td>
                    <div class="d-flex gap-8">
                        <button class="btn btn-sm btn-ghost edit-btn" data-id="${r.id}" title="${t('btn_edit')}">✏️</button>
                        <button class="btn btn-sm btn-danger delete-btn" data-id="${r.id}" data-num="${r.record_number}">🗑️</button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Row selection click handler
        tbody.querySelectorAll('tr.clickable-row').forEach(row => {
            row.onclick = (e) => {
                if (e.target.closest('button')) return;
                tbody.querySelectorAll('tr.clickable-row').forEach(r => r.classList.remove('selected-row'));
                row.classList.add('selected-row');
                state.selectedLicenseId = row.getAttribute('data-id');
            };
        });

        // Action events
        tbody.querySelectorAll('.edit-btn').forEach(btn => {
            btn.onclick = (e) => {
                e.stopPropagation();
                openEditModal(btn.getAttribute('data-id'));
            };
        });

        tbody.querySelectorAll('.delete-btn').forEach(btn => {
            btn.onclick = () => {
                const id = btn.getAttribute('data-id');
                const num = btn.getAttribute('data-num');
                confirmAction(t('confirm_delete_title'), `${t('confirm_delete_msg')} (${num})`, async () => {
                    try {
                        await API.deleteLicense(id);
                        showToast(t('deleted_ok'));
                        loadSearchResults();
                    } catch (err) {
                        showToast(err.message, 'error');
                    }
                });
            };
        });

        // Pagination UI
        const totalPages = Math.ceil(result.total / result.limit);
        pagination.innerHTML = `
            <div class="pagination-info">${t('showing')} ${(result.page-1)*result.limit + 1} - ${Math.min(result.page*result.limit, result.total)} ${t('of')} ${result.total}</div>
            <div class="pagination-btns">
                <button class="page-btn" ${result.page === 1 ? 'disabled' : ''} onclick="changePage(${result.page-1})">«</button>
                ${Array.from({length: totalPages}, (_, i) => i + 1).map(p => `
                    <button class="page-btn ${p === result.page ? 'active' : ''}" onclick="changePage(${p})">${p}</button>
                `).join('')}
                <button class="page-btn" ${result.page === totalPages ? 'disabled' : ''} onclick="changePage(${result.page+1})">»</button>
            </div>
        `;

        const resultsTable = document.getElementById('results-table');
        if (resultsTable) {
            resultsTable.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="error-state">${err.message}</td></tr>`;
    }
}

window.changePage = (p) => {
    searchParams.page = p;
    loadSearchResults();
};

// ── Deleted Contracts Page ──────────────────────────────

async function renderDeletedContracts() {
    el.content.innerHTML = `
        <div class="card mb-16">
            <div class="card-body">
                <div class="search-bar">
                    <div class="search-input-wrap">
                        <span class="search-icon">🔍</span>
                        <input type="text" class="form-control" id="deleted-search-input" placeholder="${t('search_ph')}" value="${deletedSearchParams.search}">
                    </div>
                    <div style="width: 180px">
                        <label>${t('deleted_status_filter')}</label>
                        <select class="form-control" id="deleted-filter-status">
                            <option value="">${t('opt_all')}</option>
                            <option value="active" ${deletedSearchParams.status === 'active' ? 'selected' : ''}>${t('opt_active')}</option>
                            <option value="expired" ${deletedSearchParams.status === 'expired' ? 'selected' : ''}>${t('opt_expired')}</option>
                        </select>
                    </div>
                    <div style="width: 180px">
                        <label>${t('lbl_location')}</label>
                        ${buildLocationSelectHTML('deleted-filter-location', deletedSearchParams.activity_location, 'deleted-filter-location')}
                    </div>
                    <div class="d-flex align-center gap-8 mt-16">
                        <button class="btn btn-primary" id="btn-deleted-search">${t('btn_search')}</button>
                        <button class="btn btn-ghost" id="btn-deleted-reset">${t('btn_reset')}</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="table-wrapper card">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>${t('col_record')}</th>
                        <th>${t('col_license')}</th>
                        <th>${t('col_driver')}</th>
                        <th>${t('col_vehicle')}</th>
                        <th>${t('col_company')}</th>
                        <th>${t('col_location')}</th>
                        <th>${t('col_status')}</th>
                        <th>${t('col_actions')}</th>
                    </tr>
                </thead>
                <tbody id="deleted-results-body">
                    <tr><td colspan="9" class="text-center"><div class="spinner"></div></td></tr>
                </tbody>
            </table>
        </div>
        <div id="deleted-pagination" class="pagination"></div>
    `;

    const searchInput = document.getElementById('deleted-search-input');
    const filterStatus = document.getElementById('deleted-filter-status');
    const filterLocation = document.getElementById('deleted-filter-location');

    const triggerDeletedSearch = debounce(() => {
        deletedSearchParams.search = searchInput.value;
        deletedSearchParams.status = filterStatus.value;
        deletedSearchParams.activity_location = filterLocation.value;
        deletedSearchParams.page = 1;
        loadDeletedResults();
    }, 400);

    searchInput.oninput = triggerDeletedSearch;
    filterStatus.onchange = triggerDeletedSearch;
    filterLocation.onchange = triggerDeletedSearch;

    document.getElementById('btn-deleted-search').onclick = triggerDeletedSearch;

    document.getElementById('btn-deleted-reset').onclick = () => {
        deletedSearchParams = { page: 1, limit: 50, search: '', status: '', activity_location: '' };
        renderDeletedContracts();
    };

    loadDeletedResults();
}

async function loadDeletedResults() {
    const tbody = document.getElementById('deleted-results-body');
    const pagination = document.getElementById('deleted-pagination');

    try {
        const result = await API.getDeletedLicenses(deletedSearchParams);
        if (result.records.length === 0) {
            tbody.innerHTML = `<tr><td colspan="9" class="empty-state">${t('no_deleted_records')}</td></tr>`;
            pagination.innerHTML = '';
            return;
        }

        tbody.innerHTML = result.records.map(r => `
            <tr>
                <td>${r.id}</td>
                <td>${r.record_number}</td>
                <td>${r.license_number}</td>
                <td>${r.driver_name}</td>
                <td>${r.vehicle_reg}</td>
                <td>${r.company_name}</td>
                <td>${r.activity_location || '-'}</td>
                <td><span class="badge ${r.status === 'active' ? 'badge-green' : 'badge-red'}">${t('opt_' + r.status)}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary restore-btn" data-id="${r.id}">${t('btn_restore')}</button>
                </td>
            </tr>
        `).join('');

        tbody.querySelectorAll('.restore-btn').forEach(btn => {
            btn.onclick = async () => {
                try {
                    await API.restoreLicense(btn.getAttribute('data-id'));
                    showToast(t('restore_ok'), 'success');
                    loadDeletedResults();
                } catch (err) {
                    if (err.message.includes('Associated vehicle or company is deleted') || err.message.includes('missing or deleted')) {
                        showToast(t('err_cannot_restore_deleted'), 'error');
                    } else {
                        showToast(err.message, 'error');
                    }
                }
            };
        });

        const totalPages = Math.ceil(result.total / result.limit);
        pagination.innerHTML = `
            <div class="pagination-info">${t('showing')} ${(result.page-1)*result.limit + 1} - ${Math.min(result.page*result.limit, result.total)} ${t('of')} ${result.total}</div>
            <div class="pagination-btns">
                <button class="page-btn" ${result.page === 1 ? 'disabled' : ''} onclick="changeDeletedPage(${result.page-1})">«</button>
                ${Array.from({length: totalPages}, (_, i) => i + 1).map(p => `
                    <button class="page-btn ${p === result.page ? 'active' : ''}" onclick="changeDeletedPage(${p})">${p}</button>
                `).join('')}
                <button class="page-btn" ${result.page === totalPages ? 'disabled' : ''} onclick="changeDeletedPage(${result.page+1})">»</button>
            </div>
        `;
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="9" class="error-state">${err.message}</td></tr>`;
    }
}

window.changeDeletedPage = (p) => {
    deletedSearchParams.page = p;
    loadDeletedResults();
};

// ── Statistics Page ──────────────────────────────────────────
// Displays: KPI Cards → Distribution Charts → Activity Analysis
// Uses Chart.js for professional, responsive data visualization

/**
 * ===================================================================
 *  STATISTICS PAGE RENDERER
 * ===================================================================
 * What it does: Orchestrates the rendering of the entire statistics dashboard.
 * Why it exists: To provide a modern, insightful, and performant analytics view.
 * What data it uses: Fetches comprehensive statistics from the backend API.
 */
async function renderStatistics() {
    Object.values(statsCharts).forEach(chart => chart.destroy());
    statsCharts = {};

    el.content.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const advanced = await API.statsAdvanced();

        const kpis = advanced?.kpis || { total: 0, active: 0, inactive: 0, public: 0, private: 0, total_licenses: 0, active_licenses: 0, expired_licenses: 0 };
        const municipalities = advanced?.municipalities || {};
        const activity = advanced?.activity || { daily: [], weekly: [], monthly: [], yearly: [] };
        const municipalityStats = Object.entries(municipalities)
            .map(([name, data]) => ({ name, ...data }))
            .sort((a, b) => b.total - a.total);

        const topMunicipalities = municipalityStats.slice(0, 10);

        const html = `
            <div class="stats-dashboard">
                <!-- Tier 1: KPI Cards -->
                <div class="section-title" style="margin-top:0">${t('sect_carrier_stats') || 'Carrier Statistics'}</div>
                <div class="kpi-section">
                    <div class="kpi-card total">
                        <div class="kpi-title">📊 ${t('kpi_total_carriers')}</div>
                        <div class="kpi-value">${kpis.total}</div>
                    </div>
                    <div class="kpi-card active">
                        <div class="kpi-title">✅ ${t('kpi_active_carriers')}</div>
                        <div class="kpi-value">${kpis.active}</div>
                    </div>
                    <div class="kpi-card inactive">
                        <div class="kpi-title">❌ ${t('kpi_inactive_carriers')}</div>
                        <div class="kpi-value">${kpis.inactive}</div>
                    </div>
                    <div class="kpi-card public">
                        <div class="kpi-title">🏛️ ${t('kpi_public_carriers')}</div>
                        <div class="kpi-value">${kpis.public}</div>
                    </div>
                    <div class="kpi-card private">
                        <div class="kpi-title">🏢 ${t('kpi_private_carriers')}</div>
                        <div class="kpi-value">${kpis.private}</div>
                    </div>
                </div>

                <div class="section-title mt-16">${t('sect_license_stats') || 'License Statistics'}</div>
                <div class="kpi-section">
                    <div class="kpi-card total">
                        <div class="kpi-title">📄 ${t('kpi_total_licenses')}</div>
                        <div class="kpi-value">${kpis.total_licenses || 0}</div>
                    </div>
                    <div class="kpi-card active">
                        <div class="kpi-title">✅ ${t('kpi_active_licenses')}</div>
                        <div class="kpi-value">${kpis.active_licenses || 0}</div>
                    </div>
                    <div class="kpi-card inactive">
                        <div class="kpi-title">❌ ${t('kpi_expired_licenses')}</div>
                        <div class="kpi-value">${kpis.expired_licenses || 0}</div>
                    </div>
                </div>

                <!-- Tier 2: Distribution -->
                <div class="distribution-section">
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_municipality_dist')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="municipalityPieChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_carrier_type')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="carrierTypePieChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_license_status')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="licenseStatusPieChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Tier 3: Activity Analysis -->
                <div class="activity-section">
                    <div class="activity-tabs">
                        <button class="activity-tab active" data-period="weekly">${t('weekly')}</button>
                        <button class="activity-tab" data-period="monthly">${t('monthly')}</button>
                        <button class="activity-tab" data-period="yearly">${t('yearly')}</button>
                    </div>
                    <div class="chart-container">
                         <div class="chart-title">${t('chart_title_activity')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="activityLineChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        el.content.innerHTML = html;

        // Initialize charts
        initMunicipalityPieChart(topMunicipalities);
        initCarrierTypePieChart(kpis);
        initLicenseStatusPieChart(kpis);
        initActivityLineChart('weekly', activity);

        // Setup event listeners
        setupActivityTabs(activity);

    } catch (error) {
        console.error("Failed to render statistics:", error);
        el.content.innerHTML = `<div class="empty-state"><h2>${t('error_loading_stats')}</h2><p>${error.message}</p></div>`;
    }
}

/**
 * ===================================================================
 *  CHART INITIALIZATION HELPERS
 * ===================================================================
 */

function initMunicipalityPieChart(municipalityRows) {
    const ctx = document.getElementById('municipalityPieChart').getContext('2d');
    const rows = Array.isArray(municipalityRows) ? municipalityRows : [];
    const labels = rows.map(m => m.name);
    const data = rows.map(m => m.total);

    const colorPalette = generateColorPalette(labels.length);

    statsCharts.municipalityPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colorPalette,
                hoverBackgroundColor: colorPalette.map(c => adjustBrightness(c, 1.2)),
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements && activeElements.length > 0) {
                    const firstPoint = activeElements[0];
                    const label = statsCharts.municipalityPie.data.labels[firstPoint.index];
                    
                    searchParams.activity_location = label;
                    searchParams.status = '';
                    searchParams.search = '';
                    searchParams.carrier = '';
                    searchParams.page = 1;
                    navigateTo('search');
                }
            }
        }
    });
}

function initCarrierTypePieChart(carrierTotals) {
    const ctx = document.getElementById('carrierTypePieChart').getContext('2d');
    const data = [carrierTotals?.public || 0, carrierTotals?.private || 0];

    statsCharts.carrierPie = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [t('kpi_public_carriers'), t('kpi_private_carriers')],
            datasets: [{
                data: data,
                backgroundColor: ['#3b82f6', '#8b5cf6'],
                hoverBackgroundColor: [adjustBrightness('#3b82f6', 1.2), adjustBrightness('#8b5cf6', 1.2)],
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((context.parsed / total) * 100).toFixed(1);
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements && activeElements.length > 0) {
                    const firstPoint = activeElements[0];
                    const carrierVal = firstPoint.index === 0 ? 'Public' : 'Private';
                    
                    searchParams.carrier = carrierVal;
                    searchParams.status = '';
                    searchParams.search = '';
                    searchParams.activity_location = '';
                    searchParams.page = 1;
                    navigateTo('search');
                }
            }
        }
    });
}

function initLicenseStatusPieChart(kpis) {
    const ctx = document.getElementById('licenseStatusPieChart').getContext('2d');
    const data = [kpis?.active_licenses || 0, kpis?.expired_licenses || 0];

    statsCharts.licenseStatusPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: [t('opt_active'), t('opt_expired')],
            datasets: [{
                data: data,
                backgroundColor: ['#10b981', '#ef4444'],
                hoverBackgroundColor: [adjustBrightness('#10b981', 1.2), adjustBrightness('#ef4444', 1.2)],
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements && activeElements.length > 0) {
                    const firstPoint = activeElements[0];
                    const statusVal = firstPoint.index === 0 ? 'active' : 'expired';
                    
                    searchParams.status = statusVal;
                    searchParams.search = '';
                    searchParams.carrier = '';
                    searchParams.activity_location = '';
                    searchParams.page = 1;
                    navigateTo('search');
                }
            }
        }
    });
}

function initActivityLineChart(period, activityData) {
    if (statsCharts.activityLine) {
        statsCharts.activityLine.destroy();
    }
    const ctx = document.getElementById('activityLineChart').getContext('2d');
    const periodData = Array.isArray(activityData?.[period]) ? activityData[period] : [];
    
    const labels = periodData.map(d => d.date || d.week || d.month || d.year);
    const data = periodData.map(d => d.count);

    statsCharts.activityLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: t('chart_label_new_activity'),
                data: data,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#10b981',
                pointRadius: 3,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(128, 128, 128, 0.1)' }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        maxRotation: 45,
                        autoSkip: true,
                        maxTicksLimit: 15,
                    }
                }
            },
            onClick: (event, activeElements) => {
                if (activeElements && activeElements.length > 0) {
                    const firstPoint = activeElements[0];
                    const label = statsCharts.activityLine.data.labels[firstPoint.index];
                    const val = statsCharts.activityLine.data.datasets[firstPoint.datasetIndex].data[firstPoint.index];
                    const countText = t('records') || 'contracts';
                    showToast(`${label}: ${val} ${countText}`, 'info');
                }
            }
        }
    });
}




/**
 * ===================================================================
 *  EVENT HANDLERS & UTILITIES
 * ===================================================================
 */

/**
 * What it does: Sets up click event listeners for the activity time period tabs.
 * Why it exists: To allow users to dynamically switch the view of the activity line chart.
 * What data it uses: The full \`activity\` data object to pass to the chart initializer.
 */
function setupActivityTabs(activityData) {
    const tabs = document.querySelectorAll('.activity-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            const period = tab.getAttribute('data-period');
            initActivityLineChart(period, activityData);
        });
    });
}

/**
 * What it does: Generates a palette of distinct, visually appealing colors.
 * Why it exists: To provide consistent and professional coloring for charts with multiple data points.
 * What data it uses: A count of the number of colors needed.
 */
function generateColorPalette(count) {
    const baseColors = [
        '#3b82f6', '#10b981', '#ef4444', '#f97316', '#8b5cf6',
        '#06b6d4', '#d946ef', '#f59e0b', '#65a30d', '#ec4899'
    ];
    const palette = [];
    for (let i = 0; i < count; i++) {
        palette.push(baseColors[i % baseColors.length]);
    }
    return palette;
}

/**
 * What it does: Adjusts the brightness of a hex color.
 * Why it exists: To create simple hover effects for chart elements without defining extra CSS.
 * What data it uses: A hex color string and a brightness factor.
 */
function adjustBrightness(color, factor) {
    const usePound = color.startsWith('#');
    if (usePound) color = color.slice(1);
    const num = parseInt(color, 16);
    let r = (num >> 16) * factor;
    let g = ((num >> 8) & 0x00FF) * factor;
    let b = (num & 0x0000FF) * factor;
    r = Math.min(255, Math.floor(r));
    g = Math.min(255, Math.floor(g));
    b = Math.min(255, Math.floor(b));
    return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
}

// ── Multi-item helpers for Vehicles and Drivers ──
// In-memory arrays for the active form (shared by add-contract & edit-modal)
let _formVehicles = [];
let _formDrivers = [];

function getVehiclesListFromForm() { return [..._formVehicles]; }
function getDriversListFromForm() { return [..._formDrivers]; }

// ── Render vehicle table into a container ──
function renderVehicleTable(container) {
    if (_formVehicles.length === 0) {
        container.innerHTML = `<div class="entity-empty">No vehicles added yet.</div>`;
        return;
    }
    container.innerHTML = `
        <table class="entity-table">
            <thead><tr>
                <th>#</th>
                <th>${t('vehicle_reg')}</th>
                <th>${t('vehicle_type')}</th>
                <th>${t('vehicle_category')}</th>
                <th>${t('col_actions')}</th>
            </tr></thead>
            <tbody>
                ${_formVehicles.map((v, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${v.registration_number || '-'}</td>
                        <td>${v.type || '-'}</td>
                        <td>${v.category || '-'}</td>
                        <td>
                            <div class="entity-actions-cell">
                                <button type="button" class="btn btn-sm btn-ghost veh-edit-btn" data-idx="${i}">✏️ ${t('btn_edit_item')}</button>
                                <button type="button" class="btn btn-sm btn-danger veh-del-btn" data-idx="${i}">🗑️</button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.querySelectorAll('.veh-edit-btn').forEach(btn => {
        btn.onclick = (e) => { e.preventDefault(); openVehicleMiniModal(container, parseInt(btn.dataset.idx)); };
    });
    container.querySelectorAll('.veh-del-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.preventDefault();
            _formVehicles.splice(parseInt(btn.dataset.idx), 1);
            renderVehicleTable(container);
        };
    });
}

// ── Render driver table into a container ──
function renderDriverTable(container) {
    if (_formDrivers.length === 0) {
        container.innerHTML = `<div class="entity-empty">No drivers added yet.</div>`;
        return;
    }
    container.innerHTML = `
        <table class="entity-table">
            <thead><tr>
                <th>#</th>
                <th>${t('driver_name')}</th>
                <th>${t('driver_phone')}</th>
                <th>${t('col_actions')}</th>
            </tr></thead>
            <tbody>
                ${_formDrivers.map((d, i) => `
                    <tr>
                        <td>${i + 1}</td>
                        <td>${d.name || '-'}</td>
                        <td>${d.phone || '-'}</td>
                        <td>
                            <div class="entity-actions-cell">
                                <button type="button" class="btn btn-sm btn-ghost drv-edit-btn" data-idx="${i}">✏️ ${t('btn_edit_item')}</button>
                                <button type="button" class="btn btn-sm btn-danger drv-del-btn" data-idx="${i}">🗑️</button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;

    container.querySelectorAll('.drv-edit-btn').forEach(btn => {
        btn.onclick = (e) => { e.preventDefault(); openDriverMiniModal(container, parseInt(btn.dataset.idx)); };
    });
    container.querySelectorAll('.drv-del-btn').forEach(btn => {
        btn.onclick = (e) => {
            e.preventDefault();
            _formDrivers.splice(parseInt(btn.dataset.idx), 1);
            renderDriverTable(container);
        };
    });
}

// ── Mini-modal: Add/Edit Vehicle ──
function openVehicleMiniModal(tableContainer, editIndex = -1) {
    const isEdit = editIndex >= 0;
    const existing = isEdit ? _formVehicles[editIndex] : {};

    const backdrop = document.createElement('div');
    backdrop.className = 'mini-modal-backdrop';
    backdrop.innerHTML = `
        <div class="mini-modal">
            <div class="mini-modal-header">
                <h3>${isEdit ? t('mini_title_edit_vehicle') : t('mini_title_add_vehicle')}</h3>
                <button class="modal-close mini-close">✕</button>
            </div>
            <div class="mini-modal-body">
                <div class="form-group">
                    <label>${t('vehicle_reg')} *</label>
                    <input type="text" class="form-control" id="mini-veh-reg" value="${existing.registration_number || ''}">
                    <div class="field-error" id="mini-veh-reg-err"></div>
                </div>
                <div class="form-group">
                    <label>${t('vehicle_type')}</label>
                    <select class="form-control" id="mini-veh-type">
                        <option value="">-- Choose type --</option>
                        <option value="Heavy Truck" ${existing.type === 'Heavy Truck' ? 'selected' : ''}>${t('vt_heavy_truck')}</option>
                        <option value="Semi-Trailer Tanker" ${existing.type === 'Semi-Trailer Tanker' ? 'selected' : ''}>${t('vt_semi_trailer')}</option>
                        <option value="Rigid Tanker" ${existing.type === 'Rigid Tanker' ? 'selected' : ''}>${t('vt_rigid_tanker')}</option>
                        <option value="Cargo Van" ${existing.type === 'Cargo Van' ? 'selected' : ''}>${t('vt_cargo_van')}</option>
                        <option value="Flatbed Truck" ${existing.type === 'Flatbed Truck' ? 'selected' : ''}>${t('vt_flatbed_truck')}</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>${t('vehicle_category')}</label>
                    <input type="text" class="form-control" id="mini-veh-cat" value="${existing.category || ''}">
                </div>
            </div>
            <div class="mini-modal-footer">
                <button class="btn btn-ghost mini-cancel">${t('btn_cancel')}</button>
                <button class="btn btn-primary mini-save">${t('btn_save')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(backdrop);

    const close = () => backdrop.remove();
    backdrop.querySelector('.mini-close').onclick = close;
    backdrop.querySelector('.mini-cancel').onclick = close;
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });

    backdrop.querySelector('.mini-save').onclick = () => {
        const reg = document.getElementById('mini-veh-reg').value.trim();
        const type = document.getElementById('mini-veh-type').value;
        const cat = document.getElementById('mini-veh-cat').value.trim();

        if (!reg) {
            document.getElementById('mini-veh-reg-err').textContent = t('invalid_required');
            document.getElementById('mini-veh-reg').classList.add('input-invalid');
            return;
        }

        // Check duplicate registration across other items
        const dupIdx = _formVehicles.findIndex((v, idx) =>
            v.registration_number === reg && idx !== editIndex
        );
        if (dupIdx >= 0) {
            document.getElementById('mini-veh-reg-err').textContent = `Registration "${reg}" already exists in this contract.`;
            document.getElementById('mini-veh-reg').classList.add('input-invalid');
            return;
        }

        const entry = { registration_number: reg, type, category: cat };
        if (isEdit) {
            _formVehicles[editIndex] = entry;
        } else {
            _formVehicles.push(entry);
        }
        renderVehicleTable(tableContainer);
        close();
    };
}

// ── Mini-modal: Add/Edit Driver ──
function openDriverMiniModal(tableContainer, editIndex = -1) {
    const isEdit = editIndex >= 0;
    const existing = isEdit ? _formDrivers[editIndex] : {};

    const backdrop = document.createElement('div');
    backdrop.className = 'mini-modal-backdrop';
    backdrop.innerHTML = `
        <div class="mini-modal">
            <div class="mini-modal-header">
                <h3>${isEdit ? t('mini_title_edit_driver') : t('mini_title_add_driver')}</h3>
                <button class="modal-close mini-close">✕</button>
            </div>
            <div class="mini-modal-body">
                <div class="form-group">
                    <label>${t('driver_name')} *</label>
                    <input type="text" class="form-control" id="mini-drv-name" value="${existing.name || ''}">
                    <div class="field-error" id="mini-drv-name-err"></div>
                </div>
                <div class="form-group">
                    <label>${t('driver_phone')}</label>
                    <input type="text" class="form-control" id="mini-drv-phone" value="${existing.phone || ''}">
                </div>
            </div>
            <div class="mini-modal-footer">
                <button class="btn btn-ghost mini-cancel">${t('btn_cancel')}</button>
                <button class="btn btn-primary mini-save">${t('btn_save')}</button>
            </div>
        </div>
    `;
    document.body.appendChild(backdrop);

    const close = () => backdrop.remove();
    backdrop.querySelector('.mini-close').onclick = close;
    backdrop.querySelector('.mini-cancel').onclick = close;
    backdrop.addEventListener('click', (e) => { if (e.target === backdrop) close(); });

    backdrop.querySelector('.mini-save').onclick = () => {
        const name = document.getElementById('mini-drv-name').value.trim();
        const phone = document.getElementById('mini-drv-phone').value.trim();

        if (!name) {
            document.getElementById('mini-drv-name-err').textContent = t('invalid_required');
            document.getElementById('mini-drv-name').classList.add('input-invalid');
            return;
        }

        const entry = { name, phone };
        if (isEdit) {
            _formDrivers[editIndex] = entry;
        } else {
            _formDrivers.push(entry);
        }
        renderDriverTable(tableContainer);
        close();
    };
}

// Build the vehicle section card HTML
function buildVehicleSectionHTML(containerId, addBtnId) {
    return `
        <div class="entity-section">
            <div class="entity-section-header">
                <h4>🚚 ${t('sect_vehicle')}</h4>
                <button type="button" class="btn btn-sm btn-primary" id="${addBtnId}">${t('btn_add_vehicle')}</button>
            </div>
            <div id="${containerId}"></div>
        </div>
    `;
}

// Build the driver section card HTML
function buildDriverSectionHTML(containerId, addBtnId) {
    return `
        <div class="entity-section">
            <div class="entity-section-header">
                <h4>👤 ${t('sect_driver')}</h4>
                <button type="button" class="btn btn-sm btn-primary" id="${addBtnId}">${t('btn_add_driver')}</button>
            </div>
            <div id="${containerId}"></div>
        </div>
    `;
}

// ── Add Contract Page ──────────────────────────────────────

async function renderAddContract() {
    // Reset in-memory lists for the new form
    _formVehicles = [];
    _formDrivers = [];
    
    try {
        el.content.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">${t('add_contract_title')}</h2>
                </div>
                <div class="card-body">
                    <form id="contract-form">
                        <!-- Contract -->
                        <div class="section-title">${t('sect_contract')}</div>
                        
                        <!-- Line 1: Registration Number & Registry (Record) Number -->
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('registration_number')} *</label>
                                <input type="text" class="form-control" name="registration_number" data-validate="required|numbers">
                                <div class="field-error" data-error-for="registration_number"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('record_number')} *</label>
                                <input type="text" class="form-control" name="record_number" data-validate="required|numbers">
                                <div class="field-error" data-error-for="record_number"></div>
                            </div>
                        </div>
                        
                        <!-- Line 2: Start Date & End Date -->
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('signature_date')} *</label>
                                <input type="date" class="form-control" name="signature_date" data-validate="required">
                                <div class="field-error" data-error-for="signature_date"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('expiration_date')} *</label>
                                <input type="date" class="form-control" name="expiration_date" data-validate="required">
                                <div class="field-error" data-error-for="expiration_date"></div>
                            </div>
                        </div>

                        <!-- Line 3: Activity Location -->
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('activity_location')}</label>
                                ${buildLocationSelectHTML('activity_location')}
                            </div>
                        </div>

                        <!-- Company -->
                        <div class="section-title mt-16">${t('sect_company')}</div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('company_name')} *</label>
                                <input type="text" class="form-control" name="company_name" data-validate="required|letters">
                                <div class="field-error" data-error-for="company_name"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('company_address')}</label>
                                <input type="text" class="form-control" name="company_address">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('carrier_type')}</label>
                                <select class="form-control" name="carrier_type">
                                    <option value="Public">${t('opt_public')}</option>
                                    <option value="Private">${t('opt_private')}</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>${t('account_type')}</label>
                                <select class="form-control" name="account_type">
                                    <option value="Public">${t('opt_public')}</option>
                                    <option value="Private">${t('opt_private')}</option>
                                </select>
                            </div>
                        </div>

                        <!-- Vehicles (card table) -->
                        ${buildVehicleSectionHTML('vehicles-table-body', 'btn-add-vehicle')}

                        <!-- Drivers (card table) -->
                        ${buildDriverSectionHTML('drivers-table-body', 'btn-add-driver')}

                        <!-- Route & Hazmat -->
                        <div class="section-title mt-16">${t('sect_route')}</div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('route_origin')}</label>
                                <input type="text" class="form-control" name="route_origin" data-validate="letters">
                                <div class="field-error" data-error-for="route_origin"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('route_dest')}</label>
                                <input type="text" class="form-control" name="route_dest" data-validate="letters">
                                <div class="field-error" data-error-for="route_dest"></div>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>${t('hazmat_type')}</label>
                            <select class="form-control" name="hazmat_type" id="hazmat-type-select">
                                <option value="">-- Choose type --</option>
                                <option value="Class 3 (Flammable Liquids)">${t('mat_class_3')}</option>
                                <option value="Class 1 (Explosives)">${t('mat_class_1')}</option>
                                <option value="Class 2.1 (Flammable Gases)">${t('mat_class_2_1')}</option>
                                <option value="Class 2.2 (Non-Flammable/Non-Toxic Gases)">${t('mat_class_2_2')}</option>
                                <option value="Class 2.3 (Toxic Gases)">${t('mat_class_2_3')}</option>
                                <option value="Class 4.1 (Flammable Solids)">${t('mat_class_4_1')}</option>
                                <option value="Class 5.1 (Oxidizing Substances)">${t('mat_class_5_1')}</option>
                                <option value="Class 6.1 (Toxic Substances)">${t('mat_class_6_1')}</option>
                                <option value="Class 8 (Corrosive Substances)">${t('mat_class_8')}</option>
                                <option value="Class 9 (Miscellaneous Dangerous Substances)">${t('mat_class_9')}</option>
                                <option value="Autre">${t('mat_other') || 'Other'}</option>
                            </select>
                        </div>
                        <div class="form-group hidden" id="custom-hazmat-wrapper">
                            <label>${t('lbl_custom_hazmat') || 'Custom Material Type'}</label>
                            <input type="text" class="form-control" id="custom-hazmat-input">
                        </div>

                        <!-- Actions -->
                        <div class="mt-16 d-flex gap-8">
                            <button type="submit" id="submit-btn" class="btn btn-success">${t('btn_save')}</button>
                            <button type="button" class="btn btn-ghost" onclick="navigateTo('dashboard')">${t('btn_cancel')}</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        // Initialize vehicle/driver table containers
        const vehTableBody = document.getElementById('vehicles-table-body');
        const drvTableBody = document.getElementById('drivers-table-body');
        renderVehicleTable(vehTableBody);
        renderDriverTable(drvTableBody);

        document.getElementById('btn-add-vehicle').onclick = (e) => {
            e.preventDefault();
            openVehicleMiniModal(vehTableBody);
        };
        document.getElementById('btn-add-driver').onclick = (e) => {
            e.preventDefault();
            openDriverMiniModal(drvTableBody);
        };

        // Toggle custom material input wrapper on selection
        const hazmatSelect = document.getElementById('hazmat-type-select');
        const customHazmatWrapper = document.getElementById('custom-hazmat-wrapper');
        const customHazmatInput = document.getElementById('custom-hazmat-input');
        if (hazmatSelect && customHazmatWrapper) {
            hazmatSelect.onchange = () => {
                if (hazmatSelect.value === 'Autre') {
                    customHazmatWrapper.classList.remove('hidden');
                } else {
                    customHazmatWrapper.classList.add('hidden');
                    if (customHazmatInput) customHazmatInput.value = '';
                }
            };
        }

        // Validation for the form fields
        setupContractFormValidation();
        document.getElementById('contract-form').addEventListener('submit', handleFormSubmit);

        // Fetch next record number and pre-fill
        try {
            const nextRecData = await API.nextRecordNumber();
            const recNumInput = document.querySelector('input[name="record_number"]');
            if (recNumInput && nextRecData && nextRecData.next_record_number) {
                recNumInput.value = nextRecData.next_record_number;
                // Trigger input validation so the form knows it is valid
                const event = new Event('input', { bubbles: true });
                recNumInput.dispatchEvent(event);
            }
        } catch (e) {
            console.error("Failed to fetch next record number:", e);
        }
    } catch (err) {
        el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
        showToast(err.message, 'error');
    }
}

// ── Form Handling ────────────────────────────────────────────

async function handleFormSubmit(event) {
    event.preventDefault();
    const submitBtn = document.getElementById('submit-btn');
    if (!validateContractForm()) {
        showToast(t('form_has_errors'), 'error');
        return;
    }
    submitBtn.disabled = true;
    submitBtn.textContent = t('btn_saving');

    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData.entries());

    // Map custom material type if Autre is selected
    const hazmatSelect = document.getElementById('hazmat-type-select');
    const customHazmatInput = document.getElementById('custom-hazmat-input');
    if (hazmatSelect && hazmatSelect.value === 'Autre' && customHazmatInput) {
        data.hazmat_type = customHazmatInput.value.trim() || 'Autre';
    }

    const vList = getVehiclesListFromForm();
    const dList = getDriversListFromForm();

    data.vehicles_list = JSON.stringify(vList);
    data.drivers_list = JSON.stringify(dList);

    if (vList.length > 0) {
        data.vehicle_reg = vList[0].registration_number;
        data.vehicle_type = vList[0].type;
        data.vehicle_category = vList[0].category;
    }
    if (dList.length > 0) {
        data.driver_name = dList[0].name;
        data.driver_phone = dList[0].phone;
    }

    try {
        await API.createLicense(data);
        showToast(t('saved_ok'), 'success');
        navigateTo('dashboard');
    } catch (err) {
        showToast(err.message, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = t('btn_save');
    }
}

function setupContractFormValidation() {
    const form = document.getElementById('contract-form') || document.getElementById('edit-form');
    if (!form) return;
    const submitBtn = document.getElementById('submit-btn') || document.getElementById('edit-save');
    if (!submitBtn) return;
    const trackedInputs = Array.from(form.querySelectorAll('[data-validate]'));

    function setError(input, message) {
        let errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
        if (!errorEl) {
            errorEl = input.parentNode.querySelector('.field-error');
        }
        if (!errorEl) return;
        errorEl.textContent = message || '';
        input.classList.toggle('input-invalid', Boolean(message));
    }

    function validateInput(input) {
        const rawRules = input.getAttribute('data-validate');
        if (!rawRules) return true;

        const value = input.value.trim();
        const rules = rawRules.split('|');

        if (rules.includes('required') && !value) {
            setError(input, t('invalid_required'));
            return false;
        }

        if (!value) {
            setError(input, '');
            return true;
        }

        if (rules.includes('numbers') && !/^\d+$/.test(value)) {
            setError(input, t('invalid_numbers_only'));
            return false;
        }

        if (rules.includes('letters') && !/^[\p{L}\s'\-]+$/u.test(value)) {
            setError(input, t('invalid_letters_only'));
            return false;
        }

        setError(input, '');
        return true;
    }

    function validateAll() {
        let allValid = trackedInputs.every(validateInput);

        const sigInput = form.querySelector('[name="signature_date"]');
        const expInput = form.querySelector('[name="expiration_date"]');
        if (sigInput && expInput) {
            const sigVal = sigInput.value;
            const expVal = expInput.value;
            if (sigVal && expVal) {
                if (new Date(expVal) < new Date(sigVal)) {
                    setError(expInput, t('err_date_chronology'));
                    allValid = false;
                } else {
                    let errEl = form.querySelector(`[data-error-for="expiration_date"]`) || expInput.parentNode.querySelector('.field-error');
                    if (errEl && errEl.textContent === t('err_date_chronology')) {
                        setError(expInput, '');
                    }
                }
            }
        }

        submitBtn.disabled = !allValid;
        return allValid;
    }

    trackedInputs.forEach(input => {
        // Prevent duplicate listener bindings
        if (input.dataset.hasListener) return;
        input.dataset.hasListener = "true";
        
        input.addEventListener('input', () => {
            validateInput(input);
            validateAll();
        });
        input.addEventListener('blur', () => {
            validateInput(input);
            validateAll();
        });
    });

    validateAll();
}

function validateContractForm() {
    const form = document.getElementById('contract-form') || document.getElementById('edit-form');
    if (!form) return true;
    const submitBtn = document.getElementById('submit-btn') || document.getElementById('edit-save');
    if (!submitBtn) return true;
    const inputs = Array.from(form.querySelectorAll('[data-validate]'));
    const inputEvent = new Event('blur');
    inputs.forEach(input => input.dispatchEvent(inputEvent));
    return !submitBtn.disabled;
}

// ── Add Vehicle Linked to Contract ──────────────────────────


// ── Edit Modal Logic ────────────────────────────────────────

async function openEditModal(id) {
    try {
        const data = await API.getLicense(id);
        const modal = document.getElementById('edit-modal');
        const body = document.getElementById('edit-modal-body');
        
        // Populate in-memory arrays from saved data
        _formVehicles = [];
        if (data.vehicles_list) {
            try {
                _formVehicles = JSON.parse(data.vehicles_list);
            } catch (e) {
                console.error(e);
            }
        }
        if (_formVehicles.length === 0 && data.vehicle_reg) {
            _formVehicles.push({
                registration_number: data.vehicle_reg,
                type: data.vehicle_type || '',
                category: data.vehicle_category || ''
            });
        }

        _formDrivers = [];
        if (data.drivers_list) {
            try {
                _formDrivers = JSON.parse(data.drivers_list);
            } catch (e) {
                console.error(e);
            }
        }
        if (_formDrivers.length === 0 && data.driver_name) {
            _formDrivers.push({
                name: data.driver_name,
                phone: data.driver_phone || ''
            });
        }

        body.innerHTML = `
            <form id="edit-form">
                <div class="section-title">${t('sect_contract')}</div>
                
                <!-- Line 1: Registration Number & Registry (Record) Number -->
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('registration_number')} *</label>
                        <input type="text" class="form-control" name="registration_number" value="${data.registration_number || ''}" data-validate="required|numbers">
                        <div class="field-error" data-error-for="registration_number"></div>
                    </div>
                    <div class="form-group">
                        <label>${t('record_number')} *</label>
                        <input type="text" class="form-control" name="record_number" value="${data.record_number}" data-validate="required|numbers">
                        <div class="field-error" data-error-for="record_number"></div>
                    </div>
                </div>

                <!-- Line 2: Start Date & End Date -->
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('signature_date')} *</label>
                        <input type="date" class="form-control" name="signature_date" value="${data.signature_date}" data-validate="required">
                        <div class="field-error" data-error-for="signature_date"></div>
                    </div>
                    <div class="form-group">
                        <label>${t('expiration_date')} *</label>
                        <input type="date" class="form-control" name="expiration_date" value="${data.expiration_date}" data-validate="required">
                        <div class="field-error" data-error-for="expiration_date"></div>
                    </div>
                </div>

                <!-- Line 3: Activity Location -->
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('activity_location')}</label>
                        ${buildLocationSelectHTML('activity_location', data.activity_location)}
                    </div>
                </div>

                ${buildVehicleSectionHTML('edit-vehicles-tbody', 'edit-add-vehicle-btn')}
                ${buildDriverSectionHTML('edit-drivers-tbody', 'edit-add-driver-btn')}
            </form>
        `;

        const vehTbody = document.getElementById('edit-vehicles-tbody');
        const drvTbody = document.getElementById('edit-drivers-tbody');
        renderVehicleTable(vehTbody);
        renderDriverTable(drvTbody);

        document.getElementById('edit-add-vehicle-btn').onclick = (e) => {
            e.preventDefault();
            openVehicleMiniModal(vehTbody);
        };
        document.getElementById('edit-add-driver-btn').onclick = (e) => {
            e.preventDefault();
            openDriverMiniModal(drvTbody);
        };

        modal.classList.remove('hidden');
        setupContractFormValidation();

        document.getElementById('edit-save').onclick = async () => {
            if (!validateContractForm()) {
                showToast(t('form_has_errors'), 'error');
                return;
            }
            const formData = new FormData(document.getElementById('edit-form'));
            const updateData = Object.fromEntries(formData.entries());

            const vList = getVehiclesListFromForm();
            const dList = getDriversListFromForm();

            updateData.vehicles_list = JSON.stringify(vList);
            updateData.drivers_list = JSON.stringify(dList);

            if (vList.length > 0) {
                updateData.vehicle_reg = vList[0].registration_number;
                updateData.vehicle_type = vList[0].type;
                updateData.vehicle_category = vList[0].category;
            }
            if (dList.length > 0) {
                updateData.driver_name = dList[0].name;
                updateData.driver_phone = dList[0].phone;
            }

            try {
                await API.updateLicense(id, updateData);
                showToast(t('saved_ok'));
                modal.classList.add('hidden');
                loadSearchResults();
            } catch (err) {
                showToast(err.message, 'error');
            }
        };

        document.getElementById('edit-cancel').onclick = () => modal.classList.add('hidden');
        document.getElementById('edit-modal-close').onclick = () => modal.classList.add('hidden');
        
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Welcome Page ───────────────────────────────────────

async function renderWelcome() {
    try {
        // This content is static and local, so it should be very fast.
        const welcomePage = await fetch('./pages/welcome.html');
        if (!welcomePage.ok) throw new Error('Could not load welcome page.');
        el.content.innerHTML = await welcomePage.text();

        // Add event listeners for the action cards
        document.getElementById('action-add-contract').addEventListener('click', () => navigateTo('add-contract'));
        document.getElementById('action-search').addEventListener('click', () => navigateTo('search'));
        document.getElementById('action-view-stats').addEventListener('click', () => navigateTo('statistics'));

    } catch (err) {
        el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
        showToast(err.message, 'error');
    }
}

async function renderVehiclesView() {
    el.content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
    try {
        const vehicles = await API.getVehicles();
        el.content.innerHTML = `
            <div class="card mb-16">
                <div class="card-header">
                    <h3 class="card-title">🚚 ${t('nav_vehicles')}</h3>
                </div>
                <div class="card-body">
                    <div class="table-wrapper">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>${t('vehicle_id')}</th>
                                    <th>${t('vehicle_registration')}</th>
                                    <th>${t('vehicle_type')}</th>
                                    <th>${t('vehicle_category')}</th>
                                    <th>${t('associated_company')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${vehicles.map(v => `
                                    <tr>
                                        <td><span class="badge badge-blue">#${v.id}</span></td>
                                        <td><strong>${v.registration_number}</strong></td>
                                        <td>${v.type || '-'}</td>
                                        <td>${v.category || '-'}</td>
                                        <td>${v.company_name || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        showToast(err.message, 'error');
        el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
    }
}

async function renderDriversView() {
    el.content.innerHTML = '<div class="loading-overlay"><div class="spinner"></div></div>';
    try {
        const drivers = await API.getDrivers();
        el.content.innerHTML = `
            <div class="card mb-16">
                <div class="card-header">
                    <h3 class="card-title">👤 ${t('nav_drivers')}</h3>
                </div>
                <div class="card-body">
                    <div class="table-wrapper">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>${t('driver_id')}</th>
                                    <th>${t('driver_name')}</th>
                                    <th>${t('driver_phone')}</th>
                                    <th>${t('associated_company')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${drivers.map(d => `
                                    <tr>
                                        <td><span class="badge badge-blue">#${d.id}</span></td>
                                        <td><strong>${d.driver_name}</strong></td>
                                        <td>${d.driver_phone || '-'}</td>
                                        <td>${d.company_name || '-'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    } catch (err) {
        showToast(err.message, 'error');
        el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
    }
}

function syncSidebarProfile() {
    const sidebarUser = document.getElementById('sidebar-username');
    if (sidebarUser) {
        sidebarUser.textContent = sessionStorage.getItem('auth_user') || 'admin';
    }
}

// Start app
init();
