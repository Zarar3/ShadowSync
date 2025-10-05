
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import time

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

app = FastAPI()
client = genai.Client(api_key=api_key)

# Get the base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Define paths relative to the project root
REFERENCE_VIDEOS_DIR = BASE_DIR
TEMP_UPLOADS_DIR = BASE_DIR / "temp_uploads"

# Create directories if they don't exist
REFERENCE_VIDEOS_DIR.mkdir(exist_ok=True)
TEMP_UPLOADS_DIR.mkdir(exist_ok=True)

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
    ),

    "golf": (
        "Analyze the golf swing form compared to that of a professional golfer. Evaluate grip, stance, backswing, "
        "downswing, impact, and follow-through. Comment on balance, swing plane, tempo, and consistency. "
        "Provide a similarity score (percentage) and detailed suggestions for improving swing mechanics and accuracy. "
        "If the uploaded video does not show a golf swing, reject it."
    )
}

# Use relative paths for reference videos
SPORT_VIDEOS = {
    "basketball": REFERENCE_VIDEOS_DIR / "stephShot.mp4",
    "soccer": REFERENCE_VIDEOS_DIR / "ronaldoKick.mp4",
    "boxing": REFERENCE_VIDEOS_DIR / "tysonUppercut.mp4",
    "golf": REFERENCE_VIDEOS_DIR / "tigerSwing.mp4"
}


@app.post("/analyze-video/{sport}") 
async def analyze_video(sport: str, user_video: UploadFile = File(...)):
    if sport not in SPORT_PROMPTS:
        raise HTTPException(status_code=400, detail="Unsupported sport.")
    
    reference_path = SPORT_VIDEOS[sport]
    
    # Check if reference video exists
    if not reference_path.exists():
        raise HTTPException(
            status_code=500, 
            detail=f"Reference video for {sport} not found. Please ensure {reference_path.name} is in the reference_videos directory."
        )
    
    # Upload reference video
    referenceFile = client.files.upload(file=str(reference_path))
    prompt = SPORT_PROMPTS[sport]
    
    # Save uploaded user video temporarily
    user_path = TEMP_UPLOADS_DIR / f"temp_{user_video.filename}"
    with open(user_path, "wb") as f:
        f.write(await user_video.read())
    
    myfile = client.files.upload(file=str(user_path))
    print(f"User file state: {myfile.state}, Reference file state: {referenceFile.state}")
    
    # Wait for both files to be processed
    while True:
        file_state_user = client.files.get(name=myfile.name)
        file_state_reference = client.files.get(name=referenceFile.name)

        if file_state_user.state == "ACTIVE" and file_state_reference.state == "ACTIVE":
            break
        elif file_state_user.state == "FAILED" or file_state_reference.state == "FAILED":
            raise RuntimeError(
                f"File processing failed: User={file_state_user.error}, Reference={file_state_reference.error}"
            )
        time.sleep(1)

    # Generate analysis
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, myfile, referenceFile],
    )
    
    # Clean up the temporary file
    try:
        os.remove(user_path)
    except Exception as e:
        print(f"Warning: Could not remove temp file {user_path}: {e}")
    
    return JSONResponse(content={"sport": sport, "response": response.text})