import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ClarityVisual = () => {
  return (
    <div style={{ position: 'relative', height: '300px', width: '100%', background: 'var(--ink)', borderRadius: '16px', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      
      {/* Background Fog Layers parsing apart */}
      <motion.div 
        initial={{ x: 0, opacity: 0.9 }}
        animate={{ x: '-100%', opacity: 0 }}
        transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
        style={{ position: 'absolute', top: 0, left: 0, bottom: 0, width: '50%', background: 'linear-gradient(90deg, rgba(200,200,220,0.8), rgba(200,200,220,0))', zIndex: 2 }}
      />
      <motion.div 
        initial={{ x: 0, opacity: 0.9 }}
        animate={{ x: '100%', opacity: 0 }}
        transition={{ duration: 2, ease: "easeInOut", delay: 0.5 }}
        style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: '50%', background: 'linear-gradient(-90deg, rgba(200,200,220,0.8), rgba(200,200,220,0))', zIndex: 2 }}
      />

      {/* Rays of Clarity */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1.5, delay: 1.5 }}
        style={{ position: 'absolute', width: '100%', height: '100%', background: 'radial-gradient(circle at center, rgba(227,168,87,0.3) 0%, transparent 60%)', zIndex: 1 }}
      />

      {/* Floating Factors */}
      <motion.div 
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 1, delay: 1.8 }}
        style={{ zIndex: 3, display: 'flex', flexDirection: 'column', gap: '1rem' }}
      >
        <div style={{ background: 'var(--sage)', color: '#fff', padding: '0.75rem 1.5rem', borderRadius: '99px', transform: 'translateX(-20px)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', fontWeight: 500 }}>Sleep: 6.5h</div>
        <div style={{ background: 'var(--amber)', color: '#fff', padding: '0.75rem 1.5rem', borderRadius: '99px', transform: 'translateX(30px)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', fontWeight: 500 }}>High Pressure</div>
        <div style={{ background: 'var(--sage)', color: '#fff', padding: '0.75rem 1.5rem', borderRadius: '99px', transform: 'translateX(-10px)', boxShadow: '0 4px 12px rgba(0,0,0,0.2)', fontWeight: 500 }}>Good Support</div>
      </motion.div>
    </div>
  );
};

const Home = () => {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <section className="hero">
        <div className="mono">ISCOR AI</div>
        <h1>See what's really going on.</h1>
        <p>
          A student mental-health screening demo that separates ML prediction, 
          SHAP explainability, safety routing, and constrained wellness language. 
          It is a screening aid, not a diagnosis.
        </p>
      </section>

      <div style={{display: 'flex', gap: '3rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '4rem'}}>
        <div style={{flex: '1 1 400px'}}>
          <ClarityVisual />
        </div>
        
        <div style={{flex: 1, minWidth: '300px'}}>
          <div className="glass-strip" style={{marginBottom: '1rem'}}>
            <h4>How it works</h4>
            <p><strong>1. Screen:</strong> Answer questions about your lifestyle and stressors.</p>
            <p><strong>2. Predict:</strong> Our ML model estimates your current stress-related risk level.</p>
            <p><strong>3. Explain:</strong> SHAP analysis identifies exactly which factors drove your result.</p>
            <p><strong>4. Guide:</strong> A safety-routed LLM generates personalized, non-clinical wellness suggestions.</p>
          </div>
          <Link to="/screening">
            <button style={{width: '100%', fontSize: '1.1rem', padding: '1rem'}}>Take the Screening</button>
          </Link>
        </div>
      </div>
    </motion.div>
  );
};

export default Home;
