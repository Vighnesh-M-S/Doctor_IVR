import whisper

model = whisper.load_model("base")  # Use "small", "medium", or "large" for better accuracy
result = model.transcribe("Backend/temp_audio_recording.wav")
print(result["text"])