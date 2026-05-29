/**
 * app.js — Main UI Controller
 * Handles routing, themes, language, and core UI events.
 */

const state = {
    currentPath: 'dashboard',
    history: [],
    theme: localStorage.getItem('theme') || 'light',
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

let setifCommunesData = null;

async function fetchCommunes() {
    if (setifCommunesData) return setifCommunesData;
    try {
        const resp = await fetch('./data/setif_communes.json');
        if (resp.ok) {
            setifCommunesData = await resp.json();
            return setifCommunesData;
        }
    } catch (e) {
        console.error("Failed to load communes:", e);
    }
    return null;
}

async function populateCommunesSelect(selectEl, selectedValue = '', isFilter = false) {
    if (!selectEl) return;
    const data = await fetchCommunes();
    if (!data || !data.communes) return;

    selectEl.innerHTML = isFilter 
        ? `<option value="">${t('opt_all')}</option>`
        : `<option value="">${t('select_address')}</option>`;

    data.communes.forEach(commune => {
        const opt = document.createElement('option');
        const val = isFilter ? commune : `${commune}, ${data.wilaya}`;
        opt.value = val;
        opt.textContent = isFilter ? commune : `${commune} (${data.wilaya})`;
        if (val === selectedValue || (isFilter && val.toLowerCase() === selectedValue.toLowerCase())) {
            opt.selected = true;
        }
        selectEl.appendChild(opt);
    });
}

// ── Initialization ───────────────────────────────────────────

async function init() {
    await initApiBase();
    applyTheme();
    applyLanguage();
    setupEventListeners();
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

    // Theme toggle
    el.darkToggle.addEventListener('click', toggleTheme);

    // Language
    el.langBtn.addEventListener('click', () => {
        el.langMenu.classList.toggle('open');
    });

    document.querySelectorAll('.lang-option').forEach(opt => {
        opt.addEventListener('click', () => {
            const lang = opt.getAttribute('data-lang');
            setLanguage(lang);
            el.langMenu.classList.remove('open');
        });
    });

    // Close lang menu on click outside
    document.addEventListener('click', (e) => {
        if (!el.langBtn.contains(e.target) && !el.langMenu.contains(e.target)) {
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
    el.content.innerHTML = `<div class="loading-overlay"><div class="spinner"></div><p style="margin-top: 10px;">${t('loading') || 'Loading...'}</p></div>`;

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
                default:
                    el.content.innerHTML = `<div class="empty-state"><h2>${t('page_not_found') || '404 - Page Not Found'}</h2><p>${t('page_not_exist') || "The requested page does not exist."}</p></div>`;
            }
        } catch (err) {
            showToast(err.message, 'error');
            el.content.innerHTML = `<div class="empty-state"><h2>${t('toast_error')}</h2><p>${translateError(err.message)}</p></div>`;
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
    el.content.innerHTML = `<div class="loading-overlay"><div class="spinner"></div><p style="margin-top: 10px;">${t('loading') || 'Loading...'}</p></div>`;
    
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
        default:
            el.content.innerHTML = `<h2>${t('page_not_found') || 'Page not found'}</h2>`;
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
    el.darkToggle.textContent = state.theme === 'light' ? '🌙' : '☀️';
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
            <div class="toast-msg">${translateError(message)}</div>
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

async function renderDashboard() {
    try {
        const stats = await API.stats();
        const expiring = await API.expiringLicenses(30);

        let expiringHtml = '';
        if (expiring.length > 0) {
            expiringHtml = `
                <div class="alert-strip warning">
                    <span>⚠️ ${t('expiring_soon_title')} (${expiring.length})</span>
                </div>
                <div class="card mb-16">
                    <div class="card-body">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>${t('col_license')}</th>
                                    <th>${t('company_name')}</th>
                                    <th>${t('col_expiry')}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${expiring.map(ex => `
                                    <tr>
                                        <td>${ex.license_number}</td>
                                        <td>${ex.company_name}</td>
                                        <td><span class="badge badge-amber">${ex.expiration_date}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        } else {
            expiringHtml = `<div class="empty-state"><p>${t('no_expiring')}</p></div>`;
        }

        const advStats = await API.statsAdvanced();
        const forecast = advStats.activity?.forecast || [];

        let forecastHtml = `
            <div class="card mb-16">
                <div class="card-header"><h3 class="card-title">🔮 ${t('predictive_insights') || 'Predictive Insights: Expiry Forecast'}</h3></div>
                <div class="card-body">
                    <div class="stats-grid">
                        ${forecast.map(f => {
                            const num = f.label.split(' ')[0];
                            let daysStr = t('days') || 'days';
                            if (currentLang === 'ar') daysStr = 'يوم';
                            else if (currentLang === 'fr') daysStr = 'jours';
                            const localizedLabel = t('expiring_in') + ' ' + num + ' ' + daysStr;
                            return `
                                <div class="stat-card" style="border-left: 4px solid var(--warning)">
                                    <div class="stat-info">
                                        <div class="stat-value">${f.count}</div>
                                        <div class="stat-label">${localizedLabel}</div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                    <p class="text-muted mt-8 text-sm">${t('expiring_in_forecast_label')}</p>
                </div>
            </div>
        `;

        el.content.innerHTML = `
            <div class="stats-grid mb-24">
                <div class="stat-card" style="border-top: 4px solid var(--accent)">
                    <div class="stat-icon purple">📄</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.active_licenses}</div>
                        <div class="stat-label">${t('stat_active')}</div>
                    </div>
                </div>
                <div class="stat-card" style="border-top: 4px solid var(--danger)">
                    <div class="stat-icon red">⏰</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.expired_licenses}</div>
                        <div class="stat-label">${t('stat_expired')}</div>
                    </div>
                </div>
                <div class="stat-card" style="border-top: 4px solid var(--success)">
                    <div class="stat-icon green">📋</div>
                    <div class="stat-info">
                        <div class="stat-value">${stats.total_contracts}</div>
                        <div class="stat-label">${t('stat_total_contracts')}</div>
                    </div>
                </div>
            </div>
            
            <h2 class="mb-16">🛡️ ${t('expiring_soon_title')}</h2>
            ${expiringHtml}

            <h2 class="mb-16 mt-24">📈 ${t('system_forecasting') || 'System Forecasting'}</h2>
            ${forecastHtml}
        `;
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Settings Page ────────────────────────────────────────────

async function renderSettings() {
    try {
        const settings = await API.getSettings();
        
        el.content.innerHTML = `
            <div class="card">
                <div class="card-header"><h2 class="card-title">${t('nav_settings')}</h2></div>
                <div class="card-body">
                    <form id="settings-form">
                        <div class="section-title">${t('sect_smtp')}</div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('smtp_server')}</label>
                                <input type="text" class="form-control" name="smtp_server" value="${settings.smtp_server || ''}">
                            </div>
                            <div class="form-group">
                                <label>${t('smtp_port')}</label>
                                <input type="number" class="form-control" name="smtp_port" value="${settings.smtp_port || '587'}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('smtp_email')}</label>
                                <input type="email" class="form-control" name="smtp_email" value="${settings.smtp_email || ''}">
                            </div>
                            <div class="form-group">
                                <label>${t('smtp_password')}</label>
                                <input type="password" class="form-control" name="smtp_password" value="${settings.smtp_password || ''}">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>${t('smtp_recipient')}</label>
                            <input type="email" class="form-control" name="smtp_recipient" value="${settings.smtp_recipient || ''}">
                        </div>
                        
                        <div class="section-title">${t('sect_backup')}</div>
                        <div class="form-group">
                            <label>${t('backup_folder')}</label>
                            <input type="text" class="form-control" name="backup_folder" value="${settings.backup_folder || ''}" readonly>
                        </div>

                        <div class="mt-16 d-flex gap-8">
                            <button type="submit" class="btn btn-primary">${t('btn_save_settings')}</button>
                            <button type="button" class="btn btn-ghost" id="test-email-btn">${t('btn_test_email')}</button>
                        </div>
                    </form>
                    <hr/>
                    <form id="change-password-form" class="mt-12">
                        <div class="section-title">${t('change_password')}</div>
                        <div class="form-group">
                            <label>${t('lbl_username')}</label>
                            <input type="text" class="form-control" name="username" value="${sessionStorage.getItem('auth_user')||''}">
                        </div>
                        <div class="form-group">
                            <label>${t('lbl_current_password')}</label>
                            <input type="password" class="form-control" name="current_password">
                        </div>
                        <div class="form-group">
                            <label>${t('lbl_new_password')}</label>
                            <input type="password" class="form-control" name="new_password">
                        </div>
                        <div class="mt-8">
                            <button type="submit" class="btn btn-secondary">${t('btn_change_password')||'Change Password'}</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        document.getElementById('settings-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            try {
                await API.saveSettings(data);
                showToast(t('settings_saved'), 'success');
            } catch (err) {
                showToast(err.message, 'error');
            }
        };
        document.getElementById('change-password-form').onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());
            try {
                await API.changePassword(data.username, data.current_password, data.new_password);
                showToast(t('password_changed'), 'success');
            } catch (err) {
                showToast(err.message || t('password_change_failed'), 'error');
            }
        };
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Search Page ──────────────────────────────────────────────

