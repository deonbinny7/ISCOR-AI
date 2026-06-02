import React, { useState, useEffect } from 'react';
import { createSession, submitScreening, getHistory, getReport } from '../api/iscorApi';
import ReportCard from '../components/ReportCard';

const Screening = () => {
  const [hasConsent, setHasConsent] = useState(false);
  const [formData, setFormData] = useState({
    // Step 0: Basics
    age: 21,
    gender: 'Male',
    family_history: 'No',
    
    // Step 1: Core Mental Wellness
    mood: 3,
    anxiety: 3,
    energy_level: 3,
    concentration: 3,
    appetite_changes: 'No Change',
    loneliness: 3,
    
    // Step 2: Lifestyle & Stressors
    sleep_hours: 6.5,
    sleep_quality: 3,
    study_hours: 6.0,
    physical_activity: 3.0,
    screen_time: 4.0,
    academic_pressure: 3,
    financial_stress: 3,
    
    // Step 3: Major Life Events
    major_life_events: [],
    
    // Step 4: Protective Factors
    family_support: 3,
    friend_support: 3,
    hobbies: 3,
    ability_to_relax: 3,
    life_satisfaction: 3,
    social_support: 'Moderate', // existing string categorical
    
    // Step 5: Optional Health Context
    recent_illness: false,
    chronic_condition: false,
    medication: false,
    surgery: false,
    substance_use: false,
    health_notes: '',
    menstrual_status: '',
    cycle_phase: '',
    pms_pmdd: false,
    pregnancy_status: false,
    postpartum_status: false,
    menopause: false,
    
    // Step 6: Submit
    question: ''
  });
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  const [step, setStep] = useState(0);

  useEffect(() => {
    // Check if session exists
    const token = localStorage.getItem("iscor_session_token");
    if (token) {
      setHasConsent(true);
    }
  }, []);

  const handleConsent = async () => {
    try {
      await createSession();
      setHasConsent(true);
    } catch (e) {
      setError("Could not create session. Is the backend running?");
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      if (name === 'major_life_events') {
        setFormData(prev => {
          if (checked) {
            return { ...prev, major_life_events: [...prev.major_life_events, value] };
          } else {
            return { ...prev, major_life_events: prev.major_life_events.filter(item => item !== value) };
          }
        });
      } else {
        setFormData(prev => ({ ...prev, [name]: checked }));
      }
    } else {
      let parsedValue = value;
      if (type === 'number' || type === 'range') parsedValue = Number(value);
      setFormData(prev => ({ ...prev, [name]: parsedValue }));
    }
  };

  const nextStep = (e) => {
    e.preventDefault();
    setStep(prev => prev + 1);
  };

  const prevStep = (e) => {
    e.preventDefault();
    setStep(prev => prev - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const payload = { ...formData, consent: true };
      const result = await submitScreening(payload);
      setReport(result);
      setStep(4); // Move to a "Report generated" state or just let the report show
      // Scroll to report
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }, 100);
    } catch (e) {
      console.error(e);
      setError("Failed to submit screening: " + (e.message || "Please try again."));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateReport = async () => {
    if (report && report.screening_id) {
      try {
        const updated = await getReport(report.screening_id);
        setReport(updated);
      } catch (e) {
        console.error(e);
      }
    }
  };

  if (!hasConsent) {
    return (
      <div className="fade-in" style={{ maxWidth: '600px', margin: '0 auto', textAlign: 'center' }}>
        <h2>Consent Required</h2>
        <p style={{ marginBottom: '2rem' }}>
          Before screening, confirm that you understand this tool is for project demonstration 
          and educational screening only. It cannot diagnose or replace professional support.
        </p>
        <button onClick={handleConsent} style={{ fontSize: '1.1rem' }}>I Understand and Consent</button>
        {error && <p style={{ color: 'red', marginTop: '1rem' }}>{error}</p>}
      </div>
    );
  }

  const renderStepContent = () => {
    switch (step) {
      case 0: // Basics
        return (
          <div className="fade-in">
            <h3>Step 1: The Basics</h3>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Age</label>
              <input type="number" name="age" value={formData.age} onChange={handleChange} min={16} max={80} />
            </div>
            <div className="form-group">
              <label>Gender</label>
              <select name="gender" value={formData.gender} onChange={handleChange}>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Family History of Mental Illness</label>
              <select name="family_history" value={formData.family_history} onChange={handleChange}>
                <option value="No">No</option>
                <option value="Yes">Yes</option>
              </select>
            </div>
          </div>
        );
      case 1: // Core Mental Wellness
        return (
          <div className="fade-in">
            <h3>Step 2: Core Mental Wellness</h3>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Mood last 2 weeks (1-5, higher is better): {formData.mood}</label>
              <input type="range" name="mood" value={formData.mood} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Anxiety Frequency (1-5, higher is more frequent): {formData.anxiety}</label>
              <input type="range" name="anxiety" value={formData.anxiety} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Energy Level (1-5): {formData.energy_level}</label>
              <input type="range" name="energy_level" value={formData.energy_level} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Difficulty Concentrating (1-5): {formData.concentration}</label>
              <input type="range" name="concentration" value={formData.concentration} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Loneliness (1-5): {formData.loneliness}</label>
              <input type="range" name="loneliness" value={formData.loneliness} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Appetite Changes</label>
              <select name="appetite_changes" value={formData.appetite_changes} onChange={handleChange}>
                <option value="No Change">No Change</option>
                <option value="Eating Less">Eating Less</option>
                <option value="Eating More">Eating More</option>
              </select>
            </div>
          </div>
        );
      case 2: // Lifestyle & Stressors
        return (
          <div className="fade-in">
            <h3>Step 3: Lifestyle & Stressors</h3>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Sleep Hours/Night ({formData.sleep_hours})</label>
              <input type="range" name="sleep_hours" value={formData.sleep_hours} onChange={handleChange} min={0} max={12} step={0.5} />
            </div>
            <div className="form-group">
              <label>Sleep Quality (1-5): {formData.sleep_quality}</label>
              <input type="range" name="sleep_quality" value={formData.sleep_quality} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Study Hours/Day ({formData.study_hours})</label>
              <input type="range" name="study_hours" value={formData.study_hours} onChange={handleChange} min={0} max={18} step={0.5} />
            </div>
            <div className="form-group">
              <label>Physical Activity Hours/Week ({formData.physical_activity})</label>
              <input type="range" name="physical_activity" value={formData.physical_activity} onChange={handleChange} min={0} max={14} step={0.5} />
            </div>
            <div className="form-group">
              <label>Screen Time Hours/Day ({formData.screen_time})</label>
              <input type="range" name="screen_time" value={formData.screen_time} onChange={handleChange} min={0} max={16} step={0.5} />
            </div>
            <div className="form-group">
              <label>Academic Pressure (1-5): {formData.academic_pressure}</label>
              <input type="range" name="academic_pressure" value={formData.academic_pressure} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Financial Stress (1-5): {formData.financial_stress}</label>
              <input type="range" name="financial_stress" value={formData.financial_stress} onChange={handleChange} min={1} max={5} step={1} />
            </div>
          </div>
        );
      case 3: // Major Life Events
        return (
          <div className="fade-in">
            <h3>Step 4: Major Life Events (Last 6 Months)</h3>
            <div className="form-group" style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {['Loss of family member', 'Breakup', 'Financial hardship', 'Relocation', 'Academic failure'].map(ev => (
                <label key={ev} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                  <input type="checkbox" name="major_life_events" value={ev} checked={formData.major_life_events.includes(ev)} onChange={handleChange} />
                  {ev}
                </label>
              ))}
            </div>
          </div>
        );
      case 4: // Protective Factors
        return (
          <div className="fade-in">
            <h3>Step 5: Protective Factors</h3>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Family Support (1-5): {formData.family_support}</label>
              <input type="range" name="family_support" value={formData.family_support} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Friend Support (1-5): {formData.friend_support}</label>
              <input type="range" name="friend_support" value={formData.friend_support} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>General Social Support (Low/Mod/High)</label>
              <select name="social_support" value={formData.social_support} onChange={handleChange}>
                <option value="Low">Low</option>
                <option value="Moderate">Moderate</option>
                <option value="High">High</option>
              </select>
            </div>
            <div className="form-group">
              <label>Participation in Hobbies (1-5): {formData.hobbies}</label>
              <input type="range" name="hobbies" value={formData.hobbies} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Ability to Relax (1-5): {formData.ability_to_relax}</label>
              <input type="range" name="ability_to_relax" value={formData.ability_to_relax} onChange={handleChange} min={1} max={5} step={1} />
            </div>
            <div className="form-group">
              <label>Overall Life Satisfaction (1-5): {formData.life_satisfaction}</label>
              <input type="range" name="life_satisfaction" value={formData.life_satisfaction} onChange={handleChange} min={1} max={5} step={1} />
            </div>
          </div>
        );
      case 5: // Optional Health Context
        return (
          <div className="fade-in">
            <h3>Step 6: Optional Health Context</h3>
            <p style={{ opacity: 0.8, fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              This section is entirely optional and helps the AI personalize lifestyle suggestions. It is not used for diagnosis.
            </p>
            <div className="form-group" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                <input type="checkbox" name="recent_illness" checked={formData.recent_illness} onChange={handleChange} /> Recent serious illness
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                <input type="checkbox" name="chronic_condition" checked={formData.chronic_condition} onChange={handleChange} /> Current chronic condition
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                <input type="checkbox" name="medication" checked={formData.medication} onChange={handleChange} /> Medication affecting mood
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                <input type="checkbox" name="surgery" checked={formData.surgery} onChange={handleChange} /> Recent surgery
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                <input type="checkbox" name="substance_use" checked={formData.substance_use} onChange={handleChange} /> Substance use
              </label>
            </div>
            
            {formData.gender === 'Female' && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '1rem', fontSize: '1rem' }}>Female Health (Optional)</h4>
                <div className="form-group">
                  <label>Menstrual Status</label>
                  <input type="text" name="menstrual_status" value={formData.menstrual_status} onChange={handleChange} placeholder="e.g. Regular, Irregular" />
                </div>
                <div className="form-group">
                  <label>Cycle Phase</label>
                  <input type="text" name="cycle_phase" value={formData.cycle_phase} onChange={handleChange} placeholder="e.g. Luteal, Follicular" />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                    <input type="checkbox" name="pms_pmdd" checked={formData.pms_pmdd} onChange={handleChange} /> Experience PMS/PMDD
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                    <input type="checkbox" name="pregnancy_status" checked={formData.pregnancy_status} onChange={handleChange} /> Pregnant
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                    <input type="checkbox" name="postpartum_status" checked={formData.postpartum_status} onChange={handleChange} /> Postpartum
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'normal' }}>
                    <input type="checkbox" name="menopause" checked={formData.menopause} onChange={handleChange} /> Menopause / Perimenopause
                  </label>
                </div>
              </div>
            )}
            
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Additional Health Notes</label>
              <textarea name="health_notes" value={formData.health_notes} onChange={handleChange} rows={3} placeholder="Any other context you'd like to share..." />
            </div>
          </div>
        );
      case 6: // Review
        return (
          <div className="fade-in">
            <h3>Step 7: Review & Submit</h3>
            <div className="form-group" style={{ marginTop: '1.5rem' }}>
              <label>Optional follow-up question (Answered via AI)</label>
              <input type="text" name="question" value={formData.question} onChange={handleChange} placeholder="e.g. How can I balance study and sleep better?" />
            </div>
            <p style={{ marginTop: '2rem', opacity: 0.8 }}>
              You are about to submit your screening. This tool is for educational purposes only.
            </p>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="fade-in">
      <h2 style={{ marginBottom: '2rem' }}>Screening</h2>
      
      {!report && (
        <div className="glass-panel" style={{ marginBottom: '3rem', maxWidth: '600px', margin: '0 auto 3rem auto' }}>
          
          {/* Progress Indicator */}
          <div style={{ display: 'flex', gap: '4px', marginBottom: '2rem' }}>
            {[0, 1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} style={{ 
                flex: 1, 
                height: '4px', 
                background: step >= i ? 'var(--ink)' : 'rgba(43,36,56,.1)',
                borderRadius: '2px',
                transition: 'background 0.3s ease'
              }} />
            ))}
          </div>

          <form onSubmit={step === 6 ? handleSubmit : nextStep}>
            {renderStepContent()}

            {error && <div style={{ color: '#d64e12', marginTop: '1rem', fontWeight: 500 }}>{error}</div>}

            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '2.5rem' }}>
              {step > 0 ? (
                <button type="button" className="outline" onClick={prevStep}>Back</button>
              ) : <div />}
              
              {step < 6 ? (
                <button type="submit">Next</button>
              ) : (
                <button type="submit" disabled={loading}>
                  {loading ? 'Processing...' : 'Run Screening'}
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      {report && (
        <div className="fade-in" style={{ paddingBottom: '4rem' }}>
          <h2 style={{ marginBottom: '1.5rem' }}>Your Report</h2>
          <ReportCard report={report} onUpdate={handleUpdateReport} />
          
          <div style={{ textAlign: 'center', marginTop: '3rem' }}>
            <button className="outline" onClick={() => {
              setReport(null);
              setStep(0);
              window.scrollTo(0,0);
            }}>Take another screening</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Screening;
