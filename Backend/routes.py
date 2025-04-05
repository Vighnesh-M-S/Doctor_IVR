# backend/routes.py
from memory import call_logs
from datetime import datetime

def log_interaction(call_sid, transcription, gemini_response, booked_specialization=None):
    if call_sid not in call_logs:
        call_logs[call_sid] = []

    call_logs[call_sid].append({
        "timestamp": datetime.utcnow().isoformat(),
        "transcription": transcription,
        "gemini_response": gemini_response,
        "booked_specialization": booked_specialization,
    })
