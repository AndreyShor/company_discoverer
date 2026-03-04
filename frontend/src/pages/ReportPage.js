import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Building, Users, TrendingUp, Newspaper, Target, Link as LinkIcon } from 'lucide-react';
import './ReportPage.css';

const ReportPage = ({ reportData }) => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect back if no data (e.g., page refresh)
    if (!reportData) {
      navigate('/');
    }
  }, [reportData, navigate]);

  if (!reportData) return null;

  return (
    <div className="report-page">
      <button className="back-btn" onClick={() => navigate('/')}>
        <ArrowLeft size={16} /> Back to Search
      </button>

      <div className="report-header">
        <h2>{reportData.company_name}</h2>
        <span className="badge">Intelligence Report</span>
      </div>

      <div className="report-grid">
        <div className="card overview-card col-span-2">
          <div className="card-header">
            <Building className="icon text-blue" />
            <h3>Company Overview</h3>
          </div>
          <div className="card-body">
            <p>{reportData.overview}</p>
          </div>
        </div>

        <div className="card executives-card">
          <div className="card-header">
            <Users className="icon text-purple" />
            <h3>Key Executives</h3>
          </div>
          <div className="card-body">
            {reportData.key_executives && reportData.key_executives.length > 0 ? (
              <ul className="executive-list">
                {reportData.key_executives.map((exec, idx) => (
                  <li key={idx}>
                    <strong>{exec.name}</strong>
                    <span>{exec.role}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No key executives found.</p>
            )}
          </div>
        </div>

        <div className="card financials-card">
          <div className="card-header">
            <TrendingUp className="icon text-green" />
            <h3>Financial Summary</h3>
          </div>
          <div className="card-body">
             <p>{reportData.financial_summary || 'Not explicitly available'}</p>
          </div>
        </div>

        <div className="card news-card col-span-2">
          <div className="card-header">
            <Newspaper className="icon text-orange" />
            <h3>Recent News & Milestones</h3>
          </div>
          <div className="card-body">
            {reportData.recent_news && reportData.recent_news.length > 0 ? (
              <ul className="bullet-list">
                {reportData.recent_news.map((news, idx) => (
                  <li key={idx}>{news}</li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No recent news found.</p>
            )}
          </div>
        </div>

        <div className="card competitors-card">
          <div className="card-header">
            <Target className="icon text-red" />
            <h3>Competitors</h3>
          </div>
          <div className="card-body">
             {reportData.competitors && reportData.competitors.length > 0 ? (
              <ul className="bullet-list">
                {reportData.competitors.map((comp, idx) => (
                  <li key={idx}>{comp}</li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No competitors identified.</p>
            )}
          </div>
        </div>

        <div className="card sources-card">
          <div className="card-header">
            <LinkIcon className="icon text-gray" />
            <h3>Sources</h3>
          </div>
          <div className="card-body">
             {reportData.sources && reportData.sources.length > 0 ? (
              <ul className="source-list">
                {reportData.sources.map((source, idx) => (
                  <li key={idx}>
                    <a href={source} target="_blank" rel="noopener noreferrer">
                      {source.length > 50 ? source.substring(0, 50) + '...' : source}
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-muted">No explicit sources provided by LLM.</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default ReportPage;
