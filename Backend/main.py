from fastapi import FastAPI, UploadFile, File, Form, HTTPException
# from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import aiofiles
import whisper
import os

model = whisper.load_model("base")
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
    
    result = model.transcribe(out_file_path )
    return {
        "message": result["text"],
        "filename": audio.filename,
        "content_type": audio.content_type,
        "size": f"{len(content) / 1024:.2f} KB"
    }


