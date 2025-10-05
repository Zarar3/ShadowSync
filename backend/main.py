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
        "IMPORTANT: First, verify that the user's video shows a BASKETBALL SHOOTING motion. If the video shows any completely "
        "unrelated activity (dancing, walking, other sports, random movements, etc.), respond ONLY with: "
        "'REJECTED: This video does not show a basketball shooting motion. Please upload a video of yourself performing a basketball shot.' "
        "and provide no further analysis.\n\n"
        "If the video DOES show a basketball shooting motion (even without a ball or hoop), proceed with analysis:\n"
        "Analyze the basketball shooting FORM and TECHNIQUE compared to Stephen Curry in the reference video. "
        "FOCUS ONLY ON FORM - ignore equipment, ball presence, or environment. Even if shooting without a ball or hoop, "
        "analyze the shooting motion itself. Compare: guide hand position, follow-through mechanics, shooting stance, "
        "footwork, elbow alignment, release motion, and overall fluidity. Provide a SIMILARITY SCORE (percentage) clearly stated, "
        "highlight strengths, differences, and specific areas for improvement in their form."
    ),
    "soccer": (
        "IMPORTANT: First, verify that the user's video shows a SOCCER KICKING/PASSING motion. If the video shows any completely "
        "unrelated activity (dancing, walking, other sports, random movements, etc.), respond ONLY with: "
        "'REJECTED: This video does not show a soccer kicking motion. Please upload a video of yourself performing a soccer kick or pass.' "
        "and provide no further analysis.\n\n"
        "If the video DOES show a soccer kicking/passing motion (even without a ball), proceed with analysis:\n"
        "Analyze the soccer kicking FORM and TECHNIQUE compared to the professional player in the reference video. "
        "FOCUS ONLY ON FORM - ignore ball presence, field, or equipment. Even if kicking without a ball, analyze the kicking motion. "
        "Evaluate: body alignment, plant foot placement, kicking leg mechanics, follow-through, balance, hip rotation, and approach angle. "
        "Provide a SIMILARITY SCORE (percentage) clearly stated and give feedback on how to improve their kicking form."
    ),
    "boxing": (
        "IMPORTANT: First, verify that the user's video shows a BOXING PUNCHING motion (jab, cross, hook, or uppercut). If the video shows any completely "
        "unrelated activity (dancing, walking, other sports, random movements, etc.), respond ONLY with: "
        "'REJECTED: This video does not show a boxing punch. Please upload a video of yourself performing a boxing punch (jab, cross, hook, or uppercut).' "
        "and provide no further analysis.\n\n"
        "If the video DOES show a boxing punching motion (even without gloves or equipment), proceed with analysis:\n"
        "Analyze the boxing punch FORM and TECHNIQUE compared to the professional boxer in the reference video. "
        "FOCUS ONLY ON FORM - ignore gloves, bag, or equipment. Even if punching air, analyze the punch mechanics. "
        "Evaluate: stance, guard position, punch form (jab, cross, hook, uppercut), hip rotation, shoulder turn, weight transfer, "
        "and defensive positioning. Provide a SIMILARITY SCORE (percentage) clearly stated and explain where the technique aligns "
        "or differs from professional form. Suggest targeted improvements for better mechanics, power generation, and form."
    ),
    "golf": (
        "IMPORTANT: First, verify that the user's video shows a GOLF SWING motion. If the video shows any completely "
        "unrelated activity (dancing, walking, other sports, random movements, etc.), respond ONLY with: "
        "'REJECTED: This video does not show a golf swing. Please upload a video of yourself performing a golf swing.' "
        "and provide no further analysis.\n\n"
        "If the video DOES show a golf swing motion (even without a club or ball), proceed with analysis:\n"
        "Analyze the golf swing FORM and TECHNIQUE compared to the professional golfer in the reference video. "
        "FOCUS ONLY ON FORM - ignore club, ball, or environment. Even if swinging without equipment, analyze the swing motion. "
        "Evaluate: grip position, stance, posture, backswing mechanics, downswing path, hip rotation, shoulder turn, weight transfer, "
        "and follow-through. Comment on balance, swing plane, tempo, and consistency. Provide a SIMILARITY SCORE (percentage) clearly stated "
        "and detailed suggestions for improving swing mechanics."
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
