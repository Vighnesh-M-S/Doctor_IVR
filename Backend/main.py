from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS Middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to the frontend's URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for input text
class TextInput(BaseModel):
    text: str

@app.post("/submit")
async def receive_text(data: TextInput):
    return {"message": f"You wrote: {data.text}"}
