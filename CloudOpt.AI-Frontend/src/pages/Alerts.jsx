import React, { useState } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  CheckCircle2, 
  ShieldAlert, 
  DollarSign, 
  Zap, 
  Info, 
  Search, 
  Filter, 
  Check, 
  Clock,
  Eye,
  RotateCcw
} from 'lucide-react';

export default function Alerts({ 
  alerts = [], 
  onAcknowledgeAlert, 
  onResolveAlert,
  onResetAlerts 
}) {
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ACTIVE');
  const [searchTerm, setSearchTerm] = useState('');
  const [actionLoading, setActionLoading] = useState({});
  const [isResetting, setIsResetting] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  const handleAck = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'ack' }));
    try {
      await onAcknowledgeAlert(id);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  const handleRes = async (id) => {
    setActionLoading(prev => ({ ...prev, [id]: 'res' }));
    try {
      await onResolveAlert(id);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: null }));
    }
  };

  const handleConfirmReset = async () => {
    setShowConfirmModal(false);
    setIsResetting(true);
    try {
      if (onResetAlerts) {
        await onResetAlerts();
      }
      setStatusFilter('ACTIVE');
    } finally {
      setIsResetting(false);
    }
  };

  const activeAlerts = alerts.filter(a => a.status === 'active' || (!a.is_acknowledged && !a.is_resolved));
  const ackedAlerts = alerts.filter(a => a.status === 'acknowledged' || (a.is_acknowledged && !a.is_resolved));
  const resolvedAlerts = alerts.filter(a => a.status === 'resolved' || a.is_resolved);

  const filteredAlerts = alerts.filter(alert => {
    const term = searchTerm.toLowerCase();
    const matchesSearch = 
      (alert.resource_id && alert.resource_id.toLowerCase().includes(term)) ||
      (alert.alert_type && alert.alert_type.toLowerCase().includes(term)) ||
      (alert.message && alert.message.toLowerCase().includes(term));
    
    const matchesSeverity = severityFilter === 'ALL' || alert.severity === severityFilter;
    
    let matchesStatus = true;
    if (statusFilter === 'ACTIVE') {
      matchesStatus = alert.status === 'active' || (!alert.is_acknowledged && !alert.is_resolved);
    } else if (statusFilter === 'ACKNOWLEDGED') {
      matchesStatus = alert.status === 'acknowledged' || (alert.is_acknowledged && !alert.is_resolved);
    } else if (statusFilter === 'RESOLVED') {
      matchesStatus = alert.status === 'resolved' || alert.is_resolved;
    }

    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const criticalCount = alerts.filter(a => a.severity === 'Critical' && (a.status === 'active' || !a.is_resolved)).length;
  const warningCount = alerts.filter(a => a.severity === 'Warning' && (a.status === 'active' || !a.is_resolved)).length;
  const costCount = alerts.filter(a => a.severity === 'Cost Alert' && (a.status === 'active' || !a.is_resolved)).length;
  const optCount = alerts.filter(a => a.severity === 'Optimization Alert' && (a.status === 'active' || !a.is_resolved)).length;

  const getSeverityIcon = (sev) => {
    switch (sev) {
      case 'Critical': return <ShieldAlert size={18} color="var(--danger)" />;
      case 'Warning': return <AlertTriangle size={18} color="var(--warning)" />;
      case 'Cost Alert': return <DollarSign size={18} color="var(--warning)" />;
      case 'Optimization Alert': return <Zap size={18} color="var(--accent-cyan)" />;
      default: return <Info size={18} color="var(--primary-light)" />;
    }
  };

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'Critical': return <span className="badge badge-critical">Critical</span>;
      case 'Warning': return <span className="badge badge-warning">Warning</span>;
      case 'Cost Alert': return <span className="badge badge-warning">Cost Alert</span>;
      case 'Optimization Alert': return <span className="badge badge-normal">Optimization</span>;
      default: return <span className="badge badge-idle">Info</span>;
    }
  };

  return (
    <div className="page-wrapper">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Alerts & Anomaly Center</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Live anomaly stream stored in PostgreSQL. Acknowledging or resolving alerts updates the database in real-time.
          </p>
        </div>
        <button
          onClick={() => setShowConfirmModal(true)}
          disabled={isResetting}
          className="btn btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', opacity: isResetting ? 0.7 : 1 }}
          title="Reset all alerts to the initial demo state in PostgreSQL"
        >
          <RotateCcw size={15} className={isResetting ? 'spin-animation' : ''} />
          <span>{isResetting ? 'Resetting...' : 'Reset Alerts'}</span>
        </button>
      </div>

      {/* Quick Summary Counts */}
      <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: '1.5rem' }}>
        <div className="glass-card" style={{ borderColor: criticalCount > 0 ? 'var(--danger-border)' : 'var(--border-subtle)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>CRITICAL ALERTS</span>
            <ShieldAlert size={18} color="var(--danger)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: criticalCount > 0 ? 'var(--danger)' : 'var(--text-main)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {criticalCount}
          </div>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>WARNING ALERTS</span>
            <AlertTriangle size={18} color="var(--warning)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--warning)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {warningCount}
          </div>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>COST ANOMALIES</span>
            <DollarSign size={18} color="var(--warning)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {costCount}
          </div>
        </div>

        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>OPTIMIZATION FLAGS</span>
            <Zap size={18} color="var(--accent-cyan)" />
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
            {optCount}
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1.3fr', gap: '1rem', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="Search alert by resource, type, or message..." 
              value={searchTerm} 
              onChange={e => setSearchTerm(e.target.value)} 
              className="form-input" 
              style={{ paddingLeft: '36px' }}
            />
          </div>

          {/* Severity Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Severity:</span>
            <select 
              value={severityFilter} 
              onChange={e => setSeverityFilter(e.target.value)} 
              className="form-select"
            >
              <option value="ALL">All Categories</option>
              <option value="Critical">Critical Only</option>
              <option value="Warning">Warning Only</option>
              <option value="Cost Alert">Cost Alerts Only</option>
              <option value="Optimization Alert">Optimization Alerts</option>
            </select>
          </div>

          {/* Status Filter Tabs */}
          <div style={{ display: 'flex', gap: '0.35rem' }}>
            <button 
              onClick={() => setStatusFilter('ACTIVE')} 
              className={`btn btn-sm ${statusFilter === 'ACTIVE' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.35rem' }}
            >
              <span>Active</span>
              <span className="badge" style={{ background: statusFilter === 'ACTIVE' ? 'rgba(255,255,255,0.2)' : 'var(--bg-subtle)', padding: '0.05rem 0.35rem', fontSize: '0.65rem' }}>
                {activeAlerts.length}
              </span>
            </button>
            <button 
              onClick={() => setStatusFilter('ACKNOWLEDGED')} 
              className={`btn btn-sm ${statusFilter === 'ACKNOWLEDGED' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.35rem' }}
            >
              <span>Ack'd</span>
              <span className="badge" style={{ background: statusFilter === 'ACKNOWLEDGED' ? 'rgba(255,255,255,0.2)' : 'var(--bg-subtle)', padding: '0.05rem 0.35rem', fontSize: '0.65rem' }}>
                {ackedAlerts.length}
              </span>
            </button>
            <button 
              onClick={() => setStatusFilter('RESOLVED')} 
              className={`btn btn-sm ${statusFilter === 'RESOLVED' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.35rem' }}
            >
              <span>Resolved</span>
              <span className="badge" style={{ background: statusFilter === 'RESOLVED' ? 'rgba(255,255,255,0.2)' : 'var(--bg-subtle)', padding: '0.05rem 0.35rem', fontSize: '0.65rem' }}>
                {resolvedAlerts.length}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Alerts Stream List */}
      {filteredAlerts.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-muted)' }}>
          <CheckCircle2 size={36} color="var(--success)" style={{ margin: '0 auto 0.75rem auto' }} />
          <h3>No Alerts in this View</h3>
          <p style={{ fontSize: '0.88rem' }}>No alerts matched your current status tab ({statusFilter}) and filters.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
          {filteredAlerts.map(alert => {
            const isResolved = alert.status === 'resolved' || alert.is_resolved;
            const isAcked = (alert.status === 'acknowledged' || alert.is_acknowledged) && !isResolved;
            const isAckLoading = actionLoading[alert.id] === 'ack';
            const isResLoading = actionLoading[alert.id] === 'res';

            return (
              <div 
                key={alert.id || alert.alert_id}
                className="glass-card"
                style={{
                  borderColor: alert.severity === 'Critical' && !isResolved ? 'var(--danger-border)' : 'var(--border-subtle)',
                  background: isResolved ? 'var(--bg-card)' : alert.severity === 'Critical' ? 'linear-gradient(180deg, rgba(239, 68, 68, 0.08) 0%, var(--bg-card) 100%)' : 'var(--bg-card)',
                  opacity: isResolved ? 0.65 : 1,
                  transition: 'all 0.2s ease'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem', flex: 1 }}>
                    <div style={{ padding: '0.45rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', marginTop: '2px' }}>
                      {getSeverityIcon(alert.severity)}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', flexWrap: 'wrap' }}>
                        <span className="badge" style={{ background: 'var(--bg-subtle)', color: 'var(--text-muted)', fontSize: '0.7rem', fontFamily: 'var(--font-mono)' }}>
                          {alert.alert_id || `ALT-00${alert.id}`}
                        </span>
                        {alert.resource_id && (
                          <span className="badge badge-provider">{alert.resource_id}</span>
                        )}
                        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}>
                          {alert.alert_type}
                        </span>
                        {getSeverityBadge(alert.severity)}
                        {isAcked && (
                          <span className="badge badge-idle" style={{ fontSize: '0.65rem', background: 'rgba(245, 158, 11, 0.15)', color: '#F59E0B' }}>
                            Acknowledged
                          </span>
                        )}
                        {isResolved && (
                          <span className="badge badge-normal" style={{ fontSize: '0.65rem', background: 'rgba(16, 185, 129, 0.15)', color: '#10B981' }}>
                            Resolved
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {alert.message}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                          <Clock size={12} />
                          <span>Triggered: {new Date(alert.created_at).toLocaleTimeString()}</span>
                        </div>
                        {alert.acknowledged_at && (
                          <div style={{ color: '#F59E0B' }}>
                            Ack'd: {new Date(alert.acknowledged_at).toLocaleTimeString()}
                          </div>
                        )}
                        {alert.resolved_at && (
                          <div style={{ color: '#10B981' }}>
                            Resolved: {new Date(alert.resolved_at).toLocaleTimeString()}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: 'flex', gap: '0.5rem', flexShrink: 0 }}>
                    {!isResolved && !isAcked && (
                      <button 
                        onClick={() => handleAck(alert.id)}
                        disabled={isAckLoading}
                        className="btn btn-secondary btn-sm"
                        title="Mark alert as acknowledged and move to Ack'd tab"
                      >
                        <Eye size={14} />
                        <span>{isAckLoading ? 'Saving...' : 'Acknowledge'}</span>
                      </button>
                    )}
                    {!isResolved && (
                      <button 
                        onClick={() => handleRes(alert.id)}
                        disabled={isResLoading}
                        className="btn btn-primary btn-sm"
                        title="Mark alert as resolved and save to PostgreSQL"
                      >
                        <Check size={14} />
                        <span>{isResLoading ? 'Saving...' : 'Resolve'}</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Confirmation Modal for Reset Alerts */}
      {showConfirmModal && (
        <div className="modal-backdrop" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" style={{ maxWidth: '460px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem' }}>
              <div style={{ padding: '0.5rem', background: 'rgba(56, 189, 248, 0.15)', borderRadius: 'var(--radius-md)' }}>
                <RotateCcw size={20} color="var(--primary-light)" />
              </div>
              <h3 style={{ fontSize: '1.15rem' }}>Reset Alerts to Demo State</h3>
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5, marginBottom: '1.25rem' }}>
              Reset all alerts to the initial demo state? This will set all 5 standard alerts back to <strong>Active</strong> in PostgreSQL and clear acknowledged/resolved timestamps.
            </p>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button 
                onClick={() => setShowConfirmModal(false)}
                className="btn btn-secondary btn-sm"
              >
                Cancel
              </button>
              <button 
                onClick={handleConfirmReset}
                className="btn btn-primary btn-sm"
              >
                Confirm Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
