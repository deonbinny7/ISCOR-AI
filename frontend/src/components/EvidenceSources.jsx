import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react';

const EvidenceSources = ({ evidence }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="glass-panel fade-in" style={{ marginTop: '1.5rem', padding: '1.5rem', borderLeft: '4px solid var(--sage)' }}>
      <div 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <BookOpen size={20} color="var(--sage)" />
          <h4 style={{ margin: 0, color: 'var(--ink)' }}>Evidence Used (RAG Context)</h4>
        </div>
        {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </div>
      
      {isOpen && (
        <div style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p style={{ fontSize: '0.9rem', opacity: 0.8 }}>
            The AI suggestions above were grounded in the following vetted clinical and psychoeducational guidelines:
          </p>
          {evidence.map((chunk, idx) => (
            <div key={idx} style={{ 
              background: 'rgba(255,255,255,0.7)', 
              padding: '1rem', 
              borderRadius: '6px',
              border: '1px solid rgba(43,36,56,.1)'
            }}>
              <div style={{ fontWeight: 600, marginBottom: '0.5rem', fontFamily: 'var(--mono)', fontSize: '0.85rem' }}>
                Source {idx + 1}: {chunk.source}
              </div>
              <div style={{ fontSize: '0.95rem', lineHeight: 1.5 }}>
                {chunk.text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EvidenceSources;
