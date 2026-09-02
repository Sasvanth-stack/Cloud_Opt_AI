import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar 
} from 'recharts';
import { 
  Server, 
  Cpu, 
  Layers, 
  TrendingDown, 
  Sparkles, 
  AlertTriangle, 
  CheckCircle2, 
  ArrowUpRight, 
  ChevronRight,
  ShieldCheck,
  Zap,
  Activity,
  Bot
} from 'lucide-react';

const COLORS = ['#2563EB', '#06B6D4', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899'];

export default function Dashboard({ 
  stats, 
  resources = [], 
  alerts = [], 
  recommendations = [], 
  onApplyRecommendation,
  onNavigate 
}) {
  const { permissions } = useAuth();
  const [selectedRec, setSelectedRec] = useState(null);

  const pendingRecs = recommendations.filter(r => (r.status || '').toLowerCase() === 'pending').slice(0, 3);
  const activeAlerts = alerts.filter(a => !a.is_resolved).slice(0, 4);

  const optScore = stats?.optimization_score ?? 76;
  const scoreColor = optScore >= 80 ? 'var(--success)' : optScore >= 60 ? 'var(--warning)' : 'var(--danger)';

  // Resource Type Breakdown Chart Data
  const typeData = stats?.type_breakdown || [
    { name: 'VM', value: resources.filter(r => r.resource_type === 'VM').length || 4 },
    { name: 'Database', value: resources.filter(r => r.resource_type === 'DATABASE').length || 2 },
    { name: 'Container', value: resources.filter(r => r.resource_type === 'CONTAINER').length || 2 },
    { name: 'Storage', value: resources.filter(r => r.resource_type === 'STORAGE').length || 1 },
    { name: 'Network', value: resources.filter(r => r.resource_type === 'NETWORK').length || 1 },
    { name: 'Serverless', value: resources.filter(r => r.resource_type === 'SERVERLESS').length || 1 },
  ].filter(t => t.value > 0);

  const trendData = stats?.trend_series || [];

  return (
    <div className="page-wrapper">
      {/* Page Header */}
      <div style={{ marginBottom: '2rem', display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Cloud Operations Dashboard</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Real-time PostgreSQL telemetry, Random Forest predictive modeling, and n8n autonomous AI Agent optimization.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            onClick={() => onNavigate('agent')} 
            className="btn btn-primary"
          >
            <Sparkles size={16} />
            <span>AI Optimization Center</span>
          </button>
        </div>
      </div>

      {/* Top Metric KPI Cards */}
      <div className="kpi-grid">
        {/* KPI 1: Cloud Assets */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>MONITORED ASSETS</span>
            <div style={{ padding: '0.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <Server size={18} color="var(--primary-light)" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>
            {resources.length || stats?.total_resources || 11}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.4rem', fontSize: '0.78rem' }}>
            <span style={{ color: 'var(--success)' }}>● {stats?.active_resources ?? 9} Active</span>
            <span style={{ color: 'var(--idle)' }}>● {stats?.idle_resources ?? 2} Idle</span>
          </div>
        </div>

        {/* KPI 2: Optimization Score */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>OPTIMIZATION SCORE</span>
            <div style={{ padding: '0.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <ShieldCheck size={18} color={scoreColor} />
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
            <span style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: scoreColor }}>
              {optScore}
            </span>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>/ 100</span>
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Based on current CPU/RAM utilization
          </div>
        </div>

        {/* KPI 3: Overloaded Resources */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>OVERLOADED ASSETS</span>
            <div style={{ padding: '0.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <AlertTriangle size={18} color="var(--danger)" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: stats?.overloaded_resources > 0 ? 'var(--danger)' : 'var(--text-main)' }}>
            {stats?.overloaded_resources ?? 3}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--danger)', marginTop: '0.4rem' }}>
            High priority scaling recommended
          </div>
        </div>

        {/* KPI 4: Pending AI Recommendations */}
        <div className="glass-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', fontWeight: 600 }}>AI RECOMMENDATIONS</span>
            <div style={{ padding: '0.35rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              <Bot size={18} color="var(--accent-cyan)" />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
            {recommendations.filter(r => (r.status || '').toLowerCase() === 'pending').length}
          </div>
          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.4rem' }}>
            Evaluated by Random Forest & n8n
          </div>
        </div>
      </div>

      {/* Main Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* Real-Time vs Forecast Telemetry Chart */}
        <div className="glass-card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Activity size={18} color="var(--primary-light)" />
                <span>Fleet Telemetry & Forecasts</span>
              </div>
              <div className="card-subtitle">
                Historical telemetry vs ML predictive workload modeling
              </div>
            </div>
            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#38BDF8' }}></span>
                <span>Actual CPU</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', background: '#8B5CF6' }}></span>
                <span>Actual RAM</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '2px', border: '1px dashed #06B6D4' }}></span>
                <span>ML Forecast</span>
              </div>
            </div>
          </div>

          <div style={{ height: '240px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#38BDF8" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.0}/>
                  </linearGradient>
                  <linearGradient id="predCpuGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} domain={[0, 100]} unit="%" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--bg-card)', 
                    borderColor: 'var(--border-medium)', 
                    borderRadius: 'var(--radius-md)', 
                    color: 'var(--text-main)',
                    fontSize: '0.8rem'
                  }} 
                />
                <Area type="monotone" dataKey="actual_cpu" stroke="#38BDF8" strokeWidth={2} fillOpacity={1} fill="url(#cpuGrad)" />
                <Area type="monotone" dataKey="actual_ram" stroke="#8B5CF6" strokeWidth={2} fillOpacity={1} fill="url(#ramGrad)" />
                <Area 
                  type="monotone" 
                  dataKey="predicted_cpu" 
                  stroke="#06B6D4" 
                  strokeWidth={2} 
                  strokeDasharray="4 4"
                  fillOpacity={1} 
                  fill="url(#predCpuGrad)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Resource Fleet Breakdown by Type */}
        <div className="glass-card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Layers size={18} color="var(--accent-cyan)" />
                <span>Fleet Distribution by Resource Type</span>
              </div>
              <div className="card-subtitle">
                Monitored assets stored in PostgreSQL
              </div>
            </div>
          </div>

          <div style={{ height: '180px', width: '100%' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={typeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {typeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => [`${value} Units`, 'Count']}
                  contentStyle={{ 
                    backgroundColor: 'var(--bg-card)', 
                    borderColor: 'var(--border-medium)', 
                    borderRadius: 'var(--radius-md)', 
                    color: 'var(--text-main)',
                    fontSize: '0.8rem'
                  }} 
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.75rem', marginTop: '0.5rem', borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
            {typeData.map((t, idx) => (
              <div key={t.name} style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: COLORS[idx % COLORS.length] }}></span>
                <span style={{ color: 'var(--text-secondary)' }}>{t.name}:</span>
                <span style={{ fontWeight: 700 }}>{t.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Lower Section: Urgent AI Recommendations & Live Alerts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: '1.5rem' }}>
        {/* Urgent AI Agent Recommendations */}
        <div className="glass-card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <Sparkles size={18} color="var(--primary-light)" />
                <span>Urgent AI Recommendations</span>
              </div>
              <div className="card-subtitle">
                Autonomous decision support requiring Cloud Administrator review
              </div>
            </div>
            <button 
              onClick={() => onNavigate('agent')} 
              className="btn btn-secondary btn-sm"
            >
              View All ({recommendations.filter(r => (r.status || '').toLowerCase() === 'pending').length})
              <ChevronRight size={14} />
            </button>
          </div>

          {pendingRecs.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              <CheckCircle2 size={32} color="var(--success)" style={{ margin: '0 auto 0.5rem auto' }} />
              <div>All recommendations applied! System is operating at peak efficiency.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              {pendingRecs.map(rec => (
                <div 
                  key={rec.id || rec.resource_id}
                  style={{
                    background: 'var(--bg-subtle)',
                    border: '1px solid var(--border-medium)',
                    borderRadius: 'var(--radius-md)',
                    padding: '1rem 1.15rem',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.65rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="badge" style={{ background: 'var(--bg-card)', color: 'var(--text-muted)', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                        {rec.resource_id}
                      </span>
                      <span style={{ fontWeight: 700, fontSize: '0.92rem', color: 'var(--text-main)' }}>
                        {rec.resource_name || `Resource ${rec.resource_id}`}
                      </span>
                      <span className={`badge ${rec.priority?.toUpperCase() === 'HIGH' ? 'badge-critical' : 'badge-warning'}`}>
                        {rec.priority?.toUpperCase() || 'MEDIUM'} Priority
                      </span>
                    </div>

                    <span className={`badge ${rec.prediction === 'scale_up' ? 'badge-critical' : 'badge-warning'}`} style={{ fontSize: '0.72rem', fontWeight: 800 }}>
                      {rec.prediction?.toUpperCase() || 'ACTION REQUIRED'}
                    </span>
                  </div>

                  <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                    <strong>Recommendation:</strong> {rec.recommended_action}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.25rem' }}>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Cost analysis available after optimization.
                    </span>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        onClick={() => setSelectedRec(rec)}
                        className="btn btn-secondary btn-sm"
                      >
                        Inspect Reasoning
                      </button>
                      {permissions.canApprove && (
                        <button 
                          onClick={() => onApplyRecommendation(rec.id)}
                          className="btn btn-primary btn-sm"
                        >
                          <CheckCircle2 size={13} />
                          <span>Approve Recommendation</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Live Alerts Feed */}
        <div className="glass-card">
          <div className="card-header">
            <div>
              <div className="card-title">
                <AlertTriangle size={18} color="var(--warning)" />
                <span>Active Cloud Alerts</span>
              </div>
              <div className="card-subtitle">
                Anomalies and telemetry threshold breaches in PostgreSQL
              </div>
            </div>
            <button 
              onClick={() => onNavigate('alerts')} 
              className="btn btn-secondary btn-sm"
            >
              Alerts Center
            </button>
          </div>

          {activeAlerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
              <CheckCircle2 size={32} color="var(--success)" style={{ margin: '0 auto 0.5rem auto' }} />
              <div>No active unresolved alerts.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {activeAlerts.map(alert => (
                <div 
                  key={alert.id}
                  style={{
                    background: alert.severity === 'Critical' ? 'var(--danger-bg)' : 'var(--bg-subtle)',
                    border: `1px solid ${alert.severity === 'Critical' ? 'var(--danger-border)' : 'var(--border-subtle)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: '0.75rem 0.9rem',
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '0.65rem'
                  }}
                >
                  <AlertTriangle 
                    size={16} 
                    color={alert.severity === 'Critical' ? 'var(--danger)' : 'var(--warning)'} 
                    style={{ flexShrink: 0, marginTop: '2px' }} 
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-main)' }}>
                        {alert.resource_id ? `${alert.resource_id} &bull; ` : ''}{alert.alert_type}
                      </span>
                      <span className={`badge ${alert.severity === 'Critical' ? 'badge-critical' : 'badge-warning'}`} style={{ fontSize: '0.65rem' }}>
                        {alert.severity}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                      {alert.message}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Inspect AI Reasoning Modal */}
      {selectedRec && (
        <div className="modal-backdrop" onClick={() => setSelectedRec(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <div className="badge" style={{ background: 'var(--bg-subtle)', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  {selectedRec.resource_id}
                </div>
                <h2>AI Agent Recommendation Details</h2>
              </div>
              <button 
                onClick={() => setSelectedRec(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginBottom: '1.5rem' }}>
              <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>AI RECOMMENDATION</div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', marginTop: '0.25rem', fontWeight: 600 }}>
                  {selectedRec.recommended_action}
                </div>
              </div>

              <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>AI RATIONALE</div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.6 }}>
                  {selectedRec.reason}
                </div>
              </div>

              {selectedRec.risk && (
                <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--danger)', fontWeight: 700 }}>RISK</div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.6 }}>
                    {selectedRec.risk}
                  </div>
                </div>
              )}

              {selectedRec.what_if && (
                <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--accent-cyan)', fontWeight: 700 }}>WHAT-IF</div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.25rem', lineHeight: 1.6 }}>
                    {selectedRec.what_if}
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button 
                onClick={() => setSelectedRec(null)} 
                className="btn btn-secondary"
              >
                Close
              </button>
              <button 
                onClick={() => {
                  onApplyRecommendation(selectedRec.id);
                  setSelectedRec(null);
                }} 
                className="btn btn-primary"
              >
                <CheckCircle2 size={16} />
                <span>Approve Recommendation</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
