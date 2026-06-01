/**
 * api.js — All calls to the Python Flask backend.
 * Never makes DB calls directly — everything goes through the API.
 */

let API_BASE = "http://127.0.0.1:5757"; // default, overridden on init

async function initApiBase() {
  // Electron injects the real API base at runtime so the renderer never guesses
  // the backend address. If this were hard-coded only, packaged builds or future
  // port changes would break every request path in the UI.
  if (window.electronAPI) {
    API_BASE = await window.electronAPI.getApiBase();
  }
}

// ── Auth helpers ───────────────────────────────────────────────────────────

function getAuthToken() {
  return sessionStorage.getItem("auth_token");
}

function getAuthHeaders() {
  const token = getAuthToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(path, options = {}) {
  // This wrapper enforces one response contract for the entire renderer layer.
  // Every page depends on the same JSON shape, so centralizing the parse and error
  // check here keeps the UI logic simple and prevents duplicated fetch handling.
  const url = `${API_BASE}${path}`;
  const resp = await fetch(url, {
    headers: { "Content-Type": "application/json", ...getAuthHeaders(), ...options.headers },
    ...options,
  });
  const data = await resp.json();
  if (!resp.ok || data.status === "error") {
    throw new Error(data.message || `HTTP ${resp.status}`);
  }
  return data.data;
}

// ── Stats ──────────────────────────────────────────────────
const API = {
  ping: ()                => apiFetch("/api/ping"),
  stats: ()               => apiFetch("/api/stats"),
  statsAdvanced: ()       => apiFetch("/api/statistics/dashboard"),
  statsMonthly: (m=12)    => apiFetch(`/api/stats/monthly?months=${m}`),

  // Auth
  login: (username, password) => apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    headers: {},  // no auth header needed for login
  }),
  logout: () => apiFetch("/auth/logout", { method: "POST" }),
  validateSession: () => apiFetch("/auth/validate"),
  changePassword: (username, current_password, new_password) => apiFetch("/auth/change-password", {
    method: "POST",
    body: JSON.stringify({ username, current_password, new_password }),
  }),

  // Licenses
  getLicenses: (params={}) => apiFetch("/api/licenses?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([,v]) => v !== null && v !== undefined && v !== ""))
  )),
  getLicense: (id)         => apiFetch(`/api/licenses/${id}`),
  createLicense: (body)    => apiFetch("/api/licenses", { method:"POST", body: JSON.stringify(body) }),
  updateLicense: (id,body) => apiFetch(`/api/licenses/${id}`, { method:"PUT", body: JSON.stringify(body) }),
  deleteLicense: (id)      => apiFetch(`/api/licenses/${id}`, { method:"DELETE" }),
  getDeletedLicenses: (params={}) => apiFetch("/api/licenses/deleted?" + new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([,v]) => v !== null && v !== undefined && v !== ""))
  )),
  restoreLicense: (id)      => apiFetch(`/api/licenses/${id}/restore`, { method:"POST" }),
  expiringLicenses: (start=0, end=30, limit=null) => apiFetch(`/api/licenses/expiring?start_days=${start}&end_days=${end}` + (limit ? `&limit=${limit}` : '')),
  nextRecordNumber: ()     => apiFetch("/api/licenses/next-record-number"),

  // Companies / Vehicles
  getCompanies: ()         => apiFetch("/api/companies"),
  getVehicles:  ()         => apiFetch("/api/vehicles"),
  getDrivers:   ()         => apiFetch("/api/drivers"),

  // Settings
  getSettings: ()          => apiFetch("/api/settings"),
  saveSettings: (body)     => apiFetch("/api/settings", { method:"PUT", body: JSON.stringify(body) }),
};
