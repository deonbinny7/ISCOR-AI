import React, { useState, useEffect } from 'react';
import { submitAssessment, getLatestAssessment } from '../api/iscorApi';

const Assessment = () => {
  const [scores, setScores] = useState({
    openness: 3,
    conscientiousness: 3,
    extraversion: 3,
    agreeableness: 3,
    neuroticism: 3
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [viewingHistory, setViewingHistory] = useState(true); // Attempt to load latest on mount

  useEffect(() => {
    const fetchLatest = async () => {
      try {
        const data = await getLatestAssessment();
        if (data.assessment) {
          setResult(data.assessment);
        } else {
          setViewingHistory(false);
        }
      } catch (e) {
        console.error(e);
        setViewingHistory(false);
      }
    };
    fetchLatest();
  }, []);

  const handleChange = (e) => {
    setScores(prev => ({ ...prev, [e.target.name]: Number(e.target.value) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await submitAssessment(scores);
      if (response.error) throw new Error(response.error);
      setResult({
        scores: response.scores,
        summary: response.summary,
        created_at: new Date().toISOString()
      });
      setViewingHistory(true);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (e) {
      setError(e.message || "Failed to submit assessment.");
    } finally {
      setLoading(false);
    }
  };

  const labels = {
    openness: { left: "Consistent/Cautious", right: "Inventive/Curious" },
    conscientiousness: { left: "Easy-going/Careless", right: "Efficient/Organized" },
    extraversion: { left: "Solitary/Reserved", right: "Outgoing/Energetic" },
    agreeableness: { left: "Challenging/Detached", right: "Friendly/Compassionate" },
    neuroticism: { left: "Secure/Confident", right: "Sensitive/Nervous" }
  };

  return (
    <div className="fade-in">
      <h2 style={{ marginBottom: '1rem' }}>Big Five Self-Reflection</h2>
      <p style={{ opacity: 0.8, maxWidth: '800px', marginBottom: '2rem' }}>
        This instrument is designed to help you reflect on your personality traits (OCEAN model). 
        It is <strong>not a clinical diagnosis</strong>. Your scores are used to generate a short, 
        encouraging summary of your strengths and potential areas of growth to aid in your self-awareness.
      </p>

      {result && viewingHistory ? (
        <div className="glass-panel fade-in" style={{ marginBottom: '3rem', borderLeft: '4px solid var(--amber)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
            <h3 style={{ margin: 0 }}>Your Reflection Summary</h3>
            <span style={{ fontSize: '0.85rem', opacity: 0.7 }}>
              {new Date(result.created_at).toLocaleDateString()}
            </span>
          </div>
          
          <div style={{ marginTop: '1.5rem', whiteSpace: 'pre-wrap', lineHeight: 1.6, fontSize: '1.05rem', color: 'var(--ink)' }}>
            {result.summary}
          </div>

          <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
            {Object.entries(result.scores).map(([trait, score]) => (
              <div key={trait} style={{ background: 'rgba(255,255,255,0.5)', padding: '0.5rem 1rem', borderRadius: '999px', fontSize: '0.9rem', fontWeight: 500, fontFamily: 'var(--mono)' }}>
                {trait}: {score}/5
              </div>
            ))}
          </div>

          <button className="outline" style={{ marginTop: '2rem' }} onClick={() => setViewingHistory(false)}>
            Retake Assessment
          </button>
        </div>
      ) : (
        <div className="glass-panel">
          <form onSubmit={handleSubmit}>
            {Object.keys(scores).map((trait) => (
              <div key={trait} style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{trait}</span>
                  <span className="mono">{scores[trait]}/5</span>
                </div>
                <input 
                  type="range" 
                  name={trait} 
                  value={scores[trait]} 
                  onChange={handleChange} 
                  min={1} max={5} step={1}
                  style={{ width: '100%' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', opacity: 0.7, marginTop: '0.25rem' }}>
                  <span>{labels[trait].left}</span>
                  <span>{labels[trait].right}</span>
                </div>
              </div>
            ))}

            {error && <div style={{ color: '#d64e12', marginBottom: '1rem', fontWeight: 500 }}>{error}</div>}

            <div style={{ marginTop: '3rem', textAlign: 'center' }}>
              <button type="submit" disabled={loading} style={{ fontSize: '1.1rem', minWidth: '200px' }}>
                {loading ? 'Reflecting...' : 'Generate Reflection'}
              </button>
              {result && (
                <button type="button" className="outline" style={{ marginLeft: '1rem' }} onClick={() => setViewingHistory(true)}>
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
      )}
    </div>
  );
};

export default Assessment;
