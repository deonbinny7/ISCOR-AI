import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import Home from './pages/Home';
import Screening from './pages/Screening';
import Reports from './pages/Reports';
import Companion from './pages/Companion';
import Checkin from './pages/Checkin';
import About from './pages/About';
import Assessment from './pages/Assessment';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navigation />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/screening" element={<Screening />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/assessment" element={<Assessment />} />
          <Route path="/companion" element={<Companion />} />
          <Route path="/checkin" element={<Checkin />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
