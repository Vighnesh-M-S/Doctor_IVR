from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import requests
import base64
from twilio.rest import Client
# from pydantic import BaseModel
from requests.auth import HTTPBasicAuth
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

# Doctor database (for demo purposes)
DOCTORS_DB = {
    "1": ["Doctor. Smith - Cardiologist", "Doctor. Patel - Cardiologist"],
    "2": ["Doctor. Khan - Dermatologist", "Doctor. Lee - Dermatologist"],
    "3": ["Doctor. Davis - Orthopedic", "Doctor. Mehta - Orthopedic"]
}

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
    """Initial IVR menu"""
    response = VoiceResponse()
    
    gather = Gather(num_digits=1, action="/menu-selection", timeout=5)
    gather.say("Press 1 to book an appointment. Press 2 to state your health concern.")
    response.append(gather)

    response.say("No input received. Redirecting to the main menu.")
    response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

@app.post("/menu-selection")
async def menu_selection(request: Request):
    """Handles user menu selection"""
    form_data = await request.form()
    digit_pressed = form_data.get("Digits")

    response = VoiceResponse()

    if digit_pressed == "1":
        gather = Gather(num_digits=1, action="/select-department", timeout=5)
        gather.say("Press 1 for Cardiology. Press 2 for Dermatology. Press 3 for Orthopedic.")
        response.append(gather)
    
    elif digit_pressed == "2":
        response.say("Please state your concern after the beep.")
        response.record(action="/process-audio", method="POST", play_beep=True, timeout=10)

    else:
        response.say("Invalid choice. Redirecting to the main menu.")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

@app.post("/select-department")
async def select_department(request: Request):
    """Handles department selection"""
    form_data = await request.form()
    dept_selected = form_data.get("Digits")

    response = VoiceResponse()

    if dept_selected in DOCTORS_DB:
        doctors = DOCTORS_DB[dept_selected]
        gather = Gather(num_digits=1, action=f"/book-appointment?dept={dept_selected}", timeout=5)
        
        for i, doctor in enumerate(doctors, start=1):
            gather.say(f"Press {i} for {doctor}.")
        
        response.append(gather)
    else:
        response.say("Invalid selection. Redirecting to main menu.")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")


@app.post("/book-appointment")
async def book_appointment(request: Request, dept: str):
    """Handles appointment booking"""
    form_data = await request.form()
    doctor_index = form_data.get("Digits")

    response = VoiceResponse()

    if dept in DOCTORS_DB:
        doctors = DOCTORS_DB[dept]

        try:
            doctor_index = int(doctor_index) - 1  # Convert to zero-based index
            if 0 <= doctor_index < len(doctors):
                doctor_name = doctors[doctor_index]
                response.say(f"Your appointment with {doctor_name} has been booked. Thank you!")
            else:
                response.say("Invalid selection. Redirecting to main menu.")
                response.redirect("/ivr")
        except ValueError:
            response.say("Invalid input. Redirecting to main menu.")
            response.redirect("/ivr")
    else:
        response.say("Invalid department selection. Redirecting to main menu.")
        response.redirect("/ivr")

    return Response(content=str(response), media_type="application/xml")

@app.post("/process-audio")
async def process_audio(request: Request):
    """Download Twilio audio, transcribe it, and generate a response."""
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl")
    audio_path = "twilio_recording.wav"

    if not recording_url:
        return {"detail": "Recording URL is missing."}

    try:
        response = requests.get(recording_url, stream=True)
        response.raise_for_status()

        with open(audio_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"Audio downloaded successfully to {audio_path}")

    except requests.exceptions.RequestException as e:
        return {"detail": f"Error downloading audio: {str(e)}"}
    except Exception as e:
        return {"detail": f"An unexpected error occurred: {str(e)}"}

    # Transcribe using Whisper
    result = model.transcribe(audio_path)
    transcribed_text = result["text"]
    print(f"Transcribed text: {transcribed_text}")

    # Respond with confirmation
    twilio_response = VoiceResponse()
    twilio_response.say(f"You said: {transcribed_text}. If this is correct, press 1. Otherwise, press 2 to re-record.")
    
    gather = twilio_response.gather(num_digits=1, action="/confirm-input", method="POST")
    twilio_response.append(gather)  # Attach the gather input to the response

    return Response(content=str(twilio_response), media_type="application/xml")

@app.post("/confirm-input")
async def confirm_input(request: Request):
    """Handle user confirmation of transcribed text."""
    form_data = await request.form()
    digit = form_data.get("Digits")
    response = VoiceResponse()
    
    if digit == "1":
        response.say("Thank you! Your input has been recorded.")
    elif digit == "2":
        response.say("Please state your concern again after the beep.")
        response.record(action="/process-audio", method="POST", play_beep=True, timeout=10)
    else:
        response.say("Invalid selection. Please try again.")
        response.redirect("/process-audio")
    
    return Response(content=str(response), media_type="application/xml")