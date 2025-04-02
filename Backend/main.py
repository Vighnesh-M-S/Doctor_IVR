from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse
import requests
import base64
from twilio.rest import Client
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

#google client
client = genai.Client(api_key=api_key2)

twilio_sid = os.getenv("TWILIO_SID")
twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
INDIA_PHONE_NUMBER = "+918088012208"

#twilio client
twilio_client = Client(twilio_sid, twilio_auth_token)

app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/make-call")
def make_call():
    """Make an outbound call to an Indian number."""
    call = twilio_client.calls.create(
        to=INDIA_PHONE_NUMBER, 
        from_=twilio_phone_number,
        url="https://257c-122-252-228-30.ngrok-free.app/ivr"  # Your IVR webhook
    )
    return {"status": "Call initiated", "call_sid": call.sid}


@app.post("/ivr")
async def ivr_response():
    """Handle incoming IVR call and provide response."""
    response = VoiceResponse()

    response.say("Welcome to the AI-powered IVR. Please state your symptoms after the beep.")
    response.record(action="/process-audio", method="POST", play_beep=True, timeout=10)
    
    # Fallback in case no input is received
    # response.say("Sorry, we didn't hear anything.")
    # response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

@app.post("/process-audio")
async def process_audio(request: Request):
    """Download Twilio audio, transcribe it, and generate a response."""
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl")
    recording_sid = form_data.get("RecordingSid")

    if not recording_url or not recording_sid:
        return {"detail": "Recording URL or SID missing."}

    # Ensure URL has proper format
    if not recording_url.endswith(".wav"):
        recording_url += ".wav"
    
    # Fetch recording metadata (optional but recommended)
    metadata_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Recordings/{recording_sid}.json"
    auth = (twilio_sid, twilio_auth_token)
    
    try:
        metadata_response = requests.get(metadata_url, auth=auth)
        metadata_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"detail": f"Failed to fetch recording metadata: {str(e)}"}
    
    # Download the audio file from Twilio
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{twilio_sid}:{twilio_auth_token}'.encode()).decode()}",
        "Accept": "audio/wav"
    }

    try:
        audio_response = requests.get(recording_url, headers=headers)
        audio_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"detail": f"Failed to download audio from Twilio: {str(e)}"}
    
    # Save the audio file locally
    audio_path = "twilio_recording.wav"
    with open(audio_path, "wb") as audio_file:
        audio_file.write(audio_response.content)
    
    # Transcribe the audio using Whisper
    result = model.transcribe(audio_path)
    transcribed_text = result["text"]
    print(f"Transcribed text: {transcribed_text}")

    # Generate IVR response
    twilio_response = VoiceResponse()
    twilio_response.say(f"You said: {transcribed_text}. Thank you!")
    
    return Response(content=str(twilio_response), media_type="application/xml")
