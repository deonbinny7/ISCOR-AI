import React, { useState, useEffect } from 'react';
import { getRecentMoods, submitMoodCheckin } from '../api/iscorApi';
import { Flame, CheckCircle, ExternalLink, Activity } from 'lucide-react';

const Checkin = () => {
  const [moods, setMoods] = useState([]);
  const [streak, setStreak] = useState(0);
  const [todaysMood, setTodaysMood] = useState(null);
  const [noteInput, setNoteInput] = useState('');
  const [crisisAlert, setCrisisAlert] = useState(null);
  const [isBreathing, setIsBreathing] = useState(false);
  const [breatheText, setBreatheText] = useState('Start');

  useEffect(() => {
    const fetchMoods = async () => {
      try {
        const data = await getRecentMoods();
        if (data.history) {
          setMoods(data.history);
          calculateStreak(data.history);
          
          // Check if checked in today
          const today = new Date().toISOString().split('T')[0];
          const todayEntry = data.history.find(m => m.created_at.startsWith(today));
          if (todayEntry) setTodaysMood(todayEntry.mood_score);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchMoods();
  }, []);

  const calculateStreak = (history) => {
    if (!history || history.length === 0) return setStreak(0);
    
    // Sort descending by date
    const sortedDates = history.map(h => h.created_at.split('T')[0])
                               .sort((a,b) => new Date(b) - new Date(a));
    
    // Remove duplicates (multiple checkins on same day)
    const uniqueDates = [...new Set(sortedDates)];
    
    let currentStreak = 0;
    const today = new Date();
    today.setHours(0,0,0,0);
    
    let d = new Date(today);
    
    // Check if they missed yesterday and today to break streak
    const hasToday = uniqueDates.includes(d.toISOString().split('T')[0]);
    
    d.setDate(d.getDate() - 1);
    const hasYesterday = uniqueDates.includes(d.toISOString().split('T')[0]);
    
    if (!hasToday && !hasYesterday && uniqueDates.length > 0) {
      setStreak(0);
      return;
    }

    // Trace backwards
    d = new Date(today);
    while (true) {
      const dateStr = d.toISOString().split('T')[0];
      if (uniqueDates.includes(dateStr)) {
        currentStreak++;
        d.setDate(d.getDate() - 1);
      } else if (dateStr === today.toISOString().split('T')[0]) {
        // missed today, but maybe did yesterday, keep checking
        d.setDate(d.getDate() - 1);
      } else {
        break;
      }
    }
    
    setStreak(currentStreak);
  };

  const handleMoodSubmit = async (score) => {
    try {
      const response = await submitMoodCheckin(score, noteInput.trim() || null);
      if (response.crisis_intercept) {
        setCrisisAlert(response.message);
      } else {
        setCrisisAlert(null);
      }
      
      setTodaysMood(score);
      // Trigger a re-fetch to update streak
      const data = await getRecentMoods();
      if (data.history) {
        setMoods(data.history);
        calculateStreak(data.history);
      }
    } catch (e) {
      console.error(e);
      alert("Failed to submit mood. Please ensure you have completed a screening first to log in.");
    }
  };

  const startBreathing = () => {
    setIsBreathing(true);
    setBreatheText('Breathe In...');
    
    let cycle = 0;
    const interval = setInterval(() => {
      cycle++;
      if (cycle === 12) { // 3 full Box Breathing cycles (16s each = ~48s)
        clearInterval(interval);
        setIsBreathing(false);
        setBreatheText('Start');
        return;
      }
      
      const phase = cycle % 4;
      if (phase === 0) setBreatheText('Breathe In...');
      else if (phase === 1) setBreatheText('Hold...');
      else if (phase === 2) setBreatheText('Breathe Out...');
      else if (phase === 3) setBreatheText('Hold...');
    }, 4000);
  };

  const RESOURCES = [
    { name: "iCall Helpline (India)", desc: "Psychosocial helpline for emotional support.", link: "https://icallhelpline.org" },
    { name: "Student Minds", desc: "Resources for university student mental health.", link: "https://www.studentminds.org.uk/" },
    { name: "Mindful.org", desc: "Free mindfulness and meditation practices.", link: "https://www.mindful.org/" },
    { name: "Sleep Hygiene Guidelines (CDC)", desc: "Tips for better sleep quality.", link: "https://www.cdc.gov/sleep/about_sleep/sleep_hygiene.html" }
  ];

  return (
    <div className="fade-in">
      <h2>Daily Engagement</h2>

      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        
        {/* Left Column: Mood & Streak */}
        <div style={{ flex: '1 1 400px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Flame color="var(--amber)" size={24} /> 
                Check-in Streak
              </h3>
              <p style={{ opacity: 0.8, marginTop: '0.5rem' }}>Consecutive days logged</p>
            </div>
            <div style={{ fontSize: '3rem', fontWeight: 700, fontFamily: 'var(--mono)', color: 'var(--ink)' }}>
              {streak} <span style={{ fontSize: '1rem' }}>days</span>
            </div>
          </div>

          <div className="glass-panel">
            <h3>How are you feeling today?</h3>
            {todaysMood ? (
              <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--sage)' }}>
                {crisisAlert ? (
                  <div style={{ color: 'var(--ink)', background: 'rgba(255,100,100,0.1)', padding: '1.5rem', borderRadius: '12px', border: '1px solid rgba(255,0,0,0.2)', textAlign: 'left', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                    {crisisAlert}
                  </div>
                ) : (
                  <>
                    <CheckCircle size={48} style={{ margin: '0 auto 1rem' }} />
                    <h4>Check-in complete!</h4>
                    <p>You rated your mood a {todaysMood}/5.</p>
                  </>
                )}
              </div>
            ) : (
              <div style={{ marginTop: '2rem' }}>
                <textarea
                  placeholder="Optional: Add a note about your day..."
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  style={{ width: '100%', padding: '1rem', borderRadius: '12px', background: 'rgba(255,255,255,0.6)', border: '1px solid rgba(43,36,56,.1)', minHeight: '80px', marginBottom: '1.5rem', resize: 'vertical' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button 
                      key={score} 
                      className="outline" 
                      onClick={() => handleMoodSubmit(score)}
                      style={{ padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem' }}
                    >
                      <span style={{ fontSize: '1.5rem' }}>
                        {score === 1 ? '😢' : score === 2 ? '😕' : score === 3 ? '😐' : score === 4 ? '🙂' : '😄'}
                      </span>
                      <span>{score}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Right Column: Breathing & Resources */}
        <div style={{ flex: '1 1 400px', display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          
          <div className="glass-panel" style={{ textAlign: 'center', minHeight: '320px' }}>
            <h3>Guided Breathing</h3>
            <p style={{ opacity: 0.8 }}>Box breathing (4s in, 4s hold, 4s out, 4s hold)</p>
            
            {isBreathing ? (
              <div className="breathe-circle" style={{ animation: 'breatheInOut 16s infinite ease-in-out' }}>
                {breatheText}
              </div>
            ) : (
              <div style={{ marginTop: '4rem' }}>
                <button onClick={startBreathing}>
                  <Activity size={18} style={{ marginRight: '8px', verticalAlign: 'text-bottom' }} />
                  Start Exercise (45s)
                </button>
              </div>
            )}
          </div>

          <div className="glass-panel">
            <h3>Curated Resources</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1.5rem' }}>
              {RESOURCES.map((res, idx) => (
                <a key={idx} href={res.link} target="_blank" rel="noreferrer" style={{ 
                  display: 'block', 
                  padding: '1rem', 
                  background: 'rgba(255,255,255,0.6)', 
                  borderRadius: '8px',
                  textDecoration: 'none',
                  color: 'var(--ink)',
                  border: '1px solid rgba(43,36,56,.1)'
                }}>
                  <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    {res.name} <ExternalLink size={14} />
                  </div>
                  <div style={{ fontSize: '0.9rem', opacity: 0.8, marginTop: '0.25rem' }}>{res.desc}</div>
                </a>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};

export default Checkin;
