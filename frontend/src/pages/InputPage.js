import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Search, Loader2 } from 'lucide-react';
import './InputPage.css';

const InputPage = ({ setReportData }) => {
  const [companyName, setCompanyName] = useState('');
  const [companyRegion, setCompanyRegion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!companyName.trim() || !companyRegion.trim()) {
      setError('Please fill in both fields.');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/api/generate-report', {
        company_name: companyName,
        company_region: companyRegion
      });
      
      setReportData(response.data);
      navigate('/report');
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to generate report. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="input-page">
      <div className="hero-section">
        <h2>Generate Structured Intelligence Reports</h2>
        <p>Enter a company and region to instantly gather insights, news, and executive info from across the web.</p>
      </div>

      <div className="form-card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="companyName">Company Name</label>
            <input 
              type="text" 
              id="companyName"
              placeholder="e.g. Spotify" 
              value={companyName} 
              onChange={(e) => setCompanyName(e.target.value)} 
              disabled={isLoading}
            />
          </div>
          <div className="form-group">
            <label htmlFor="companyRegion">Company Region</label>
            <input 
              type="text" 
              id="companyRegion"
              placeholder="e.g. Sweden or Global" 
              value={companyRegion} 
              onChange={(e) => setCompanyRegion(e.target.value)}
              disabled={isLoading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="submit-btn" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 className="spinner" size={18} />
                <span>Analyzing Data...</span>
              </>
            ) : (
              <>
                <Search size={18} />
                <span>Generate Report</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

export default InputPage;
