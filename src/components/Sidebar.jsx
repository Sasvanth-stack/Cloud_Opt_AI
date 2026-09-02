import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  Server, 
  Bell, 
  TrendingUp, 
  Bot, 
  FileText, 
  Activity
} from 'lucide-react';

export default function Sidebar({ activeTab, onTabChange, alertsCount, pendingRecsCount }) {
  const { user, role } = useAuth();

  const allMenuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null, show: true },
    { id: 'resources', label: 'Cloud Resources', icon: Server, badge: null, show: true },
    { id: 'alerts', label: 'Alerts & Anomalies', icon: Bell, badge: alertsCount > 0 ? alertsCount : null, badgeColor: 'var(--danger)', show: true },
    { id: 'predictions', label: 'AI Predictions (ML)', icon: TrendingUp, badge: null, show: true },
    { id: 'agent', label: 'AI Agent & Optimization', icon: Bot, badge: pendingRecsCount > 0 ? pendingRecsCount : null, badgeColor: 'var(--primary-light)', show: true },
    { id: 'reports', label: 'Reports & Export', icon: FileText, badge: null, show: true },
  ];

  const visibleMenuItems = allMenuItems.filter(item => item.show);

  const getRoleColor = (r) => {
    const roleUpper = (r || '').toUpperCase();
    if (roleUpper === 'ADMIN') return '#38BDF8';
    if (roleUpper === 'DEVOPS_ENGINEER') return '#10B981';
    if (roleUpper === 'FINOPS_ANALYST') return '#F59E0B';
    if (roleUpper === 'SRE_OPERATIONS') return '#8B5CF6';
    return '#94A3B8';
  };

  return (
    <aside style={{
      width: '260px',
      backgroundColor: 'var(--bg-card)',
      borderRight: '1px solid var(--border-subtle)',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      padding: '1.5rem 1rem',
      flexShrink: 0
    }}>
      {/* Navigation List */}
      <div>
        <div style={{
          fontSize: '0.72rem',
          fontWeight: 700,
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.08em',
          padding: '0 0.75rem 0.75rem 0.75rem'
        }}>
          Operations & Intelligence
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
          {visibleMenuItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  width: '100%',
                  padding: '0.7rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'var(--bg-subtle)' : 'transparent',
                  color: isActive ? 'var(--text-main)' : 'var(--text-secondary)',
                  border: isActive ? '1px solid var(--border-medium)' : '1px solid transparent',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.88rem',
                  fontWeight: isActive ? 600 : 500,
                  transition: 'all 0.15s ease',
                  textAlign: 'left'
                }}
                onMouseEnter={e => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)';
                    e.currentTarget.style.color = 'var(--text-main)';
                  }
                }}
                onMouseLeave={e => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <Icon 
                    size={18} 
                    color={isActive ? 'var(--primary-light)' : 'var(--text-muted)'} 
                  />
                  <span>{item.label}</span>
                </div>

                {item.badge && (
                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    padding: '0.15rem 0.45rem',
                    borderRadius: '9999px',
                    backgroundColor: item.badgeColor ? `${item.badgeColor}25` : 'var(--bg-subtle)',
                    color: item.badgeColor || 'var(--text-main)',
                    border: item.badgeColor ? `1px solid ${item.badgeColor}40` : '1px solid var(--border-medium)'
                  }}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* System Status & Current User Session Footer */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        {/* User Role Card */}
        {user && (
          <div style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-medium)',
            borderRadius: 'var(--radius-md)',
            padding: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.65rem'
          }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '50%',
              backgroundColor: 'var(--bg-subtle)',
              border: `1px solid ${getRoleColor(role)}40`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: getRoleColor(role),
              fontWeight: 700,
              fontSize: '0.82rem'
            }}>
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#fff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user.username}
              </div>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: getRoleColor(role), textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                {role}
              </div>
            </div>
          </div>
        )}

        {/* System Orchestrator Card */}
        <div style={{
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)',
          padding: '0.8rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.4rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Activity size={14} color="var(--success)" />
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-main)' }}>
                CloudOpt AI Engine
              </span>
            </div>
            <span className="badge badge-normal" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
              Online
            </span>
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
            Multi-Cloud &bull; Random Forest &bull; PostgreSQL
          </div>
        </div>
      </div>
    </aside>
  );
}
