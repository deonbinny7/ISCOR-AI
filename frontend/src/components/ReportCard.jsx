import React, { useState } from 'react';
import FactorChart from './FactorChart';
import EvidenceSources from './EvidenceSources';
import WeeklyPlanCards from './WeeklyPlanCards';
import ChatThread from './ChatThread';
import { sendChat } from '../api/iscorApi';
import { MessageSquare } from 'lucide-react';

const renderMarkdown = (text) => {
  if (!text) return null;
  return text.split('\n').map((line, index) => {
    if (line.startsWith('### ')) {
      return <h4 key={index} style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: 'var(--ink)' }}>{line.replace('### ', '')}</h4>;
    }
    if (line.startsWith('## ')) {
      return <h3 key={index} style={{ marginTop: '1.5rem', marginBottom: '0.5rem', color: 'var(--ink)' }}>{line.replace('## ', '')}</h3>;
    }
    if (line.trim().startsWith('- ')) {
      return <div key={index} style={{ display: 'flex', marginLeft: '1rem', marginBottom: '0.25rem' }}><span style={{ marginRight: '0.5rem' }}>•</span><span>{line.replace(/^- /, '')}</span></div>;
    }
    return <p key={index} style={{ margin: '0 0 0.5rem 0', minHeight: line.trim() === '' ? '1rem' : 'auto' }}>{line}</p>;
  });
};

const ReportCard = ({ report, onUpdate }) => {
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const [activeTab, setActiveTab] = useState('Overview');

  const confidence = report.risk_probabilities?.[report.risk_label] || 0;
  const llmLabel = report.llm_provider ? `🤖 AI-generated (${report.llm_provider})` : '⚙️ Standard summary';

  const handleChatSubmit = async (message) => {
    setIsChatting(true);
    try {
      await sendChat(report.screening_id, message);
      if (onUpdate) onUpdate(); // Trigger a refresh to get the updated conversation history
    } catch (e) {
      console.error(e);
      alert("Failed to send message: " + (e.message || "Please try again."));
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="glass-panel fade-in">
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <span className="risk-tag">Risk: {report.risk_label} — {(confidence * 100).toFixed(0)}% confidence</span>
        <span style={{ fontSize: '0.9em', opacity: 0.8, fontWeight: 500 }}>{llmLabel}</span>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '2px solid rgba(43,36,56,.1)', paddingBottom: '0.5rem', marginBottom: '2rem', overflowX: 'auto', whiteSpace: 'nowrap' }}>
        {['Overview', 'Factors', 'Explanation', 'Weekly Plan', 'Q&A'].map(tab => {
          // Hide Q&A tab if in crisis mode
          if (report.crisis_mode && tab === 'Q&A') return null;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                background: activeTab === tab ? 'var(--ink)' : 'transparent',
                color: activeTab === tab ? 'var(--cloudlight)' : 'var(--ink)',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: 'pointer',
                opacity: activeTab === tab ? 1 : 0.7
              }}
            >
              {tab}
            </button>
          );
        })}
      </div>

      <div style={{ minHeight: '300px' }}>
        {activeTab === 'Overview' && (
          <div className="fade-in">
            {report.crisis_mode && (
              <div style={{ padding: '1rem', background: '#ffebee', color: '#c62828', borderRadius: '6px', marginBottom: '1.5rem', fontWeight: 500 }}>
                Safety router active: wellness suggestions were bypassed for this result.
              </div>
            )}
            <h4>Summary</h4>
            <div style={{ lineHeight: 1.6 }}>
              {renderMarkdown(report.explanation)}
            </div>
          </div>
        )}

        {activeTab === 'Factors' && (
          <div className="fade-in" style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem' }}>
            <div style={{ flex: '1 1 400px' }}>
              <FactorChart factors={report.top_factors} />
            </div>
            
            {report.top_factors && report.top_factors.length > 0 && (
              <div style={{ flex: '1 1 300px' }}>
                <h4>Factor Insights</h4>
                {report.top_factors.map((f, i) => (
                  <div key={i} style={{
                    padding: '1rem', 
                    borderLeft: `4px solid ${f.direction === 'increases_risk' ? 'var(--amber)' : 'var(--sage)'}`, 
                    background: 'rgba(248,241,232,0.6)', 
                    borderRadius: '6px', 
                    marginBottom: '0.8rem'
                  }}>
                    <div style={{ fontWeight: 600, marginBottom: '0.2rem' }}>
                      {f.feature.replace(/_/g, ' ')} 
                      <span style={{ fontSize: '0.8em', fontWeight: 400, opacity: 0.8, marginLeft: '6px' }}>
                        ({f.cohort_percentile === 0 || f.cohort_percentile === 100 ? 'insufficient comparison data' : `Higher than ${f.cohort_percentile || 50}% of respondents`})
                      </span>
                    </div>
                    <div style={{ fontSize: '0.95em', lineHeight: 1.5, color: 'var(--ink)' }}>
                      {f.counterfactual || `If ${f.feature.replace(/_/g, ' ')} changed, your risk might decrease.`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'Explanation' && (
          <div className="fade-in">
            {report.wellness_suggestions ? (
              <div style={{ lineHeight: 1.6 }}>
                {renderMarkdown(report.wellness_suggestions)}
              </div>
            ) : (
              <p>No wellness suggestions available.</p>
            )}
            <EvidenceSources evidence={report.retrieved_evidence} />
          </div>
        )}

        {activeTab === 'Weekly Plan' && (
          <div className="fade-in">
            {report.weekly_plan ? (
              <WeeklyPlanCards planText={report.weekly_plan} />
            ) : (
              <p>No weekly plan available.</p>
            )}
          </div>
        )}

        {activeTab === 'Q&A' && !report.crisis_mode && (
          <div className="fade-in">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <MessageSquare size={20} />
              <h4 style={{ margin: 0 }}>Follow-up Q&A</h4>
            </div>
            
            <div style={{ height: '400px' }}>
              <ChatThread 
                history={report.conversation_history} 
                onSendMessage={handleChatSubmit} 
                isProcessing={isChatting} 
                placeholder="Ask a follow-up question based on this report..."
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportCard;