let searchParams = { page: 1, limit: 50, search: '', status: '', carrier: '', activity_location: '', contract_type: '', sort_by: 'signature_date', sort_dir: 'DESC' };
let deletedSearchParams = { page: 1, limit: 50, search: '', status: '', activity_location: '', contract_type: '', sort_by: 'signature_date', sort_dir: 'DESC' };

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
                        <label>${t('lbl_location')}</label>
                        <select class="form-control" id="filter-location">
                            <!-- Populated dynamically -->
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_ctype')}</label>
                        <select class="form-control" id="filter-ctype">
                            <option value="">${t('opt_all')}</option>
                            <option value="Public" ${searchParams.contract_type === 'Public' ? 'selected' : ''}>${t('opt_public')}</option>
                            <option value="Private" ${searchParams.contract_type === 'Private' ? 'selected' : ''}>${t('opt_private')}</option>
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_sort')}</label>
                        <select class="form-control" id="filter-sort">
                            <option value="signature_date|ASC" ${searchParams.sort_by === 'signature_date' && searchParams.sort_dir === 'ASC' ? 'selected' : ''}>${t('sort_oldest')}</option>
                            <option value="signature_date|DESC" ${searchParams.sort_by === 'signature_date' && searchParams.sort_dir === 'DESC' ? 'selected' : ''}>${t('sort_newest')}</option>
                            <option value="company_name|ASC" ${searchParams.sort_by === 'company_name' && searchParams.sort_dir === 'ASC' ? 'selected' : ''}>${t('sort_alpha_asc')}</option>
                            <option value="company_name|DESC" ${searchParams.sort_by === 'company_name' && searchParams.sort_dir === 'DESC' ? 'selected' : ''}>${t('sort_alpha_desc')}</option>
                        </select>
                    </div>
                    <div class="d-flex align-center gap-8 mt-16">
                        <button class="btn btn-primary" id="btn-search">${t('btn_search')}</button>
                        <button class="btn btn-ghost" id="btn-reset">${t('btn_reset')}</button>
                    </div>
                </div>
            </div>
        </div>

        <div class="table-wrapper card">
            <table id="results-table">
                <thead>
                    <tr>
                        <th>${t('col_record')} / ${t('license_number')}</th>
                        <th>${t('signing_date')}</th>
                        <th>${t('company_carrier_name')}</th>
                        <th>${t('registration_code')}</th>
                        <th>${t('company_address')}</th>
                        <th>${t('vehicle_registration_number')}</th>
                        <th>${t('vehicle_type_category')}</th>
                        <th>${t('route')}</th>
                        <th>${t('license_expiry_date')}</th>
                        <th>${t('carrier_type')}</th>
                        <th>${t('transported_materials')}</th>
                        <th>${t('col_status')}</th>
                        <th>${t('col_actions')}</th>
                    </tr>
                </thead>
                <tbody id="results-body">
                    <tr><td colspan="13" class="text-center"><div class="spinner"></div></td></tr>
                </tbody>
            </table>
        </div>
        <div id="pagination" class="pagination"></div>
    `;

    const filterLocation = document.getElementById('filter-location');
    await populateCommunesSelect(filterLocation, searchParams.activity_location, true);

    const searchInput = document.getElementById('search-input');
    const filterStatus = document.getElementById('filter-status');
    const filterCtype = document.getElementById('filter-ctype');
    const filterSort = document.getElementById('filter-sort');

    const triggerSearch = () => {
        searchParams.search = searchInput.value;
        searchParams.status = filterStatus.value;
        searchParams.activity_location = filterLocation.value;
        searchParams.contract_type = filterCtype.value;
        
        const [sort_by, sort_dir] = filterSort.value.split('|');
        searchParams.sort_by = sort_by;
        searchParams.sort_dir = sort_dir;
        
        searchParams.page = 1;
        loadSearchResults();
    };

    searchInput.oninput = debounce(triggerSearch, 400);
    filterStatus.onchange = triggerSearch;
    filterLocation.onchange = triggerSearch;
    filterCtype.onchange = triggerSearch;
    filterSort.onchange = triggerSearch;

    document.getElementById('btn-search').onclick = triggerSearch;

    document.getElementById('btn-reset').onclick = () => {
        searchParams = { page: 1, limit: 50, search: '', status: '', carrier: '', activity_location: '', contract_type: '', sort_by: 'signature_date', sort_dir: 'DESC' };
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
                    <td colspan="13">
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
            <tr>
                <td>${r.record_number} / ${r.license_number}</td>
                <td>${r.signature_date || '-'}</td>
                <td>${r.company_name}</td>
                <td>${r.company_reg || '-'}</td>
                <td>${r.company_address || '-'}</td>
                <td>${r.vehicle_reg}</td>
                <td>${r.vehicle_type || ''} ${r.vehicle_category || ''}</td>
                <td>${r.route_origin || ''} ${r.route_dest ? '→ ' + r.route_dest : ''}</td>
                <td>${r.expiration_date}</td>
                <td>${t('opt_' + r.carrier_type.toLowerCase()) || r.carrier_type}</td>
                <td>${r.hazmat_type || '-'}</td>
                <td><span class="badge ${r.status === 'active' ? 'badge-green' : 'badge-red'}">${t('opt_' + r.status)}</span></td>
                <td>
                    <div class="d-flex gap-8">
                        <button class="btn btn-sm btn-ghost edit-btn" data-id="${r.id}" title="${t('btn_edit')}">✏️</button>
                        <button class="btn btn-sm btn-danger delete-btn" data-id="${r.id}" data-num="${r.record_number}">🗑️</button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Action events
        tbody.querySelectorAll('.edit-btn').forEach(btn => {
            btn.onclick = () => openEditModal(btn.getAttribute('data-id'));
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
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="13" class="error-state">${err.message}</td></tr>`;
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
                    <div style="width: 150px">
                        <label>${t('deleted_status_filter')}</label>
                        <select class="form-control" id="deleted-filter-status">
                            <option value="">${t('opt_all')}</option>
                            <option value="active" ${deletedSearchParams.status === 'active' ? 'selected' : ''}>${t('opt_active')}</option>
                            <option value="expired" ${deletedSearchParams.status === 'expired' ? 'selected' : ''}>${t('opt_expired')}</option>
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_location')}</label>
                        <select class="form-control" id="deleted-filter-location">
                            <!-- Populated dynamically -->
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_ctype')}</label>
                        <select class="form-control" id="deleted-filter-ctype">
                            <option value="">${t('opt_all')}</option>
                            <option value="Public" ${deletedSearchParams.contract_type === 'Public' ? 'selected' : ''}>${t('opt_public')}</option>
                            <option value="Private" ${deletedSearchParams.contract_type === 'Private' ? 'selected' : ''}>${t('opt_private')}</option>
                        </select>
                    </div>
                    <div style="width: 150px">
                        <label>${t('lbl_sort')}</label>
                        <select class="form-control" id="deleted-filter-sort">
                            <option value="signature_date|ASC" ${deletedSearchParams.sort_by === 'signature_date' && deletedSearchParams.sort_dir === 'ASC' ? 'selected' : ''}>${t('sort_oldest')}</option>
                            <option value="signature_date|DESC" ${deletedSearchParams.sort_by === 'signature_date' && deletedSearchParams.sort_dir === 'DESC' ? 'selected' : ''}>${t('sort_newest')}</option>
                            <option value="company_name|ASC" ${deletedSearchParams.sort_by === 'company_name' && deletedSearchParams.sort_dir === 'ASC' ? 'selected' : ''}>${t('sort_alpha_asc')}</option>
                            <option value="company_name|DESC" ${deletedSearchParams.sort_by === 'company_name' && deletedSearchParams.sort_dir === 'DESC' ? 'selected' : ''}>${t('sort_alpha_desc')}</option>
                        </select>
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
                        <th>${t('col_record')} / ${t('license_number')}</th>
                        <th>${t('signing_date')}</th>
                        <th>${t('company_carrier_name')}</th>
                        <th>${t('registration_code')}</th>
                        <th>${t('company_address')}</th>
                        <th>${t('vehicle_registration_number')}</th>
                        <th>${t('vehicle_type_category')}</th>
                        <th>${t('route')}</th>
                        <th>${t('license_expiry_date')}</th>
                        <th>${t('carrier_type')}</th>
                        <th>${t('transported_materials')}</th>
                        <th>${t('col_status')}</th>
                        <th>${t('col_actions')}</th>
                    </tr>
                </thead>
                <tbody id="deleted-results-body">
                    <tr><td colspan="13" class="text-center"><div class="spinner"></div></td></tr>
                </tbody>
            </table>
        </div>
        <div id="deleted-pagination" class="pagination"></div>
    `;

    const filterLocation = document.getElementById('deleted-filter-location');
    await populateCommunesSelect(filterLocation, deletedSearchParams.activity_location, true);

    const searchInput = document.getElementById('deleted-search-input');
    const filterStatus = document.getElementById('deleted-filter-status');
    const filterCtype = document.getElementById('deleted-filter-ctype');
    const filterSort = document.getElementById('deleted-filter-sort');

    const triggerSearch = () => {
        deletedSearchParams.search = searchInput.value;
        deletedSearchParams.status = filterStatus.value;
        deletedSearchParams.activity_location = filterLocation.value;
        deletedSearchParams.contract_type = filterCtype.value;
        
        const [sort_by, sort_dir] = filterSort.value.split('|');
        deletedSearchParams.sort_by = sort_by;
        deletedSearchParams.sort_dir = sort_dir;
        
        deletedSearchParams.page = 1;
        loadDeletedResults();
    };

    searchInput.oninput = debounce(triggerSearch, 400);
    filterStatus.onchange = triggerSearch;
    filterLocation.onchange = triggerSearch;
    filterCtype.onchange = triggerSearch;
    filterSort.onchange = triggerSearch;

    document.getElementById('btn-deleted-search').onclick = triggerSearch;

    document.getElementById('btn-deleted-reset').onclick = () => {
        deletedSearchParams = { page: 1, limit: 50, search: '', status: '', activity_location: '', contract_type: '', sort_by: 'signature_date', sort_dir: 'DESC' };
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
            tbody.innerHTML = `<tr><td colspan="13" class="empty-state">${t('no_deleted_records')}</td></tr>`;
            pagination.innerHTML = '';
            return;
        }

        tbody.innerHTML = result.records.map(r => `
            <tr>
                <td>${r.record_number} / ${r.license_number}</td>
                <td>${r.signature_date || '-'}</td>
                <td>${r.company_name}</td>
                <td>${r.company_reg || '-'}</td>
                <td>${r.company_address || '-'}</td>
                <td>${r.vehicle_reg}</td>
                <td>${r.vehicle_type || ''} ${r.vehicle_category || ''}</td>
                <td>${r.route_origin || ''} ${r.route_dest ? '→ ' + r.route_dest : ''}</td>
                <td>${r.expiration_date}</td>
                <td>${t('opt_' + r.carrier_type.toLowerCase()) || r.carrier_type}</td>
                <td>${r.hazmat_type || '-'}</td>
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
                    showToast(err.message, 'error');
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
        tbody.innerHTML = `<tr><td colspan="13" class="error-state">${err.message}</td></tr>`;
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
    /**
     * What it does: Destroys all existing Chart.js instances.
     * Why it exists: To prevent memory leaks and canvas conflicts when re-rendering the page.
     */
    Object.values(statsCharts).forEach(chart => chart.destroy());
    statsCharts = {};

    el.content.innerHTML = '<div class="loading-spinner"></div>';

    try {
        const advanced = await API.statsAdvanced();

        const kpis = advanced?.kpis || { total: 0, active: 0, inactive: 0, public: 0, private: 0 };
        const municipalities = advanced?.municipalities || {};
        const activity = advanced?.activity || { daily: [], weekly: [], monthly: [] };
        const municipalityStats = Object.entries(municipalities)
            .map(([name, data]) => ({ name, ...data }))
            .sort((a, b) => b.total - a.total);

        const topMunicipalities = municipalityStats.slice(0, 10);

        const html = `
            <div class="stats-dashboard">
                <!-- Tier 1: KPI Cards -->
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

                <!-- Tier 2: Distribution -->
                <div class="distribution-section">
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_municipality_dist')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="municipalityBarChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_carrier_type')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="carrierTypePieChart"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Tier 3: Activity Analysis -->
                <div class="activity-section">
                    <div class="activity-tabs">
                        <button class="activity-tab active" data-period="daily">${t('daily')}</button>
                        <button class="activity-tab" data-period="weekly">${t('weekly')}</button>
                        <button class="activity-tab" data-period="monthly">${t('monthly')}</button>
                    </div>
                    <div class="chart-container">
                         <div class="chart-title">${t('chart_title_activity')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="activityLineChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <div class="municipality-section">
                    <div class="chart-container">
                        <div class="chart-title">${t('chart_title_compliance_by_municipality')}</div>
                        <div class="chart-canvas-container">
                            <canvas id="municipalityGroupChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        `;
        el.content.innerHTML = html;

        // Initialize charts
        initMunicipalityBarChart(topMunicipalities);
        initCarrierTypePieChart(kpis);
        initActivityLineChart('daily', activity);
        initMunicipalityGroupChart(topMunicipalities);

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

/**
 * What it does: Renders a bar chart showing the top 10 municipalities by carrier count.
 * Why it exists: To visually identify the main geographic hubs of carrier activity.
 * What data it uses: A sorted array of municipality statistics objects.
 */
function initMunicipalityBarChart(municipalityRows) {
    const ctx = document.getElementById('municipalityBarChart').getContext('2d');
    const rows = Array.isArray(municipalityRows) ? municipalityRows : [];
    const labels = rows.map(m => m.name);
    const data = rows.map(m => m.total);

    const colorPalette = generateColorPalette(labels.length);

    statsCharts.municipalityBar = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: t('chart_label_total_carriers'),
                data: data,
                backgroundColor: colorPalette.map(c => `${c}b3`), // Add alpha
                borderColor: colorPalette,
                borderWidth: 1,
                borderRadius: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.dataset.label}: ${context.parsed.y}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(128, 128, 128, 0.1)' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
}

