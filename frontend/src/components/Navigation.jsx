import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Shield, Brain, Activity, Heart, History, User, Compass } from 'lucide-react';

const Navigation = () => {
  return (
    <nav className="navbar fade-in">
      <Link to="/" className="brand">ISCOR AI</Link>
      
      <NavLink to="/screening" className={({isActive}) => isActive ? "active" : ""}>
        <Activity size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        Screening
      </NavLink>
      
      <NavLink to="/reports" className={({isActive}) => isActive ? "active" : ""}>
        <History size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        My Reports
      </NavLink>
      
      <NavLink to="/assessment" className={({isActive}) => isActive ? "active" : ""}>
        <Compass size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        Self-Reflection
      </NavLink>
      
      <NavLink to="/companion" className={({isActive}) => isActive ? "active" : ""}>
        <Brain size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        Companion
      </NavLink>
      
      <NavLink to="/checkin" className={({isActive}) => isActive ? "active" : ""}>
        <Heart size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        Check-in
      </NavLink>
      
      <NavLink to="/about" className={({isActive}) => isActive ? "active" : ""}>
        <Shield size={18} style={{marginRight: 6, display: 'inline', verticalAlign: 'text-bottom'}} />
        About/Trust
      </NavLink>
    </nav>
  );
};

export default Navigation;
