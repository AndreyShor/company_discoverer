import React, { useState, useCallback } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import axios from 'axios';
import InputPage  from './pages/InputPage';
import ReportPage from './pages/ReportPage';
import Sidebar    from './components/Sidebar';
import './App.css';

const API = 'http://localhost:8000';

/* Inner component so we can useNavigate() */
function AppInner() {
  const navigate = useNavigate();
  const [reportData,     setReportData]     = useState(null);
  const [activeReportId, setActiveReportId] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  /* Called by Sidebar when user clicks a historical entry */
  const handleSelectReport = useCallback(async (id) => {
    if (activeReportId === id) return;  // already viewing
    setLoadingHistory(true);
    try {
      const res = await axios.get(`${API}/api/reports/${id}`);
      setReportData(res.data);
      setActiveReportId(id);
      navigate('/report');
    } catch (e) {
      console.error('Failed to load report:', e);
    } finally {
      setLoadingHistory(false);
    }
  }, [activeReportId, navigate]);

  /* Called by InputPage after a fresh generation */
  const handleNewReport = useCallback((data) => {
    setReportData(data);
    setActiveReportId(null);  // sidebar will refresh and highlight on next poll
    navigate('/report');
  }, [navigate]);

  /* Called by Sidebar "+ New" button */
  const handleNewSearch = useCallback(() => {
    setActiveReportId(null);
    navigate('/');
  }, [navigate]);

  return (
    <div className="App">
      {/* Sticky top bar */}
      <header className="app-header">
        <h1>Company Intelligence Discoverer</h1>
      </header>

      {/* Body: sidebar + main content */}
      <div className="app-body">
        <Sidebar
          activeReportId={activeReportId}
          onSelectReport={handleSelectReport}
          onNewSearch={handleNewSearch}
        />

        <main className="app-main">
          {loadingHistory && (
            <div className="history-loading">Loading report…</div>
          )}
          <Routes>
            <Route path="/"       element={<InputPage  setReportData={handleNewReport} />} />
            <Route path="/report" element={<ReportPage reportData={reportData} />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppInner />
    </BrowserRouter>
  );
}

export default App;
