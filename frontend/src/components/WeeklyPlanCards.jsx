import React from 'react';

const WeeklyPlanCards = ({ planText }) => {
  if (!planText) return null;

  // Attempt to parse the block of text into individual days.
  // We split by "Day X:" or "**Day X**" or just "Day X"
  const daysRegex = /(?:(?:\*\*Day \d\*\*)|(?:Day \d:?))/gi;
  
  // Split the text. The first element is likely intro text if any exists before Day 1
  const parts = planText.split(daysRegex);
  const matches = planText.match(daysRegex);

  if (!matches || matches.length === 0) {
    // If we couldn't parse it into days, just render it as paragraphs
    return (
      <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
        {planText}
      </div>
    );
  }

  const intro = parts[0].trim();
  
  const cards = matches.map((match, idx) => {
    // Clean up the match (e.g. "**Day 1**:" -> "Day 1")
    const title = match.replace(/[*:]/g, '').trim();
    // The content is in parts[idx + 1]
    const content = parts[idx + 1] ? parts[idx + 1].trim() : '';
    
    return { title, content };
  });

  return (
    <div>
      {intro && <p style={{ marginBottom: '1.5rem', opacity: 0.9 }}>{intro}</p>}
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {cards.map((card, idx) => (
          <div key={idx} style={{ 
            background: 'rgba(255,255,255,0.7)', 
            border: '1px solid rgba(43,36,56,.1)', 
            borderRadius: '12px',
            padding: '1.25rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
          }}>
            <h5 style={{ margin: '0 0 0.75rem 0', color: 'var(--ink)', borderBottom: '2px solid rgba(43,36,56,.1)', paddingBottom: '0.5rem' }}>
              {card.title}
            </h5>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.5, opacity: 0.9 }}>
              {card.content.split('\n').map((line, i) => (
                <span key={i}>
                  {line}
                  <br />
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeeklyPlanCards;
