import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import InputPage from './pages/InputPage';
import ReportPage from './pages/ReportPage';
import './App.css';

function App() {
  const [reportData, setReportData] = useState(null);

  return (
    <BrowserRouter>
      <div className="App">
        <header className="app-header">
          <h1>Company Intelligence Discoverer</h1>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<InputPage setReportData={setReportData} />} />
            <Route path="/report" element={<ReportPage reportData={reportData} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
