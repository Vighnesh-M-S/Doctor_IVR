from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import whisper
from google import genai
from dotenv import load_dotenv
import os



model = whisper.load_model("base")
load_dotenv() 
api_key2 = os.getenv("API_KEY")
client = genai.Client(api_key=api_key2)
app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# New endpoint for audio upload
@app.post("/submit-audio")
async def receive_audio(audio: UploadFile = File(...)):
    # Save the file temporarily (optional)
    out_file_path = f"temp_audio_{audio.filename}"
    
    async with aiofiles.open(out_file_path, 'wb') as out_file:
        content = await audio.read()  # Read the file content
        await out_file.write(content)  # Write to disk
    
    result = model.transcribe(out_file_path)
    transcribed_text = result["text"]

     # Generate response using Gemini API
    # gemini_model = genai.GenerativeModel("gemini-pro")
    # response = gemini_model.generate_content(f"""
    # A patient reports these ENT symptoms:\n{transcribed_text}
    # Based on these symptoms, ask the patient a relevant follow-up question to narrow down possible causes.
    # """)
    response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=f"""
    A patient reports these ENT symptoms:\n{transcribed_text}
    Based on these symptoms, ask the patient a relevant follow-up question to narrow down possible causes.
    """,
)

    # Cleanup temp file
    # os.remove(out_file_path)

    return {
        "message": transcribed_text + response.text,
        "gemini_reply": response.text if response.text else "No response generated",
    }


