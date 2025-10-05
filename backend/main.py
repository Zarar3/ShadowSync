from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import timedelta
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import time

from database import get_db, User, init_db
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

load_dotenv()

app = FastAPI(title="ShadowSync API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Gemini client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None

BASE_DIR = Path(__file__).resolve().parent
TEMP_UPLOADS_DIR = BASE_DIR / "temp_uploads"
TEMP_UPLOADS_DIR.mkdir(exist_ok=True)

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str

# Sport configuration
SPORT_PROMPTS = {
    "basketball": (
        "Describe the basketball shooting form compared to the player in the video on the Golden State Warriors "
        "with the number 30 jersey (Stephen Curry). Compare elements like guide hand, follow-through, shooting stance, "
        "footwork, release speed, and overall fluidity. Provide a similarity score (percentage) and highlight strengths, "
        "differences, and areas for improvement. If the uploaded video doesn't depict a basketball shooting motion, reject it."
    ),
    "soccer": (
        "Analyze the soccer shooting or passing technique compared to a professional player's form. "
        "Evaluate aspects such as body alignment, foot placement, follow-through, balance, and accuracy. "
        "Include comments on approach angle and timing. Provide a similarity score (percentage) and give feedback "
        "on how to improve the user's shooting or passing technique. "
        "If the uploaded video does not show a soccer shooting or passing action, reject it."
    ),
    "boxing": (
        "Analyze the boxing technique compared to that of a professional boxer. Focus on stance, guard position, "
        "punch form (jab, cross, hook, uppercut), hip rotation, and defensive movements. "
        "Provide a similarity score (percentage) and explain where the user's technique aligns with or differs from "
        "a professional's form. Suggest targeted improvements for power, precision, and defense. "
        "If the uploaded video does not show a boxing action, reject it."
    ),
    "golf": (
        "Analyze the golf swing form compared to that of a professional golfer. Evaluate grip, stance, backswing, "
        "downswing, impact, and follow-through. Comment on balance, swing plane, tempo, and consistency. "
        "Provide a similarity score (percentage) and detailed suggestions for improving swing mechanics and accuracy. "
        "If the uploaded video does not show a golf swing, reject it."
    )
}

SPORT_VIDEOS = {
    "basketball": BASE_DIR / "stephShot.mp4",
    "soccer": BASE_DIR / "ronaldoKick.mp4",
    "boxing": BASE_DIR / "tysonUppercut.mp4",
    "golf": BASE_DIR / "tigerSwing.mp4"
}

# Auth endpoints
@app.post("/api/signup", response_model=Token)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create new user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# Video analysis endpoint
@app.post("/api/analyze-video/{sport}")
async def analyze_video(
    sport: str,
    user_video: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    try:
        if not client:
            raise HTTPException(status_code=500, detail="Gemini API key not configured")

        if sport not in SPORT_PROMPTS:
            raise HTTPException(status_code=400, detail="Unsupported sport")

        reference_path = SPORT_VIDEOS[sport]

        if not reference_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Reference video for {sport} not found"
            )

        print(f"Starting analysis for sport: {sport}")

        # Upload reference video
        print(f"Uploading reference video: {reference_path}")
        referenceFile = client.files.upload(path=str(reference_path))
        prompt = SPORT_PROMPTS[sport]

        # Save uploaded user video temporarily
        user_path = TEMP_UPLOADS_DIR / f"temp_{current_user.id}_{user_video.filename}"
        print(f"Saving user video to: {user_path}")
        with open(user_path, "wb") as f:
            f.write(await user_video.read())

        print(f"Uploading user video to Gemini")
        myfile = client.files.upload(path=str(user_path))

        # Wait for both files to be processed
        print("Waiting for files to be processed...")
        max_wait = 60  # Maximum 60 seconds wait time
        waited = 0
        while waited < max_wait:
            file_state_user = client.files.get(name=myfile.name)
            file_state_reference = client.files.get(name=referenceFile.name)

            if file_state_user.state == "ACTIVE" and file_state_reference.state == "ACTIVE":
                print("Both files are active")
                break
            elif file_state_user.state == "FAILED" or file_state_reference.state == "FAILED":
                # Get detailed error information
                user_error = getattr(file_state_user, 'error', 'Unknown error') if file_state_user.state == "FAILED" else None
                ref_error = getattr(file_state_reference, 'error', 'Unknown error') if file_state_reference.state == "FAILED" else None

                error_details = []
                if user_error:
                    error_details.append(f"Your video failed: {user_error}")
                if ref_error:
                    error_details.append(f"Reference video failed: {ref_error}")

                error_msg = " | ".join(error_details) if error_details else "File processing failed"

                # Add helpful message for user video failures
                if file_state_user.state == "FAILED":
                    error_msg += ". Try converting your video to MP4 format or reducing its size/length."

                print(f"File processing failed - User state: {file_state_user.state}, Reference state: {file_state_reference.state}")
                print(f"Error details: {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
            time.sleep(1)
            waited += 1

        if waited >= max_wait:
            raise HTTPException(status_code=500, detail="File processing timeout")

        # Generate analysis
        print("Generating analysis with Gemini...")

        # Create the content parts with file URIs
        from google.genai.types import Part

        contents = [
            prompt,
            Part.from_uri(file_uri=myfile.uri, mime_type=myfile.mime_type),
            Part.from_uri(file_uri=referenceFile.uri, mime_type=referenceFile.mime_type),
        ]

        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=contents,
        )

        print("Analysis complete!")

        # Clean up the temporary file
        try:
            os.remove(user_path)
            print(f"Cleaned up temp file: {user_path}")
        except Exception as e:
            print(f"Warning: Could not remove temp file {user_path}: {e}")

        return {"sport": sport, "analysis": response.text}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.get("/api/sports")
def get_sports():
    return {"sports": list(SPORT_PROMPTS.keys())}


@app.get("/")
def root():
    return {"message": "ShadowSync API"}
