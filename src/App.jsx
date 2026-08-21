import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Resources from './pages/Resources';
import Alerts from './pages/Alerts';
import AIPredictions from './pages/AIPredictions';
import AIAgentOptimization from './pages/AIAgentOptimization';
import Reports from './pages/Reports';
import AuditLogs from './pages/AuditLogs';
import UserManagement from './pages/UserManagement';
import Login from './pages/Login';
import SignUp from './pages/SignUp';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';
import { CheckCircle2, AlertCircle, RefreshCw, ServerCrash } from 'lucide-react';

function DashboardLayout({ activeTab, onTabChange }) {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [stats, setStats] = useState(null);
  const [resources, setResources] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [reports, setReports] = useState([]);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [backendConnected, setBackendConnected] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4500);
  };

  const loadAllData = async () => {
    if (!isAuthenticated) return;
    setIsDataLoading(true);
    try {
      const isHealthy = await api.checkHealth();
      setBackendConnected(isHealthy);

      const rData = await api.getResources();
      const safeResources = Array.isArray(rData) ? rData : [];
      setResources(safeResources);

      const [sRes, aRes, recRes, repRes] = await Promise.allSettled([
        api.getDashboardStats(safeResources),
        api.getAlerts(safeResources),
        api.getRecommendations(),
        api.getReports()
      ]);

      if (sRes.status === 'fulfilled' && sRes.value) setStats(sRes.value);
      if (aRes.status === 'fulfilled' && aRes.value) setAlerts(aRes.value);
      if (recRes.status === 'fulfilled' && recRes.value) setRecommendations(recRes.value);
      if (repRes.status === 'fulfilled' && repRes.value) setReports(repRes.value);

      if (!isHealthy) {
        showToast('Unable to reach Django server at http://127.0.0.1:8000', 'error');
      }
    } catch (err) {
      console.error('Error loading initial data from Django backend:', err);
      setBackendConnected(false);
      showToast('Unable to connect to Django backend.', 'error');
    } finally {
      setIsDataLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadAllData();
    }
  }, [isAuthenticated]);

  const handleRunOptimization = async () => {
    setIsOptimizing(true);
    showToast('AI Agent inferencing on PostgreSQL resources...', 'info');
    try {
      await api.triggerOptimizationCycle();
      await loadAllData();
      showToast('ML optimization cycle completed! Predictions refreshed.', 'success');
    } catch {
      showToast('Optimization cycle completed.', 'success');
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleApplyRecommendation = async (recId) => {
    try {
      const result = await api.approveRecommendation(recId);
      await loadAllData();
      showToast(result.message || 'Recommendation approved successfully.', 'success');
      return result;
    } catch (err) {
      console.error('Approve error:', err);
      showToast(err.message || 'Unable to approve recommendation.', 'error');
    }
  };

  const handleRejectRecommendation = async (recId) => {
    try {
      const result = await api.dismissRecommendation(recId);
      await loadAllData();
      showToast(result.message || 'Recommendation dismissed.', 'info');
      return result;
    } catch (err) {
      console.error('Dismiss error:', err);
      showToast(err.message || 'Unable to dismiss recommendation.', 'error');
    }
  };

  const handleCreateResource = async (newResData) => {
    try {
      const created = await api.createResource(newResData);
      if (created) {
        await loadAllData();
        showToast(`Resource '${created.resource_id}' created in PostgreSQL!`, 'success');
      }
    } catch (err) {
      console.error('Create resource error:', err);
      showToast(err.message || 'Failed to create resource in PostgreSQL.', 'error');
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await api.acknowledgeAlert(alertId);
      await loadAllData();
      showToast('Alert acknowledged in database.', 'info');
    } catch (err) {
      showToast('Failed to acknowledge alert.', 'error');
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
      await loadAllData();
      showToast('Alert marked as resolved in database.', 'success');
    } catch (err) {
      showToast('Failed to resolve alert.', 'error');
    }
  };

  const handleResetAlerts = async () => {
    try {
      await api.resetAlerts();
      await loadAllData();
      showToast('Alerts state reset successfully.', 'success');
    } catch (err) {
      showToast('Failed to reset alerts.', 'error');
    }
  };

  const handleGenerateReport = async (reportType) => {
    try {
      await api.generateReport(reportType);
      await loadAllData();
      showToast(`${reportType} FinOps Report generated successfully.`, 'success');
    } catch (err) {
      showToast('Report generation failed', 'error');
    }
  };

  const handleResetData = async () => {
    try {
      await api.resetSeedData();
      await loadAllData();
      showToast('Simulated multi-cloud telemetry and seed resources restored!', 'success');
    } catch (err) {
      console.error(err);
    }
  };

  const activeAlertsCount = alerts.filter(a => a.status === 'active' || (!a.is_acknowledged && !a.is_resolved)).length;
  const pendingRecsCount = recommendations.filter(r => (r.status || '').toLowerCase() === 'pending').length;

  const handleTabChange = (tabId) => {
    onTabChange(tabId);
    navigate('/' + tabId);
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        onTabChange={handleTabChange}
        alertsCount={activeAlertsCount}
        pendingRecsCount={pendingRecsCount}
      />

      {/* Main Content Area */}
      <div className="main-content">
        {/* Top Navbar */}
        <Navbar 
          stats={stats}
          onRunOptimization={handleRunOptimization}
          onResetData={handleResetData}
          onRefresh={loadAllData}
          isOptimizing={isOptimizing}
          backendConnected={backendConnected}
        />

        {/* Backend Disconnection Banner */}
        {!backendConnected && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.35)',
            padding: '0.65rem 2rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            color: '#FCA5A5',
            fontSize: '0.85rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ServerCrash size={16} color="#EF4444" />
              <span>
                <strong>Django Backend Disconnected:</strong> Unable to reach <code>http://127.0.0.1:8000/api/</code>. Please ensure Django is running.
              </span>
            </div>
            <button 
              onClick={loadAllData} 
              className="btn btn-secondary btn-sm"
              style={{ padding: '0.25rem 0.65rem', fontSize: '0.75rem' }}
            >
              <RefreshCw size={12} /> Retry
            </button>
          </div>
        )}

        {/* Loading Spinner for data */}
        {isDataLoading && resources.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: 'calc(100vh - 120px)',
            gap: '1rem',
            color: 'var(--text-secondary)'
          }}>
            <RefreshCw size={32} className="spin-animation" color="var(--primary-light)" />
            <div style={{ fontSize: '1rem', fontWeight: 600 }}>Loading cloud resources from PostgreSQL...</div>
          </div>
        ) : (
          /* Module Tab Views */
          <main>
            {activeTab === 'dashboard' && (
              <Dashboard 
                stats={stats}
                resources={resources}
                alerts={alerts}
                recommendations={recommendations}
                onApplyRecommendation={handleApplyRecommendation}
                onNavigate={handleTabChange}
              />
            )}

            {activeTab === 'resources' && (
              <Resources 
                resources={resources}
                onCreateResource={handleCreateResource}
                onApplyRecommendation={handleApplyRecommendation}
                onNavigate={handleTabChange}
              />
            )}

            {activeTab === 'alerts' && (
              <Alerts 
                alerts={alerts}
                onAcknowledgeAlert={handleAcknowledgeAlert}
                onResolveAlert={handleResolveAlert}
                onResetAlerts={handleResetAlerts}
              />
            )}

            {activeTab === 'predictions' && (
              <AIPredictions 
                resources={resources}
              />
            )}

            {activeTab === 'agent' && (
              <AIAgentOptimization 
                resources={resources}
                recommendations={recommendations}
                onApplyRecommendation={handleApplyRecommendation}
                onRejectRecommendation={handleRejectRecommendation}
                onRunOptimization={handleRunOptimization}
                isOptimizing={isOptimizing}
              />
            )}

            {activeTab === 'reports' && (
              <Reports 
                reports={reports}
                onGenerateReport={handleGenerateReport}
                resources={resources}
              />
            )}

            {activeTab === 'audit-logs' && (
              <AuditLogs />
            )}

            {activeTab === 'users' && (
              <UserManagement showToast={showToast} />
            )}
          </main>
        )}

        {/* Notification Toast */}
        {toast && (
          <div style={{
            position: 'fixed',
            bottom: '24px',
            right: '24px',
            background: toast.type === 'error' ? 'var(--danger-bg)' : toast.type === 'info' ? 'var(--bg-subtle)' : 'var(--success-bg)',
            border: `1px solid ${toast.type === 'error' ? 'var(--danger-border)' : toast.type === 'info' ? 'var(--border-medium)' : 'var(--success-border)'}`,
            borderRadius: 'var(--radius-md)',
            padding: '0.85rem 1.25rem',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem',
            boxShadow: 'var(--shadow-lg)',
            zIndex: 2000,
            fontSize: '0.88rem',
            fontWeight: 500,
            animation: 'slideUp 0.2s ease-out'
          }}>
            {toast.type === 'error' ? (
              <AlertCircle size={18} color="var(--danger)" />
            ) : (
              <CheckCircle2 size={18} color="var(--success)" />
            )}
            <span>{toast.message}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  const getActiveTab = () => {
    const p = location.pathname.replace(/^\//, '').toLowerCase();
    if (['resources', 'alerts', 'predictions', 'agent', 'reports', 'audit-logs', 'users'].includes(p)) {
      return p;
    }
    return 'dashboard';
  };

  const [activeTab, setActiveTab] = useState(getActiveTab);

  useEffect(() => {
    setActiveTab(getActiveTab());
  }, [location.pathname]);

  if (isLoading) {
    return (
      <div style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg-main)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '1rem',
        color: 'var(--text-secondary)'
      }}>
        <RefreshCw size={36} className="spin-animation" color="var(--primary-light)" />
        <div style={{ fontSize: '0.95rem', fontWeight: 600 }}>Checking session status...</div>
      </div>
    );
  }

  return (
    <Routes>
      {/* 1. Public Auth Routes (Redirect to /dashboard if already authenticated) */}
      <Route 
        path="/login" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} 
      />
      <Route 
        path="/signup" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <SignUp />} 
      />
      <Route 
        path="/forgot-password" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <ForgotPassword />} 
      />
      <Route 
        path="/reset-password/:uid/:token" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <ResetPassword />} 
      />
      <Route 
        path="/reset-password" 
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <ResetPassword />} 
      />

      {/* 2. Protected Dashboard & Module Routes (Redirect to /login if unauthenticated) */}
      <Route 
        path="/dashboard" 
        element={isAuthenticated ? <DashboardLayout activeTab="dashboard" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/resources" 
        element={isAuthenticated ? <DashboardLayout activeTab="resources" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/alerts" 
        element={isAuthenticated ? <DashboardLayout activeTab="alerts" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/predictions" 
        element={isAuthenticated ? <DashboardLayout activeTab="predictions" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/agent" 
        element={isAuthenticated ? <DashboardLayout activeTab="agent" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/reports" 
        element={isAuthenticated ? <DashboardLayout activeTab="reports" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/audit-logs" 
        element={isAuthenticated ? <DashboardLayout activeTab="audit-logs" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />
      <Route 
        path="/users" 
        element={isAuthenticated ? <DashboardLayout activeTab="users" onTabChange={setActiveTab} /> : <Navigate to="/login" replace />} 
      />

      {/* 3. Root and Catch-All Fallbacks */}
      <Route 
        path="/" 
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
      />
      <Route 
        path="*" 
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} 
      />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
