import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";
import { videoAPI } from "../api";
import ReactMarkdown from "react-markdown";
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from "recharts";
import "../styles/Home.css";

const SPORTS = [
  {
    id: "basketball",
    name: "Basketball Shot",
    icon: "🏀",
    athlete: "Stephen Curry",
    description: "Master the shot like the Warriors' #30"
  },
  {
    id: "soccer",
    name: "Soccer Penalty Kick",
    icon: "⚽",
    athlete: "Cristiano Ronaldo",
    description: "Perfect your kick like CR7"
  },
  {
    id: "boxing",
    name: "Boxing Uppercut",
    icon: "🥊",
    athlete: "Mike Tyson",
    description: "Punch like Iron Mike"
  },
  {
    id: "golf",
    name: "Golf Swing",
    icon: "⛳",
    athlete: "Tiger Woods",
    description: "Swing like the GOAT"
  },
];

const Home: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [selectedSport, setSelectedSport] = useState<string | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [similarityScore, setSimilarityScore] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadMode, setUploadMode] = useState<"upload" | "record">("upload");
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const streamRef = React.useRef<MediaStream | null>(null);

  // Function to extract similarity score from analysis text
  const extractSimilarityScore = (text: string): number | null => {
    console.log('Extracting similarity score from text...');

    const patterns = [
      // Similarity score: 75%
      /similarity\s*score[:\s-]*(\d+)\s*%/i,
      // Similarity: 75%
      /similarity[:\s-]*(\d+)\s*%/i,
      // 75% similarity
      /(\d+)\s*%\s*similarity/i,
      // Score: 75%
      /\bscore[:\s-]*(\d+)\s*%/i,
      // Overall: 75%
      /overall[:\s-]*(\d+)\s*%/i,
      // Match: 75%
      /match[:\s-]*(\d+)\s*%/i,
      // Any number followed by % in the first 500 characters (fallback)
      /(\d+)\s*%/,
    ];

    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match && match[1]) {
        const score = parseInt(match[1]);
        if (score >= 0 && score <= 100) {
          console.log('Found similarity score:', score, '% using pattern:', pattern);
          return score;
        }
      }
    }

    console.log('No similarity score found in analysis text');
    return null;
  };

  const handleVideoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log('File selected:', file.name, 'Type:', file.type);

      // Clear previous state
      setError(null);
      setAnalysis(null);
      setSimilarityScore(null);

      // Check if it's a video file
      const isVideo = file.type.startsWith('video/') || file.name.match(/\.(mp4|mov|avi|mkv|webm)$/i);

      if (!isVideo) {
        setError('Please upload a valid video file (MP4, MOV, AVI, MKV, or WEBM)');
        setVideoFile(null);
        setVideoPreview(null);
        return;
      }

      // Set the file and create preview
      setVideoFile(file);
      const previewUrl = URL.createObjectURL(file);
      console.log('Preview URL created:', previewUrl);
      setVideoPreview(previewUrl);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedSport || !videoFile) {
      setError("Please select a sport and upload a video");
      return;
    }

    setLoading(true);
    setError(null);
    setAnalysis(null);

    try {
      const response = await videoAPI.analyzeVideo(selectedSport, videoFile);
      const analysisText = response.data.analysis;
      setAnalysis(analysisText);

      // Extract similarity score from the analysis
      const score = extractSimilarityScore(analysisText);
      setSimilarityScore(score);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    const wasInRecordMode = uploadMode === "record";

    setVideoFile(null);
    setVideoPreview(null);
    setAnalysis(null);
    setSimilarityScore(null);
    setError(null);

    // If we were in record mode, restart the camera
    if (wasInRecordMode) {
      stopCamera();
      // Small delay to ensure camera is fully stopped before restarting
      setTimeout(() => {
        startCamera();
      }, 100);
    }
  };

  // Start camera for recording
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user" },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error("Camera access error:", err);
      setError("Unable to access camera. Please check permissions.");
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  // Start recording
  const startRecording = () => {
    if (!streamRef.current) return;

    // Try to use mp4 if supported, otherwise use webm
    let mimeType = "video/webm";
    let extension = "webm";

    if (MediaRecorder.isTypeSupported("video/mp4")) {
      mimeType = "video/mp4";
      extension = "mp4";
    } else if (MediaRecorder.isTypeSupported("video/webm;codecs=h264")) {
      mimeType = "video/webm;codecs=h264";
    } else if (MediaRecorder.isTypeSupported("video/webm;codecs=vp9")) {
      mimeType = "video/webm;codecs=vp9";
    }

    console.log("Recording with mimeType:", mimeType);

    const recorder = new MediaRecorder(streamRef.current, { mimeType });

    const chunks: Blob[] = [];

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunks.push(event.data);
      }
    };

    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: mimeType });
      const file = new File([blob], `recording_${Date.now()}.${extension}`, {
        type: mimeType,
      });
      console.log("Recorded file:", file.name, file.type);
      setVideoFile(file);
      setVideoPreview(URL.createObjectURL(blob));
      stopCamera();
    };

    setMediaRecorder(recorder);
    recorder.start();
    setIsRecording(true);
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  // Handle mode change
  const handleModeChange = (mode: "upload" | "record") => {
    setUploadMode(mode);
    setVideoFile(null);
    setVideoPreview(null);
    setAnalysis(null);
    setSimilarityScore(null);
    setError(null);

    if (mode === "record") {
      startCamera();
    } else {
      stopCamera();
    }
  };

  return (
    <div className="home-container">
      <nav className="navbar">
        <div className="nav-left">
          <button onClick={() => navigate("/")} className="back-button">
            ← Back
          </button>
          <h1>Shadow⛓️‍💥Sync</h1>
        </div>
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
                className={`sport-card ${
                  selectedSport === sport.id ? "selected" : ""
                }`}
                onClick={() => setSelectedSport(sport.id)}
              >
                <span className="sport-icon">{sport.icon}</span>
                <div className="sport-info">
                  <span className="sport-name">{sport.name}</span>
                  <span className="sport-athlete">vs {sport.athlete}</span>
                  <span className="sport-description">{sport.description}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {selectedSport && !videoFile && (
          <div className="upload-section">
            <h3>Choose Input Method</h3>

            <div className="mode-toggle">
              <button
                className={`mode-button ${uploadMode === "upload" ? "active" : ""}`}
                onClick={() => handleModeChange("upload")}
              >
                📁 Upload Video
              </button>
              <button
                className={`mode-button ${uploadMode === "record" ? "active" : ""}`}
                onClick={() => handleModeChange("record")}
              >
                📹 Record Video
              </button>
            </div>

            {uploadMode === "upload" ? (
              <div className="upload-area">
                <input
                  type="file"
                  accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska,video/webm,.mp4,.mov,.avi,.mkv,.webm"
                  onChange={handleVideoChange}
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="upload-button">
                  Choose Video File
                </label>
              </div>
            ) : (
              <div className="record-area">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                  className="camera-preview"
                />
                <div className="record-controls">
                  {!isRecording ? (
                    <button onClick={startRecording} className="record-button">
                      ⏺ Start Recording
                    </button>
                  ) : (
                    <button onClick={stopRecording} className="stop-button">
                      ⏹ Stop Recording
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {videoFile && (
          <div className="preview-section">
            <h3>Video Preview</h3>
            {videoPreview ? (
              <video
                src={videoPreview}
                controls
                className="video-preview"
                onError={(e) => {
                  console.error('Video preview error:', e);
                  setError('Unable to preview this video format, but you can still analyze it.');
                }}
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              <div className="video-placeholder">
                <p>Video file selected: {videoFile.name}</p>
                <p>Preview unavailable, but you can still analyze.</p>
              </div>
            )}
            <button
              onClick={handleAnalyze}
              disabled={loading}
              className="analyze-button"
            >
              {loading ? "Analyzing..." : "Analyze My Form"}
            </button>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}

        {analysis && (
          <div className="analysis-section">
            <h3>Analysis Results</h3>

            {similarityScore !== null && (
              <div className="score-visualization">
                <h4>Similarity Score</h4>
                <div className="pie-chart-container">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={[
                          { name: "Match", value: similarityScore },
                          { name: "Gap", value: 100 - similarityScore },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        <Cell fill="#9b59b6" />
                        <Cell fill="#333" />
                      </Pie>
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="score-text">
                    <span className="score-number">{similarityScore}%</span>
                    <span className="score-label">Match</span>
                  </div>
                </div>
              </div>
            )}

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
