import React, { useState, useEffect, useRef } from 'react';
import { getCompanionHistory, sendCompanionChat } from '../api/iscorApi';
import ChatThread from '../components/ChatThread';
import { Send, Bot, User } from 'lucide-react';

const Companion = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await getCompanionHistory();
        if (data.history) {
          // history is ordered old to new: [{role: 'user', content: '...'}, {role: 'companion', content: '...'}]
          // Need to group them into {question, response} pairs
          const grouped = [];
          for (let i = 0; i < data.history.length; i++) {
            if (data.history[i].role === 'user') {
              grouped.push({
                question: data.history[i].content,
                response: data.history[i+1]?.role === 'companion' ? data.history[i+1].content : ''
              });
              i++; // skip the companion message we just grabbed
            }
          }
          setMessages(grouped);
        }
      } catch (e) {
        console.error(e);
        setError("Failed to load chat history. Ensure you are logged in by completing a screening first.");
      }
    };
    fetchHistory();
  }, []);

  const handleSend = async (userMessage) => {
    if (!userMessage.trim() || loading) return;

    // Add optimistically as a new pair
    setMessages(prev => [...prev, { question: userMessage, response: '' }]);
    setLoading(true);

    try {
      const data = await sendCompanionChat(userMessage);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].response = data.response;
        return updated;
      });
    } catch (e) {
      console.error(e);
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1].response = 'Sorry, I am having trouble connecting right now.';
        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 120px)' }}>
      <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
        <h2 style={{ marginBottom: '0.5rem' }}>Wellness Companion</h2>
        <p style={{ opacity: 0.8, fontSize: '0.9rem' }}>
          I'm here to chat about stress, wellness, or your screening results. 
          <em> Not a substitute for professional help.</em>
        </p>
      </div>

      <div className="glass-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        {error && <div style={{ padding: '1rem', color: '#d64e12', textAlign: 'center' }}>{error}</div>}
        
        <ChatThread 
          history={messages} 
          onSendMessage={handleSend} 
          isProcessing={loading} 
          placeholder="Type your message..."
        />
      </div>
    </div>
  );
};

export default Companion;
