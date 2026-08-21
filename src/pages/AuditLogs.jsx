import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { 
  FileCheck2, 
  Search, 
  Filter, 
  RefreshCw, 
  ShieldAlert, 
  ShieldCheck, 
  User, 
  Clock, 
  Server, 
  Bot, 
  Sparkles, 
  TrendingUp, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Lock,
  ArrowUpDown
} from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [resourceSearch, setResourceSearch] = useState('');
  const [limit, setLimit] = useState('100');

  const loadAuditLogs = async () => {
    setIsLoading(true);
    try {
      const data = await api.getAuditLogs({
        action: actionFilter || undefined,
        user: userSearch.trim() || undefined,
        resource: resourceSearch.trim() || undefined,
        limit: limit
      });
      setLogs(data || []);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [actionFilter, limit]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadAuditLogs();
  };

  const getActionBadge = (action) => {
    const act = (action || '').toUpperCase();
    if (act.includes('APPROVE') || act.includes('CREATE')) {
      return { color: 'var(--success)', bg: 'var(--success-bg)', border: 'var(--success-border)', icon: CheckCircle };
    }
    if (act.includes('DISMISS') || act.includes('DELETE')) {
      return { color: 'var(--danger)', bg: 'var(--danger-bg)', border: 'var(--danger-border)', icon: XCircle };
    }
    if (act.includes('PREDICTION') || act.includes('ML')) {
      return { color: '#06B6D4', bg: 'rgba(6, 182, 212, 0.12)', border: 'rgba(6, 182, 212, 0.3)', icon: TrendingUp };
    }
    if (act.includes('AI') || act.includes('OPTIMIZATION')) {
      return { color: 'var(--primary-light)', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.3)', icon: Sparkles };
    }
    if (act.includes('ALERT') || act.includes('RESOLVE') || act.includes('ACKNOWLEDGE')) {
      return { color: 'var(--warning)', bg: 'var(--warning-bg)', border: 'var(--warning-border)', icon: AlertTriangle };
    }
    if (act.includes('LOGIN') || act.includes('LOGOUT')) {
      return { color: '#818CF8', bg: 'rgba(129, 140, 248, 0.12)', border: 'rgba(129, 140, 248, 0.3)', icon: Lock };
    }
    return { color: 'var(--text-secondary)', bg: 'var(--bg-subtle)', border: 'var(--border-medium)', icon: FileCheck2 };
  };

  const getRoleBadge = (role) => {
    const r = (role || '').toUpperCase();
    if (r === 'ADMIN') return { color: '#38BDF8', bg: 'rgba(56, 189, 248, 0.12)' };
    if (r === 'DEVOPS_ENGINEER') return { color: '#10B981', bg: 'rgba(16, 185, 129, 0.12)' };
    if (r === 'FINOPS_ANALYST') return { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.12)' };
    if (r === 'SRE_OPERATIONS') return { color: '#8B5CF6', bg: 'rgba(139, 92, 246, 0.12)' };
    return { color: '#94A3B8', bg: 'rgba(148, 163, 184, 0.12)' };
  };

  return (
    <div style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff'
            }}>
              <FileCheck2 size={20} />
            </div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', color: '#fff' }}>
              Security & Operational Audit Logs
            </h1>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.35rem', marginBottom: 0 }}>
            Immutable, append-only PostgreSQL audit trail capturing user actions, RBAC roles, ML/AI executions, and resource modifications.
          </p>
        </div>

        <button 
          onClick={loadAuditLogs} 
          disabled={isLoading}
          className="btn btn-secondary btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}
        >
          <RefreshCw size={14} className={isLoading ? "spin-animation" : ""} />
          <span>Refresh Logs</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)',
        padding: '1rem 1.25rem',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center', flex: 1 }}>
          {/* Action Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
            <Filter size={15} color="var(--text-muted)" />
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              style={{
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-main)',
                padding: '0.45rem 0.75rem',
                fontSize: '0.85rem',
                outline: 'none',
                fontFamily: 'var(--font-sans)'
              }}
            >
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="APPROVE_RECOMMENDATION">APPROVE_RECOMMENDATION</option>
              <option value="DISMISS_RECOMMENDATION">DISMISS_RECOMMENDATION</option>
              <option value="RUN_ML_PREDICTION">RUN_ML_PREDICTION</option>
              <option value="RUN_AI_OPTIMIZATION">RUN_AI_OPTIMIZATION</option>
              <option value="CREATE_RESOURCE">CREATE_RESOURCE</option>
              <option value="UPDATE_RESOURCE">UPDATE_RESOURCE</option>
              <option value="DELETE_RESOURCE">DELETE_RESOURCE</option>
              <option value="ACKNOWLEDGE_ALERT">ACKNOWLEDGE_ALERT</option>
              <option value="RESOLVE_ALERT">RESOLVE_ALERT</option>
              <option value="RESET_ALERTS">RESET_ALERTS</option>
              <option value="EXPORT_REPORT">EXPORT_REPORT</option>
              <option value="CREATE_USER">CREATE_USER</option>
              <option value="UPDATE_USER">UPDATE_USER</option>
            </select>
          </div>

          {/* User Search */}
          <div style={{ position: 'relative' }}>
            <User size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              placeholder="Search user..."
              style={{
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-main)',
                padding: '0.45rem 0.75rem 0.45rem 2rem',
                fontSize: '0.85rem',
                width: '140px',
                outline: 'none',
                fontFamily: 'var(--font-sans)'
              }}
            />
          </div>

          {/* Resource Search */}
          <div style={{ position: 'relative' }}>
            <Server size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              value={resourceSearch}
              onChange={(e) => setResourceSearch(e.target.value)}
              placeholder="Resource ID (e.g. VM-001)..."
              style={{
                backgroundColor: 'var(--bg-subtle)',
                border: '1px solid var(--border-medium)',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-main)',
                padding: '0.45rem 0.75rem 0.45rem 2rem',
                fontSize: '0.85rem',
                width: '180px',
                outline: 'none',
                fontFamily: 'var(--font-sans)'
              }}
            />
          </div>

          <button type="submit" className="btn btn-primary btn-sm" style={{ padding: '0.45rem 0.85rem' }}>
            <Search size={14} /> Search
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span>Limit:</span>
          <select
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
            style={{
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-main)',
              padding: '0.25rem 0.5rem',
              fontSize: '0.8rem',
              outline: 'none'
            }}
          >
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
            <option value="250">250</option>
          </select>
          <span>records</span>
        </div>
      </div>

      {/* Audit Log Table */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-medium)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden'
      }}>
        {isLoading ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '4rem',
            gap: '1rem',
            color: 'var(--text-muted)'
          }}>
            <RefreshCw size={28} className="spin-animation" color="var(--primary-light)" />
            <span>Loading PostgreSQL audit trail...</span>
          </div>
        ) : logs.length === 0 ? (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '4rem',
            gap: '0.75rem',
            color: 'var(--text-muted)'
          }}>
            <ShieldCheck size={36} color="var(--primary-light)" />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>No Audit Logs Found</div>
            <div style={{ fontSize: '0.85rem' }}>No events matched your current search filters.</div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{
                  borderBottom: '1px solid var(--border-medium)',
                  backgroundColor: 'var(--bg-subtle)',
                  color: 'var(--text-muted)',
                  fontSize: '0.75rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em'
                }}>
                  <th style={{ padding: '0.85rem 1rem' }}>Timestamp</th>
                  <th style={{ padding: '0.85rem 1rem' }}>User</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Role</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Action</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Resource / Target</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Module</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Description</th>
                  <th style={{ padding: '0.85rem 1rem' }}>Client IP</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => {
                  const badge = getActionBadge(log.action);
                  const roleBadge = getRoleBadge(log.user_role);
                  const Icon = badge.icon;

                  return (
                    <tr 
                      key={log.id} 
                      style={{ 
                        borderBottom: '1px solid var(--border-subtle)',
                        transition: 'background-color 0.15s ease'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--bg-subtle)'}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                    >
                      {/* Timestamp */}
                      <td style={{ padding: '0.85rem 1rem', whiteSpace: 'nowrap', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)', fontSize: '0.78rem' }}>
                        {log.formatted_timestamp || log.timestamp}
                      </td>

                      {/* User */}
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: 'var(--text-main)' }}>
                        {log.username || 'System'}
                      </td>

                      {/* Role */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <span style={{
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.5rem',
                          borderRadius: '4px',
                          backgroundColor: roleBadge.bg,
                          color: roleBadge.color,
                          border: `1px solid ${roleBadge.color}30`
                        }}>
                          {log.user_role || 'UNKNOWN'}
                        </span>
                      </td>

                      {/* Action */}
                      <td style={{ padding: '0.85rem 1rem' }}>
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: 'var(--radius-sm)',
                          backgroundColor: badge.bg,
                          color: badge.color,
                          border: `1px solid ${badge.border}`
                        }}>
                          <Icon size={12} />
                          <span>{log.action}</span>
                        </div>
                      </td>

                      {/* Resource */}
                      <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: log.resource_id ? 'var(--primary-light)' : 'var(--text-muted)' }}>
                        {log.resource_id || '—'}
                      </td>

                      {/* Module */}
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-secondary)' }}>
                        {log.module}
                      </td>

                      {/* Description */}
                      <td style={{ padding: '0.85rem 1rem', color: 'var(--text-main)', maxWidth: '320px' }}>
                        {log.description}
                      </td>

                      {/* IP */}
                      <td style={{ padding: '0.85rem 1rem', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {log.ip_address || '127.0.0.1'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