/**
 * What it does: Renders a doughnut chart showing the distribution of public vs. private carriers.
 * Why it exists: To provide a quick, at-a-glance understanding of the market composition.
 * What data it uses: The \`kpis\` object containing public and private carrier counts.
 */
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
            }
        }
    });
}

/**
 * What it does: Renders a line chart showing carrier activity over a specified time period.
 * Why it exists: To identify trends, seasonality, and patterns in carrier registration or activity.
 * What data it uses: The \`activity\` object from the backend, filtered by the selected period.
 */
function initActivityLineChart(period, activityData) {
    if (statsCharts.activityLine) {
        statsCharts.activityLine.destroy();
    }
    const ctx = document.getElementById('activityLineChart').getContext('2d');
    const periodData = Array.isArray(activityData?.[period]) ? activityData[period] : [];
    
    const labels = periodData.map(d => d.date || d.week || d.month);
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
            }
        }
    });
}

/**
 * What it does: Renders a grouped bar chart comparing active vs. inactive carriers per municipality.
 * Why it exists: To pinpoint specific geographic areas with potential compliance or data-quality issues.
 * What data it uses: A sorted array of municipality statistics objects.
 */
function initMunicipalityGroupChart(municipalityRows) {
    const ctx = document.getElementById('municipalityGroupChart').getContext('2d');
    const rows = Array.isArray(municipalityRows) ? municipalityRows : [];
    const labels = rows.map(m => m.name);
    const activeData = rows.map(m => m.active);
    const inactiveData = rows.map(m => m.inactive);

    statsCharts.municipalityGroup = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: t('kpi_active_carriers'),
                    data: activeData,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 4,
                },
                {
                    label: t('kpi_inactive_carriers'),
                    data: inactiveData,
                    backgroundColor: 'rgba(239, 68, 68, 0.7)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    borderRadius: 4,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false,
                    grid: { color: 'rgba(128, 128, 128, 0.1)' }
                },
                x: {
                    stacked: false,
                    grid: { display: false }
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

// ── Add Contract Page ──────────────────────────────────────

async function renderAddContract() {
    try {
        // The contract create page intentionally stays single-window so users can
        // enter every required field in one pass without a follow-up stepper.
        el.content.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">${t('add_contract_title')}</h2>
                </div>
                <div class="card-body">
                    <form id="contract-form">
                        <!-- Single Section Add Contract -->
                        <div class="section-title">${t('add_contract_title')}</div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('record_number')} *</label>
                                <input type="text" class="form-control" name="record_number" data-validate="required|numbers">
                                <div class="field-error" data-error-for="record_number"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('signing_date')}</label>
                                <input type="date" class="form-control" name="signature_date">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('company_carrier_name')} *</label>
                                <input type="text" class="form-control" name="company_name" data-validate="required|letters">
                                <div class="field-error" data-error-for="company_name"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('registration_code')}</label>
                                <input type="text" class="form-control" name="company_reg" data-validate="numbers">
                                <div class="field-error" data-error-for="company_reg"></div>
                            </div>
                        </div>

                        <div class="form-group">
                            <label>${t('company_address')}</label>
                            <select class="form-control" name="company_address">
                                <!-- Options: populated later by user -->
                                <option value="">${t('select_address')}</option>
                            </select>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('vehicle_registration_number')} *</label>
                                <input type="text" class="form-control" name="vehicle_reg" data-validate="required|numbers">
                                <div class="field-error" data-error-for="vehicle_reg"></div>
                            </div>
                            <div class="form-group">
                                <label>${t('vehicle_type_category')}</label>
                                <input type="text" class="form-control" name="vehicle_type_category" placeholder="e.g. Truck A">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>${t('route')}</label>
                                <input type="text" class="form-control" name="route" placeholder="e.g. Setif → Algiers">
                            </div>
                            <div class="form-group">
                                <label>${t('license_expiry_date')}</label>
                                <input type="date" class="form-control" name="expiration_date">
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
                                <label>${t('transported_materials')}</label>
                                <input type="text" class="form-control" name="hazmat_type">
                            </div>
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

        // Validation for the form fields
        setupContractFormValidation();
        document.getElementById('contract-form').addEventListener('submit', handleFormSubmit);

        // Populate company address options from Setif communes JSON
        const select = document.querySelector('select[name="company_address"]');
        await populateCommunesSelect(select, '');
    } catch (err) {
        el.content.innerHTML = `<div class="empty-state"><h2>Error</h2><p>${err.message}</p></div>`;
        showToast(err.message, 'error');
    }
}

