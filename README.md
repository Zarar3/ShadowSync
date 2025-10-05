# ShadowSync

**ShadowSync** is an AI-powered sports form analysis application that helps athletes improve their technique by comparing their movements to professional athletes. Upload a video of yourself performing a basketball shot, soccer penalty kick, boxing uppercut, or golf swing, and get detailed feedback powered by Google's Gemini AI.

## Features

- **User Authentication**: Secure signup and login system
- **Multi-Sport Support**: Analyze 4 different sports movements
  - Basketball shooting (compared to Stephen Curry)
  - Soccer penalty kicks (compared to Cristiano Ronaldo)
  - Boxing uppercuts (compared to Mike Tyson)
  - Golf swings (compared to Tiger Woods)
- **AI-Powered Analysis**: Leverages Google Gemini to provide detailed form comparisons and improvement suggestions
- **Simple & Clean UI**: Built with React and TypeScript for a smooth user experience

## Tech Stack

### Backend
- **FastAPI** (Python) - REST API framework
- **SQLAlchemy** - Database ORM
- **SQLite** - Database
- **JWT** - Authentication
- **Google Gemini AI** - Video analysis

### Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **React Router** - Navigation
- **Axios** - HTTP client
- **Vite** - Build tool

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn
- Google Gemini API key ([Get one here](https://ai.google.dev/))

## Installation & Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd ShadowSync
```

### 2. Backend Setup

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
# SECRET_KEY=your_random_secret_key_here
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# The default API URL is http://localhost:8000
# Edit .env if you need to change it
```

## Running the Application

### 1. Start the Backend

```bash
cd backend

# Make sure your virtual environment is activated
# Then run:
uvicorn main:app --reload --port 8000
```

The backend API will be available at `http://localhost:8000`

### 2. Start the Frontend

Open a new terminal window:

```bash
cd frontend

npm run dev
```

The frontend will be available at `http://localhost:5173`

### 3. Access the Application

1. Open your browser and go to `http://localhost:5173`
2. Sign up for a new account
3. Log in with your credentials
4. Select a sport
5. Upload a video of yourself performing that movement
6. Click "Analyze My Form" to get AI-powered feedback

## Project Structure

```
ShadowSync/
├── backend/
│   ├── main.py                 # Main FastAPI application
│   ├── database.py             # Database models and setup
│   ├── auth.py                 # Authentication logic
│   ├── gemini_comparision.py   # Original Gemini integration (legacy)
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example           # Environment variables template
│   ├── stephShot.mp4          # Reference video - Steph Curry
│   ├── ronaldoKick.mp4        # Reference video - Ronaldo
│   ├── tysonUppercut.mp4      # Reference video - Mike Tyson
│   └── tigerSwing.mp4         # Reference video - Tiger Woods
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Login.tsx      # Login page
    │   │   ├── Signup.tsx     # Signup page
    │   │   └── Home.tsx       # Main analysis page
    │   ├── styles/
    │   │   ├── Auth.css       # Auth pages styles
    │   │   └── Home.css       # Home page styles
    │   ├── api.ts             # API client
    │   ├── AuthContext.tsx    # Auth state management
    │   ├── App.tsx            # Main app component
    │   └── main.tsx           # Entry point
    ├── package.json           # Node dependencies
    └── .env.example          # Environment variables template
```

## API Endpoints

- `POST /api/signup` - Create a new user account
- `POST /api/login` - Login and get JWT token
- `GET /api/me` - Get current user info (requires auth)
- `GET /api/sports` - Get list of supported sports
- `POST /api/analyze-video/{sport}` - Upload and analyze video (requires auth)

## Notes

- The application uses SQLite database which will be created automatically on first run
- Uploaded videos are temporarily stored during analysis and then deleted
- Each video analysis may take 10-30 seconds depending on video size and Gemini API response time
- Make sure you have a valid Gemini API key with sufficient quota

## Demo Tips

When pitching to investors:
1. Have a pre-recorded demo video ready for each sport
2. Keep videos short (5-10 seconds) for faster analysis
3. Ensure good lighting and clear view of the form
4. Test your Gemini API connection before the demo

## Troubleshooting

**Backend won't start:**
- Make sure your virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check that your `.env` file has a valid Gemini API key

**Frontend won't connect to backend:**
- Verify the backend is running on port 8000
- Check the `VITE_API_URL` in frontend `.env` file
- Look for CORS errors in browser console

**Video analysis fails:**
- Verify your Gemini API key is valid and has quota
- Check that reference video files exist in the backend directory
- Ensure uploaded video is in a supported format (mp4, mov, avi)

## License

This project is for demonstration purposes.
