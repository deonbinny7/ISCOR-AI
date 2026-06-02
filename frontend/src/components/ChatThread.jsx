import React, { useState } from 'react';
import { Send } from 'lucide-react';

const ChatThread = ({ history, onSendMessage, isProcessing, placeholder = "Type your message..." }) => {
  const [input, setInput] = useState('');
  const [pendingMessage, setPendingMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isProcessing) return;
    setPendingMessage(input.trim());
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ 
        flex: 1, 
        overflowY: 'auto', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '1rem',
        padding: '1rem',
        marginBottom: '1rem',
        borderRadius: '12px',
        background: 'rgba(255,255,255,0.4)',
        border: '1px solid rgba(43,36,56,.1)',
        minHeight: '200px'
      }}>
        {(!history || history.length === 0) && !isProcessing && (
          <div style={{ margin: 'auto', opacity: 0.5, fontStyle: 'italic' }}>
            No messages yet. Start the conversation!
          </div>
        )}
        
        {history && history.map((msg, idx) => (
          <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ 
              alignSelf: 'flex-end', 
              background: 'rgba(43,36,56,.05)', 
              padding: '0.75rem 1rem', 
              borderRadius: '12px 12px 0 12px', 
              maxWidth: '85%' 
            }}>
              {msg.question}
            </div>
            {msg.response && (
              <div style={{ 
                alignSelf: 'flex-start', 
                background: 'var(--ink)', 
                color: 'var(--cloudlight)', 
                padding: '0.75rem 1rem', 
                borderRadius: '12px 12px 12px 0', 
                maxWidth: '85%', 
                whiteSpace: 'pre-wrap',
                lineHeight: 1.5
              }}>
                {msg.response}
              </div>
            )}
          </div>
        ))}
        
        {isProcessing && pendingMessage && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ 
              alignSelf: 'flex-end', 
              background: 'rgba(43,36,56,.05)', 
              padding: '0.75rem 1rem', 
              borderRadius: '12px 12px 0 12px', 
              maxWidth: '85%' 
            }}>
              {pendingMessage}
            </div>
            <div style={{ 
              alignSelf: 'flex-start', 
              background: 'var(--ink)', 
              color: 'var(--cloudlight)', 
              padding: '0.75rem 1rem', 
              borderRadius: '12px 12px 12px 0', 
              opacity: 0.7 
            }}>
              Thinking...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder}
          style={{ flex: 1, padding: '0.75rem 1rem', borderRadius: '999px', border: '1px solid rgba(43,36,56,.2)' }}
          disabled={isProcessing}
        />
        <button 
          type="submit" 
          disabled={isProcessing || !input.trim()} 
          style={{ 
            padding: '0.75rem', 
            borderRadius: '50%', 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            width: '48px', 
            height: '48px',
            background: input.trim() && !isProcessing ? 'var(--amber)' : '#ccc',
            border: 'none',
            color: '#fff',
            cursor: input.trim() && !isProcessing ? 'pointer' : 'default'
          }}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

export default ChatThread;