// ── Form Handling ────────────────────────────────────────────

async function handleFormSubmit(event) {
    event.preventDefault();
    const form = event.target;
    
    // Validate form to display errors if any are present
    if (!validateContractForm()) {
        showToast(t('form_has_errors'), 'error');
        return;
    }
    
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = t('btn_saving');

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Map frontend clean fields to backend legacy model structure
    const payload = {
        record_number: data.record_number,
        company_name: data.company_name,
        company_reg: data.company_reg || "",
        company_address: data.company_address || "",
        vehicle_reg: data.vehicle_reg,
        expiration_date: data.expiration_date || "",
        signature_date: data.signature_date || "",
        carrier_type: data.carrier_type || "Public",
        account_type: data.carrier_type || "Public",
        contract_type: data.carrier_type || "Public",
        hazmat_type: data.hazmat_type || "",
        // Default empty strings/null for un-exposed required schema keys
        driver_name: "",
        driver_phone: "",
        route_checkpoints: "",
        deletion_days: null,
        // Auto-generate license_number based on record_number
        license_number: 'LIC-' + data.record_number,
        // Default activity location to the commune name from address
        activity_location: data.company_address ? data.company_address.split(',')[0].trim() : ""
    };

    // Split vehicle type and category by space
    const typeCat = (data.vehicle_type_category || "").trim();
    if (typeCat) {
        const parts = typeCat.split(/\s+/);
        payload.vehicle_type = parts[0] || "";
        payload.vehicle_category = parts.slice(1).join(" ") || "";
    } else {
        payload.vehicle_type = "";
        payload.vehicle_category = "";
    }

    // Split route by → or -> separator
    const route = (data.route || "").trim();
    if (route) {
        const parts = route.split(/→|->/);
        payload.route_origin = (parts[0] || "").trim();
        payload.route_dest = (parts[1] || "").trim();
    } else {
        payload.route_origin = "";
        payload.route_dest = "";
    }

    try {
        await API.createLicense(payload);
        showToast(t('saved_ok'), 'success');
        navigateTo('dashboard');
    } catch (err) {
        showToast(err.message, 'error');
        submitBtn.disabled = false;
        submitBtn.textContent = t('btn_save');
    }
}

