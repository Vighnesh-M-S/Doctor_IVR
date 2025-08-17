# IVR Doctor Consultation System

## Overview
This project is an AI-powered IVR (Interactive Voice Response) system designed to help women in both remote and urban areas access doctor consultations and book appointments. By integrating voice input, language models, and backend processing, the system enables natural and efficient communication for medical assistance.

## Features
- Voice-based interaction via Twilio IVR.
- AI-generated responses using Google's Gemini.
- Doctor appointment booking functionality.
- Query logging and persistent session handling.
- Deployment-ready with Google Cloud (Cloud Run + Cloud SQL).

## Tech Stack
- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript
- **AI Integration**: Google Gemini API, Whisper(OpenAI)
- **Telephony**: Twilio
- **Database**: PostgreSQL (Cloud SQL)
- **Deployment**: Docker, Google Cloud Run

## Getting Started
1. Clone the repo.
2. Set environment variables in a `.env` file.
3. Run the backend with Docker or directly with `uvicorn`.
4. Configure Twilio to point to your public backend URL (e.g., via ngrok or GCP).
