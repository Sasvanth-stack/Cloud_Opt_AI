import React, { useState, useEffect } from 'react';
import { 
  Bot, 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  Download, 
  Workflow, 
  ShieldAlert, 
  Zap, 
  Activity, 
  AlertTriangle, 
  Check, 
  RefreshCw,
  Server,
  HelpCircle,
  Clock,
  Layers,
  X,
  Lock
} from 'lucide-react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function AIAgentOptimization({ 
  resources = [],
  recommendations = [], 
  onApplyRecommendation, 
  onRejectRecommendation,
  onRunOptimization,
  isOptimizing 
}) {
  const { role, permissions } = useAuth();
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [showN8nModal, setShowN8nModal] = useState(false);
  const [dismissModalRec, setDismissModalRec] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  // Single-Resource Interactive Optimization State
  const defaultResourceId = resources.find(r => r.resource_id === 'VM-010')?.id || resources[0]?.id || '';
  const [selectedResourceId, setSelectedResourceId] = useState(defaultResourceId);
  const [isAnalyzingResource, setIsAnalyzingResource] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [optimizationError, setOptimizationError] = useState(null);

  // Auto-update selected resource if list loads dynamically
  useEffect(() => {
    if (!selectedResourceId && resources.length > 0) {
      const vm10 = resources.find(r => r.resource_id === 'VM-010');
      setSelectedResourceId(vm10 ? vm10.id : resources[0].id);
    }
  }, [resources, selectedResourceId]);

  const handleRunSingleOptimization = async () => {
    if (!selectedResourceId) return;
    setIsAnalyzingResource(true);
    setOptimizationError(null);
    try {
      const result = await api.optimizeResource(selectedResourceId);
      setOptimizationResult(result);
      // Trigger parent fleet sync so recommendations stay fresh
      if (onRunOptimization) {
        await onRunOptimization();
      }
    } catch (err) {
      console.error(err);
      setOptimizationError('Unable to run AI optimization. Check Django/n8n connection.');
    } finally {
      setIsAnalyzingResource(false);
    }
  };

  const handleApprove = async (recId) => {
    setActionLoadingId(recId);
    try {
      await onApplyRecommendation(recId);
    } catch (err) {
      console.error('Approve failed in UI:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleConfirmDismiss = async () => {
    if (!dismissModalRec) return;
    const recId = dismissModalRec.id;
    setActionLoadingId(recId);
    try {
      await onRejectRecommendation(recId);
      setDismissModalRec(null);
    } catch (err) {
      console.error('Dismiss failed in UI:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const formatPredictionText = (pred) => {
    if (!pred) return 'NO ACTION';
    switch (pred.toLowerCase()) {
      case 'scale_up': return 'SCALE UP';
      case 'scale_down': return 'SCALE DOWN';
      case 'no_action': return 'NO ACTION';
      default: return pred.toUpperCase();
    }
  };

  const getPredictionBadgeClass = (pred) => {
    switch (pred?.toLowerCase()) {
      case 'scale_up': return 'badge-critical';
      case 'scale_down': return 'badge-warning';
      default: return 'badge-normal';
    }
  };

  const getPriorityBadgeClass = (prio) => {
    switch (prio?.toUpperCase()) {
      case 'HIGH': return 'badge-critical';
      case 'MEDIUM': return 'badge-warning';
      default: return 'badge-normal';
    }
  };

  // Database-driven status counts calculated dynamically from PostgreSQL recommendations state
  const totalCount = recommendations.length;
  const pendingCount = recommendations.filter(r => (r.status || '').toLowerCase() === 'pending').length;
  const approvedCount = recommendations.filter(r => (r.status || '').toLowerCase() === 'approved').length;
  const dismissedCount = recommendations.filter(r => (r.status || '').toLowerCase() === 'dismissed').length;

  const filteredRecs = recommendations.filter(r => {
    const st = (r.status || '').toLowerCase();
    if (filterStatus === 'ALL') return true;
    if (filterStatus === 'pending') return st === 'pending';
    if (filterStatus === 'approved') return st === 'approved';
    if (filterStatus === 'dismissed') return st === 'dismissed';
    return true;
  });

  const downloadN8nJson = () => {
    const jsonWorkflow = {
      name: "Cloud Resource Optimization - AI Agent Workflow",
      nodes: [
        {
          name: "Webhook Receiver",
          type: "n8n-nodes-base.webhook",
          position: [240, 300],
          parameters: { httpMethod: "POST", path: "cloud-optimization" }
        },
        {
          name: "Extract Telemetry & Predictions",
          type: "n8n-nodes-base.set",
          position: [460, 300],
          parameters: {
            values: {
              string: [
                { name: "resource_id", value: "={{ $json.body.resource_id }}" },
                { name: "prediction", value: "={{ $json.body.prediction }}" },
                { name: "confidence", value: "={{ $json.body.confidence }}" }
              ]
            }
          }
        },
        {
          name: "AI Agent Reasoning & LLM Decision",
          type: "@n8n/n8n-nodes-langchain.agent",
          position: [680, 300],
          parameters: {
            prompt: "Analyze resource metrics and Scikit-Learn predictions. Output structured recommendation with action, priority, reason, risk, and what-if projection."
          }
        },
        {
          name: "Save Recommendation to Django API",
          type: "n8n-nodes-base.httpRequest",
          position: [920, 300],
          parameters: { method: "POST", url: "http://localhost:8000/api/resources/" }
        }
      ]
    };
    const blob = new Blob([JSON.stringify(jsonWorkflow, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'n8n_cloud_optimizer_workflow.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="page-wrapper">
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>AI Agent Decision & Optimization Center</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Autonomous agentic reasoning layer combining Django + PostgreSQL telemetry with Random Forest ML predictions and n8n AI Agent.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button 
            onClick={() => setShowN8nModal(true)} 
            className="btn btn-secondary"
          >
            <Workflow size={16} />
            <span>n8n Workflow Blueprint</span>
          </button>
          <button 
            onClick={onRunOptimization} 
            disabled={isOptimizing}
            className="btn btn-primary"
            style={{ opacity: isOptimizing ? 0.7 : 1 }}
          >
            <Sparkles size={16} />
            <span>{isOptimizing ? 'Agent Analyzing Fleet...' : 'Run AI Fleet Optimization'}</span>
          </button>
        </div>
      </div>

      {/* Interactive Single-Resource AI Optimization Engine (Real ML + n8n Live Workflow) */}
      <div className="glass-card" style={{ marginBottom: '1.75rem', borderColor: 'var(--primary-light)', background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(6, 182, 212, 0.05) 100%)' }}>
        <div className="card-header" style={{ marginBottom: '1.25rem' }}>
          <div className="card-title">
            <Bot size={20} color="var(--accent-cyan)" />
            <span>Live AI Resource Optimization Engine (ML + n8n Agent)</span>
          </div>
          <span className="badge badge-normal" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)', fontWeight: 700 }}>
            POST /api/resources/&lt;id&gt;/optimize/
          </span>
        </div>

        {/* Resource Selector Toolbar */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr auto', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem' }}>
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              SELECT CLOUD RESOURCE (POSTGRESQL):
            </label>
            <select
              value={selectedResourceId}
              onChange={(e) => setSelectedResourceId(e.target.value)}
              className="form-select"
              style={{ width: '100%', fontFamily: 'var(--font-mono)' }}
            >
              {resources.map(r => (
                <option key={r.id} value={r.id}>
                  {r.resource_id} &mdash; {r.name || r.resource_name} (CPU: {r.cpu_usage}%, RAM: {r.memory_usage}%, {r.resource_type || 'VM'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'block', marginBottom: '0.35rem' }}>
              TARGET ENDPOINT:
            </label>
            <div style={{ fontSize: '0.82rem', fontFamily: 'var(--font-mono)', color: 'var(--text-main)', padding: '0.55rem 0.75rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-medium)' }}>
              n8n: localhost:5678
            </div>
          </div>

          <div style={{ alignSelf: 'flex-end' }}>
            <button
              onClick={handleRunSingleOptimization}
              disabled={isAnalyzingResource || !selectedResourceId}
              className="btn btn-primary"
              style={{ padding: '0.6rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: isAnalyzingResource ? 0.7 : 1 }}
            >
              {isAnalyzingResource ? (
                <>
                  <RefreshCw size={16} className="spin-animation" />
                  <span>AI Agent analyzing resource...</span>
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  <span>Run AI Optimization</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Loading Banner */}
        {isAnalyzingResource && (
          <div style={{ padding: '1.75rem', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', textAlign: 'center', border: '1px dashed var(--primary-light)', marginBottom: '1rem' }}>
            <RefreshCw size={28} className="spin-animation" color="var(--primary-light)" style={{ margin: '0 auto 0.5rem auto' }} />
            <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-main)' }}>AI Agent analyzing resource...</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              PostgreSQL &rarr; Django &rarr; Random Forest ML &rarr; n8n Webhook &rarr; AI Agent &rarr; Django Response
            </div>
          </div>
        )}

        {/* Error Banner */}
        {optimizationError && (
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)', borderRadius: 'var(--radius-md)', color: '#FCA5A5', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '1rem' }}>
            <AlertTriangle size={18} color="#EF4444" />
            <span>{optimizationError}</span>
          </div>
        )}

        {/* AI Agent Result Display */}
        {optimizationResult && !isAnalyzingResource && (
          <div style={{ background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)', padding: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                <span className="badge badge-normal" style={{ fontSize: '0.85rem', fontWeight: 800, background: 'var(--bg-card)' }}>
                  {optimizationResult.resource_id}
                </span>
                <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  AI Optimization Analysis
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ML Prediction:</span>
                  <span className={`badge ${getPredictionBadgeClass(optimizationResult.prediction)}`} style={{ fontWeight: 800 }}>
                    {formatPredictionText(optimizationResult.prediction)}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Confidence:</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                    {(optimizationResult.confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Priority:</span>
                  <span className={`badge ${getPriorityBadgeClass(optimizationResult.ai_analysis?.priority)}`} style={{ fontWeight: 800 }}>
                    {optimizationResult.ai_analysis?.priority?.toUpperCase() || 'MEDIUM'}
                  </span>
                </div>
              </div>
            </div>

            {/* Analysis Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              {/* AI Recommendation */}
              <div style={{ background: 'var(--bg-card)', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', gridColumn: 'span 2' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--primary-light)', display: 'flex', alignItems: 'center', gap: '0.35rem', marginBottom: '0.35rem' }}>
                  <Sparkles size={14} /> AI RECOMMENDATION:
                </div>
                <div style={{ fontSize: '0.98rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  {optimizationResult.ai_analysis?.recommendation}
                </div>
              </div>

              {/* AI Rationale / Reason */}
              <div style={{ background: 'var(--bg-card)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                  AI RATIONALE:
                </div>
                <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
                  {optimizationResult.ai_analysis?.reason}
                </div>
              </div>

              {/* Risk */}
              <div style={{ background: 'var(--bg-card)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--danger)', marginBottom: '0.35rem' }}>
                  RISK:
                </div>
                <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
                  {optimizationResult.ai_analysis?.risk}
                </div>
              </div>

              {/* What-If Analysis */}
              <div style={{ background: 'var(--bg-card)', padding: '0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', gridColumn: 'span 2' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.35rem' }}>
                  WHAT-IF:
                </div>
                <div style={{ fontSize: '0.86rem', color: 'var(--text-secondary)', lineHeight: 1.55 }}>
                  {optimizationResult.ai_analysis?.what_if}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* n8n Agent End-to-End Workflow Pipeline Visualizer */}
      <div className="glass-card" style={{ marginBottom: '1.75rem', background: 'linear-gradient(135deg, rgba(17, 24, 39, 0.95) 0%, rgba(30, 41, 59, 0.6) 100%)' }}>
        <div className="card-header" style={{ marginBottom: '1rem' }}>
          <div className="card-title">
            <Bot size={18} color="var(--primary-light)" />
            <span>n8n Agentic Orchestration Pipeline</span>
          </div>
          <span className="badge badge-normal" style={{ fontSize: '0.7rem' }}>
            HUMAN-IN-THE-LOOP SAFETY ENABLED
          </span>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(5, 1fr)',
          gap: '0.75rem',
          position: 'relative'
        }}>
          {/* Step 1 */}
          <div style={{ background: 'var(--bg-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--primary-light)' }}>STEP 1</span>
              <span className="pulse-indicator" style={{ background: '#38BDF8' }}></span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Webhook Ingest</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Collects current CPU, RAM, storage, and network metrics.
            </div>
          </div>

          {/* Step 2 */}
          <div style={{ background: 'var(--bg-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>STEP 2</span>
              <span className="pulse-indicator" style={{ background: '#06B6D4' }}></span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>ML Prediction</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Reads Scikit-Learn Random Forest forecasts.
            </div>
          </div>

          {/* Step 3 */}
          <div style={{ background: 'var(--bg-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--accent-purple)' }}>STEP 3</span>
              <span className="pulse-indicator" style={{ background: '#8B5CF6' }}></span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Agent Reasoning</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              LLM evaluates risk, SLA degradation, & waste.
            </div>
          </div>

          {/* Step 4 */}
          <div style={{ background: 'var(--bg-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--success)' }}>STEP 4</span>
              <span className="pulse-indicator" style={{ background: '#10B981' }}></span>
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Impact Analysis</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Evaluates resource utilization and optimization impact.
            </div>
          </div>

          {/* Step 5 */}
          <div style={{ background: 'var(--bg-subtle)', padding: '0.9rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-medium)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--warning)' }}>STEP 5</span>
              <CheckCircle2 size={12} color="var(--warning)" />
            </div>
            <div style={{ fontWeight: 700, fontSize: '0.85rem' }}>Human Approval</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              User reviews and approves the AI recommendation.
            </div>
          </div>
        </div>
      </div>

      {/* Summary KPI & Database-Driven Filter Tabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            onClick={() => setFilterStatus('ALL')} 
            className={`btn btn-sm ${filterStatus === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
          >
            All Recommendations ({totalCount})
          </button>
          <button 
            onClick={() => setFilterStatus('pending')} 
            className={`btn btn-sm ${filterStatus === 'pending' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Pending Review ({pendingCount})
          </button>
          <button 
            onClick={() => setFilterStatus('approved')} 
            className={`btn btn-sm ${filterStatus === 'approved' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Applied ({approvedCount})
          </button>
          <button 
            onClick={() => setFilterStatus('dismissed')} 
            className={`btn btn-sm ${filterStatus === 'dismissed' ? 'btn-primary' : 'btn-secondary'}`}
          >
            Dismissed ({dismissedCount})
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
          <span>PostgreSQL Records:</span>
          <span style={{ fontWeight: 800, color: 'var(--primary-light)', fontFamily: 'var(--font-mono)' }}>
            {totalCount} Total
          </span>
        </div>
      </div>

      {/* Recommendations List */}
      {filteredRecs.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '3rem 1.5rem', color: 'var(--text-muted)' }}>
          <CheckCircle2 size={36} color="var(--success)" style={{ margin: '0 auto 0.75rem auto' }} />
          <h3 style={{ marginBottom: '0.35rem' }}>No recommendations in this filter.</h3>
          <p style={{ fontSize: '0.88rem' }}>Click "Run AI Optimization" above to analyze a resource or select another tab.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredRecs.map(rec => {
            const predText = formatPredictionText(rec.prediction);
            const isScaleUp = rec.prediction === 'scale_up';
            const isScaleDown = rec.prediction === 'scale_down';
            const recStatus = (rec.status || 'pending').toLowerCase();
            const isApproved = recStatus === 'approved';
            const isDismissed = recStatus === 'dismissed';
            const isPending = recStatus === 'pending';
            const isActionLoading = actionLoadingId === rec.id;

            return (
              <div 
                key={rec.id || rec.resource_id}
                className="glass-card"
                style={{
                  borderColor: isApproved ? 'var(--success-border)' : isDismissed ? 'var(--border-subtle)' : isScaleUp ? 'rgba(239, 68, 68, 0.35)' : isScaleDown ? 'rgba(245, 158, 11, 0.35)' : 'var(--border-medium)',
                  background: isApproved 
                    ? 'linear-gradient(180deg, rgba(16, 185, 129, 0.04) 0%, var(--bg-card) 100%)' 
                    : isDismissed 
                    ? 'linear-gradient(180deg, rgba(100, 116, 139, 0.04) 0%, var(--bg-card) 100%)' 
                    : 'var(--bg-card)',
                  opacity: isDismissed ? 0.75 : 1
                }}
              >
                {/* Card Header: Resource ID, Name, ML Prediction, Confidence, Priority, Status */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', flexWrap: 'wrap' }}>
                    <span className="badge" style={{ background: 'var(--bg-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 800 }}>
                      {rec.resource_id}
                    </span>
                    <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)' }}>
                      {rec.resource_name || `Resource ${rec.resource_id}`}
                    </span>

                    {/* ML Prediction Badge */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>ML:</span>
                      <span className={`badge ${getPredictionBadgeClass(rec.prediction)}`} style={{ fontWeight: 800 }}>
                        {predText}
                      </span>
                    </div>

                    {/* Confidence */}
                    {rec.confidence !== undefined && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Confidence:</span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                          {(rec.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    )}

                    {/* Priority Badge */}
                    <span className={`badge ${getPriorityBadgeClass(rec.priority)}`}>
                      {rec.priority?.toUpperCase() || 'MEDIUM'} PRIORITY
                    </span>

                    {/* Approval Lifecycle Status Badge */}
                    {isApproved ? (
                      <span className="badge badge-success" style={{ fontWeight: 800 }}>
                        <Check size={11} /> APPROVED
                      </span>
                    ) : isDismissed ? (
                      <span className="badge" style={{ background: 'var(--bg-subtle)', color: 'var(--text-muted)', border: '1px solid var(--border-medium)', fontWeight: 800 }}>
                        <X size={11} /> DISMISSED
                      </span>
                    ) : (
                      <span className="badge badge-warning" style={{ fontWeight: 800 }}>
                        <Clock size={11} /> PENDING REVIEW
                      </span>
                    )}
                  </div>
                </div>

                {/* AI Recommendation */}
                <div style={{ background: 'var(--bg-subtle)', padding: '0.85rem 1rem', borderRadius: 'var(--radius-md)', marginBottom: '0.85rem' }}>
                  <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.2rem' }}>
                    <span style={{ color: 'var(--primary-light)' }}>AI Recommendation:</span> {rec.recommendation || rec.recommended_action}
                  </div>
                </div>

                {/* AI Rationale, Risk & What-If Sections */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  {/* AI Rationale */}
                  <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem 0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', gridColumn: rec.what_if ? 'span 1' : 'span 2' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      AI RATIONALE:
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {rec.reason || 'Sustained metric utilization evaluated by AI Agent.'}
                    </div>
                  </div>

                  {/* Risk */}
                  <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem 0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', gridColumn: rec.what_if ? 'span 1' : 'span 2' }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--danger)', marginBottom: '0.25rem' }}>
                      RISK:
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                      {rec.risk || 'Workload stability monitored.'}
                    </div>
                  </div>

                  {/* What-If */}
                  {rec.what_if && (
                    <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem 0.9rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', gridColumn: 'span 2' }}>
                      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '0.25rem' }}>
                        WHAT-IF:
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                        {rec.what_if}
                      </div>
                    </div>
                  )}
                </div>

                {/* Footer: Accurate Cost Notice & Real Action Buttons */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderTop: '1px solid var(--border-subtle)',
                  paddingTop: '0.75rem'
                }}>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    Cost analysis available after optimization.
                  </div>

                  <div style={{ display: 'flex', gap: '0.65rem', alignItems: 'center' }}>
                    {isPending && (
                      permissions.canApprove ? (
                        <>
                          <button 
                            onClick={() => setDismissModalRec(rec)}
                            disabled={isActionLoading}
                            className="btn btn-secondary btn-sm"
                          >
                            <XCircle size={14} />
                            <span>Dismiss</span>
                          </button>
                          <button 
                            onClick={() => handleApprove(rec.id)}
                            disabled={isActionLoading}
                            className="btn btn-primary btn-sm"
                            style={{ opacity: isActionLoading ? 0.7 : 1 }}
                          >
                            {isActionLoading ? (
                              <>
                                <RefreshCw size={14} className="spin-animation" />
                                <span>Approving...</span>
                              </>
                            ) : (
                              <>
                                <CheckCircle2 size={14} />
                                <span>Approve Recommendation</span>
                              </>
                            )}
                          </button>
                        </>
                      ) : (
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.35rem',
                          fontSize: '0.75rem',
                          color: 'var(--text-muted)',
                          padding: '0.3rem 0.6rem',
                          background: 'var(--bg-subtle)',
                          borderRadius: 'var(--radius-sm)',
                          border: '1px solid var(--border-medium)'
                        }}>
                          <Lock size={12} color="var(--text-muted)" />
                          <span>Approval Restricted ({role})</span>
                        </div>
                      )
                    )}

                    {isApproved && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--success)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <CheckCircle2 size={15} /> Approved by Administrator
                      </span>
                    )}

                    {isDismissed && (
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                        <X size={15} /> Dismissed by Administrator
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Dismiss Confirmation Dialog Modal (Task 3 & 7) */}
      {dismissModalRec && (
        <div className="modal-backdrop" onClick={() => setDismissModalRec(null)}>
          <div className="modal-content" style={{ maxWidth: '480px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ padding: '0.5rem', background: 'rgba(239, 68, 68, 0.15)', borderRadius: 'var(--radius-md)' }}>
                <AlertTriangle size={22} color="var(--danger)" />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Dismiss Recommendation</h3>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Resource: {dismissModalRec.resource_id}</div>
              </div>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem', lineHeight: 1.55 }}>
              Dismiss this optimization recommendation? The recommendation status will be updated to <strong>dismissed</strong> in PostgreSQL.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button
                onClick={() => setDismissModalRec(null)}
                className="btn btn-secondary"
                disabled={actionLoadingId === dismissModalRec.id}
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDismiss}
                className="btn btn-primary"
                style={{ background: 'var(--danger)', borderColor: 'var(--danger)' }}
                disabled={actionLoadingId === dismissModalRec.id}
              >
                {actionLoadingId === dismissModalRec.id ? 'Dismissing...' : 'Dismiss Recommendation'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* n8n Workflow JSON & Webhook Modal */}
      {showN8nModal && (
        <div className="modal-backdrop" onClick={() => setShowN8nModal(false)}>
          <div className="modal-content" style={{ maxWidth: '720px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <h2>n8n AI Agent Workflow Blueprint</h2>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                  Import this production workflow into your n8n workspace to automate multi-cloud resource optimization.
                </p>
              </div>
              <button 
                onClick={() => setShowN8nModal(false)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                &times;
              </button>
            </div>

            <div style={{ background: 'var(--bg-subtle)', border: '1px solid var(--border-medium)', borderRadius: 'var(--radius-md)', padding: '1rem', marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '0.4rem' }}>
                WEBHOOK INTEGRATION ENDPOINT:
              </div>
              <div style={{ background: 'var(--bg-card)', padding: '0.65rem 0.85rem', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--primary-light)', display: 'flex', justifyContent: 'space-between' }}>
                <span>POST http://localhost:5678/webhook/cloud-optimization</span>
                <span className="badge badge-normal" style={{ fontSize: '0.65rem' }}>Active</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                Endpoint: <code>http://127.0.0.1:8000/api/resources/&lt;id&gt;/optimize/</code>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <button onClick={() => setShowN8nModal(false)} className="btn btn-secondary">
                Close
              </button>
              <button onClick={downloadN8nJson} className="btn btn-primary">
                <Download size={16} />
                <span>Download n8n_workflow.json</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
