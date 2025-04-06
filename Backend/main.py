from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Query
from fastapi.responses import Response, JSONResponse, HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
import uvicorn
import time
import urllib.parse
from google.genai import types
from fastapi import APIRouter
from memory import call_logs
from datetime import datetime

conversation_store = {}

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
    "1": ["Doctor. Kumar", "Doctor. Patel"],
    "2": ["Doctor. Ramesh", "Doctor. Suresh"],
    "3": ["Doctor. Maya", "Doctor. Neha"]
}

call_logs = {
    "session_1": ["User called", "Asked about appointment", "System replied with available slots"],
    "session_2": ["User called", "Asked about pregnancy tips", "System replied with advice"],
}

def log_step(call_sid: str, message: str):
    if call_sid not in call_logs:
        call_logs[call_sid] = []
    call_logs[call_sid].append(message)

app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def serve_home():
    return FileResponse(os.path.join("Backend/Template", "index.html"))

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
    call_sid = form_data.get("CallSid")
    log_step(call_sid, "User called and reached main menu")

    response = VoiceResponse()

    if digit_pressed == "1":
        log_step(call_sid, "User chose to book an appointment")
        gather = Gather(num_digits=1, action="/select-department", timeout=5)
        gather.say("Press 1 for Obstetrics and Gynecology . Press 2 for Midwifery Department. Press 3 for Radiology/Imaging Department.")
        response.append(gather)
    
    elif digit_pressed == "2":
        log_step(call_sid, "User chose to state a health concern")
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
    call_sid = form_data.get("CallSid")
    # log_step(call_sid, f"User selected department {dept_selected}")
    if dept_selected == "1":
        log_step(call_sid, f"User selected department Obstetrics and Gynecology")
    elif dept_selected == "2":
        log_step(call_sid, f"User selected department Midwifery")
    else:
        log_step(call_sid, f"User selected department Radiology/Imaging")


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
    call_sid = form_data.get("CallSid")
    # log_step(call_sid, f"Appointment booked with {doctor_name}")

    response = VoiceResponse()

    if dept in DOCTORS_DB:
        doctors = DOCTORS_DB[dept]

        try:
            doctor_index = int(doctor_index) - 1  # Convert to zero-based index
            if 0 <= doctor_index < len(doctors):
                doctor_name = doctors[doctor_index]
                log_step(call_sid, f"Appointment booked with {doctor_name}")
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
    form_data = await request.form()
    recording_url = form_data.get("RecordingUrl")
    audio_path = "twilio_recording.wav"
    call_sid = form_data.get("CallSid")


    if not recording_url:
        return {"detail": "Recording URL is missing."}

    print(f"[DEBUG] Received recording URL: {recording_url}")

    success = False
    for attempt in range(3):
        try:
            print(f"[DEBUG] Attempt {attempt+1}: Trying to download audio...")
            response = requests.get(recording_url, stream=True)
            if response.status_code == 200:
                with open(audio_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[DEBUG] Audio downloaded successfully to {audio_path}")
                success = True
                break
            else:
                print(f"[DEBUG] Received status {response.status_code} from Twilio")
        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] Error on attempt {attempt+1}: {str(e)}")

        time.sleep(2)

    if not success:
        return {"detail": "Error downloading audio: Recording URL not available after retries."}

    result = model.transcribe(audio_path)
    transcribed_text = result["text"].strip()
    print(f"[DEBUG] Transcribed text: {transcribed_text}")
    log_step(call_sid, f"User said: {transcribed_text}")

    # ✅ Encode text for URL
    encoded_text = urllib.parse.quote(transcribed_text)

    twilio_response = VoiceResponse()
    gather = twilio_response.gather(
        num_digits=1,
        action=f"/confirm-input?query={encoded_text}",
        method="POST"
    )
    gather.say(f"You said: {transcribed_text}. If this is correct, press 1. Otherwise, press 2 to re-record.")

    return Response(content=str(twilio_response), media_type="application/xml")

def get_gemini_response(prompt: str) -> str:
    system_instruction = (
        "You are a helpful assistant responding to women's health concerns, especially related to pregnancy. "
        "Your reply should be short, clear, and easy to understand. Avoid using complex medical terms. "
        "Use simple language and a supportive tone."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            contents=prompt
        )
        return response.text if hasattr(response, "text") else "Sorry, I couldn't understand that."

    except Exception as e:
        return f"An error occurred: {e}"


@app.post("/confirm-input")
async def confirm_input(request: Request, query: str = Query(default="")):
    form_data = await request.form()
    digit = form_data.get("Digits")
    call_sid = form_data.get("CallSid")
    response = VoiceResponse()

    if digit == "1":
        user_query = urllib.parse.unquote(query)
        if not user_query:
            response.say("Sorry, your request could not be found.")
            return Response(content=str(response), media_type="application/xml")

        gemini_reply = get_gemini_response(user_query)
        conversation_store[call_sid] = gemini_reply
        log_step(call_sid, f"Gemini replied: {gemini_reply}")

        response.say(gemini_reply)

        gather = response.gather(num_digits=1, action="/next-action", method="POST")
        gather.say("Press 1 to repeat. Press 2 to ask a follow-up. Press 3 to end the conversation.")

    elif digit == "2":
        response.say("Please state your concern again after the beep.")
        response.record(action="/process-audio", method="POST", play_beep=True, timeout=10)

    else:
        response.say("Invalid input. Redirecting.")
        response.redirect("/process-audio")

    return Response(content=str(response), media_type="application/xml")

@app.post("/next-action")
async def next_action(request: Request):
    form_data = await request.form()
    digit = form_data.get("Digits")
    call_sid = form_data.get("CallSid")
    response = VoiceResponse()

    if digit == "1":
        reply = conversation_store.get(call_sid, "Sorry, nothing to repeat.")
        response.say(reply)
        response.redirect("/confirm-input")  # This can be adapted to keep context if needed

    elif digit == "2":
        response.say("Please state your follow-up after the beep.")
        response.record(action="/process-audio", method="POST", play_beep=True, timeout=10)

    elif digit == "3":
        response.say("Thank you for calling. Goodbye!")

    else:
        response.say("Invalid choice. Let's try again.")
        response.redirect("/confirm-input")

    return Response(content=str(response), media_type="application/xml")

# In-memory store
# call_logs = {}

# Example of how you might add logs
# def log_call(sid: str, transcription: str, gemini_response: str, booked_specialization: str = None):
#     entry = {
#         "timestamp": datetime.utcnow().isoformat(),
#         "transcription": transcription,
#         "gemini_response": gemini_response,
#         "booked_specialization": booked_specialization
#     }
#     call_logs.setdefault(sid, []).append(entry)

@app.get("/logs")
def get_call_logs():
    return JSONResponse(content=call_logs)

# Shutdown event
# @app.on_event("shutdown")
# def shutdown_event():
#     client.close()

@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down FastAPI app.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)