function setupContractFormValidation() {
    const form = document.getElementById('contract-form');
    const submitBtn = document.getElementById('submit-btn');
    const trackedInputs = Array.from(form.querySelectorAll('[data-validate]'));

    function setError(input, message) {
        const errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
        if (!errorEl) return;
        
        // Show validation error only if it's touched or if form is submitted
        const shouldShowError = input.classList.contains('touched') || form.classList.contains('submitted');
        
        if (shouldShowError && message) {
            errorEl.textContent = message;
            input.classList.add('input-invalid');
        } else {
            errorEl.textContent = '';
            input.classList.remove('input-invalid');
        }
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
        let formIsValid = true;
        trackedInputs.forEach(input => {
            const isInputValid = validateInput(input);
            if (!isInputValid) {
                formIsValid = false;
            }
        });
        submitBtn.disabled = !formIsValid;
        return formIsValid;
    }

    trackedInputs.forEach(input => {
        input.addEventListener('input', () => {
            input.classList.add('touched');
            validateInput(input);
            validateAll();
        });
        input.addEventListener('blur', () => {
            input.classList.add('touched');
            validateInput(input);
            validateAll();
        });
    });

    validateAll();
}

function validateContractForm() {
    const form = document.getElementById('contract-form');
    if (!form) return false;
    form.classList.add('submitted');
    
    const inputs = Array.from(form.querySelectorAll('[data-validate]'));
    let allValid = true;
    
    inputs.forEach(input => {
        input.classList.add('touched');
        const rawRules = input.getAttribute('data-validate');
        if (rawRules) {
            const value = input.value.trim();
            const rules = rawRules.split('|');
            let message = '';
            
            if (rules.includes('required') && !value) {
                message = t('invalid_required');
                allValid = false;
            } else if (value) {
                if (rules.includes('numbers') && !/^\d+$/.test(value)) {
                    message = t('invalid_numbers_only');
                    allValid = false;
                } else if (rules.includes('letters') && !/^[\p{L}\s'\-]+$/u.test(value)) {
                    message = t('invalid_letters_only');
                    allValid = false;
                }
            }
            
            const errorEl = form.querySelector(`[data-error-for="${input.name}"]`);
            if (errorEl) {
                errorEl.textContent = message;
            }
            input.classList.toggle('input-invalid', Boolean(message));
        }
    });
    
    const submitBtn = document.getElementById('submit-btn');
    if (submitBtn) {
        submitBtn.disabled = !allValid;
    }
    return allValid;
}

// ── Add Vehicle Linked to Contract ──────────────────────────


// ── Edit Modal Logic ────────────────────────────────────────

async function openEditModal(id) {
    try {
        const data = await API.getLicense(id);
        const modal = document.getElementById('edit-modal');
        const body = document.getElementById('edit-modal-body');
        
        document.getElementById('edit-modal-title').textContent = t('edit_contract_title');
        
        body.innerHTML = `
            <form id="edit-form">
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('record_number')}</label>
                        <input type="text" class="form-control" name="record_number" value="${data.record_number}">
                    </div>
                    <div class="form-group">
                        <label>${t('license_number')}</label>
                        <input type="text" class="form-control" name="license_number" value="${data.license_number}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('signature_date')}</label>
                        <input type="date" class="form-control" name="signature_date" value="${data.signature_date}">
                    </div>
                    <div class="form-group">
                        <label>${t('expiration_date')}</label>
                        <input type="date" class="form-control" name="expiration_date" value="${data.expiration_date}">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>${t('activity_location')}</label>
                        <select class="form-control" name="activity_location">
                            <!-- Populated dynamically -->
                        </select>
                    </div>
                    <div class="form-group">
                        <label>${t('carrier_type')}</label>
                        <select class="form-control" name="contract_type">
                            <option value="Public" ${data.contract_type === 'Public' ? 'selected' : ''}>${t('opt_public')}</option>
                            <option value="Private" ${data.contract_type === 'Private' ? 'selected' : ''}>${t('opt_private')}</option>
                        </select>
                    </div>
                </div>
            </form>
        `;

        const select = body.querySelector('select[name="activity_location"]');
        await populateCommunesSelect(select, data.activity_location, true);

        modal.classList.remove('hidden');

        document.getElementById('edit-save').onclick = async () => {
            const formData = new FormData(document.getElementById('edit-form'));
            const updateData = Object.fromEntries(formData.entries());
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
        
        // Translate welcome page content dynamically since it is loaded via fetch
        applyLanguageToContainer(el.content);

        // Add event listeners for the action cards
        document.getElementById('action-add-contract').addEventListener('click', () => navigateTo('add-contract'));
        document.getElementById('action-search').addEventListener('click', () => navigateTo('search'));
        document.getElementById('action-view-stats').addEventListener('click', () => navigateTo('statistics'));

    } catch (err) {
        el.content.innerHTML = `<div class="empty-state"><h2>${t('toast_error')}</h2><p>${translateError(err.message)}</p></div>`;
        showToast(err.message, 'error');
    }
}

// Start app
init();
