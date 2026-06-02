import React, { useState, useEffect } from 'react';
import { getHistory, getTrendSummary, getReport } from '../api/iscorApi';
import TrendChart from '../components/TrendChart';
import ReportCard from '../components/ReportCard';

const Reports = () => {
  const [history, setHistory] = useState([]);
  const [trendSummary, setTrendSummary] = useState('');
  const [selectedReportId, setSelectedReportId] = useState('');
  const [loadedReport, setLoadedReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const hist = await getHistory(50);
        setHistory(hist);
        
        if (hist.length >= 3) {
          const trend = await getTrendSummary();
          setTrendSummary(trend.summary);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleSelectReport = async (e) => {
    const id = e.target.value;
    setSelectedReportId(id);
    if (!id) {
      setLoadedReport(null);
      return;
    }
    
    try {
      const report = await getReport(id);
      setLoadedReport(report);
    } catch (e) {
      console.error(e);
      alert("Failed to load report");
    }
  };

  const handleUpdate = async () => {
    // Refresh loaded report (e.g. after sending a chat message)
    if (selectedReportId) {
      try {
        const report = await getReport(selectedReportId);
        setLoadedReport(report);
      } catch (e) {
        console.error(e);
      }
    }
  };

  if (loading) {
    return <div>Loading reports...</div>;
  }

  return (
    <div className="fade-in">
      <h2>My Reports Dashboard</h2>
      
      {history.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
          <h3 style={{ opacity: 0.6 }}>No screenings found</h3>
          <p>Complete a screening to start tracking your well-being over time.</p>
        </div>
      ) : (
        <>
          {history.length >= 3 && (
            <div className="glass-panel" style={{ marginBottom: '3rem' }}>
              <h3>Risk Trend</h3>
              {trendSummary && (
                <div style={{ background: 'rgba(159,176,140,.18)', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', borderLeft: '4px solid var(--sage)' }}>
                  {trendSummary}
                </div>
              )}
              <TrendChart history={history} />
            </div>
          )}

          <div className="glass-panel">
            <h3>Past Screenings</h3>
            <div className="form-group" style={{ maxWidth: '400px' }}>
              <label>Select a report to view details</label>
              <select value={selectedReportId} onChange={handleSelectReport}>
                <option value="">-- Select a Report --</option>
                {history.map(item => (
                  <option key={item.screening_id} value={item.screening_id}>
                    #{item.screening_id} — {item.risk_label} ({new Date(item.screened_at).toLocaleDateString()})
                  </option>
                ))}
              </select>
            </div>

            {loadedReport && (
              <div style={{ marginTop: '3rem' }} className="fade-in">
                <h3 style={{ marginBottom: '1.5rem' }}>Loaded Report #{loadedReport.screening_id}</h3>
                <ReportCard report={loadedReport} onUpdate={handleUpdate} />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default Reports;
