import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import time

load_dotenv(dotenv_path=r"c:\\Users\\zarar\\projects\\APIKEY.env.txt")
api_key = os.getenv("API_KEY")
app = FastAPI()
client = genai.Client(api_key=api_key)

SPORT_PROMPTS = {
    "basketball": (
        "Describe the basketball shooting form compared to the player in the video on the Golden State Warriors "
        "with the number 30 jersey (Stephen Curry). Compare elements like guide hand, follow-through, shooting stance, "
        "footwork, release speed, and overall fluidity. Provide a similarity score (percentage) and highlight strengths, "
        "differences, and areas for improvement. If the uploaded video doesn’t depict a basketball shooting motion, reject it."
    ),

    "soccer": (
        "Analyze the soccer shooting or passing technique compared to a professional player’s form. "
        "Evaluate aspects such as body alignment, foot placement, follow-through, balance, and accuracy. "
        "Include comments on approach angle and timing. Provide a similarity score (percentage) and give feedback "
        "on how to improve the user’s shooting or passing technique." 
        "If the uploaded video does not show a soccer shooting or passing action, reject it."
    ),

    "boxing": (
        "Analyze the boxing technique compared to that of a professional boxer. Focus on stance, guard position, "
        "punch form (jab, cross, hook, uppercut), hip rotation, and defensive movements. "
        "Provide a similarity score (percentage) and explain where the user’s technique aligns with or differs from "
        "a professional’s form. Suggest targeted improvements for power, precision, and defense."
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
    "basketball": r"C:\\Users\\zarar\\projects\\stephShot - Made with Clipchamp.mp4",
    "soccer": r"C:\\Users\\zarar\\projects\\ronaldoKick.mp4",
    "boxing": r"C:\\Users\\zarar\\projects\\tysonUppercut.mp4",
    "golf": r"C:\\Users\\zarar\\projects\\tigerSwing.mp4"
}    


@app.post("/analyze-video/{sport}")
async def analyze_video(sport: str, user_video: UploadFile = File(...)):
    if sport not in SPORT_PROMPTS:
        raise HTTPException(status_code=400, detail="Unsupported sport.")
    reference_path = SPORT_VIDEOS[sport]
    referenceFile = client.files.upload(file=reference_path)
    prompt = SPORT_PROMPTS[sport]
    
    # Save uploaded user video temporarily
    user_path = f"temp_{user_video.filename}"
    with open(user_path, "wb") as f:
        f.write(await user_video.read())
    myfile = client.files.upload(file= user_path)
    print(myfile.state, referenceFile.state)
    while True:
        file_state_user = client.files.get(name=myfile.name)
        file_state_reference = client.files.get(name=referenceFile.name)

        if file_state_user.state == "ACTIVE" and file_state_reference.state == "ACTIVE":
            break
        elif file_state_user.state == "FAILED" or file_state_reference.state == "FAILED":
            raise RuntimeError(f"File processing failed: {file_state_user.error} {file_state_reference.error}")
        time.sleep(1)  # wait 1 second before checking again

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, myfile, referenceFile],
    )
    os.remove(user_path)  # Clean up the temporary file
    return JSONResponse(content={"sport": sport, "response": response.text})



