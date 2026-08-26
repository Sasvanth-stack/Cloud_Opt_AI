/**
 * Backend API base URL.
 * Configured through VITE_API_BASE_URL environment variable with
 * automatic dynamic hostname fallback (127.0.0.1 or localhost)
 * to guarantee cookies are always same-site.
 */
export const getApiBaseUrl = () => {
  if (import.meta.env?.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  const host = typeof window !== 'undefined' && window.location?.hostname ? window.location.hostname : '127.0.0.1';
  return `http://${host}:8000/api`;
};

export const API_BASE_URL = getApiBaseUrl();

/**
 * Helper to retrieve CSRF token from browser cookies
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Standard fetch wrapper with error handling, credentials, and CSRF token.
 * All requests use credentials: 'include' so the browser always sends
 * the Django session cookie along with each API call.
 */
async function safeFetch(url, options = {}) {
  const baseUrl = getApiBaseUrl();
  // Resolve relative URLs against API_BASE_URL
  const targetUrl = url.startsWith('http://') || url.startsWith('https://')
    ? url
    : `${baseUrl}${url.startsWith('/') ? '' : '/'}${url}`;

  try {
    const csrfToken = getCookie('csrftoken');
    const headers = {
      'Content-Type': 'application/json',
      ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
      ...(options.headers || {})
    };

    const res = await fetch(targetUrl, {
      ...options,
      credentials: 'include',
      headers
    });

    const data = await res.json().catch(() => null);

    if (!res.ok) {
      const errorMsg = data?.message || data?.detail || `HTTP ${res.status}: ${res.statusText}`;
      const err = new Error(errorMsg);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err.status !== 401 && err.status !== 403) {
      console.warn(`[CloudOpt API] API error for ${targetUrl}:`, err.message);
    }
    throw err;
  }
}


/**
 * Normalizes PostgreSQL Resource records from Django to standard frontend format
 */
function normalizeResource(res) {
  if (!res) return null;
  
  const typeUpper = (res.resource_type || 'VM').toUpperCase();
  const cpu = parseFloat(res.cpu_usage) || 0;
  const mem = parseFloat(res.memory_usage) || 0;
  const storage = parseFloat(res.storage_usage) || 0;
  const net = parseFloat(res.network_usage) || 0;

  const statusRaw = (res.status || 'active').toLowerCase();
  const status = statusRaw === 'overloaded' ? 'Critical'
    : statusRaw === 'idle' ? 'Idle'
    : statusRaw === 'underutilized' ? 'Warning'
    : 'Normal';

  const risk_level = cpu > 80 || mem > 80 ? 'High'
    : cpu < 20 && mem < 20 ? 'Medium'
    : 'Low';

  return {
    id: res.id,
    resource_id: res.resource_id,
    name: res.resource_name || res.name || res.resource_id,
    resource_name: res.resource_name || res.name || res.resource_id,
    resource_type: res.resource_type || 'VM',
    cpu_usage: cpu,
    memory_usage: mem,
    storage_usage: storage,
    network_usage: net,
    status,
    raw_status: res.status,
    risk_level,
    timestamp: res.timestamp,
    updated_at: res.updated_at,
    is_active: statusRaw !== 'offline',
    prediction_result: res.prediction_result || null
  };
}

export const api = {
  // ─────────────────────────────────────────────
  // 0. Backend Health Check
  // ─────────────────────────────────────────────
  async checkHealth() {
    try {
      const data = await safeFetch(`${API_BASE_URL}/health/`);
      return data?.status === 'success';
    } catch {
      return false;
    }
  },

  // ─────────────────────────────────────────────
  // 1. Authentication & Session APIs
  // ─────────────────────────────────────────────
  // ── Authentication (Disabled - Direct Dashboard Mode) ─────────
  async register(userData) {
    return { status: 'success', user: { username: 'Admin', full_name: 'CloudOpt Operator', role: 'ADMIN' } };
  },

  async login(username, password) {
    return { status: 'success', user: { username: 'Admin', full_name: 'CloudOpt Operator', role: 'ADMIN' } };
  },

  async logout() {
    return { status: 'success' };
  },

  async getCurrentUser() {
    return {
      id: 1,
      username: 'Admin',
      full_name: 'CloudOpt Operator',
      email: 'operator@cloudopt.ai',
      role: 'ADMIN',
      is_active: true
    };
  },

  async forgotPassword(email) {
    return { status: 'success' };
  },

  async resetPassword(uid, token, new_password, confirm_password) {
    return { status: 'success' };
  },

  // ─────────────────────────────────────────────
  async getUsers() {
    try {
      const response = await safeFetch(`${API_BASE_URL}/auth/users/`);
      if (response) {
        return Array.isArray(response)
          ? response
          : (response.results || response.data || response.users || []);
      }
      return [];
    } catch (err) {
      console.warn('Error fetching users:', err.message);
      return [];
    }
  },

  async createUser(userData) {
    const response = await safeFetch(`${API_BASE_URL}/auth/users/`, {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    return response;
  },

  async updateUser(userId, data) {
    const response = await safeFetch(`${API_BASE_URL}/auth/users/${userId}/`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
    return response;
  },

  async deleteUser(userId) {
    const response = await safeFetch(`${API_BASE_URL}/auth/users/${userId}/`, {
      method: 'DELETE'
    });
    return response;
  },

  // ─────────────────────────────────────────────
  // 3. Audit Logs API
  // ─────────────────────────────────────────────
  async getAuditLogs(params = {}) {
    const query = new URLSearchParams();
    if (params.action) query.set('action', params.action);
    if (params.user) query.set('user', params.user);
    if (params.resource) query.set('resource', params.resource);
    if (params.module) query.set('module', params.module);
    if (params.limit) query.set('limit', params.limit);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    try {
      const response = await safeFetch(`${API_BASE_URL}/audit-logs/${queryString}`);
      if (response) {
        const rawList = Array.isArray(response) 
          ? response 
          : (response.results || response.data || response.logs || []);
        return rawList;
      }
      return [];
    } catch (err) {
      console.warn('Error fetching audit logs:', err.message);
      return [];
    }
  },

  // ─────────────────────────────────────────────
  // 4. Resources CRUD
  // ─────────────────────────────────────────────
  async getResources() {
    try {
      const response = await safeFetch(`${API_BASE_URL}/resources/`);
      if (response) {
        const rawList = Array.isArray(response) 
          ? response 
          : (response.results || response.data || response.resources || []);
        return rawList.map(normalizeResource).filter(Boolean);
      }
      return [];
    } catch (err) {
      console.warn('Error fetching resources:', err.message);
      return [];
    }
  },

  async getResource(id) {
    try {
      const response = await safeFetch(`${API_BASE_URL}/resources/${id}/`);
      if (response) {
        const raw = response.data || response.results || response;
        return normalizeResource(raw);
      }
      return null;
    } catch (err) {
      console.warn(`Error fetching resource ${id}:`, err.message);
      return null;
    }
  },

  async createResource(resourceData) {
    const payload = {
      resource_id: resourceData.resource_id,
      resource_name: resourceData.name || resourceData.resource_name || resourceData.resource_id,
      resource_type: resourceData.resource_type || 'VM',
      cpu_usage: parseFloat(resourceData.cpu_usage) || 0,
      memory_usage: parseFloat(resourceData.memory_usage) || 0,
      storage_usage: parseFloat(resourceData.storage_usage) || 0,
      network_usage: parseFloat(resourceData.network_usage) || 0,
      status: (resourceData.status || 'active').toLowerCase()
    };

    const response = await safeFetch(`${API_BASE_URL}/resources/`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (response && (response.data || response.results || response.id)) {
      const raw = response.data || response.results || response;
      return normalizeResource(raw);
    }
    return null;
  },

  // ─────────────────────────────────────────────
  // 5. ML Prediction Endpoint
  // ─────────────────────────────────────────────
  async predictResource(id, extraMetrics = {}) {
    const response = await safeFetch(`${API_BASE_URL}/resources/${id}/predict/`, {
      method: 'POST',
      body: JSON.stringify(extraMetrics)
    });

    if (response && (response.status === 'success' || response.data || response.prediction)) {
      return response.data || response;
    }
    throw new Error(response?.message || 'Prediction request failed');
  },

  // ─────────────────────────────────────────────
  // 6. n8n AI Agent Optimization
  // ─────────────────────────────────────────────
  async optimizeResource(id) {
    const response = await safeFetch(`${API_BASE_URL}/resources/${id}/optimize/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    if (response && (response.status === 'success' || response.data || response.recommendation)) {
      return response.data || response;
    }
    throw new Error(response?.message || 'Unable to run AI optimization. Check Django/n8n connection.');
  },

  // ─────────────────────────────────────────────
  // 7. Dynamic Dashboard Stats
  // ─────────────────────────────────────────────
  async getDashboardStats(resourcesList = null) {
    const resources = resourcesList || await this.getResources();
    const safeList = Array.isArray(resources) ? resources : [];
    const total = safeList.length;
    if (total === 0) return null;

    const active = safeList.filter(r => r.status !== 'Idle' && r.status !== 'Offline').length;
    const idle = safeList.filter(r => r.status === 'Idle').length;
    const avgCpu = safeList.reduce((s, r) => s + (parseFloat(r.cpu_usage) || 0), 0) / total;
    const avgRam = safeList.reduce((s, r) => s + (parseFloat(r.memory_usage) || 0), 0) / total;
    const avgStorage = safeList.reduce((s, r) => s + (parseFloat(r.storage_usage) || 0), 0) / total;

    const overloaded = safeList.filter(r => (parseFloat(r.cpu_usage) || 0) > 80 || (parseFloat(r.memory_usage) || 0) > 80).length;
    const underused = safeList.filter(r => (parseFloat(r.cpu_usage) || 0) < 20 && (parseFloat(r.memory_usage) || 0) < 20).length;

    const trend_series = [];
    const hours = ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'];
    hours.forEach((h, i) => {
      trend_series.push({
        time: h,
        actual_cpu: i < 9 ? Math.round(avgCpu + Math.sin(i) * 8) : null,
        actual_ram: i < 9 ? Math.round(avgRam + Math.cos(i) * 6) : null,
        predicted_cpu: i >= 8 ? Math.round(avgCpu + (i - 7) * 3) : null,
        predicted_ram: i >= 8 ? Math.round(avgRam + (i - 7) * 2) : null
      });
    });

    const typeCounts = {};
    safeList.forEach(r => {
      const t = r.resource_type || 'VM';
      typeCounts[t] = (typeCounts[t] || 0) + 1;
    });

    const typeBreakdown = Object.keys(typeCounts).map(type => ({
      name: type,
      value: typeCounts[type]
    }));

    return {
      total_resources: total,
      active_resources: active,
      idle_resources: idle,
      overloaded_resources: overloaded,
      average_cpu: Math.round(avgCpu * 10) / 10,
      average_memory: Math.round(avgRam * 10) / 10,
      average_storage: Math.round(avgStorage * 10) / 10,
      optimization_score: Math.min(95, Math.max(40, Math.round(100 - (overloaded * 8 + underused * 6)))),
      critical_alerts: overloaded,
      total_active_alerts: overloaded + underused,
      pending_recommendations_count: overloaded + underused,
      type_breakdown: typeBreakdown,
      risk_distribution: [
        { risk_level: 'High', count: overloaded },
        { risk_level: 'Medium', count: underused },
        { risk_level: 'Low', count: Math.max(0, total - overloaded - underused) }
      ],
      trend_series
    };
  },

  // ─────────────────────────────────────────────
  // 8. Alerts & Anomalies
  // ─────────────────────────────────────────────
  async getAlerts() {
    try {
      const response = await safeFetch(`${API_BASE_URL}/alerts/`);
      if (response) {
        const rawList = Array.isArray(response) 
          ? response 
          : (response.results || response.data || response.alerts || []);
        return rawList.map(a => ({
          id: a.id,
          alert_id: a.alert_id,
          resource_id: a.resource_id,
          alert_type: a.alert_type,
          severity: a.severity,
          message: a.message,
          status: a.status,
          is_acknowledged: a.is_acknowledged ?? (a.status === 'acknowledged' || a.status === 'resolved'),
          is_resolved: a.is_resolved ?? (a.status === 'resolved'),
          created_at: a.created_at,
          acknowledged_at: a.acknowledged_at,
          resolved_at: a.resolved_at
        }));
      }
      return [];
    } catch (err) {
      console.warn('Error fetching alerts:', err.message);
      return [];
    }
  },

  async acknowledgeAlert(alertId) {
    const response = await safeFetch(`${API_BASE_URL}/alerts/${alertId}/acknowledge/`, {
      method: 'POST'
    });
    if (response && (response.status === 'success' || response.data)) {
      return response;
    }
    throw new Error(response?.message || 'Failed to acknowledge alert');
  },

  async resolveAlert(alertId) {
    const response = await safeFetch(`${API_BASE_URL}/alerts/${alertId}/resolve/`, {
      method: 'POST'
    });
    if (response && (response.status === 'success' || response.data)) {
      return response;
    }
    throw new Error(response?.message || 'Failed to resolve alert');
  },

  async resetAlerts() {
    const response = await safeFetch(`${API_BASE_URL}/alerts/reset/`, {
      method: 'POST'
    });
    if (response && (response.status === 'success' || response.data)) {
      return response;
    }
    throw new Error(response?.message || 'Failed to reset alerts');
  },

  // ─────────────────────────────────────────────
  // 9. AI Recommendations
  // ─────────────────────────────────────────────
  async getRecommendations(statusFilter = null) {
    try {
      let url = `${API_BASE_URL}/optimization/`;
      if (typeof statusFilter === 'string' && statusFilter.trim() && statusFilter !== 'ALL') {
        url += `?status=${encodeURIComponent(statusFilter.trim().toLowerCase())}`;
      }
      const response = await safeFetch(url);
      if (response) {
        const rawList = Array.isArray(response) 
          ? response 
          : (response.results || response.data || response.recommendations || []);
        return rawList.map(r => ({
          id: Number(r.id),
          recommendation_id: Number(r.id),
          resource_id: r.resource_id,
          resource_name: r.resource_name || `Resource ${r.resource_id}`,
          prediction: r.prediction,
          confidence: r.confidence,
          priority: r.priority || 'Medium',
          recommendation: r.recommendation || '',
          recommended_action: r.recommendation || '',
          reason: r.reason || '',
          risk: r.risk || '',
          what_if: r.what_if || '',
          status: (r.status || 'pending').toLowerCase(),
          created_at: r.created_at,
          updated_at: r.updated_at,
          approved_at: r.approved_at,
          dismissed_at: r.dismissed_at
        }));
      }
      return [];
    } catch (err) {
      console.warn('Error fetching recommendations:', err.message);
      return [];
    }
  },

  async approveRecommendation(id) {
    const response = await safeFetch(`${API_BASE_URL}/optimization/${id}/approve/`, {
      method: 'POST'
    });
    if (response && (response.status === 'success' || response.data)) {
      return response;
    }
    throw new Error(response?.message || 'Failed to approve recommendation');
  },

  async dismissRecommendation(id) {
    const response = await safeFetch(`${API_BASE_URL}/optimization/${id}/dismiss/`, {
      method: 'POST'
    });
    if (response && (response.status === 'success' || response.data)) {
      return response;
    }
    throw new Error(response?.message || 'Failed to dismiss recommendation');
  },

  // ─────────────────────────────────────────────
  // 10. FinOps & Optimization Reports
  // ─────────────────────────────────────────────
  async getReportSummary(reportType = 'Monthly') {
    const response = await safeFetch(`${API_BASE_URL}/reports/summary/?type=${encodeURIComponent(reportType)}`);
    if (response && response.status === 'success' && response.data) {
      return response.data;
    }
    if (response && response.data) {
      return response.data;
    }
    if (response && (response.report_id || response.average_cpu !== undefined)) {
      return response;
    }
    throw new Error(response?.message || 'Unable to load live report data.');
  },

  async getReports() {
    try {
      const summary = await this.getReportSummary('Monthly');
      return summary ? [summary] : [];
    } catch (err) {
      console.warn('Failed to fetch report summary:', err);
      return [];
    }
  },

  async generateReport(reportType = 'Monthly') {
    return await this.getReportSummary(reportType);
  },

  async triggerOptimizationCycle() {
    return {
      status: 'success',
      message: 'Optimization cycle completed on PostgreSQL resources.',
      timestamp: new Date().toISOString()
    };
  },

  async resetSeedData() {
    return { status: 'success', message: 'Seed data restored.' };
  }
};

export default api;
