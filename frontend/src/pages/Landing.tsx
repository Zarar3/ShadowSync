import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import '../styles/Landing.css';

const Landing: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleStartTraining = () => {
    navigate('/analyze');
  };

  return (
    <div className="landing-container">
      <nav className="navbar">
        <h1>Shadow⛓️Sync</h1>
        <div className="nav-right">
          <span>Welcome, {user?.username}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </nav>

      <div className="landing-content">
        <div className="welcome-box">
          <h2>Hello, {user?.username}</h2>
          <h3>Welcome to your training grounds</h3>
          <p>Analyze your form and train like the pros. Compare your technique to the world's greatest athletes.</p>

          <button onClick={handleStartTraining} className="start-button">
            Start Training
          </button>
        </div>

        <div className="features-grid">
          <div className="feature-card">
            <span className="feature-icon">🏀</span>
            <h4>Basketball</h4>
            <p>Master your shot like Steph Curry</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">⚽</span>
            <h4>Soccer</h4>
            <p>Perfect your kick like Ronaldo</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">🥊</span>
            <h4>Boxing</h4>
            <p>Punch like Mike Tyson</p>
          </div>
          <div className="feature-card">
            <span className="feature-icon">⛳</span>
            <h4>Golf</h4>
            <p>Swing like Tiger Woods</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Landing;
