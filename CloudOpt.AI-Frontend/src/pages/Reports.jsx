import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Download, 
  TrendingUp, 
  DollarSign, 
  Cpu, 
  CheckCircle2, 
  Sparkles, 
  Plus,
  RefreshCw,
  AlertTriangle,
  Bot,
  BrainCircuit,
  Bell,
  Activity,
  Calendar,
  Layers
} from 'lucide-react';
import api from '../services/api';
import { generateReportPDF } from '../utils/reportPdf';

export default function Reports({ reports = [], onGenerateReport, resources = [] }) {
  const [selectedReportType, setSelectedReportType] = useState('Monthly');
  const [isGenerating, setIsGenerating] = useState(false);
  const [pdfGenerating, setPdfGenerating] = useState(false);
  const [reportData, setReportData] = useState(reports[0] || null);
  const [error, setError] = useState(null);

  const fetchLiveReport = async (type = selectedReportType) => {
    setIsGenerating(true);
    setError(null);
    try {
      const data = await api.getReportSummary(type);
      setReportData(data);
    } catch (err) {
      console.error('Report fetch error:', err);
      setError('Unable to load live report data. Check Django + PostgreSQL connection.');
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    fetchLiveReport(selectedReportType);
  }, [selectedReportType]);

  const handleGenerate = async () => {
    await fetchLiveReport(selectedReportType);
    if (onGenerateReport) {
      await onGenerateReport(selectedReportType);
    }
  };

  const handleExportPdf = () => {
    if (!activeReport) {
      setError('Unable to generate report. Load the report data first.');
      return;
    }
    setPdfGenerating(true);
    try {
      generateReportPDF(activeReport);
    } catch (err) {
      console.error('PDF generation failed:', err);
      setError('Unable to generate report. Load the report data first.');
    } finally {
      setPdfGenerating(false);
    }
  };

  const activeReport = reportData || reports[0] || {
    report_id: `REP-2026-${selectedReportType.toUpperCase()}-0819`,
    report_type: selectedReportType,
    period_start: new Date(Date.now() - 30 * 86400000).toISOString(),
    period_end: new Date().toISOString(),
    formatted_period: 'Period loading...',
    generated_at: new Date().toLocaleString(),
    total_cloud_spend: 'Data unavailable',
    total_cost: 'Data unavailable',
    realized_savings: 0.0,
    total_savings: 0.0,
    average_cpu: 0.0,
    average_memory: 0.0,
    average_storage: 0.0,
    peak_cpu: 0.0,
    peak_ram: 0.0,
    peak_storage: 0.0,
    telemetry_count: resources.length,
    optimization_score: 80,
    active_resources_count: resources.length,
    optimizations_applied: 0,
    recommendations: { total: 0, pending: 0, approved: 0, dismissed: 0 },
    alerts: { active: 0, acknowledged: 0, resolved: 0, critical: 0 },
    ml_predictions: { scale_up: 0, scale_down: 0, no_action: 0, total: 0 },
    has_trend_data: false,
    trend_message: 'Insufficient historical telemetry for trend analysis.',
    trends: [],
    summary_text: 'Loading live timestamped FinOps metrics from PostgreSQL database.',
    created_at: new Date().toISOString(),
    resources: []
  };

  const reportResources = (activeReport.resources && activeReport.resources.length > 0) 
    ? activeReport.resources 
    : resources;

  const handleExportCsv = () => {
    const rows = [
      ['CloudOpt.AI - Multi-Cloud Resource Optimization Audit Report', `Type: ${activeReport.report_type}`],
      ['Report ID', activeReport.report_id, 'Generated At', activeReport.generated_at || new Date(activeReport.created_at).toLocaleString()],
      ['Reporting Period', activeReport.formatted_period || `${activeReport.period_start} to ${activeReport.period_end}`],
      ['Total Monitored Resources', reportResources.length],
      ['System Optimization Score', `${activeReport.optimization_score}/100`],
      ['Total Cloud Spend', activeReport.total_cloud_spend || 'Data unavailable'],
      ['Realized FinOps Savings', `$${typeof activeReport.realized_savings === 'number' ? activeReport.realized_savings.toFixed(2) : '0.00'}`],
      ['Average Fleet CPU (%)', `${activeReport.average_cpu}%`, 'Average Fleet RAM (%)', `${activeReport.average_memory}%`],
      ['Peak Fleet CPU (%)', `${activeReport.peak_cpu || activeReport.average_cpu}%`, 'Peak Fleet RAM (%)', `${activeReport.peak_ram || activeReport.average_memory}%`],
      ['Optimizations Applied', activeReport.optimizations_applied],
      [],
      ['Resource ID', 'Name', 'Resource Type', 'CPU %', 'RAM %', 'Storage %', 'Status', 'Risk Level', 'ML Prediction', 'AI Recommendation Status']
    ];

    reportResources.forEach(r => {
      rows.push([
        r.resource_id,
        r.name || r.resource_name,
        r.resource_type,
        `${r.cpu_usage}%`,
        `${r.memory_usage}%`,
        `${r.storage_usage || 0}%`,
        r.status,
        r.risk_level,
        r.prediction || 'no_action',
        r.recommendation_status || 'none'
      ]);
    });

    const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.join(',')).join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `CloudOpt_AI_${activeReport.report_type}_Report.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const optScore = activeReport.optimization_score ?? 76;
  const scoreColor = optScore >= 80 ? 'var(--success)' : optScore >= 60 ? 'var(--warning)' : 'var(--danger)';

  return (
    <div className="page-wrapper">
      {/* Header & Controls */}
      <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>FinOps & Optimization Reports</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Auditable timestamp-filtered cloud usage summaries, realized FinOps cost savings, and executive resource reports.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={() => fetchLiveReport(selectedReportType)} disabled={isGenerating} className="btn btn-secondary">
            <RefreshCw size={16} className={isGenerating ? 'spin-animation' : ''} />
            <span>Refresh Report</span>
          </button>
          <button onClick={handleExportCsv} className="btn btn-secondary">
            <Download size={16} />
            <span>Export CSV</span>
          </button>
          <button onClick={handleExportPdf} disabled={pdfGenerating || isGenerating} className="btn btn-primary">
            <FileText size={16} />
            <span>{pdfGenerating ? 'Generating PDF...' : 'Export PDF'}</span>
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="no-print" style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', borderRadius: 'var(--radius-md)', color: '#FCA5A5', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1.25rem' }}>
          <AlertTriangle size={18} color="#EF4444" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Generator Controls (hidden on print) */}
      <div className="glass-card no-print" style={{ marginBottom: '1.5rem', padding: '1.15rem 1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              REPORT TIMEFRAME:
            </span>
            <div style={{ display: 'flex', gap: '0.4rem' }}>
              {['Daily', 'Weekly', 'Monthly'].map(type => (
                <button
                  key={type}
                  onClick={() => setSelectedReportType(type)}
                  className={`btn btn-sm ${selectedReportType === type ? 'btn-primary' : 'btn-secondary'}`}
                >
                  {type} Report
                </button>
              ))}
            </div>
          </div>

          <button 
            onClick={handleGenerate} 
            disabled={isGenerating} 
            className="btn btn-primary"
            style={{ opacity: isGenerating ? 0.7 : 1 }}
          >
            <Plus size={15} />
            <span>{isGenerating ? 'Compiling Metrics...' : `Generate ${selectedReportType} Report`}</span>
          </button>
        </div>
      </div>

      {/* Printable Report Document Card */}
      <div className="glass-card" style={{ padding: '2rem' }}>
        {/* Document Header */}
        <div style={{ borderBottom: '2px solid var(--border-medium)', paddingBottom: '1.5rem', marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
              <span className="badge badge-normal" style={{ fontSize: '0.75rem', fontWeight: 800 }}>
                {activeReport.report_type.toUpperCase()} FINOPS REPORT
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary-light)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                ID: {activeReport.report_id}
              </span>
            </div>
            <h2 style={{ fontSize: '1.6rem' }}>Multi-Cloud Resource Optimization Executive Summary</h2>
            <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.45rem' }}>
              <div>
                Reporting Period: <strong style={{ color: 'var(--text-main)' }}>{activeReport.formatted_period || `${activeReport.period_start} → ${activeReport.period_end}`}</strong>
              </div>
              <div>
                Generated At: <strong style={{ color: 'var(--text-main)' }}>{activeReport.generated_at || new Date(activeReport.created_at).toLocaleString()}</strong>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>SYSTEM OPTIMIZATION SCORE</div>
            <div style={{ fontSize: '2rem', fontWeight: 900, color: scoreColor, fontFamily: 'var(--font-mono)' }}>
              {activeReport.optimization_score} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>/ 100</span>
            </div>
          </div>
        </div>

        {/* High-Level Executive Summary Narrative */}
        <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '0.35rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Sparkles size={15} />
            <span>EXECUTIVE ANALYSIS & HIGHLIGHTS ({selectedReportType.toUpperCase()} TIMEFRAME)</span>
          </div>
          <div style={{ fontSize: '0.92rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
            {activeReport.summary_text}
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.75rem' }}>
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>TOTAL CLOUD SPEND</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
              {activeReport.total_cloud_spend || 'Data unavailable'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              PostgreSQL telemetry
            </div>
          </div>

          <div style={{ background: 'var(--success-bg)', border: '1px solid var(--success-border)', padding: '1rem', borderRadius: 'var(--radius-md)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--success)', fontWeight: 700 }}>REALIZED SAVINGS</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
              +${typeof activeReport.realized_savings === 'number' ? activeReport.realized_savings.toFixed(2) : '0.00'}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              From {activeReport.optimizations_applied} approved action(s)
            </div>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>
              {selectedReportType === 'Daily' ? 'PEAK FLEET CPU / RAM' : 'AVG FLEET CPU / RAM'}
            </div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
              {selectedReportType === 'Daily' 
                ? `${activeReport.peak_cpu || activeReport.average_cpu}% / ${activeReport.peak_ram || activeReport.average_memory}%` 
                : `${activeReport.average_cpu}% / ${activeReport.average_memory}%`}
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              {selectedReportType === 'Daily' ? `Avg: ${activeReport.average_cpu}% / ${activeReport.average_memory}%` : `Storage Avg: ${activeReport.average_storage}%`}
            </div>
          </div>

          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>OPTIMIZATIONS APPLIED</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--primary-light)', fontFamily: 'var(--font-mono)', marginTop: '0.2rem' }}>
              {activeReport.optimizations_applied} Actions
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Approved in {selectedReportType.toLowerCase()} period
            </div>
          </div>
        </div>

        {/* Intelligence Summaries Row: ML + AI Agent + Alerts */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
          {/* ML Optimization Summary */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.65rem' }}>
              <BrainCircuit size={15} />
              <span>ML PREDICTIONS SUMMARY ({selectedReportType.toUpperCase()})</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Scale Up:</span>
              <span className="badge badge-critical" style={{ fontSize: '0.72rem' }}>{activeReport.ml_predictions?.scale_up ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Scale Down:</span>
              <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>{activeReport.ml_predictions?.scale_down ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>No Action:</span>
              <span className="badge badge-normal" style={{ fontSize: '0.72rem' }}>{activeReport.ml_predictions?.no_action ?? 0}</span>
            </div>
          </div>

          {/* AI Agent Recommendations Summary */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 700, color: 'var(--primary-light)', marginBottom: '0.65rem' }}>
              <Bot size={15} />
              <span>AI AGENT RECOMMENDATIONS ({selectedReportType.toUpperCase()})</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Pending Review:</span>
              <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>{activeReport.recommendations?.pending ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Approved:</span>
              <span className="badge badge-success" style={{ fontSize: '0.72rem' }}>{activeReport.recommendations?.approved ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Dismissed:</span>
              <span className="badge" style={{ background: 'var(--bg-card)', color: 'var(--text-muted)', fontSize: '0.72rem' }}>{activeReport.recommendations?.dismissed ?? 0}</span>
            </div>
          </div>

          {/* Infrastructure Alerts Summary */}
          <div style={{ background: 'var(--bg-subtle)', padding: '1rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.78rem', fontWeight: 700, color: 'var(--warning)', marginBottom: '0.65rem' }}>
              <Bell size={15} />
              <span>INFRASTRUCTURE ALERTS ({selectedReportType.toUpperCase()})</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Active Alerts:</span>
              <span className="badge badge-warning" style={{ fontSize: '0.72rem' }}>{activeReport.alerts?.active ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Critical Alerts:</span>
              <span className="badge badge-critical" style={{ fontSize: '0.72rem' }}>{activeReport.alerts?.critical ?? 0}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', padding: '0.25rem 0' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Resolved:</span>
              <span className="badge badge-normal" style={{ fontSize: '0.72rem' }}>{activeReport.alerts?.resolved ?? 0}</span>
            </div>
          </div>
        </div>

        {/* Telemetry Trends Section (Requirement 14) */}
        <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '1.25rem', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.75rem' }}>
            <Activity size={16} color="var(--primary-light)" />
            <span>TELEMETRY TREND ANALYSIS ({selectedReportType.toUpperCase()} PERIOD)</span>
          </div>
          {activeReport.has_trend_data && activeReport.trends && activeReport.trends.length > 0 ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="custom-table" style={{ fontSize: '0.8rem' }}>
                <thead>
                  <tr>
                    <th>Interval</th>
                    <th>Avg CPU (%)</th>
                    <th>Avg RAM (%)</th>
                    <th>Recorded Alerts</th>
                  </tr>
                </thead>
                <tbody>
                  {activeReport.trends.map((t, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{t.label}</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{t.avg_cpu}%</td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{t.avg_ram}%</td>
                      <td>
                        <span className={`badge ${t.alerts > 0 ? 'badge-warning' : 'badge-normal'}`}>
                          {t.alerts} Alert(s)
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '0.5rem 0' }}>
              {activeReport.trend_message || 'Insufficient historical telemetry for trend analysis.'}
            </div>
          )}
        </div>

        {/* Detailed Monitored Fleet Breakdown Table */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.1rem', marginBottom: '0.85rem' }}>
            Monitored Fleet Breakdown ({reportResources.length} Assets &bull; {selectedReportType} Telemetry)
          </h3>
          <table className="custom-table">
            <thead>
              <tr>
                <th>Resource ID</th>
                <th>Name & Resource Type</th>
                <th>CPU %</th>
                <th>RAM %</th>
                <th>Storage %</th>
                <th>Status</th>
                <th>Risk Level</th>
                <th>ML Prediction</th>
                <th>Action Status</th>
              </tr>
            </thead>
            <tbody>
              {reportResources.map(res => (
                <tr key={res.id || res.resource_id}>
                  <td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{res.resource_id}</td>
                  <td>{res.name || res.resource_name} ({res.resource_type || 'VM'})</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{res.cpu_usage}%</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{res.memory_usage}%</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>{res.storage_usage || 0}%</td>
                  <td>
                    <span className={`badge ${res.status === 'Critical' ? 'badge-critical' : res.status === 'Warning' ? 'badge-warning' : 'badge-normal'}`}>
                      {res.status}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${res.risk_level === 'High' ? 'badge-critical' : res.risk_level === 'Medium' ? 'badge-warning' : 'badge-normal'}`}>
                      {res.risk_level}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${(res.prediction || '').toLowerCase() === 'scale_up' ? 'badge-critical' : (res.prediction || '').toLowerCase() === 'scale_down' ? 'badge-warning' : 'badge-normal'}`} style={{ fontSize: '0.7rem', fontWeight: 800 }}>
                      {(res.prediction || 'no_action').replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td>
                    {(res.recommendation_status || '').toLowerCase() === 'approved' ? (
                      <span className="badge badge-success" style={{ fontSize: '0.7rem', fontWeight: 800 }}>APPROVED</span>
                    ) : (res.recommendation_status || '').toLowerCase() === 'dismissed' ? (
                      <span className="badge" style={{ background: 'var(--bg-card)', color: 'var(--text-muted)', fontSize: '0.7rem' }}>DISMISSED</span>
                    ) : (res.recommendation_status || '').toLowerCase() === 'pending' ? (
                      <span className="badge badge-warning" style={{ fontSize: '0.7rem' }}>PENDING</span>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>&mdash;</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Signature / Audit Footer */}
        <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '1.25rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <div>Generated by CloudOpt AI Engine &bull; System Timestamp: {new Date(activeReport.created_at).toLocaleString()}</div>
          <div>Authorized Cloud Administrator: Admin &bull; Status: VERIFIED AUDIT</div>
        </div>
      </div>
    </div>
  );
}
