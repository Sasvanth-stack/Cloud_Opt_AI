import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Cloud, 
  Sparkles, 
  RefreshCw, 
  RotateCcw
} from 'lucide-react';

export default function Navbar({ 
  stats, 
  onRunOptimization, 
  onResetData, 
  onRefresh, 
  isOptimizing 
}) {
  const { user, permissions } = useAuth();

  const score = stats?.optimization_score ?? 72.5;
  const scoreColor = score >= 80 ? 'var(--success)' : score >= 60 ? 'var(--warning)' : 'var(--danger)';

  return (
    <header style={{
      height: '70px',
      backgroundColor: 'var(--bg-card)',
      borderBottom: '1px solid var(--border-subtle)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: 'var(--shadow-sm)'
    }}>
      {/* Brand & Live Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, #2563EB 0%, #06B6D4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            boxShadow: '0 0 15px rgba(56, 189, 248, 0.35)'
          }}>
            <Cloud size={22} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#fff' }}>
                CloudOpt<span style={{ color: 'var(--primary-light)' }}>.AI</span>
              </span>
              <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.12)', color: 'var(--primary-light)', border: '1px solid rgba(56, 189, 248, 0.3)', fontSize: '0.65rem', padding: '0.15rem 0.45rem' }}>
                PROD v2.4
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Intelligent Multi-Cloud FinOps & ML Scaling
            </div>
          </div>
        </div>
      </div>

      {/* Right Controls & User Session Info */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Optimization Score Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          background: 'var(--bg-subtle)',
          padding: '0.4rem 0.9rem',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-medium)'
        }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            Optimization Score
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ fontSize: '1.1rem', fontWeight: 800, color: scoreColor, fontFamily: 'var(--font-mono)' }}>
              {score}
            </span>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>/ 100</span>
          </div>
        </div>

        {/* Quick Refresh */}
        <button 
          onClick={onRefresh}
          className="btn btn-secondary btn-sm"
          title="Refresh Telemetry Data"
          style={{ padding: '0.5rem' }}
        >
          <RefreshCw size={15} />
        </button>

        {/* Seed Data Reset (Only if user has mutation permission) */}
        {permissions.canModifyResources && (
          <button 
            onClick={onResetData}
            className="btn btn-secondary btn-sm"
            title="Reset & Reseed Simulated Multi-Cloud Telemetry"
          >
            <RotateCcw size={14} />
            <span>Reset Data</span>
          </button>
        )}

        {/* Trigger AI Agent Optimization Cycle (ADMIN, DEVOPS, SRE only) */}
        {permissions.canRunOptimization && (
          <button 
            onClick={onRunOptimization}
            disabled={isOptimizing}
            className="btn btn-primary btn-sm"
            style={{
              opacity: isOptimizing ? 0.7 : 1,
              cursor: isOptimizing ? 'not-allowed' : 'pointer'
            }}
          >
            {isOptimizing ? (
              <>
                <RefreshCw size={14} className="spin-animation" />
                <span>Analyzing Fleet...</span>
              </>
            ) : (
              <>
                <Sparkles size={14} />
                <span>Run AI Agent</span>
              </>
            )}
          </button>
        )}

        {/* Vertical Divider */}
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--border-medium)', margin: '0 0.25rem' }} />

        {/* Live Database Status */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.45rem',
          background: 'var(--bg-subtle)',
          border: '1px solid var(--border-medium)',
          borderRadius: 'var(--radius-md)',
          padding: '0.4rem 0.7rem'
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: 'var(--success)',
            boxShadow: '0 0 8px rgba(16, 185, 129, 0.6)'
          }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#fff', lineHeight: 1.1 }}>
              PostgreSQL
            </span>
            <span style={{ fontSize: '0.62rem', fontWeight: 600, color: 'var(--primary-light)', letterSpacing: '0.02em' }}>
              Connected
            </span>
          </div>
        </div>

        {/* User Info */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-medium)',
              borderRadius: 'var(--radius-md)',
              padding: '0.35rem 0.75rem'
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #2563EB, #06B6D4)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: '0.75rem',
                fontWeight: 700
              }}>
                {(user.username || 'A')[0].toUpperCase()}
              </div>
              <span style={{ fontSize: '0.84rem', fontWeight: 600, color: '#fff' }}>
                {user.full_name || user.username}
              </span>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}
