import React, { useState } from 'react';
import { useAuth } from '../AuthContext';
import { videoAPI } from '../api';
import ReactMarkdown from 'react-markdown';
import '../styles/Home.css';

const SPORTS = [
  { id: 'basketball', name: 'Basketball Shot', icon: '🏀' },
  { id: 'soccer', name: 'Soccer Penalty Kick', icon: '⚽' },
  { id: 'boxing', name: 'Boxing Uppercut', icon: '🥊' },
  { id: 'golf', name: 'Golf Swing', icon: '⛳' },
];

const Home: React.FC = () => {
  const { user, logout } = useAuth();
  const [selectedSport, setSelectedSport] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      setVideoPreview(URL.createObjectURL(file));
      setAnalysis(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedSport || !videoFile) {
      setError('Please select a sport and upload a video');
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await videoAPI.analyzeVideo(selectedSport, videoFile);
      setAnalysis(response.data.analysis);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedSport(null);
    setVideoFile(null);
    setVideoPreview(null);
    setAnalysis(null);
    setError(null);
  };

  return (
    <div className="home-container">
      <nav className="navbar">
        <h1>ShadowSync</h1>
        <div className="nav-right">
          <span>Welcome, {user?.username}</span>
          <button onClick={logout}>Logout</button>
        </div>
      </nav>

      <div className="content">
        <h2>Improve Your Sports Form</h2>
        <p>Upload a video and compare your technique to the pros</p>

        <div className="sport-selection">
          <h3>Select a Sport</h3>
          <div className="sport-grid">
            {SPORTS.map((sport) => (
              <button
                key={sport.id}
                className={`sport-card ${selectedSport === sport.id ? 'selected' : ''}`}
                onClick={() => setSelectedSport(sport.id)}
              >
                <span className="sport-icon">{sport.icon}</span>
                <span className="sport-name">{sport.name}</span>
              </button>
            ))}
          </div>
        </div>

        {selectedSport && (
          <div className="upload-section">
            <h3>Upload Your Video</h3>
            <input
              type="file"
              accept="video/*"
              onChange={handleVideoChange}
              id="video-upload"
            />
            <label htmlFor="video-upload" className="upload-button">
              Choose Video File
            </label>
            {videoFile && <p className="file-name">{videoFile.name}</p>}
          </div>
        )}

        {videoPreview && (
          <div className="preview-section">
            <h3>Video Preview</h3>
            <video src={videoPreview} controls className="video-preview" />
            <button onClick={handleAnalyze} disabled={loading} className="analyze-button">
              {loading ? 'Analyzing...' : 'Analyze My Form'}
            </button>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {analysis && (
          <div className="analysis-section">
            <h3>Analysis Results</h3>
            <div className="analysis-content">
              <ReactMarkdown>{analysis}</ReactMarkdown>
            </div>
            <button onClick={handleReset} className="reset-button">
              Analyze Another Video
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
