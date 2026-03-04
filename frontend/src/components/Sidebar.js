import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import { Search, Clock, ChevronRight, Building2, Loader2, Trash2, Circle } from 'lucide-react';
import './Sidebar.css';

const API = 'http://localhost:8000';

function timeAgo(isoString) {
  if (!isoString) return '';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

const Sidebar = ({ activeReportId, onSelectReport, onNewSearch }) => {
  const [reports, setReports]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [query, setQuery]       = useState('');
  const [deleting, setDeleting] = useState(null); // id currently being deleted

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API}/api/reports`);
      setReports(res.data || []);
    } catch (e) {
      console.error('Failed to load report history:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusCycle = useCallback(async (e, id, currentStatus) => {
    e.stopPropagation();
    const states = ['default', 'active', 'red'];
    const nextStatus = states[(states.indexOf(currentStatus || 'default') + 1) % states.length];
    
    // Optimistic update
    setReports(prev => prev.map(r => r.id === id ? { ...r, status: nextStatus } : r));
    
    try {
      await axios.patch(`${API}/api/reports/${id}/status`, { status: nextStatus });
    } catch (err) {
      console.error('Failed to update status:', err);
      // Rollback
      setReports(prev => prev.map(r => r.id === id ? { ...r, status: currentStatus } : r));
    }
  }, []);

  const handleDelete = useCallback(async (e, id) => {
    e.stopPropagation(); // don't trigger item selection
    if (!window.confirm('Delete this report from history?')) return;
    setDeleting(id);
    try {
      await axios.delete(`${API}/api/reports/${id}`);
      setReports(prev => prev.filter(r => r.id !== id));
      // If we just deleted the currently viewed report, go home
      if (activeReportId === id) onNewSearch();
    } catch (e) {
      console.error('Failed to delete report:', e);
    } finally {
      setDeleting(null);
    }
  }, [activeReportId, onNewSearch]);

  useEffect(() => {
    fetchReports();
    // Poll every 10s so newly generated reports appear without refresh
    const interval = setInterval(fetchReports, 10000);
    return () => clearInterval(interval);
  }, []);

  const filtered = reports.filter(r =>
    r.company_name.toLowerCase().includes(query.toLowerCase()) ||
    r.company_region.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <aside className="sidebar">
      {/* Header */}
      <div className="sidebar-header">
        <span className="sidebar-title">History</span>
        <button className="sidebar-new-btn" onClick={onNewSearch} title="New search">
          + New
        </button>
      </div>

      {/* Search filter */}
      <div className="sidebar-search">
        <Search size={14} />
        <input
          type="text"
          placeholder="Filter companies…"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
      </div>

      {/* List */}
      <div className="sidebar-list">
        {loading ? (
          <div className="sidebar-empty">
            <Loader2 size={20} className="spin" />
            <span>Loading…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="sidebar-empty">
            <Clock size={18} />
            <span>{query ? 'No matches.' : 'No searches yet.'}</span>
          </div>
        ) : (
          filtered.map(r => (
            <button
              key={r.id}
              className={`sidebar-item 
                ${activeReportId === r.id ? 'sidebar-item--selected' : ''} 
                sidebar-item--status-${r.status || 'default'}`}
              onClick={() => onSelectReport(r.id)}
            >
              <button 
                className={`sidebar-status-btn sidebar-status-btn--${r.status || 'default'}`}
                onClick={(e) => handleStatusCycle(e, r.id, r.status)}
                title="Cycle status (Default -> Active -> Red)"
              >
                <Circle size={12} fill={
                  r.status === 'active' ? '#4ade80' : 
                  r.status === 'red' ? '#f87171' : 
                  'transparent'
                } />
              </button>

              <div className="sidebar-item-text">
                <span className="sidebar-item-name">{r.company_name}</span>
                <span className="sidebar-item-meta">
                  {r.company_region} · {timeAgo(r.created_at)}
                </span>
              </div>

              <button
                className={`sidebar-delete-btn ${deleting === r.id ? 'sidebar-delete-btn--loading' : ''}`}
                onClick={e => handleDelete(e, r.id)}
                disabled={deleting === r.id}
                title="Delete report"
              >
                {deleting === r.id
                  ? <Loader2 size={13} className="spin" />
                  : <Trash2 size={13} />
                }
              </button>
            </button>
          ))
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
