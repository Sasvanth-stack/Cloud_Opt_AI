import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Server, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  TrendingUp, 
  Cpu, 
  HardDrive, 
  Activity, 
  DollarSign, 
  CheckCircle2, 
  AlertTriangle,
  Zap,
  Sparkles,
  RefreshCw,
  X
} from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { api } from '../services/api';

export default function Resources({ 
  resources = [], 
  onCreateResource, 
  onApplyRecommendation,
  onNavigate 
}) {
  const { permissions } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [providerFilter, setProviderFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedResource, setSelectedResource] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // Predictions state map: { [resourceId]: { prediction, confidence, loading, error } }
  const [predictions, setPredictions] = useState({});

  const safeResources = Array.isArray(resources) ? resources : [];

  // New resource form state
  const [newResource, setNewResource] = useState({
    resource_id: `VM-00${safeResources.length + 1}`,
    name: 'New Microservice Node',
    resource_type: 'VM',
    cpu_usage: 45,
    memory_usage: 50,
    storage_usage: 40,
    network_usage: 120,
    status: 'active'
  });

  const handlePredict = async (res) => {
    const key = res.id || res.resource_id;
    setPredictions(prev => ({
      ...prev,
      [key]: { loading: true }
    }));

    try {
      const data = await api.predictResource(res.id || 1);
      setPredictions(prev => ({
        ...prev,
        [key]: {
          prediction: data.prediction,
          confidence: data.confidence,
          timestamp: data.timestamp,
          loading: false
        }
      }));
    } catch (err) {
      setPredictions(prev => ({
        ...prev,
        [key]: {
          error: err.message || 'Prediction failed',
          loading: false
        }
      }));
    }
  };

  const filteredResources = safeResources.filter(res => {
    if (!res) return false;
    const rId = (res.resource_id || '').toLowerCase();
    const rName = (res.name || res.resource_name || '').toLowerCase();
    const rType = (res.resource_type || '').toLowerCase();
    const sTerm = (searchTerm || '').toLowerCase();

    const matchesSearch = !sTerm || rId.includes(sTerm) || rName.includes(sTerm) || rType.includes(sTerm);
    const matchesProvider = providerFilter === 'ALL' || 
      (res.provider && res.provider.toUpperCase() === providerFilter.toUpperCase()) || 
      (res.resource_type && res.resource_type.toUpperCase() === providerFilter.toUpperCase());
    const matchesStatus = statusFilter === 'ALL' || 
      (res.status && res.status.toLowerCase() === statusFilter.toLowerCase()) || 
      (res.raw_status && res.raw_status.toLowerCase() === statusFilter.toLowerCase());
    return matchesSearch && matchesProvider && matchesStatus;
  });

  const handleCreate = (e) => {
    e.preventDefault();
    onCreateResource(newResource);
    setShowAddModal(false);
    setNewResource({
      resource_id: `VM-00${resources.length + 2}`,
      name: 'Custom Worker Instance',
      resource_type: 'VM',
      cpu_usage: 50,
      memory_usage: 50,
      storage_usage: 40,
      network_usage: 150,
      status: 'active'
    });
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    switch (s) {
      case 'overloaded':
      case 'critical': 
        return <span className="badge badge-critical">Overloaded</span>;
      case 'underutilized':
      case 'warning': 
        return <span className="badge badge-warning">Underutilized</span>;
      case 'idle': 
        return <span className="badge badge-idle">Idle</span>;
      default: 
        return <span className="badge badge-normal">Active</span>;
    }
  };

  const getPredictionBadge = (pred, conf) => {
    if (!pred) return null;
    const p = pred.toLowerCase();
    const confPct = conf ? `${(conf * 100).toFixed(1)}%` : '';

    if (p === 'scale_up') {
      return (
        <span className="badge" style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', border: '1px solid rgba(239, 68, 68, 0.3)', fontWeight: 700 }}>
          ▲ SCALE_UP {confPct && `(${confPct})`}
        </span>
      );
    } else if (p === 'scale_down') {
      return (
        <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.3)', fontWeight: 700 }}>
          ▼ SCALE_DOWN {confPct && `(${confPct})`}
        </span>
      );
    } else {
      return (
        <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', border: '1px solid rgba(16, 185, 129, 0.3)', fontWeight: 700 }}>
          ✔ NO_ACTION {confPct && `(${confPct})`}
        </span>
      );
    }
  };

  const generateTelemetry = (res) => {
    if (!res) return [];
    const points = [];
    const baseCpu = res.cpu_usage;
    const baseRam = res.memory_usage;
    for (let i = 12; i >= 0; i--) {
      points.push({
        time: `${12 - i}h ago`,
        cpu: Math.max(5, Math.min(99, Math.round(baseCpu + Math.sin(i) * 8))),
        ram: Math.max(10, Math.min(98, Math.round(baseRam + Math.cos(i) * 6))),
      });
    }
    return points;
  };

  return (
    <div className="page-wrapper">
      {/* Header & Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.85rem', marginBottom: '0.35rem' }}>Cloud Resource Inventory</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem' }}>
            Live PostgreSQL database records connected to Scikit-Learn Random Forest optimization classifier.
          </p>
        </div>
        {permissions.canModifyResources && (
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button 
              onClick={() => setShowAddModal(true)} 
              className="btn btn-primary"
            >
              <Plus size={16} />
              <span>Add Resource</span>
            </button>
          </div>
        )}
      </div>

      {/* Filters & Search Toolbar */}
      <div className="glass-card" style={{ marginBottom: '1.5rem', padding: '1rem 1.25rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr', gap: '1rem', alignItems: 'center' }}>
          {/* Search */}
          <div style={{ position: 'relative' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="Search by ID, name, or type..." 
              value={searchTerm} 
              onChange={e => setSearchTerm(e.target.value)} 
              className="form-input" 
              style={{ paddingLeft: '36px' }}
            />
          </div>

          {/* Type Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Type:</span>
            <select 
              value={providerFilter} 
              onChange={e => setProviderFilter(e.target.value)} 
              className="form-select"
            >
              <option value="ALL">All Resource Types</option>
              <option value="VM">Virtual Machines (VM)</option>
              <option value="CONTAINER">Containers</option>
              <option value="DATABASE">Databases</option>
              <option value="STORAGE">Storage</option>
              <option value="NETWORK">Network</option>
              <option value="SERVERLESS">Serverless</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>Status:</span>
            <select 
              value={statusFilter} 
              onChange={e => setStatusFilter(e.target.value)} 
              className="form-select"
            >
              <option value="ALL">All Statuses</option>
              <option value="active">Active</option>
              <option value="overloaded">Overloaded</option>
              <option value="underutilized">Underutilized</option>
              <option value="idle">Idle</option>
            </select>
          </div>
        </div>
      </div>

      {/* Resources Table */}
      <div className="glass-card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="custom-table">
          <thead>
            <tr>
              <th>Resource ID & Name</th>
              <th>Type</th>
              <th style={{ width: '120px' }}>CPU Usage</th>
              <th style={{ width: '120px' }}>RAM Usage</th>
              <th>Storage</th>
              <th>Network</th>
              <th>Status</th>
              <th>ML Optimization</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredResources.map(res => {
              const key = res.id || res.resource_id;
              const predState = predictions[key];

              return (
                <tr key={key}>
                  <td>
                    <div style={{ fontWeight: 700, color: 'var(--text-main)' }}>{res.resource_id}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>{res.name || res.resource_name}</div>
                  </td>
                  <td>
                    <span className="badge badge-provider" style={{ fontFamily: 'var(--font-mono)' }}>
                      {res.resource_type || 'VM'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 600 }}>{res.cpu_usage}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div 
                        className={`progress-bar-fill ${res.cpu_usage >= 80 ? 'fill-high' : res.cpu_usage >= 50 ? 'fill-medium' : 'fill-low'}`}
                        style={{ width: `${Math.min(100, res.cpu_usage)}%` }}
                      ></div>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontWeight: 600 }}>{res.memory_usage}%</span>
                    </div>
                    <div className="progress-bar-bg">
                      <div 
                        className={`progress-bar-fill ${res.memory_usage >= 80 ? 'fill-high' : res.memory_usage >= 50 ? 'fill-medium' : 'fill-low'}`}
                        style={{ width: `${Math.min(100, res.memory_usage)}%` }}
                      ></div>
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                      {res.storage_usage}%
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
                      {res.network_usage} Mbps
                    </div>
                  </td>
                  <td>{getStatusBadge(res.raw_status || res.status)}</td>
                  <td>
                    {predState?.loading ? (
                      <span style={{ fontSize: '0.75rem', color: 'var(--primary-light)', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                        <RefreshCw size={12} className="spin-animation" /> Inferencing...
                      </span>
                    ) : predState?.prediction ? (
                      getPredictionBadge(predState.prediction, predState.confidence)
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Ready</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', gap: '0.4rem', justifyContent: 'flex-end' }}>
                      <button 
                        onClick={() => handlePredict(res)}
                        disabled={predState?.loading}
                        className="btn btn-sm btn-primary"
                        style={{ padding: '0.35rem 0.65rem', fontSize: '0.75rem' }}
                        title="Run Random Forest prediction on this resource"
                      >
                        <Zap size={12} />
                        <span>Predict</span>
                      </button>
                      <button 
                        onClick={() => setSelectedResource(res)}
                        className="btn btn-secondary btn-sm"
                        style={{ padding: '0.35rem 0.55rem' }}
                        title="Inspect full telemetry & prediction"
                      >
                        <Eye size={13} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Resource Detail & Telemetry Modal */}
      {selectedResource && (
        <div className="modal-backdrop" onClick={() => setSelectedResource(null)}>
          <div className="modal-content" style={{ maxWidth: '780px' }} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.25rem' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
                  <span className="badge badge-provider">{selectedResource.resource_type}</span>
                  <span style={{ fontSize: '1.25rem', fontWeight: 800 }}>{selectedResource.resource_id}</span>
                  {getStatusBadge(selectedResource.raw_status || selectedResource.status)}
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  {selectedResource.name || selectedResource.resource_name}
                </div>
              </div>
              <button 
                onClick={() => setSelectedResource(null)}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', fontSize: '1.5rem', cursor: 'pointer' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Hardware & Live Metrics Specs */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CPU UTILIZATION</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '0.15rem' }}>
                  {selectedResource.cpu_usage}%
                </div>
              </div>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RAM CONSUMPTION</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '0.15rem' }}>
                  {selectedResource.memory_usage}%
                </div>
              </div>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>STORAGE SATURATION</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', marginTop: '0.15rem' }}>
                  {selectedResource.storage_usage}%
                </div>
              </div>
              <div style={{ background: 'var(--bg-subtle)', padding: '0.75rem', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>NETWORK I/O</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--primary-light)', marginTop: '0.15rem' }}>
                  {selectedResource.network_usage} Mbps
                </div>
              </div>
            </div>

            {/* Random Forest Action Prediction Box */}
            <div style={{
              background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.08) 0%, rgba(6, 182, 212, 0.08) 100%)',
              border: '1px solid rgba(56, 189, 248, 0.25)',
              borderRadius: 'var(--radius-md)',
              padding: '1rem',
              marginBottom: '1.25rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Sparkles size={18} color="var(--primary-light)" />
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>Random Forest ML Optimization Engine</span>
                </div>
                <button
                  onClick={() => handlePredict(selectedResource)}
                  disabled={predictions[selectedResource.id || selectedResource.resource_id]?.loading}
                  className="btn btn-primary btn-sm"
                >
                  <Zap size={14} />
                  <span>
                    {predictions[selectedResource.id || selectedResource.resource_id]?.loading ? 'Calculating...' : 'Run Prediction API'}
                  </span>
                </button>
              </div>

              {predictions[selectedResource.id || selectedResource.resource_id]?.prediction && (
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '1.5rem', alignItems: 'center', padding: '0.65rem 0.85rem', background: 'var(--bg-card)', borderRadius: 'var(--radius-sm)' }}>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>RECOMMENDED ACTION</span>
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--primary-light)', fontFamily: 'var(--font-mono)' }}>
                      {predictions[selectedResource.id || selectedResource.resource_id].prediction.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>CONFIDENCE</span>
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--success)', fontFamily: 'var(--font-mono)' }}>
                      {(predictions[selectedResource.id || selectedResource.resource_id].confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Model: <strong>RandomForestClassifier (99.25% Acc)</strong> via Django REST API
                  </div>
                </div>
              )}
            </div>

            {/* Historical Telemetry Chart */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                TELEMETRY SATURATION (CPU vs MEMORY)
              </div>
              <div style={{ height: '180px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={generateTelemetry(selectedResource)}>
                    <defs>
                      <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2563EB" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="ramGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.4}/>
                        <stop offset="95%" stopColor="#06B6D4" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} />
                    <YAxis stroke="var(--text-muted)" fontSize={11} domain={[0, 100]} />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-medium)', borderRadius: '8px' }} />
                    <Area type="monotone" dataKey="cpu" stroke="#2563EB" fillOpacity={1} fill="url(#cpuGrad)" name="CPU %" />
                    <Area type="monotone" dataKey="ram" stroke="#06B6D4" fillOpacity={1} fill="url(#ramGrad)" name="RAM %" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setSelectedResource(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add Resource Modal */}
      {showAddModal && (
        <div className="modal-backdrop" onClick={() => setShowAddModal(false)}>
          <div className="modal-content" style={{ maxWidth: '520px' }} onClick={e => e.stopPropagation()}>
            <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Register New Cloud Resource</h2>
            <form onSubmit={handleCreate}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label className="form-label">Resource ID</label>
                  <input 
                    type="text" 
                    value={newResource.resource_id} 
                    onChange={e => setNewResource({ ...newResource, resource_id: e.target.value })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Resource Type</label>
                  <select 
                    value={newResource.resource_type} 
                    onChange={e => setNewResource({ ...newResource, resource_type: e.target.value })} 
                    className="form-select"
                  >
                    <option value="VM">VM (Virtual Machine)</option>
                    <option value="CONTAINER">Container</option>
                    <option value="DATABASE">Database</option>
                    <option value="STORAGE">Storage</option>
                    <option value="NETWORK">Network</option>
                    <option value="SERVERLESS">Serverless</option>
                  </select>
                </div>
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label className="form-label">Resource Name</label>
                <input 
                  type="text" 
                  value={newResource.name} 
                  onChange={e => setNewResource({ ...newResource, name: e.target.value })} 
                  className="form-input" 
                  required 
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <label className="form-label">CPU Usage (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    value={newResource.cpu_usage} 
                    onChange={e => setNewResource({ ...newResource, cpu_usage: e.target.value })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Memory Usage (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    value={newResource.memory_usage} 
                    onChange={e => setNewResource({ ...newResource, memory_usage: e.target.value })} 
                    className="form-input" 
                    required 
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
                <div>
                  <label className="form-label">Storage Usage (%)</label>
                  <input 
                    type="number" 
                    min="0" 
                    max="100" 
                    value={newResource.storage_usage} 
                    onChange={e => setNewResource({ ...newResource, storage_usage: e.target.value })} 
                    className="form-input" 
                    required 
                  />
                </div>
                <div>
                  <label className="form-label">Network Usage (Mbps)</label>
                  <input 
                    type="number" 
                    min="0" 
                    value={newResource.network_usage} 
                    onChange={e => setNewResource({ ...newResource, network_usage: e.target.value })} 
                    className="form-input" 
                    required 
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button type="button" onClick={() => setShowAddModal(false)} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save to PostgreSQL
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
