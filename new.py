from fastapi import FastAPI
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")  # +1 712 227 5136
INDIA_PHONE_NUMBER = "+919480984031"  # Replace with your Indian phone number

twilio_client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

@app.get("/make-call")
def make_call():
    """Make an outbound call to an Indian number."""
    call = twilio_client.calls.create(
        to=INDIA_PHONE_NUMBER, 
        from_=TWILIO_PHONE_NUMBER,
        url="https://ac80-122-252-228-30.ngrok-free.app/ivr"  # Your IVR webhook
    )
    return {"status": "Call initiated", "call_sid": call.sid}
