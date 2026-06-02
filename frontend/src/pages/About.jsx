import React from 'react';

const About = () => {
  return (
    <div className="fade-in glass-panel" style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>Trust & Privacy</h2>
      
      <div style={{ marginBottom: '2rem' }}>
        <h4>Data Encryption</h4>
        <p>
          We take privacy seriously. Your raw answers, free-text explanations, and chat history are 
          encrypted at rest in our database using Fernet symmetric encryption. We do not use your 
          inputs to train our models.
        </p>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <h4>AI and Clinical Safety</h4>
        <p>
          This tool provides an educational screening aid, not a clinical diagnosis. 
          The underlying risk prediction is powered by a machine learning model, which is then 
          explained via SHAP (SHapley Additive exPlanations) values to provide transparency.
        </p>
        <p style={{ marginTop: '1rem' }}>
          Our AI generator is strictly constrained. It cannot diagnose you and is forbidden from 
          recommending medication. Furthermore, a deterministic <strong>Risk Gate</strong> intercepts 
          all High-risk inputs and bypasses the AI generation entirely, routing instead to verified 
          crisis support resources.
        </p>
      </div>

      <div>
        <h4>RAG Evidence</h4>
        <p>
          Where applicable, wellness suggestions are grounded in retrieved snippets from vetted 
          psychoeducational materials (e.g., CDC, WHO, NHS guidelines) using Retrieval-Augmented Generation (RAG). 
          You can view the exact source texts used to ground the AI's advice in the "Evidence Used" 
          section of your report.
        </p>
      </div>
    </div>
  );
};

export default About;
